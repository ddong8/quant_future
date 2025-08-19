"""
算法交易引擎 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from ...core.dependencies import get_current_user
from ...services.algo_trading_engine import algo_trading_engine
# from ...models.user import User

router = APIRouter(tags=["算法交易"])


class StrategyConfig(BaseModel):
    """策略配置模型"""
    strategy_id: str = Field(..., description="策略ID")
    strategy_type: str = Field(..., description="策略类型")
    name: str = Field(..., description="策略名称")
    symbols: List[str] = Field(..., description="交易品种列表")
    parameters: Dict[str, Any] = Field(default={}, description="策略参数")
    risk_limits: Dict[str, Any] = Field(default={}, description="风险限制")
    enabled: bool = Field(default=True, description="是否启用")


class EngineControlRequest(BaseModel):
    """引擎控制请求模型"""
    action: str = Field(..., description="操作类型: start/stop/pause/resume")
    force: bool = Field(default=False, description="是否强制执行")


@router.get("/status", summary="获取引擎状态")
async def get_engine_status(
    current_user: dict = Depends(get_current_user)
):
    """获取算法交易引擎状态"""
    try:
        status_info = await algo_trading_engine.get_engine_status()
        
        return {
            "success": True,
            "data": status_info,
            "message": "获取引擎状态成功"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取引擎状态失败: {str(e)}"
        )


@router.post("/control", summary="控制引擎")
async def control_engine(
    request: EngineControlRequest,
    current_user: dict = Depends(get_current_user)
):
    """控制算法交易引擎"""
    try:
        user_id = str(current_user['id'])
        
        if request.action == "start":
            result = await algo_trading_engine.start_engine(user_id)
        elif request.action == "stop":
            result = await algo_trading_engine.stop_engine(user_id)
        elif request.action == "pause":
            # 暂停引擎（保持策略但停止交易）
            result = {"success": True, "message": "暂停功能待实现"}
        elif request.action == "resume":
            # 恢复引擎
            result = {"success": True, "message": "恢复功能待实现"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的操作类型: {request.action}"
            )
        
        if result["success"]:
            return {
                "success": True,
                "data": result,
                "message": f"引擎{request.action}操作成功"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "操作失败")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"控制引擎失败: {str(e)}"
        )


@router.get("/strategies", summary="获取活跃策略列表")
async def get_active_strategies(
    current_user: dict = Depends(get_current_user)
):
    """获取当前活跃的交易策略列表"""
    try:
        status_info = await algo_trading_engine.get_engine_status()
        strategies = status_info.get("strategies", [])
        
        return {
            "success": True,
            "data": strategies,
            "message": "获取策略列表成功"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略列表失败: {str(e)}"
        )


@router.post("/strategies", summary="添加交易策略")
async def add_strategy(
    strategy_config: StrategyConfig,
    current_user: dict = Depends(get_current_user)
):
    """添加新的交易策略"""
    try:
        # 转换为字典格式
        config_dict = strategy_config.dict()
        config_dict["user_id"] = str(current_user['id'])
        
        result = await algo_trading_engine.add_strategy(config_dict)
        
        if result["success"]:
            return {
                "success": True,
                "data": result,
                "message": "策略添加成功"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "添加策略失败")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加策略失败: {str(e)}"
        )


@router.delete("/strategies/{strategy_id}", summary="移除交易策略")
async def remove_strategy(
    strategy_id: str,
    current_user: dict = Depends(get_current_user)
):
    """移除指定的交易策略"""
    try:
        result = await algo_trading_engine.remove_strategy(strategy_id)
        
        if result["success"]:
            return {
                "success": True,
                "data": result,
                "message": "策略移除成功"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "移除策略失败")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"移除策略失败: {str(e)}"
        )


@router.get("/orders", summary="获取订单历史")
async def get_orders(
    strategy_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """获取订单历史记录"""
    try:
        # 从引擎获取订单信息
        engine_status = await algo_trading_engine.get_engine_status()
        
        # 这里可以根据参数过滤订单
        orders = []
        
        # 从pending_orders获取订单信息
        for order_id, order_info in algo_trading_engine.pending_orders.items():
            if strategy_id and order_info.get("strategy_id") != strategy_id:
                continue
            
            if status_filter and order_info.get("status") != status_filter:
                continue
            
            order_data = {
                "order_id": order_id,
                "strategy_id": order_info.get("strategy_id"),
                "symbol": order_info.get("symbol"),
                "direction": order_info.get("direction"),
                "volume": order_info.get("volume"),
                "price": order_info.get("price"),
                "status": order_info.get("status"),
                "created_at": order_info.get("created_at").isoformat() if order_info.get("created_at") else None,
                "filled_at": order_info.get("filled_at").isoformat() if order_info.get("filled_at") else None,
                "signal_info": order_info.get("signal_info", {})
            }
            orders.append(order_data)
        
        # 限制返回数量
        orders = orders[:limit]
        
        return {
            "success": True,
            "data": {
                "orders": orders,
                "total": len(orders)
            },
            "message": "获取订单历史成功"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取订单历史失败: {str(e)}"
        )


@router.get("/signals", summary="获取交易信号历史")
async def get_signals(
    strategy_id: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """获取交易信号历史记录"""
    try:
        # 获取信号历史
        signals = algo_trading_engine.signal_history.copy()
        
        # 根据策略ID过滤
        if strategy_id:
            signals = [s for s in signals if s.get("strategy_id") == strategy_id]
        
        # 限制数量并按时间倒序
        signals = sorted(signals, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
        
        return {
            "success": True,
            "data": {
                "signals": signals,
                "total": len(signals)
            },
            "message": "获取信号历史成功"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取信号历史失败: {str(e)}"
        )


@router.get("/performance", summary="获取策略表现")
async def get_strategy_performance(
    strategy_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """获取策略表现统计"""
    try:
        performance_data = {}
        
        # 获取引擎状态
        engine_status = await algo_trading_engine.get_engine_status()
        strategies = engine_status.get("strategies", [])
        
        if strategy_id:
            # 获取特定策略的表现
            strategy_info = next((s for s in strategies if s["strategy_id"] == strategy_id), None)
            if strategy_info:
                performance_data = {
                    "strategy_id": strategy_id,
                    "total_trades": strategy_info.get("total_trades", 0),
                    "profit_loss": strategy_info.get("profit_loss", 0.0),
                    "win_rate": 0.0,  # 需要计算
                    "avg_profit": 0.0,  # 需要计算
                    "max_drawdown": 0.0,  # 需要计算
                    "sharpe_ratio": 0.0,  # 需要计算
                }
        else:
            # 获取所有策略的汇总表现
            total_trades = sum(s.get("total_trades", 0) for s in strategies)
            total_profit_loss = sum(s.get("profit_loss", 0.0) for s in strategies)
            
            performance_data = {
                "total_strategies": len(strategies),
                "total_trades": total_trades,
                "total_profit_loss": total_profit_loss,
                "active_strategies": len([s for s in strategies if s.get("status") == "active"]),
                "strategies_detail": strategies
            }
        
        return {
            "success": True,
            "data": performance_data,
            "message": "获取策略表现成功"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略表现失败: {str(e)}"
        )


@router.get("/events", summary="获取引擎事件日志")
async def get_engine_events(
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """获取引擎事件日志"""
    try:
        # 从Redis获取事件日志
        events_key = "algo_engine:events"
        events_data = await algo_trading_engine.redis_client.lrange(events_key, 0, limit - 1)
        
        events = []
        for event_data in events_data:
            try:
                import json
                event = json.loads(event_data)
                events.append(event)
            except:
                continue
        
        return {
            "success": True,
            "data": {
                "events": events,
                "total": len(events)
            },
            "message": "获取事件日志成功"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取事件日志失败: {str(e)}"
        )


@router.post("/test-strategy", summary="测试策略配置")
async def test_strategy(
    strategy_config: StrategyConfig,
    current_user: dict = Depends(get_current_user)
):
    """测试策略配置是否有效"""
    try:
        # 验证策略配置
        config_dict = strategy_config.dict()
        validation_result = await algo_trading_engine._validate_strategy_config(config_dict)
        
        if validation_result["valid"]:
            # 尝试创建策略实例进行测试
            test_instance = await algo_trading_engine._create_strategy_instance(config_dict)
            
            if test_instance:
                # 测试信号生成
                test_signals = await test_instance.generate_signals()
                
                return {
                    "success": True,
                    "data": {
                        "config_valid": True,
                        "instance_created": True,
                        "test_signals": test_signals[:5] if test_signals else [],  # 返回前5个信号作为示例
                        "signals_count": len(test_signals)
                    },
                    "message": "策略测试成功"
                }
            else:
                return {
                    "success": False,
                    "data": {
                        "config_valid": True,
                        "instance_created": False
                    },
                    "message": "策略实例创建失败"
                }
        else:
            return {
                "success": False,
                "data": {
                    "config_valid": False,
                    "error": validation_result["error"]
                },
                "message": "策略配置无效"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试策略失败: {str(e)}"
        )