"""
订单相关的Pydantic模式
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from ..models.order import OrderType, OrderSide, OrderStatus, OrderTimeInForce, OrderPriority


class OrderBase(BaseModel):
    """订单基础模式"""
    symbol: str = Field(..., min_length=1, max_length=20, description="交易标的")
    order_type: OrderType = Field(..., description="订单类型")
    side: OrderSide = Field(..., description="订单方向")
    quantity: Decimal = Field(..., gt=0, description="订单数量")
    price: Optional[Decimal] = Field(None, gt=0, description="订单价格")
    stop_price: Optional[Decimal] = Field(None, gt=0, description="止损价格")
    time_in_force: OrderTimeInForce = Field(OrderTimeInForce.DAY, description="有效期类型")
    priority: OrderPriority = Field(OrderPriority.NORMAL, description="订单优先级")
    
    # 高级订单参数
    iceberg_quantity: Optional[Decimal] = Field(None, gt=0, description="冰山单显示数量")
    trailing_amount: Optional[Decimal] = Field(None, gt=0, description="跟踪止损金额")
    trailing_percent: Optional[float] = Field(None, gt=0, le=100, description="跟踪止损百分比")
    
    # 时间相关
    expire_time: Optional[datetime] = Field(None, description="过期时间")
    
    # 风险控制
    max_position_size: Optional[Decimal] = Field(None, gt=0, description="最大持仓限制")
    
    # 关联信息
    strategy_id: Optional[int] = Field(None, description="策略ID")
    backtest_id: Optional[int] = Field(None, description="回测ID")
    parent_order_id: Optional[int] = Field(None, description="父订单ID")
    
    # 执行信息
    broker: Optional[str] = Field(None, max_length=50, description="券商/交易所")
    account_id: Optional[str] = Field(None, max_length=100, description="账户ID")
    
    # 元数据
    tags: List[str] = Field(default_factory=list, description="标签")
    notes: Optional[str] = Field(None, description="备注")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    @validator('price')
    def validate_price(cls, v, values):
        order_type = values.get('order_type')
        if order_type == OrderType.MARKET and v is not None:
            raise ValueError('市价单不需要指定价格')
        if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and v is None:
            raise ValueError('限价单必须指定价格')
        return v

    @validator('stop_price')
    def validate_stop_price(cls, v, values):
        order_type = values.get('order_type')
        if order_type in [OrderType.STOP, OrderType.STOP_LIMIT, OrderType.TRAILING_STOP] and v is None:
            raise ValueError('止损单必须指定止损价格')
        return v

    @validator('iceberg_quantity')
    def validate_iceberg_quantity(cls, v, values):
        if v is not None:
            quantity = values.get('quantity')
            if quantity and v >= quantity:
                raise ValueError('冰山单显示数量必须小于总数量')
        return v

    @validator('expire_time')
    def validate_expire_time(cls, v, values):
        time_in_force = values.get('time_in_force')
        if time_in_force == OrderTimeInForce.GTD and v is None:
            raise ValueError('GTD订单必须指定过期时间')
        if v and v <= datetime.now():
            raise ValueError('过期时间必须晚于当前时间')
        return v


class OrderCreate(OrderBase):
    """创建订单模式"""
    pass


class OrderUpdate(BaseModel):
    """更新订单模式"""
    quantity: Optional[Decimal] = Field(None, gt=0)
    price: Optional[Decimal] = Field(None, gt=0)
    stop_price: Optional[Decimal] = Field(None, gt=0)
    time_in_force: Optional[OrderTimeInForce] = None
    priority: Optional[OrderPriority] = None
    expire_time: Optional[datetime] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class OrderResponse(OrderBase):
    """订单响应模式"""
    id: int
    uuid: str
    status: OrderStatus
    filled_quantity: Decimal
    remaining_quantity: Optional[Decimal]
    avg_fill_price: Optional[Decimal]
    commission: Decimal
    commission_asset: Optional[str]
    total_value: Optional[Decimal]
    risk_check_passed: bool
    risk_check_message: Optional[str]
    source: str
    source_id: Optional[str]
    order_id_external: Optional[str]
    user_id: int
    submitted_at: Optional[datetime]
    accepted_at: Optional[datetime]
    filled_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    fill_ratio: float
    is_active: bool
    is_finished: bool

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """订单列表响应模式"""
    id: int
    uuid: str
    symbol: str
    order_type: OrderType
    side: OrderSide
    status: OrderStatus
    quantity: Decimal
    price: Optional[Decimal]
    filled_quantity: Decimal
    avg_fill_price: Optional[Decimal]
    time_in_force: OrderTimeInForce
    priority: OrderPriority
    strategy_id: Optional[int]
    backtest_id: Optional[int]
    tags: List[str]
    user_id: int
    created_at: datetime
    updated_at: datetime
    fill_ratio: float
    is_active: bool

    class Config:
        from_attributes = True


class OrderSearchParams(BaseModel):
    """订单搜索参数"""
    symbol: Optional[str] = Field(None, description="交易标的")
    order_type: Optional[OrderType] = Field(None, description="订单类型")
    side: Optional[OrderSide] = Field(None, description="订单方向")
    status: Optional[OrderStatus] = Field(None, description="订单状态")
    strategy_id: Optional[int] = Field(None, description="策略ID")
    backtest_id: Optional[int] = Field(None, description="回测ID")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    created_after: Optional[datetime] = Field(None, description="创建时间起始")
    created_before: Optional[datetime] = Field(None, description="创建时间结束")
    min_quantity: Optional[Decimal] = Field(None, ge=0, description="最小数量")
    max_quantity: Optional[Decimal] = Field(None, ge=0, description="最大数量")
    min_price: Optional[Decimal] = Field(None, ge=0, description="最小价格")
    max_price: Optional[Decimal] = Field(None, ge=0, description="最大价格")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")

    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = [
            'created_at', 'updated_at', 'symbol', 'quantity', 'price',
            'filled_quantity', 'status', 'priority'
        ]
        if v not in allowed_fields:
            raise ValueError(f'排序字段必须是: {", ".join(allowed_fields)}')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('排序方向必须是 asc 或 desc')
        return v.lower()


class OrderStatsResponse(BaseModel):
    """订单统计响应模式"""
    total_orders: int
    active_orders: int
    filled_orders: int
    cancelled_orders: int
    rejected_orders: int
    total_volume: Decimal
    total_value: Decimal
    avg_fill_ratio: float
    success_rate: float

    class Config:
        from_attributes = True


class OrderActionRequest(BaseModel):
    """订单操作请求模式"""
    action: str = Field(..., description="操作类型: cancel, modify")
    parameters: Optional[Dict[str, Any]] = Field(None, description="操作参数")

    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['cancel', 'modify', 'suspend', 'resume']
        if v not in allowed_actions:
            raise ValueError(f'操作类型必须是: {", ".join(allowed_actions)}')
        return v


class OrderActionResponse(BaseModel):
    """订单操作响应模式"""
    order_id: int
    action: str
    success: bool
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True


class OrderFillResponse(BaseModel):
    """订单成交响应模式"""
    id: int
    uuid: str
    order_id: int
    fill_id_external: Optional[str]
    quantity: Decimal
    price: Decimal
    value: Decimal
    commission: Decimal
    commission_asset: Optional[str]
    fill_time: datetime
    liquidity: Optional[str]
    counterparty: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class OrderTemplateBase(BaseModel):
    """订单模板基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    category: Optional[str] = Field(None, max_length=50, description="模板分类")
    template_config: Dict[str, Any] = Field(..., description="模板配置")
    default_parameters: Dict[str, Any] = Field(default_factory=dict, description="默认参数")
    tags: List[str] = Field(default_factory=list, description="标签")


class OrderTemplateCreate(OrderTemplateBase):
    """创建订单模板模式"""
    pass


class OrderTemplateUpdate(BaseModel):
    """更新订单模板模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    template_config: Optional[Dict[str, Any]] = None
    default_parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class OrderTemplateResponse(OrderTemplateBase):
    """订单模板响应模式"""
    id: int
    uuid: str
    usage_count: int
    is_official: bool
    is_active: bool
    author_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderRiskCheckRequest(BaseModel):
    """订单风险检查请求模式"""
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Optional[Decimal] = None
    order_type: OrderType
    strategy_id: Optional[int] = None


class OrderRiskCheckResponse(BaseModel):
    """订单风险检查响应模式"""
    passed: bool
    risk_level: str  # low, medium, high
    warnings: List[str]
    errors: List[str]
    suggestions: List[str]
    risk_score: float
    max_allowed_quantity: Optional[Decimal]
    estimated_margin: Optional[Decimal]

    class Config:
        from_attributes = True


class OrderExecutionReport(BaseModel):
    """订单执行报告模式"""
    order_id: int
    execution_id: str
    status: OrderStatus
    filled_quantity: Decimal
    remaining_quantity: Decimal
    avg_price: Optional[Decimal]
    last_fill_price: Optional[Decimal]
    last_fill_quantity: Optional[Decimal]
    commission: Decimal
    timestamp: datetime
    message: Optional[str]

    class Config:
        from_attributes = True