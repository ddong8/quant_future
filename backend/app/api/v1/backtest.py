"""
回测系统API路由
"""
from fastapi import APIRouter

router = APIRouter()

# 回测系统路由将在后续任务中实现
@router.get("/")
async def backtest_placeholder():
    """回测系统模块占位符"""
    return {"message": "回测系统模块将在后续任务中实现"}