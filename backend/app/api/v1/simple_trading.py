"""
简单交易API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from ...core.dependencies import get_current_user, require_trader_or_admin
from ...core.response import success_response, error_response
from ...services.simple_trading_service import simple_trading_service
from ...models import User

router = APIRouter()


class OrderRequest(BaseModel):
    """下单请求"""
    symbol: str
    direction: str  # "BUY" or "SELL"
    volume: int
    price: Optional[float] = None
    order_type: str = "LIMIT"  # "LIMIT" or "MARKET"


class CancelOrderRequest(BaseModel):
    """撤单请求"""
    order_id: str


@router.get("/account")
async def get_account_info(
    current_user: User = Depends(require_trader_or_admin),
):
    """获取账户信息"""
    try:
        account_info = await simple_trading_service.get_account_info()
        
        return success_response(
            data=account_info,
            message="获取账户信息成功"
        )
        
    except Exception as e:
        return error_response(
            error_code="ACCOUNT_ERROR",
            message=f"获取账户信息失败: {str(e)}"
        )


@router.post("/orders")
async def place_order(
    order_request: OrderRequest,
    current_user: User = Depends(require_trader_or_admin),
):
    """下单"""
    try:
        order_info = await simple_trading_service.place_order(
            symbol=order_request.symbol,
            direction=order_request.direction,
            volume=order_request.volume,
            price=order_request.price,
            order_type=order_request.order_type
        )
        
        return success_response(
            data=order_info,
            message="下单成功"
        )
        
    except Exception as e:
        return error_response(
            error_code="ORDER_ERROR",
            message=f"下单失败: {str(e)}"
        )


@router.delete("/orders/{order_id}")
async def cancel_order(
    order_id: str,
    current_user: User = Depends(require_trader_or_admin),
):
    """撤单"""
    try:
        order_info = await simple_trading_service.cancel_order(order_id)
        
        return success_response(
            data=order_info,
            message="撤单成功"
        )
        
    except Exception as e:
        return error_response(
            error_code="CANCEL_ERROR",
            message=f"撤单失败: {str(e)}"
        )


@router.get("/orders")
async def get_orders(
    status: Optional[str] = Query(None, description="订单状态筛选"),
    current_user: User = Depends(require_trader_or_admin),
):
    """获取订单列表"""
    try:
        orders = await simple_trading_service.get_orders(status)
        
        return success_response(
            data=orders,
            message=f"获取到{len(orders)}个订单"
        )
        
    except Exception as e:
        return error_response(
            error_code="ORDERS_ERROR",
            message=f"获取订单列表失败: {str(e)}"
        )


@router.get("/positions")
async def get_positions(
    current_user: User = Depends(require_trader_or_admin),
):
    """获取持仓列表"""
    try:
        positions = await simple_trading_service.get_positions()
        
        return success_response(
            data=positions,
            message=f"获取到{len(positions)}个持仓"
        )
        
    except Exception as e:
        return error_response(
            error_code="POSITIONS_ERROR",
            message=f"获取持仓列表失败: {str(e)}"
        )


@router.get("/trades")
async def get_trades(
    symbol: Optional[str] = Query(None, description="合约代码筛选"),
    limit: int = Query(20, description="限制数量"),
    current_user: User = Depends(require_trader_or_admin),
):
    """获取成交记录"""
    try:
        trades = await simple_trading_service.get_trades(limit=limit)
        
        # 如果指定了合约代码，进行筛选
        if symbol:
            trades = [trade for trade in trades if trade["symbol"] == symbol]
        
        return success_response(
            data=trades,
            message=f"获取到{len(trades)}条成交记录"
        )
        
    except Exception as e:
        return error_response(
            error_code="TRADES_ERROR",
            message=f"获取成交记录失败: {str(e)}"
        )


@router.get("/trading-status")
async def get_trading_status():
    """获取交易状态"""
    try:
        # 检查交易服务状态
        from ...services.tqsdk_adapter import tqsdk_adapter
        
        connection_status = tqsdk_adapter.get_connection_status()
        
        status_info = {
            "is_trading_available": connection_status["is_connected"],
            "is_simulation": connection_status["is_sim_trading"],
            "connection_status": "connected" if connection_status["is_connected"] else "disconnected",
            "tqsdk_available": connection_status["tqsdk_available"],
            "service_status": "running",
            "last_update": "2025-08-12T00:00:00Z"
        }
        
        return success_response(
            data=status_info,
            message="获取交易状态成功"
        )
        
    except Exception as e:
        return error_response(
            error_code="STATUS_ERROR",
            message=f"获取交易状态失败: {str(e)}"
        )