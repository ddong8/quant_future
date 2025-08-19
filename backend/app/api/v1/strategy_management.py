"""
策略管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Optional, List, Dict, Any
import logging

from ...services.strategy_service import strategy_service
from ...core.dependencies import get_current_user
from ...models import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/list")
async def get_strategy_list(
    current_user: User = Depends(get_current_user)
):
    """获取策略列表"""
    try:
        user_id = str(current_user.id) if hasattr(current_user, 'id') else "default"
        
        strategies = await strategy_service.get_strategy_list(user_id)
        
        return {
            "success": True,
            "data": strategies,
            "message": f"获取到 {len(strategies)} 个策略"
        }
        
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}")
async def get_strategy_detail(
    strategy_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取策略详情"""
    try:
        user_id = str(current_user.id) if hasattr(current_user, 'id') else "default"
        
        strategy = await strategy_service.get_strategy_detail(strategy_id, user_id)
        
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        return {
            "success": True,
            "data": strategy,
            "message": "获取策略详情成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_strategy(
    strategy_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    """创建策略"""
    try:
        user_id = str(current_user.id) if hasattr(current_user, 'id') else "default"
        
        strategy = await strategy_service.create_strategy(strategy_data, user_id)
        
        return {
            "success": True,
            "data": strategy,
            "message": "创建策略成功"
        }
        
    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{strategy_id}")
async def update_strategy(
    strategy_id: str,
    update_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    """更新策略"""
    try:
        user_id = str(current_user.id) if hasattr(current_user, 'id') else "default"
        
        strategy = await strategy_service.update_strategy(strategy_id, update_data, user_id)
        
        return {
            "success": True,
            "data": strategy,
            "message": "更新策略成功"
        }
        
    except Exception as e:
        logger.error(f"更新策略失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除策略"""
    try:
        user_id = str(current_user.id) if hasattr(current_user, 'id') else "default"
        
        result = await strategy_service.delete_strategy(strategy_id, user_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        return {
            "success": True,
            "message": "删除策略成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除策略失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{strategy_id}/test")
async def test_strategy(
    strategy_id: str,
    test_params: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    """测试策略"""
    try:
        user_id = str(current_user.id) if hasattr(current_user, 'id') else "default"
        
        result = await strategy_service.test_strategy(strategy_id, test_params, user_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "message": "策略测试完成"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}/performance")
async def get_strategy_performance(
    strategy_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取策略表现"""
    try:
        user_id = str(current_user.id) if hasattr(current_user, 'id') else "default"
        
        result = await strategy_service.get_strategy_performance(strategy_id, user_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "message": "获取策略表现成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略表现失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/built-in/templates")
async def get_built_in_templates(
    current_user: User = Depends(get_current_user)
):
    """获取内置策略模板"""
    try:
        # 获取内置策略作为模板
        strategies = await strategy_service.get_strategy_list("default")
        built_in_strategies = [s for s in strategies if s.get("is_built_in", False)]
        
        # 简化模板信息
        templates = []
        for strategy in built_in_strategies:
            templates.append({
                "template_id": strategy["strategy_id"],
                "name": strategy["name"],
                "description": strategy["description"],
                "type": strategy["type"],
                "parameters": strategy["parameters"]
            })
        
        return {
            "success": True,
            "data": templates,
            "message": f"获取到 {len(templates)} 个策略模板"
        }
        
    except Exception as e:
        logger.error(f"获取策略模板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))