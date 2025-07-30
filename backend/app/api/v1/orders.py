"""
订单管理API路由
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ...core.dependencies import (
    get_db,
    get_current_user,
    require_trader_or_admin,
    get_pagination_params,
    get_sort_params,
    PaginationParams,
    SortParams,
)
from ...core.response import (
    success_response,
    created_response,
    paginated_response,
    deleted_response,
)
from ...services.order_service import OrderService
from ...services.risk_service import RiskService
from ...services.tqsdk_adapter import TQSDKAdapter
from ...schemas.order import (
    OrderCreate,
    OrderModify,
    OrderResponse,
    OrderListResponse,
    OrderSearchRequest,
    BatchCancelRequest,
    OrderStatusUpdate,
    OrderStatistics,
    RiskCheckRequest,
    RiskCheckResponse,
    RiskSummaryResponse,
    RiskParametersUpdate,
    BatchOperationResult,
)
from ...models import User
from ...models.enums import OrderStatus, OrderDirection

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_db),
):
    """创建订单"""
    # 初始化服务
    risk_service = RiskService(db)
    tqsdk_adapter = TQSDKAdapter()
    order_service = OrderService(db, tqsdk_adapter, risk_service)
    
    order = order_service.create_order(order_data.dict(), current_user.id)
    
    return created_response(
        data=OrderResponse.from_orm(order).dict(),
        message="订单创建成功"
    )


@router.get("/", response_model=List[OrderListResponse])
async def get_orders_list(
    strategy_id: Optional[int] = Query(None, description="策略ID"),
    symbol: Optional[str] = Query(None, description="交易品种"),
    status: Optional[OrderStatus] = Query(None, description="订单状态"),
    direction: Optional[OrderDirection] = Query(None, description="交易方向"),
    pagination: PaginationParams = Depends(get_pagination_params),
    sort_params: SortParams = Depends(get_sort_params),
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_db),
):
    """获取订单列表"""
    # 初始化服务
    risk_service = RiskService(db)
    tqsdk_adapter = TQSDKAdapter()
    order_service = OrderService(db, tqsdk_adapter, risk_service)
    
    orders, total = order_service.get_orders_list(
        user_id=current_user.id,
        strategy_id=strategy_id,
        symbol=symbol,
        status=status,
        direction=direction,
        pagination=pagination,
        sort_params=sort_params
    )
    
    order_list = [OrderListResponse.from_orm(order) for order in orders]
    
    return paginated_response(
        data=[order.dict() for order in order_list],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        message="获取订单列表成功"
    )


@router.get("/pending")
async def get_pending_orders(
    strategy_id: Optional[int] = Query(None, description="策略ID"),
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_db),
):
    """获取待成交订单"""
    # 初始化服务
    risk_service = RiskService(db)
    tqsdk_adapter = TQSDKAdapter()
    order_service = OrderService(db, tqsdk_adapter, risk_service)
    
    pending_orders = order_service.get_pending_orders(current_user.id, strategy_id)
    
    return success_response(
        data=[OrderListResponse.from_orm(order).dict() for order in pending_orders],
        message="获取待成交订单成功"
    )


@router.get("/statistics", response_model=OrderStatistics)
async def get_order_statistics(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_db),
):
    """获取订单统计信息"""
    from datetime import datetime
    
    # 解析日期参数
    start_datetime = None
    end_datetime = None
    
    if start_date:
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    
    if end_date:
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
    
    # 初始化服务
    risk_service = RiskService(db)
    tqsdk_adapter = TQSDKAdapter()
    order_service = OrderService(db, tqsdk_adapter, risk_service)
    
    statistics = order_service.get_order_statistics(
        current_user.id, 
        start_datetime, 
        end_datetime
    )
    
    return success_response(
        data=statistics,
        message="获取订单统计成功"
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_by_id(
    order_id: str,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_db),
):
    """根据ID获取订单详情"""
    # 初始化服务
    risk_service = RiskService(db)
    tqsdk_adapter = TQSDKAdapter()
    order_service = OrderService(db, tqsdk_adapter, risk_service)
    
    order = order_service.get_order_by_id(order_id, current_user.id)
    
    return success_response(
        data=OrderResponse.from_orm(order).dict(),
        message="获取订单详情成功"
    )


@router.put("/{order_id}", response_model=OrderResponse)
async def modify_order(
    order_id: str,
    modify_data: OrderModify,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_db),
):
    """修改订单"""
    # 初始化服务
    risk_service = RiskService(db)
    tqsdk_adapter = TQSDKAdapter()
    order_service = OrderService(db, tqsdk_adapter, risk_service)
    
    order = order_service.modify_order(
        order_id, 
        modify_data.dict(exclude_unset=True), 
        current_user.id
    )
    
    return success_response(
        data=OrderResponse.from_orm(order).dict(),
        message="订单修改成功"
    )


@router.delete("/{order_id}")
async def cancel_order(
    order_id: str,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_db),
):
    """撤销订单"""
    # 初始化服务
    risk_service = RiskService(db)
    tqsdk_adapter = TQSDKAdapter()
    order_service = OrderService(db, tqsdk_adapter, risk_service)
    
    order = order_service.cancel_order(order_id, current_user.id)
    
    return success_response(
        data=OrderResponse.from_orm(order).dict(),
        message="订单撤销成功"
    )


@router.post("/batch-cancel", response_model=BatchOperationResult)
async def batch_cancel_orders(
    cancel_request: BatchCancelRequest,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_db),
):
    """批量撤销订单"""
    # 初始化服务
    risk_service = RiskService(db)
    tqsdk_adapter = TQSDKAdapter()
    order_service = OrderService(db, tqsdk_adapter, risk_service)
    
    result = order_service.batch_cancel_orders(cancel_request.order_ids, current_user.id)
    
    return success_response(
        data=result,
        message=f"批量撤销完成，成功: {result['success_count']}, 失败: {result['failed_count']}"
    )


@router.put("/{order_id}/status")
async def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_db),
):
    """更新订单状态（系统内部调用）"""
    # 初始化服务
    risk_service = RiskService(db)
    tqsdk_adapter = TQSDKAdapter()
    order_service = OrderService(db, tqsdk_adapter, risk_service)
    
    order = order_service.update_order_status(
        order_id=order_id,
        status=status_update.status,
        filled_volume=status_update.filled_volume,
        avg_fill_price=status_update.avg_fill_price,
        commission=status_update.commission
    )
    
    return success_response(
        data=OrderResponse.from_orm(order).dict(),
        message="订单状态更新成功"
    )


# 风险管理相关API

@router.post("/risk-check", response_model=RiskCheckResponse)
async def check_order_risk(
    risk_request: RiskCheckRequest,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_db),
):
    """检查订单风险"""
    risk_service = RiskService(db)
    
    risk_result = risk_service.check_order_risk(risk_request.dict(), current_user.id)
    
    return success_response(
        data=risk_result,
        message="风险检查完成"
    )


@router.get("/risk/summary", response_model=RiskSummaryResponse)
async def get_risk_summary(
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_db),
):
    """获取风险摘要"""
    risk_service = RiskService(db)
    
    risk_summary = risk_service.get_risk_summary(current_user.id)
    
    return success_response(
        data=risk_summary,
        message="获取风险摘要成功"
    )


@router.put("/risk/parameters")
async def update_risk_parameters(
    risk_params: RiskParametersUpdate,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_db),
):
    """更新风险参数"""
    risk_service = RiskService(db)
    
    result = risk_service.update_risk_parameters(
        current_user.id, 
        risk_params.dict(exclude_unset=True)
    )
    
    return success_response(
        data=result,
        message="风险参数更新成功" if result['success'] else "风险参数更新失败"
    )


# 持仓管理相关API

@router.get("/positions")
async def get_positions(
    strategy_id: Optional[int] = Query(None, description="策略ID"),
    symbol: Optional[str] = Query(None, description="交易品种"),
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_db),
):
    """获取持仓列表"""
    from ...models import Position, Strategy
    from ...schemas.order import PositionResponse
    from sqlalchemy import and_
    
    query = db.query(Position).join(Strategy).filter(Strategy.user_id == current_user.id)
    
    if strategy_id:
        query = query.filter(Position.strategy_id == strategy_id)
    
    if symbol:
        query = query.filter(Position.symbol == symbol)
    
    positions = query.all()
    
    return success_response(
        data=[PositionResponse.from_orm(position).dict() for position in positions],
        message="获取持仓列表成功"
    )


@router.get("/positions/summary")
async def get_position_summary(
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_db),
):
    """获取持仓汇总"""
    from ...models import Position, Strategy
    from sqlalchemy import func
    
    # 获取用户所有持仓
    positions = db.query(Position).join(Strategy).filter(
        Strategy.user_id == current_user.id
    ).all()
    
    if not positions:
        return success_response(
            data={
                'total_positions': 0,
                'total_market_value': 0.0,
                'total_unrealized_pnl': 0.0,
                'total_realized_pnl': 0.0,
                'positions_by_symbol': {},
                'risk_metrics': {}
            },
            message="获取持仓汇总成功"
        )
    
    # 计算汇总数据
    total_market_value = sum(pos.volume * pos.avg_price for pos in positions)
    total_unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)
    total_realized_pnl = sum(pos.realized_pnl for pos in positions)
    
    # 按品种分组
    positions_by_symbol = {}
    for position in positions:
        symbol = position.symbol
        if symbol not in positions_by_symbol:
            positions_by_symbol[symbol] = {
                'total_volume': 0,
                'avg_price': 0.0,
                'market_value': 0.0,
                'unrealized_pnl': 0.0,
                'realized_pnl': 0.0,
                'positions': []
            }
        
        symbol_data = positions_by_symbol[symbol]
        symbol_data['total_volume'] += position.volume
        symbol_data['market_value'] += position.volume * position.avg_price
        symbol_data['unrealized_pnl'] += position.unrealized_pnl
        symbol_data['realized_pnl'] += position.realized_pnl
        symbol_data['positions'].append({
            'id': position.id,
            'strategy_id': position.strategy_id,
            'direction': position.direction,
            'volume': position.volume,
            'avg_price': position.avg_price,
            'unrealized_pnl': position.unrealized_pnl
        })
    
    # 计算风险指标
    risk_metrics = {
        'total_exposure': total_market_value,
        'pnl_ratio': (total_unrealized_pnl + total_realized_pnl) / total_market_value if total_market_value > 0 else 0,
        'unrealized_pnl_ratio': total_unrealized_pnl / total_market_value if total_market_value > 0 else 0,
    }
    
    summary = {
        'total_positions': len(positions),
        'total_market_value': total_market_value,
        'total_unrealized_pnl': total_unrealized_pnl,
        'total_realized_pnl': total_realized_pnl,
        'positions_by_symbol': positions_by_symbol,
        'risk_metrics': risk_metrics
    }
    
    return success_response(
        data=summary,
        message="获取持仓汇总成功"
    )


# 账户管理相关API

@router.get("/account")
async def get_account_info(
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_db),
):
    """获取账户信息"""
    from ...models import Account
    from ...schemas.order import AccountResponse
    
    account = db.query(Account).filter(Account.user_id == current_user.id).first()
    
    if not account:
        return success_response(
            data=None,
            message="未找到账户信息"
        )
    
    return success_response(
        data=AccountResponse.from_orm(account).dict(),
        message="获取账户信息成功"
    )