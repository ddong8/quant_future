"""
持仓数据验证模式
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
from ..models.position import PositionStatus, PositionType

class PositionBase(BaseModel):
    """持仓基础模式"""
    symbol: str = Field(..., description="交易标的")
    position_type: PositionType = Field(..., description="持仓类型")
    quantity: Decimal = Field(..., ge=0, description="持仓数量")
    average_cost: Decimal = Field(..., ge=0, description="平均成本价")
    stop_loss_price: Optional[Decimal] = Field(None, description="止损价格")
    take_profit_price: Optional[Decimal] = Field(None, description="止盈价格")
    notes: Optional[str] = Field(None, description="备注")
    tags: List[str] = Field(default_factory=list, description="标签")

class PositionCreate(PositionBase):
    """创建持仓模式"""
    strategy_id: Optional[int] = Field(None, description="策略ID")
    backtest_id: Optional[int] = Field(None, description="回测ID")
    source: str = Field("manual", description="持仓来源")
    source_id: Optional[str] = Field(None, description="来源标识")

class PositionUpdate(BaseModel):
    """更新持仓模式"""
    stop_loss_price: Optional[Decimal] = Field(None, description="止损价格")
    take_profit_price: Optional[Decimal] = Field(None, description="止盈价格")
    notes: Optional[str] = Field(None, description="备注")
    tags: Optional[List[str]] = Field(None, description="标签")

class PositionResponse(PositionBase):
    """持仓响应模式"""
    id: int
    uuid: str
    status: PositionStatus
    available_quantity: Decimal
    frozen_quantity: Decimal
    total_cost: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    current_price: Optional[Decimal]
    market_value: Optional[Decimal]
    max_drawdown: Decimal
    max_profit: Decimal
    return_rate: float
    unrealized_return_rate: float
    is_long: bool
    is_short: bool
    is_open: bool
    is_closed: bool
    strategy_id: Optional[int]
    backtest_id: Optional[int]
    source: str
    source_id: Optional[str]
    user_id: int
    opened_at: Optional[datetime]
    closed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PositionHistoryResponse(BaseModel):
    """持仓历史响应模式"""
    id: int
    uuid: str
    position_id: int
    action: str
    details: Dict[str, Any]
    quantity_snapshot: Optional[Decimal]
    average_cost_snapshot: Optional[Decimal]
    total_cost_snapshot: Optional[Decimal]
    realized_pnl_snapshot: Optional[Decimal]
    unrealized_pnl_snapshot: Optional[Decimal]
    current_price_snapshot: Optional[Decimal]
    created_at: datetime

    class Config:
        from_attributes = True

class PositionSummaryResponse(BaseModel):
    """持仓汇总响应模式"""
    id: int
    user_id: int
    symbol: str
    total_quantity: Decimal
    total_cost: Decimal
    average_cost: Decimal
    total_realized_pnl: Decimal
    total_unrealized_pnl: Decimal
    total_market_value: Decimal
    position_count: int
    last_trade_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StopLossRequest(BaseModel):
    """止损设置请求"""
    stop_price: Decimal = Field(..., gt=0, description="止损价格")
    order_id: Optional[int] = Field(None, description="关联订单ID")

    @validator('stop_price')
    def validate_stop_price(cls, v):
        if v <= 0:
            raise ValueError('止损价格必须大于0')
        return v

class TakeProfitRequest(BaseModel):
    """止盈设置请求"""
    profit_price: Decimal = Field(..., gt=0, description="止盈价格")
    order_id: Optional[int] = Field(None, description="关联订单ID")

    @validator('profit_price')
    def validate_profit_price(cls, v):
        if v <= 0:
            raise ValueError('止盈价格必须大于0')
        return v

class ClosePositionRequest(BaseModel):
    """平仓请求"""
    close_price: Decimal = Field(..., gt=0, description="平仓价格")
    reason: str = Field("", description="平仓原因")

class MarketDataUpdate(BaseModel):
    """市场数据更新"""
    symbol: str = Field(..., description="交易标的")
    price: Decimal = Field(..., gt=0, description="当前价格")
    timestamp: Optional[datetime] = Field(None, description="时间戳")

class BatchMarketDataUpdate(BaseModel):
    """批量市场数据更新"""
    price_data: Dict[str, Decimal] = Field(..., description="价格数据字典")
    timestamp: Optional[datetime] = Field(None, description="时间戳")

    @validator('price_data')
    def validate_price_data(cls, v):
        if not v:
            raise ValueError('价格数据不能为空')
        for symbol, price in v.items():
            if price <= 0:
                raise ValueError(f'标的 {symbol} 的价格必须大于0')
        return v

class PositionFilter(BaseModel):
    """持仓筛选条件"""
    status: Optional[PositionStatus] = Field(None, description="持仓状态")
    symbol: Optional[str] = Field(None, description="交易标的")
    position_type: Optional[PositionType] = Field(None, description="持仓类型")
    strategy_id: Optional[int] = Field(None, description="策略ID")
    backtest_id: Optional[int] = Field(None, description="回测ID")
    source: Optional[str] = Field(None, description="持仓来源")
    min_quantity: Optional[Decimal] = Field(None, ge=0, description="最小持仓数量")
    max_quantity: Optional[Decimal] = Field(None, ge=0, description="最大持仓数量")
    min_pnl: Optional[Decimal] = Field(None, description="最小盈亏")
    max_pnl: Optional[Decimal] = Field(None, description="最大盈亏")
    has_stop_loss: Optional[bool] = Field(None, description="是否设置止损")
    has_take_profit: Optional[bool] = Field(None, description="是否设置止盈")
    opened_after: Optional[datetime] = Field(None, description="开仓时间起始")
    opened_before: Optional[datetime] = Field(None, description="开仓时间结束")

class PortfolioMetrics(BaseModel):
    """投资组合指标"""
    total_positions: int = Field(..., description="总持仓数")
    total_market_value: float = Field(..., description="总市值")
    total_cost: float = Field(..., description="总成本")
    total_pnl: float = Field(..., description="总盈亏")
    total_realized_pnl: float = Field(..., description="总已实现盈亏")
    total_unrealized_pnl: float = Field(..., description="总未实现盈亏")
    return_rate: float = Field(..., description="收益率")
    positions_by_symbol: Dict[str, Any] = Field(..., description="按标的分组的持仓")

class PositionStatistics(BaseModel):
    """持仓统计信息"""
    total_positions: int = Field(..., description="总持仓数")
    open_positions: int = Field(..., description="开放持仓数")
    closed_positions: int = Field(..., description="已关闭持仓数")
    profit_positions: int = Field(..., description="盈利持仓数")
    loss_positions: int = Field(..., description="亏损持仓数")
    win_rate: float = Field(..., description="胜率")
    portfolio_metrics: PortfolioMetrics = Field(..., description="投资组合指标")

class StopTrigger(BaseModel):
    """止损止盈触发"""
    position_id: int = Field(..., description="持仓ID")
    symbol: str = Field(..., description="交易标的")
    trigger_type: str = Field(..., description="触发类型")
    trigger_price: float = Field(..., description="触发价格")
    current_price: float = Field(..., description="当前价格")
    order_id: Optional[int] = Field(None, description="关联订单ID")

class PositionConsistencyCheck(BaseModel):
    """持仓一致性检查结果"""
    total_positions_checked: int = Field(..., description="检查的持仓总数")
    inconsistencies_found: int = Field(..., description="发现的不一致数量")
    inconsistencies: List[Dict[str, Any]] = Field(..., description="不一致详情")
    is_consistent: bool = Field(..., description="是否一致")

class PositionRepairResult(BaseModel):
    """持仓修复结果"""
    repaired_positions: int = Field(..., description="修复的持仓数量")
    message: str = Field(..., description="修复结果消息")

class PositionListResponse(BaseModel):
    """持仓列表响应"""
    items: List[PositionResponse] = Field(..., description="持仓列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    has_next: bool = Field(..., description="是否有下一页")

class PositionHistoryListResponse(BaseModel):
    """持仓历史列表响应"""
    items: List[PositionHistoryResponse] = Field(..., description="历史记录列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    has_next: bool = Field(..., description="是否有下一页")

# 持仓操作相关模式
class PositionOperation(BaseModel):
    """持仓操作基础模式"""
    operation_type: str = Field(..., description="操作类型")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="操作参数")
    reason: Optional[str] = Field(None, description="操作原因")

class FreezeQuantityRequest(BaseModel):
    """冻结数量请求"""
    quantity: Decimal = Field(..., gt=0, description="冻结数量")
    reason: Optional[str] = Field(None, description="冻结原因")

class UnfreezeQuantityRequest(BaseModel):
    """解冻数量请求"""
    quantity: Decimal = Field(..., gt=0, description="解冻数量")
    reason: Optional[str] = Field(None, description="解冻原因")

class PositionRiskMetrics(BaseModel):
    """持仓风险指标"""
    position_id: int = Field(..., description="持仓ID")
    symbol: str = Field(..., description="交易标的")
    concentration_risk: float = Field(..., description="集中度风险")
    var_1d: Optional[float] = Field(None, description="1日VaR")
    var_5d: Optional[float] = Field(None, description="5日VaR")
    max_drawdown_ratio: float = Field(..., description="最大回撤比例")
    volatility: Optional[float] = Field(None, description="波动率")
    beta: Optional[float] = Field(None, description="贝塔系数")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")

class PositionAlert(BaseModel):
    """持仓预警"""
    position_id: int = Field(..., description="持仓ID")
    symbol: str = Field(..., description="交易标的")
    alert_type: str = Field(..., description="预警类型")
    alert_level: str = Field(..., description="预警级别")
    message: str = Field(..., description="预警消息")
    threshold: Optional[float] = Field(None, description="阈值")
    current_value: Optional[float] = Field(None, description="当前值")
    created_at: datetime = Field(..., description="创建时间")
# ==================== 持仓操作相关模式 ====================

class ClosePositionRequest(BaseModel):
    """平仓请求"""
    close_type: str = Field(..., description="平仓类型: market, limit")
    close_price: Optional[Decimal] = Field(None, description="平仓价格（限价单时必填）")
    close_quantity: Optional[Decimal] = Field(None, description="平仓数量（不填则全部平仓）")
    
    @validator('close_type')
    def validate_close_type(cls, v):
        if v not in ['market', 'limit']:
            raise ValueError('平仓类型必须是 market 或 limit')
        return v
    
    @validator('close_price')
    def validate_close_price(cls, v, values):
        if values.get('close_type') == 'limit' and v is None:
            raise ValueError('限价平仓必须指定价格')
        if v is not None and v <= 0:
            raise ValueError('平仓价格必须大于0')
        return v
    
    @validator('close_quantity')
    def validate_close_quantity(cls, v):
        if v is not None and v <= 0:
            raise ValueError('平仓数量必须大于0')
        return v


class StopLossRequest(BaseModel):
    """止损请求"""
    stop_price: Decimal = Field(..., description="止损价格")
    trigger_type: str = Field('last_price', description="触发类型: last_price, bid_price, ask_price")
    
    @validator('stop_price')
    def validate_stop_price(cls, v):
        if v <= 0:
            raise ValueError('止损价格必须大于0')
        return v
    
    @validator('trigger_type')
    def validate_trigger_type(cls, v):
        if v not in ['last_price', 'bid_price', 'ask_price']:
            raise ValueError('触发类型必须是 last_price, bid_price 或 ask_price')
        return v


class TakeProfitRequest(BaseModel):
    """止盈请求"""
    profit_price: Decimal = Field(..., description="止盈价格")
    trigger_type: str = Field('last_price', description="触发类型: last_price, bid_price, ask_price")
    
    @validator('profit_price')
    def validate_profit_price(cls, v):
        if v <= 0:
            raise ValueError('止盈价格必须大于0')
        return v
    
    @validator('trigger_type')
    def validate_trigger_type(cls, v):
        if v not in ['last_price', 'bid_price', 'ask_price']:
            raise ValueError('触发类型必须是 last_price, bid_price 或 ask_price')
        return v


# ==================== 风险管理相关模式 ====================

class ConcentrationRiskResponse(BaseModel):
    """集中度风险响应"""
    user_id: int
    total_market_value: float
    position_count: int
    concentration_analysis: Dict[str, Any]
    sector_analysis: Dict[str, Any]
    overall_risk: Dict[str, Any]
    generated_at: str


class RiskAlertResponse(BaseModel):
    """风险预警响应"""
    type: str = Field(..., description="预警类型")
    position_id: Optional[int] = Field(None, description="持仓ID")
    symbol: Optional[str] = Field(None, description="标的代码")
    severity: str = Field(..., description="严重程度: LOW, MEDIUM, HIGH")
    message: str = Field(..., description="预警消息")
    value: Optional[float] = Field(None, description="相关数值")
    timestamp: Optional[str] = Field(None, description="时间戳")


class PositionHistoryResponse(BaseModel):
    """持仓历史响应"""
    position_id: int
    symbol: str
    history: List[Dict[str, Any]]
    total_records: int


# ==================== 实时盈亏相关模式 ====================

class RealtimePnLSummaryResponse(BaseModel):
    """实时盈亏摘要响应"""
    user_id: int
    summary: Dict[str, Any] = Field(..., description="盈亏摘要")
    distribution: Dict[str, Any] = Field(..., description="盈亏分布")
    performers: Dict[str, Any] = Field(..., description="最佳/最差表现")
    updated_at: str


class PositionPnLChartResponse(BaseModel):
    """持仓盈亏图表响应"""
    position_id: int
    symbol: str
    period: str
    data: List[Dict[str, Any]]
    technical_indicators: Dict[str, Any]
    summary: Dict[str, Any]
    generated_at: str


class PortfolioPerformanceChartResponse(BaseModel):
    """组合绩效图表响应"""
    user_id: int
    period: str
    data: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    risk_metrics: Dict[str, Any]
    generated_at: str