"""
系统管理API路由
"""
from fastapi import APIRouter

router = APIRouter()

# 系统管理路由将在后续任务中实现
@router.get("/")
async def system_placeholder():
    """系统管理模块占位符"""
    return {"message": "系统管理模块将在后续任务中实现"}