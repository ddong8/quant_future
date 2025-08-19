"""
风险监控 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import logging

from ...services.risk_service import risk_service as risk_monitoring_service
from ...core.dependencies import get_current_user
from ...models import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/metrics")
async def get_risk_metrics(
    current_user: User = Depends(get_current_user)
):
    """获取实时风险指标"""
    try:
        user_id = str(current_user.id) if hasattr(current_user, 'id') else "default"
        
        result = await risk_monitoring_service.calculate_real_time_risk_metrics(user_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "message": "获取风险指标成功"
        }
        
    except Exception as e:
        logger.error(f"获取风险指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def get_risk_report(
    days: int = Query(7, description="报告天数"),
    current_user: User = Depends(get_current_user)
):
    """获取风险报告"""
    try:
        user_id = str(current_user.id) if hasattr(current_user, 'id') else "default"
        
        result = await risk_monitoring_service.get_risk_report(user_id, days)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "message": "获取风险报告成功"
        }
        
    except Exception as e:
        logger.error(f"获取风险报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/start")
async def start_risk_monitoring(
    interval: int = Query(30, description="监控间隔(秒)"),
    current_user: User = Depends(get_current_user)
):
    """启动风险监控"""
    try:
        user_id = str(current_user.id) if hasattr(current_user, 'id') else "default"
        
        # 启动监控（异步任务）
        import asyncio
        asyncio.create_task(risk_monitoring_service.start_monitoring(user_id, interval))
        
        return {
            "success": True,
            "message": f"风险监控已启动，监控间隔: {interval}秒"
        }
        
    except Exception as e:
        logger.error(f"启动风险监控失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/stop")
async def stop_risk_monitoring(
    current_user: User = Depends(get_current_user)
):
    """停止风险监控"""
    try:
        await risk_monitoring_service.stop_monitoring()
        
        return {
            "success": True,
            "message": "风险监控已停止"
        }
        
    except Exception as e:
        logger.error(f"停止风险监控失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_risk_alerts(
    current_user: User = Depends(get_current_user)
):
    """获取风险预警"""
    try:
        user_id = str(current_user.id) if hasattr(current_user, 'id') else "default"
        
        # 获取当前风险指标中的预警信息
        risk_metrics = await risk_monitoring_service.calculate_real_time_risk_metrics(user_id)
        alerts = risk_metrics.get("risk_alerts", [])
        
        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "alert_count": len(alerts),
                "critical_count": len([a for a in alerts if a.get("type") == "CRITICAL"]),
                "warning_count": len([a for a in alerts if a.get("type") == "WARNING"]),
                "timestamp": risk_metrics.get("timestamp")
            },
            "message": f"获取到 {len(alerts)} 个风险预警"
        }
        
    except Exception as e:
        logger.error(f"获取风险预警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))