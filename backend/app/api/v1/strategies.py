"""
策略管理API路由
"""
from fastapi import APIRouter

router = APIRouter()

# 策略管理路由将在后续任务中实现
@router.get("/")
async def strategies_placeholder():
    """策略管理模块占位符"""
    return {"message": "策略管理模块将在后续任务中实现"}