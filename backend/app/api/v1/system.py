"""
系统管理API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...core.response import success_response, error_response
from ...models import User
from ...services.scheduler_service import scheduler_service
from ...services.anomaly_detection_service import AnomalyDetectionService

router = APIRouter()


@router.get("/health")
async def system_health():
    """系统健康检查"""
    try:
        # 检查数据库连接
        db = next(get_db())
        try:
            db.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        finally:
            db.close()
        
        # 检查调度器状态
        scheduler_status = scheduler_service.get_job_status()
        
        # 检查系统资源
        import psutil
        system_resources = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
        
        health_status = {
            "status": "healthy" if db_status == "healthy" else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
            "scheduler": scheduler_status,
            "system_resources": system_resources
        }
        
        return success_response(data=health_status)
        
    except Exception as e:
        return error_response(message=f"系统健康检查失败: {str(e)}")


@router.get("/scheduler/status")
async def get_scheduler_status(
    current_user: User = Depends(get_current_user)
):
    """获取调度器状态"""
    try:
        # 检查用户权限（只有管理员可以查看）
        if current_user.role != "admin":
            return error_response(message="权限不足", status_code=403)
        
        status = scheduler_service.get_job_status()
        return success_response(data=status)
        
    except Exception as e:
        return error_response(message=f"获取调度器状态失败: {str(e)}")


@router.post("/scheduler/start")
async def start_scheduler(
    current_user: User = Depends(get_current_user)
):
    """启动调度器"""
    try:
        # 检查用户权限
        if current_user.role != "admin":
            return error_response(message="权限不足", status_code=403)
        
        await scheduler_service.start()
        return success_response(message="调度器启动成功")
        
    except Exception as e:
        return error_response(message=f"启动调度器失败: {str(e)}")


@router.post("/scheduler/stop")
async def stop_scheduler(
    current_user: User = Depends(get_current_user)
):
    """停止调度器"""
    try:
        # 检查用户权限
        if current_user.role != "admin":
            return error_response(message="权限不足", status_code=403)
        
        await scheduler_service.stop()
        return success_response(message="调度器停止成功")
        
    except Exception as e:
        return error_response(message=f"停止调度器失败: {str(e)}")


@router.post("/anomaly-detection/run")
async def run_anomaly_detection(
    user_id: Optional[int] = Query(None, description="指定用户ID，不指定则检测所有用户"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手动运行异常检测"""
    try:
        # 检查用户权限
        if current_user.role != "admin":
            return error_response(message="权限不足", status_code=403)
        
        anomaly_service = AnomalyDetectionService(db)
        alerts = await anomaly_service.run_anomaly_detection(user_id)
        
        return success_response(
            data={
                "alerts_count": len(alerts),
                "alerts": [
                    {
                        "anomaly_type": alert.anomaly_type.value,
                        "severity": alert.severity,
                        "title": alert.title,
                        "description": alert.description,
                        "user_id": alert.user_id,
                        "detected_at": alert.detected_at.isoformat()
                    }
                    for alert in alerts
                ]
            },
            message=f"异常检测完成，发现 {len(alerts)} 个异常"
        )
        
    except Exception as e:
        return error_response(message=f"运行异常检测失败: {str(e)}")


@router.get("/statistics")
async def get_system_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统统计信息"""
    try:
        # 检查用户权限
        if current_user.role != "admin":
            return error_response(message="权限不足", status_code=403)
        
        from ...models import User, TradingAccount, Order, Position
        
        # 基础统计
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        total_accounts = db.query(TradingAccount).count()
        active_accounts = db.query(TradingAccount).filter(TradingAccount.is_active == True).count()
        
        # 今日统计
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_orders = db.query(Order).filter(Order.created_at >= today_start).count()
        
        # 订单状态统计
        from ...models.enums import OrderStatus
        order_stats = {}
        for status in OrderStatus:
            count = db.query(Order).filter(Order.status == status).count()
            order_stats[status.value] = count
        
        # 持仓统计
        total_positions = db.query(Position).filter(Position.quantity != 0).count()
        
        statistics = {
            "users": {
                "total": total_users,
                "active": active_users
            },
            "accounts": {
                "total": total_accounts,
                "active": active_accounts
            },
            "orders": {
                "total": db.query(Order).count(),
                "today": today_orders,
                "by_status": order_stats
            },
            "positions": {
                "total": total_positions
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return success_response(data=statistics)
        
    except Exception as e:
        return error_response(message=f"获取系统统计失败: {str(e)}")


@router.get("/logs")
async def get_system_logs(
    level: str = Query("INFO", description="日志级别"),
    limit: int = Query(100, description="返回条数"),
    current_user: User = Depends(get_current_user)
):
    """获取系统日志"""
    try:
        # 检查用户权限
        if current_user.role != "admin":
            return error_response(message="权限不足", status_code=403)
        
        # 这里应该实现从日志文件或日志数据库中读取日志
        # 简化实现：返回模拟日志数据
        logs = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "系统正常运行",
                "module": "system"
            }
        ]
        
        return success_response(data=logs)
        
    except Exception as e:
        return error_response(message=f"获取系统日志失败: {str(e)}")


@router.post("/maintenance/start")
async def start_maintenance_mode(
    current_user: User = Depends(get_current_user)
):
    """启动维护模式"""
    try:
        # 检查用户权限
        if current_user.role != "admin":
            return error_response(message="权限不足", status_code=403)
        
        # 这里应该实现维护模式逻辑
        # 例如：停止接受新订单、暂停交易等
        
        return success_response(message="维护模式已启动")
        
    except Exception as e:
        return error_response(message=f"启动维护模式失败: {str(e)}")


@router.post("/maintenance/stop")
async def stop_maintenance_mode(
    current_user: User = Depends(get_current_user)
):
    """停止维护模式"""
    try:
        # 检查用户权限
        if current_user.role != "admin":
            return error_response(message="权限不足", status_code=403)
        
        # 这里应该实现停止维护模式逻辑
        
        return success_response(message="维护模式已停止")
        
    except Exception as e:
        return error_response(message=f"停止维护模式失败: {str(e)}")


@router.get("/performance")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user)
):
    """获取性能指标"""
    try:
        # 检查用户权限
        if current_user.role != "admin":
            return error_response(message="权限不足", status_code=403)
        
        import psutil
        import time
        
        # 系统资源使用情况
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 网络统计
        network = psutil.net_io_counters()
        
        # 进程信息
        process = psutil.Process()
        process_memory = process.memory_info()
        
        performance_metrics = {
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            },
            "process": {
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return success_response(data=performance_metrics)
        
    except Exception as e:
        return error_response(message=f"获取性能指标失败: {str(e)}")