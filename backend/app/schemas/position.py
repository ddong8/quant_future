"""
持仓相关的数据模型
"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field

from .base import BaseResponse


class PositionBase(BaseModel):
    """持仓基础模型"""
    symbol: str = Field(..., description="品种代码")
    side: str = Field(..., description="持仓方向")
    quantity: Decimal = Field(..., description="持仓数量")
    average_price: Decimal = Field(..., description="平均价格")
    market_value: Optional[Decimal] = Field(None, description="市值")
    unrealized_pnl: Optional[Decimal] = Field(None, description="未实现盈亏")
    realized_pnl: Optional[Decimal] = Field(None, description="已实现盈亏")
    frozen_quantity: Optional[Decimal] = Field(None, description="冻结数量")


class PositionCreate(PositionBase):
    """创建持仓"""
    pass


class PositionUpdate(BaseModel):
    """更新持仓"""
    quantity: Optional[Decimal] = None
    average_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    realized_pnl: Optional[Decimal] = None
    frozen_quantity: Optional[Decimal] = None


class Position(PositionBase):
    """持仓信息"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PositionDetail(Position):
    """持仓详情"""
    pnl_ratio: Optional[float] = Field(None, description="盈亏比例(%)")
    available_quantity: Optional[float] = Field(None, description="可用数量")
    cost_basis: Optional[float] = Field(None, description="成本基础")
    holding_days: Optional[int] = Field(None, description="持仓天数")


class PositionSummary(BaseModel):
    """持仓汇总"""
    total_positions: int = Field(..., description="总持仓数")
    long_positions: int = Field(..., description="多头持仓数")
    short_positions: int = Field(..., description="空头持仓数")
    total_market_value: float = Field(..., description="总市值")
    total_unrealized_pnl: float = Field(..., description="总未实现盈亏")
    total_realized_pnl: float = Field(..., description="总已实现盈亏")
    total_pnl_ratio: float = Field(..., description="总盈亏比例(%)")
    positions: List[dict] = Field(..., description="持仓详情列表")


class PositionHistory(BaseModel):
    """持仓历史"""
    date: str = Field(..., description="日期")
    symbol: str = Field(..., description="品种代码")
    quantity_change: float = Field(..., description="数量变化")
    realized_pnl: float = Field(..., description="已实现盈亏")
    trade_count: int = Field(..., description="交易次数")
    trades: List[dict] = Field(..., description="交易详情")


class PositionMetrics(BaseModel):
    """持仓指标"""
    symbol: str = Field(..., description="品种代码")
    quantity: float = Field(..., description="持仓数量")
    average_price: float = Field(..., description="平均价格")
    current_value: float = Field(..., description="当前市值")
    cost_basis: float = Field(..., description="成本基础")
    unrealized_pnl: float = Field(..., description="未实现盈亏")
    realized_pnl: float = Field(..., description="已实现盈亏")
    total_pnl: float = Field(..., description="总盈亏")
    pnl_ratio: float = Field(..., description="盈亏比例(%)")
    holding_days: int = Field(..., description="持仓天数")
    total_cost: float = Field(..., description="总成本")
    total_proceeds: float = Field(..., description="总收益")
    trade_count: int = Field(..., description="交易次数")
    first_trade_date: str = Field(..., description="首次交易日期")
    last_update: str = Field(..., description="最后更新时间")


class ClosePositionRequest(BaseModel):
    """平仓请求"""
    quantity: Optional[float] = Field(None, description="平仓数量，不指定则全部平仓")


class ClosePositionResponse(BaseModel):
    """平仓响应"""
    order_id: str = Field(..., description="订单ID")
    symbol: str = Field(..., description="品种代码")
    side: str = Field(..., description="订单方向")
    quantity: float = Field(..., description="平仓数量")
    status: str = Field(..., description="订单状态")
    message: str = Field(..., description="响应消息")


class PositionListRequest(BaseModel):
    """持仓列表请求"""
    symbol: Optional[str] = Field(None, description="品种代码")
    side: Optional[str] = Field(None, description="持仓方向")
    only_active: bool = Field(True, description="只显示有持仓的")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")
    sort_by: str = Field("updated_at", description="排序字段")
    sort_order: str = Field("desc", description="排序方向")


class PositionListData(BaseModel):
    """持仓列表数据"""
    positions: List[Position]
    total: int
    page: int
    page_size: int


class FreezePositionRequest(BaseModel):
    """冻结持仓请求"""
    quantity: float = Field(..., gt=0, description="冻结数量")


class UnfreezePositionRequest(BaseModel):
    """解冻持仓请求"""
    quantity: float = Field(..., gt=0, description="解冻数量")


class AvailableQuantityResponse(BaseModel):
    """可用数量响应"""
    symbol: str = Field(..., description="品种代码")
    available_quantity: float = Field(..., description="可用数量")


class MarketValueUpdateRequest(BaseModel):
    """市值更新请求"""
    current_price: float = Field(..., gt=0, description="当前价格")


# 响应模型
class PositionResponse(BaseResponse):
    """持仓响应"""
    data: Position


class PositionListResponse(BaseResponse):
    """持仓列表响应"""
    data: PositionListData


class PositionSummaryResponse(BaseResponse):
    """持仓汇总响应"""
    data: PositionSummary


class PositionHistoryResponse(BaseResponse):
    """持仓历史响应"""
    data: List[PositionHistory]


class PositionMetricsResponse(BaseResponse):
    """持仓指标响应"""
    data: PositionMetrics