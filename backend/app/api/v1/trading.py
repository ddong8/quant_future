"""
交易执行API路由
"""
from fastapi import APIRouter

router = APIRouter()

# 交易执行路由将在后续任务中实现
@router.get("/")
async def trading_placeholder():
    """交易执行模块占位符"""
    return {"message": "交易执行模块将在后续任务中实现"}