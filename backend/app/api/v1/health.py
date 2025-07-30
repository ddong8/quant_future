"""
健康检查 API 端点
提供全面的系统健康检查功能
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import asyncio

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models import User
from ...services.health_check_service import health_checker
from ...core.response import success_response, error_response

router = APIRouter(prefix="/health", tags=["健康检查"])


@router.get("/")
async def basic_health_check():
    """基础健康检查"""
    try:
        # 执行快速的基础检查
        pg_check = await health_checker.check_postgresql_health()
        
        return {
            "status": "healthy" if pg_check["status"] in ["healthy", "warning"] else "unhealthy",
            "timestamp": pg_check["timestamp"],
            "service": "trading-platform",
            "version": "0.1.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }


@router.get("/detailed")
async def detailed_health_check(
    current_user: User = Depends(get_current_user)
):
    """详细健康检查（需要认证）"""
    try:
        health_result = await health_checker.perform_comprehensive_health_check()
        return success_response(data=health_result)
    except Exception as e:
        return error_response(message=f"健康检查失败: {str(e)}")


@router.get("/database")
async def database_health_check(
    current_user: User = Depends(get_current_user)
):
    """数据库健康检查"""
    try:
        checks = await asyncio.gather(
            health_checker.check_postgresql_health(),
            health_checker.check_influxdb_health(),
            health_checker.check_redis_health(),
            return_exceptions=True
        )
        
        results = {}
        for check in checks:
            if isinstance(check, Exception):
                continue
            results[check["service"]] = check
        
        overall_status = "healthy"
        for check in results.values():
            if check["status"] == "critical":
                overall_status = "critical"
                break
            elif check["status"] == "warning" and overall_status == "healthy":
                overall_status = "warning"
        
        return success_response(data={
            "overall_status": overall_status,
            "databases": results
        })
    except Exception as e:
        return error_response(message=f"数据库健康检查失败: {str(e)}")


@router.get("/initialization")
async def initialization_status_check(
    current_user: User = Depends(get_current_user)
):
    """数据库初始化状态检查"""
    try:
        init_status = await health_checker.check_database_initialization_status()
        return success_response(data=init_status)
    except Exception as e:
        return error_response(message=f"初始化状态检查失败: {str(e)}")


@router.get("/readiness")
async def readiness_check():
    """就绪检查（用于容器编排）"""
    try:
        # 检查关键服务是否就绪
        pg_check = await health_checker.check_postgresql_health()
        init_check = await health_checker.check_database_initialization_status()
        
        # 数据库连接正常且初始化完成才算就绪
        is_ready = (
            pg_check["status"] in ["healthy", "warning"] and
            init_check.get("initialization_complete", False)
        )
        
        status_code = 200 if is_ready else 503
        
        return {
            "ready": is_ready,
            "timestamp": pg_check["timestamp"],
            "checks": {
                "database": pg_check["status"],
                "initialization": init_check["status"]
            }
        }
    except Exception as e:
        return {
            "ready": False,
            "error": str(e),
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }


@router.get("/liveness")
async def liveness_check():
    """存活检查（用于容器编排）"""
    try:
        # 简单的存活检查，只要应用能响应就算存活
        return {
            "alive": True,
            "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
            "service": "trading-platform"
        }
    except Exception as e:
        return {
            "alive": False,
            "error": str(e),
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }


@router.post("/wait-for-ready")
async def wait_for_ready(
    max_wait_time: int = Query(60, description="最大等待时间（秒）"),
    current_user: User = Depends(get_current_user)
):
    """等待系统就绪"""
    try:
        is_ready = await health_checker.wait_for_database_ready(max_wait_time)
        
        if is_ready:
            return success_response(
                data={"ready": True, "wait_time": max_wait_time},
                message="系统已就绪"
            )
        else:
            return error_response(
                message=f"系统在 {max_wait_time} 秒内未就绪",
                status_code=408
            )
    except Exception as e:
        return error_response(message=f"等待就绪检查失败: {str(e)}")


@router.get("/summary")
async def health_summary(
    time_window: int = Query(5, description="时间窗口（分钟）"),
    current_user: User = Depends(get_current_user)
):
    """健康检查摘要"""
    try:
        summary = health_checker.get_health_check_summary(time_window)
        return success_response(data=summary)
    except Exception as e:
        return error_response(message=f"获取健康检查摘要失败: {str(e)}")


@router.get("/services/{service_name}")
async def service_health_check(
    service_name: str,
    current_user: User = Depends(get_current_user)
):
    """特定服务健康检查"""
    try:
        if service_name == "postgresql":
            result = await health_checker.check_postgresql_health()
        elif service_name == "influxdb":
            result = await health_checker.check_influxdb_health()
        elif service_name == "redis":
            result = await health_checker.check_redis_health()
        elif service_name == "initialization":
            result = await health_checker.check_database_initialization_status()
        else:
            raise HTTPException(status_code=404, detail=f"未知服务: {service_name}")
        
        return success_response(data=result)
    except HTTPException:
        raise
    except Exception as e:
        return error_response(message=f"服务 {service_name} 健康检查失败: {str(e)}")


# 兼容性端点，保持与现有系统的兼容
@router.get("/check")
async def legacy_health_check():
    """兼容性健康检查端点"""
    return await basic_health_check()