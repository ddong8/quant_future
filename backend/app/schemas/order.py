"""
订单相关的Pydantic模型
"""
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.enums import OrderDirection, OrderOffset, OrderStatus


class OrderBase(BaseModel):
    """订单基础模型"""
    symbol: str
    direction: OrderDirection
    offset: OrderOffset
    volume: int
    price: float
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('交易品种不能为空')
        if len(v.strip()) > 20:
            raise ValueError('交易品种长度不能超过20个字符')
        return v.strip()
    
    @validator('volume')
    def validate_volume(cls, v):
        if v <= 0:
            raise ValueError('交易数量必须大于0')
        if v > 10000:
            raise ValueError('单笔交易数量不能超过10000手')
        return v
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('价格必须大于0')
        if v > 1000000:
            raise ValueError('价格不能超过1000000')
        return v


class OrderCreate(OrderBase):
    """创建订单模型"""
    strategy_id: int
    notes: Optional[str] = None
    
    @validator('strategy_id')
    def validate_strategy_id(cls, v):
        if v <= 0:
            raise ValueError('策略ID必须大于0')
        return v
    
    @validator('notes')
    def validate_notes(cls, v):
        if v and len(v) > 500:
            raise ValueError('备注长度不能超过500个字符')
        return v


class OrderModify(BaseModel):
    """修改订单模型"""
    volume: Optional[int] = None
    price: Optional[float] = None
    notes: Optional[str] = None
    
    @validator('volume')
    def validate_volume(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError('交易数量必须大于0')
            if v > 10000:
                raise ValueError('单笔交易数量不能超过10000手')
        return v
    
    @validator('price')
    def validate_price(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError('价格必须大于0')
            if v > 1000000:
                raise ValueError('价格不能超过1000000')
        return v
    
    @validator('notes')
    def validate_notes(cls, v):
        if v and len(v) > 500:
            raise ValueError('备注长度不能超过500个字符')
        return v


class OrderResponse(BaseModel):
    """订单响应模型"""
    id: str
    strategy_id: int
    symbol: str
    direction: str
    offset: str
    volume: int
    price: float
    status: str
    filled_volume: int
    avg_fill_price: float
    commission: float
    slippage: float
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    filled_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """订单列表响应模型"""
    id: str
    strategy_id: int
    symbol: str
    direction: str
    offset: str
    volume: int
    price: float
    status: str
    filled_volume: int
    avg_fill_price: float
    commission: float
    created_at: datetime
    filled_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class OrderSearchRequest(BaseModel):
    """订单搜索请求模型"""
    strategy_id: Optional[int] = None
    symbol: Optional[str] = None
    status: Optional[OrderStatus] = None
    direction: Optional[OrderDirection] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if v and len(v.strip()) < 1:
            raise ValueError('交易品种不能为空')
        return v.strip() if v else None


class BatchCancelRequest(BaseModel):
    """批量撤销请求模型"""
    order_ids: List[str]
    
    @validator('order_ids')
    def validate_order_ids(cls, v):
        if not v:
            raise ValueError('订单ID列表不能为空')
        if len(v) > 50:
            raise ValueError('批量操作最多支持50个订单')
        return v


class OrderStatusUpdate(BaseModel):
    """订单状态更新模型"""
    status: OrderStatus
    filled_volume: Optional[int] = None
    avg_fill_price: Optional[float] = None
    commission: Optional[float] = None
    
    @validator('filled_volume')
    def validate_filled_volume(cls, v):
        if v is not None and v < 0:
            raise ValueError('成交数量不能为负数')
        return v
    
    @validator('avg_fill_price')
    def validate_avg_fill_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError('成交价格必须大于0')
        return v
    
    @validator('commission')
    def validate_commission(cls, v):
        if v is not None and v < 0:
            raise ValueError('手续费不能为负数')
        return v


class OrderStatistics(BaseModel):
    """订单统计模型"""
    total_orders: int
    filled_orders: int
    cancelled_orders: int
    pending_orders: int
    buy_orders: int
    sell_orders: int
    fill_rate: float
    avg_fill_time_seconds: Optional[float]
    symbol_distribution: List[Dict[str, Any]]


class PositionBase(BaseModel):
    """持仓基础模型"""
    symbol: str
    direction: str
    volume: int
    avg_price: float
    margin: float
    margin_rate: float


class PositionResponse(BaseModel):
    """持仓响应模型"""
    id: int
    strategy_id: int
    symbol: str
    direction: str
    volume: int
    avg_price: float
    unrealized_pnl: float
    realized_pnl: float
    margin: float
    margin_rate: float
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AccountResponse(BaseModel):
    """账户响应模型"""
    id: int
    user_id: int
    account_id: str
    account_name: Optional[str]
    broker: Optional[str]
    balance: float
    available: float
    margin: float
    frozen: float
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    risk_ratio: float
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class RiskCheckRequest(BaseModel):
    """风险检查请求模型"""
    symbol: str
    direction: OrderDirection
    offset: OrderOffset
    volume: int
    price: float
    strategy_id: int


class RiskCheckResponse(BaseModel):
    """风险检查响应模型"""
    passed: bool
    reason: str
    warnings: List[str]
    checks: Dict[str, Any]


class RiskSummaryResponse(BaseModel):
    """风险摘要响应模型"""
    account_balance: float
    available_funds: float
    total_value: float
    margin_used: float
    fund_usage_ratio: float
    overall_risk_ratio: float
    position_risks: List[Dict[str, Any]]
    risk_level: str
    daily_pnl: float
    risk_warnings: List[str]


class RiskParametersUpdate(BaseModel):
    """风险参数更新模型"""
    max_position_ratio: Optional[float] = None
    max_daily_loss: Optional[float] = None
    max_order_value: Optional[float] = None
    max_orders_per_minute: Optional[int] = None
    min_account_balance: Optional[float] = None
    
    @validator('max_position_ratio')
    def validate_max_position_ratio(cls, v):
        if v is not None and (v <= 0 or v > 1):
            raise ValueError('最大持仓比例必须在0-1之间')
        return v
    
    @validator('max_daily_loss')
    def validate_max_daily_loss(cls, v):
        if v is not None and (v <= 0 or v > 1):
            raise ValueError('最大日亏损比例必须在0-1之间')
        return v
    
    @validator('max_order_value')
    def validate_max_order_value(cls, v):
        if v is not None and v <= 0:
            raise ValueError('最大订单金额必须大于0')
        return v
    
    @validator('max_orders_per_minute')
    def validate_max_orders_per_minute(cls, v):
        if v is not None and v <= 0:
            raise ValueError('每分钟最大订单数必须大于0')
        return v
    
    @validator('min_account_balance')
    def validate_min_account_balance(cls, v):
        if v is not None and v < 0:
            raise ValueError('最小账户余额不能为负数')
        return v


class OrderExecutionResult(BaseModel):
    """订单执行结果模型"""
    order_id: str
    success: bool
    message: str
    broker_order_id: Optional[str] = None
    execution_time: Optional[datetime] = None


class BatchOperationResult(BaseModel):
    """批量操作结果模型"""
    results: List[Dict[str, Any]]
    success_count: int
    failed_count: int


class TradingSignal(BaseModel):
    """交易信号模型"""
    strategy_id: int
    symbol: str
    signal_type: str  # buy/sell/hold
    strength: float  # 信号强度 0-1
    price: float
    volume: int
    reason: str
    timestamp: datetime
    
    @validator('strength')
    def validate_strength(cls, v):
        if v < 0 or v > 1:
            raise ValueError('信号强度必须在0-1之间')
        return v
    
    @validator('signal_type')
    def validate_signal_type(cls, v):
        allowed_types = ['buy', 'sell', 'hold']
        if v not in allowed_types:
            raise ValueError(f'信号类型必须是: {allowed_types}')
        return v


class OrderBookEntry(BaseModel):
    """订单簿条目模型"""
    price: float
    volume: int
    order_count: int


class OrderBook(BaseModel):
    """订单簿模型"""
    symbol: str
    bids: List[OrderBookEntry]  # 买盘
    asks: List[OrderBookEntry]  # 卖盘
    timestamp: datetime


class TradeRecord(BaseModel):
    """成交记录模型"""
    trade_id: str
    order_id: str
    symbol: str
    direction: str
    volume: int
    price: float
    commission: float
    timestamp: datetime


class PositionSummary(BaseModel):
    """持仓汇总模型"""
    total_positions: int
    total_market_value: float
    total_unrealized_pnl: float
    total_realized_pnl: float
    positions_by_symbol: Dict[str, Dict[str, Any]]
    risk_metrics: Dict[str, float]