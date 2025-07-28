"""
持仓管理API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import get_current_user, PaginationParams, SortParams
from ...core.response import success_response, error_response
from ...models import User
from ...schemas.position import (
    PositionResponse,
    PositionListResponse,
    PositionSummaryResponse,
    ClosePositionRequest,
    ClosePositionResponse
)
from ...services.position_service import PositionService
from ...services.order_service import OrderService

router = APIRouter()


@router.get("/", response_model=PositionListResponse)
async def get_positions(
    symbol: Optional[str] = Query(None, description="品种代码"),
    side: Optional[str] = Query(None, description="持仓方向"),
    only_active: bool = Query(True, description="只显示有持仓的"),
    pagination: PaginationParams = Depends(),
    sort_params: SortParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取持仓列表"""
    try:
        position_service = PositionService(db)
        
        positions, total = position_service.get_positions_list(
            user_id=current_user.id,
            symbol=symbol,
            side=side,
            only_active=only_active,
            pagination=pagination,
            sort_params=sort_params
        )
        
        return success_response(
            data={
                "positions": positions,
                "total": total,
                "page": pagination.page,
                "page_size": pagination.page_size
            }
        )
        
    except Exception as e:
        return error_response(message=f"获取持仓列表失败: {str(e)}")


@router.get("/{symbol}", response_model=PositionResponse)
async def get_position(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定品种的持仓"""
    try:
        position_service = PositionService(db)
        position = position_service.get_position(current_user.id, symbol)
        
        if not position:
            return error_response(message="持仓不存在", status_code=404)
        
        return success_response(data=position)
        
    except Exception as e:
        return error_response(message=f"获取持仓失败: {str(e)}")


@router.get("/summary/overview", response_model=PositionSummaryResponse)
async def get_position_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取持仓汇总"""
    try:
        position_service = PositionService(db)
        summary = position_service.get_position_summary(current_user.id)
        
        return success_response(data=summary)
        
    except Exception as e:
        return error_response(message=f"获取持仓汇总失败: {str(e)}")


@router.post("/{symbol}/close", response_model=ClosePositionResponse)
async def close_position(
    symbol: str,
    request: ClosePositionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """平仓"""
    try:
        position_service = PositionService(db)
        order_service = OrderService(db, None)  # TQSDK adapter需要单独注入
        
        # 获取平仓订单信息
        close_order_data = position_service.close_position(
            user_id=current_user.id,
            symbol=symbol,
            quantity=request.quantity
        )
        
        # 创建平仓订单
        order = order_service.create_order(close_order_data, current_user.id)
        
        return success_response(
            data={
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": order.side.value,
                "quantity": float(order.quantity),
                "status": order.status.value,
                "message": "平仓订单已提交"
            }
        )
        
    except Exception as e:
        return error_response(message=f"平仓失败: {str(e)}")


@router.get("/{symbol}/available")
async def get_available_quantity(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取可用持仓数量"""
    try:
        position_service = PositionService(db)
        available_quantity = position_service.get_available_quantity(
            current_user.id, symbol
        )
        
        return success_response(
            data={
                "symbol": symbol,
                "available_quantity": available_quantity
            }
        )
        
    except Exception as e:
        return error_response(message=f"获取可用持仓数量失败: {str(e)}")


@router.put("/{symbol}/market-value")
async def update_market_value(
    symbol: str,
    current_price: float = Query(..., description="当前价格"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新持仓市值"""
    try:
        position_service = PositionService(db)
        position_service.update_market_value(
            current_user.id, symbol, current_price
        )
        
        return success_response(message="持仓市值更新成功")
        
    except Exception as e:
        return error_response(message=f"更新持仓市值失败: {str(e)}")