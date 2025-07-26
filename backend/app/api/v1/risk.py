"""
风险管理API路由
"""
from fastapi import APIRouter

router = APIRouter()

# 风险管理路由将在后续任务中实现
@router.get("/")
async def risk_placeholder():
    """风险管理模块占位符"""
    return {"message": "风险管理模块将在后续任务中实现"}