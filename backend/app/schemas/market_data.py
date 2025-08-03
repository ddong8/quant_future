"""
市场数据Schema
"""
from typing import Optional, Dict, List, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from ..models.market_data import DataProvider, DataType, DataStatus

class SymbolBase(BaseModel):
    """交易标的基础模型"""
    symbol: str = Field(..., max_length=20, description="标的代码")
    name: str = Field(..., max_length=200, description="标的名称")
    exchange: str = Field(..., max_length=20, description="交易所")
    market: Optional[str] = Field(None, max_length=20, description="市场")
    sector: Optional[str] = Field(None, max_length=50, description="行业")
    industry: Optional[str] = Field(None, max_length=100, description="子行业")
    asset_type: str = Field(..., max_length=20, description="资产类型")
    currency: str = Field(default="USD", max_length=10, description="计价货币")
    country: Optional[str] = Field(None, max_length=10, description="国家代码")
    is_tradable: bool = Field(default=True, description="是否可交易")
    is_active: bool = Field(default=True, description="是否活跃")
    lot_size: int = Field(default=1, description="最小交易单位")
    tick_size: Optional[Decimal] = Field(None, description="最小价格变动")
    description: Optional[str] = Field(None, description="描述")
    website: Optional[str] = Field(None, description="官网")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他元数据")
    listed_date: Optional[datetime] = Field(None, description="上市日期")
    delisted_date: Optional[datetime] = Field(None, description="退市日期")

class SymbolCreate(SymbolBase):
    """创建交易标的"""
    pass

class SymbolUpdate(BaseModel):
    """更新交易标的"""
    name: Optional[str] = Field(None, max_length=200, description="标的名称")
    sector: Optional[str] = Field(None, max_length=50, description="行业")
    industry: Optional[str] = Field(None, max_length=100, description="子行业")
    is_tradable: Optional[bool] = Field(None, description="是否可交易")
    is_active: Optional[bool] = Field(None, description="是否活跃")
    description: Optional[str] = Field(None, description="描述")
    website: Optional[str] = Field(None, description="官网")
    metadata: Optional[Dict[str, Any]] = Field(None, description="其他元数据")

class SymbolResponse(SymbolBase):
    """交易标的响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class QuoteBase(BaseModel):
    """实时报价基础模型"""
    price: Decimal = Field(..., description="当前价格")
    bid_price: Optional[Decimal] = Field(None, description="买一价")
    ask_price: Optional[Decimal] = Field(None, description="卖一价")
    bid_size: Optional[Decimal] = Field(None, description="买一量")
    ask_size: Optional[Decimal] = Field(None, description="卖一量")
    change: Optional[Decimal] = Field(None, description="价格变动")
    change_percent: Optional[Decimal] = Field(None, description="涨跌幅")
    volume: Optional[Decimal] = Field(None, description="成交量")
    turnover: Optional[Decimal] = Field(None, description="成交额")
    open_price: Optional[Decimal] = Field(None, description="开盘价")
    high_price: Optional[Decimal] = Field(None, description="最高价")
    low_price: Optional[Decimal] = Field(None, description="最低价")
    prev_close: Optional[Decimal] = Field(None, description="昨收价")
    data_provider: str = Field(..., description="数据提供商")
    data_status: str = Field(default="ACTIVE", description="数据状态")
    delay_seconds: int = Field(default=0, description="延迟秒数")
    quote_time: datetime = Field(..., description="报价时间")

class QuoteCreate(QuoteBase):
    """创建实时报价"""
    symbol_id: int = Field(..., description="标的ID")

class QuoteResponse(QuoteBase):
    """实时报价响应"""
    id: int
    symbol_id: int
    received_at: datetime
    symbol: Optional[SymbolResponse] = None
    
    class Config:
        orm_mode = True

class KlineBase(BaseModel):
    """K线数据基础模型"""
    interval: str = Field(..., max_length=10, description="时间间隔")
    open_time: datetime = Field(..., description="开始时间")
    close_time: datetime = Field(..., description="结束时间")
    open_price: Decimal = Field(..., description="开盘价")
    high_price: Decimal = Field(..., description="最高价")
    low_price: Decimal = Field(..., description="最低价")
    close_price: Decimal = Field(..., description="收盘价")
    volume: Decimal = Field(..., description="成交量")
    turnover: Optional[Decimal] = Field(None, description="成交额")
    trade_count: Optional[int] = Field(None, description="成交笔数")
    vwap: Optional[Decimal] = Field(None, description="成交量加权平均价")
    data_provider: str = Field(..., description="数据提供商")
    is_final: bool = Field(default=False, description="是否最终数据")

class KlineCreate(KlineBase):
    """创建K线数据"""
    symbol_id: int = Field(..., description="标的ID")

class KlineResponse(KlineBase):
    """K线数据响应"""
    id: int
    symbol_id: int
    created_at: datetime
    updated_at: datetime
    symbol: Optional[SymbolResponse] = None
    
    class Config:
        orm_mode = True

class TradeBase(BaseModel):
    """成交数据基础模型"""
    trade_id: Optional[str] = Field(None, max_length=50, description="成交ID")
    price: Decimal = Field(..., description="成交价格")
    quantity: Decimal = Field(..., description="成交数量")
    amount: Optional[Decimal] = Field(None, description="成交金额")
    side: Optional[str] = Field(None, max_length=10, description="买卖方向")
    is_buyer_maker: Optional[bool] = Field(None, description="买方是否为挂单方")
    data_provider: str = Field(..., description="数据提供商")
    trade_time: datetime = Field(..., description="成交时间")

class TradeCreate(TradeBase):
    """创建成交数据"""
    symbol_id: int = Field(..., description="标的ID")

class TradeResponse(TradeBase):
    """成交数据响应"""
    id: int
    symbol_id: int
    received_at: datetime
    symbol: Optional[SymbolResponse] = None
    
    class Config:
        orm_mode = True

class DepthDataBase(BaseModel):
    """深度数据基础模型"""
    bids: List[List[Decimal]] = Field(..., description="买盘数据")
    asks: List[List[Decimal]] = Field(..., description="卖盘数据")
    bid_count: Optional[int] = Field(None, description="买盘档数")
    ask_count: Optional[int] = Field(None, description="卖盘档数")
    total_bid_quantity: Optional[Decimal] = Field(None, description="买盘总量")
    total_ask_quantity: Optional[Decimal] = Field(None, description="卖盘总量")
    spread: Optional[Decimal] = Field(None, description="买卖价差")
    spread_percent: Optional[Decimal] = Field(None, description="价差百分比")
    data_provider: str = Field(..., description="数据提供商")
    depth_level: int = Field(default=20, description="深度档数")
    snapshot_time: datetime = Field(..., description="快照时间")

class DepthDataCreate(DepthDataBase):
    """创建深度数据"""
    symbol_id: int = Field(..., description="标的ID")

class DepthDataResponse(DepthDataBase):
    """深度数据响应"""
    id: int
    symbol_id: int
    received_at: datetime
    symbol: Optional[SymbolResponse] = None
    
    class Config:
        orm_mode = True

class DataProviderBase(BaseModel):
    """数据提供商基础模型"""
    name: str = Field(..., max_length=50, description="提供商名称")
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")
    description: Optional[str] = Field(None, description="描述")
    api_endpoint: Optional[str] = Field(None, max_length=200, description="API端点")
    rate_limit: Optional[int] = Field(None, description="速率限制")
    supported_data_types: Optional[List[str]] = Field(default_factory=list, description="支持的数据类型")
    supported_symbols: Optional[List[str]] = Field(default_factory=list, description="支持的标的")
    supported_intervals: Optional[List[str]] = Field(default_factory=list, description="支持的时间间隔")
    is_active: bool = Field(default=True, description="是否启用")
    is_realtime: bool = Field(default=False, description="是否实时")
    delay_seconds: int = Field(default=0, description="延迟秒数")

class DataProviderCreate(DataProviderBase):
    """创建数据提供商"""
    api_key: Optional[str] = Field(None, description="API密钥")
    api_secret: Optional[str] = Field(None, description="API密钥")

class DataProviderUpdate(BaseModel):
    """更新数据提供商"""
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")
    description: Optional[str] = Field(None, description="描述")
    api_endpoint: Optional[str] = Field(None, max_length=200, description="API端点")
    api_key: Optional[str] = Field(None, description="API密钥")
    api_secret: Optional[str] = Field(None, description="API密钥")
    rate_limit: Optional[int] = Field(None, description="速率限制")
    is_active: Optional[bool] = Field(None, description="是否启用")
    delay_seconds: Optional[int] = Field(None, description="延迟秒数")

class DataProviderResponse(DataProviderBase):
    """数据提供商响应"""
    id: int
    reliability_score: Optional[Decimal]
    last_error: Optional[str]
    error_count: int
    last_connected_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class DataSubscriptionBase(BaseModel):
    """数据订阅基础模型"""
    data_types: List[str] = Field(..., description="订阅的数据类型")
    intervals: Optional[List[str]] = Field(default_factory=list, description="订阅的时间间隔")
    is_active: bool = Field(default=True, description="是否激活")
    priority: int = Field(default=1, description="优先级")
    enable_alerts: bool = Field(default=False, description="启用提醒")
    alert_conditions: Optional[Dict[str, Any]] = Field(default_factory=dict, description="提醒条件")

class DataSubscriptionCreate(DataSubscriptionBase):
    """创建数据订阅"""
    symbol_id: int = Field(..., description="标的ID")

class DataSubscriptionUpdate(BaseModel):
    """更新数据订阅"""
    data_types: Optional[List[str]] = Field(None, description="订阅的数据类型")
    intervals: Optional[List[str]] = Field(None, description="订阅的时间间隔")
    is_active: Optional[bool] = Field(None, description="是否激活")
    priority: Optional[int] = Field(None, description="优先级")
    enable_alerts: Optional[bool] = Field(None, description="启用提醒")
    alert_conditions: Optional[Dict[str, Any]] = Field(None, description="提醒条件")

class DataSubscriptionResponse(DataSubscriptionBase):
    """数据订阅响应"""
    id: int
    user_id: int
    symbol_id: int
    subscribed_at: datetime
    last_updated_at: Optional[datetime]
    symbol: Optional[SymbolResponse] = None
    
    class Config:
        orm_mode = True

class WatchlistItemBase(BaseModel):
    """自选股项目基础模型"""
    group_name: str = Field(default="默认", max_length=50, description="分组名称")
    sort_order: int = Field(default=0, description="排序")
    notes: Optional[str] = Field(None, description="备注")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")
    price_alerts: Optional[Dict[str, Any]] = Field(default_factory=dict, description="价格提醒")
    volume_alerts: Optional[Dict[str, Any]] = Field(default_factory=dict, description="成交量提醒")

class WatchlistItemCreate(WatchlistItemBase):
    """创建自选股项目"""
    symbol_id: int = Field(..., description="标的ID")

class WatchlistItemUpdate(BaseModel):
    """更新自选股项目"""
    group_name: Optional[str] = Field(None, max_length=50, description="分组名称")
    sort_order: Optional[int] = Field(None, description="排序")
    notes: Optional[str] = Field(None, description="备注")
    tags: Optional[List[str]] = Field(None, description="标签")
    price_alerts: Optional[Dict[str, Any]] = Field(None, description="价格提醒")
    volume_alerts: Optional[Dict[str, Any]] = Field(None, description="成交量提醒")

class WatchlistItemResponse(WatchlistItemBase):
    """自选股项目响应"""
    id: int
    user_id: int
    symbol_id: int
    added_at: datetime
    last_viewed_at: Optional[datetime]
    symbol: Optional[SymbolResponse] = None
    
    class Config:
        orm_mode = True

class DataQualityMetricResponse(BaseModel):
    """数据质量指标响应"""
    id: int
    data_provider: str
    symbol_id: Optional[int]
    data_type: str
    completeness_score: Optional[Decimal]
    accuracy_score: Optional[Decimal]
    timeliness_score: Optional[Decimal]
    consistency_score: Optional[Decimal]
    overall_score: Optional[Decimal]
    total_records: Optional[int]
    missing_records: Optional[int]
    duplicate_records: Optional[int]
    error_records: Optional[int]
    avg_delay_seconds: Optional[Decimal]
    max_delay_seconds: Optional[int]
    metric_date: datetime
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    created_at: datetime
    symbol: Optional[SymbolResponse] = None
    
    class Config:
        orm_mode = True

class MarketHoursBase(BaseModel):
    """市场交易时间基础模型"""
    exchange: str = Field(..., max_length=20, description="交易所")
    market: Optional[str] = Field(None, max_length=20, description="市场")
    timezone: str = Field(..., max_length=50, description="时区")
    open_time: str = Field(..., max_length=8, description="开市时间")
    close_time: str = Field(..., max_length=8, description="收市时间")
    pre_market_open: Optional[str] = Field(None, max_length=8, description="盘前开始时间")
    pre_market_close: Optional[str] = Field(None, max_length=8, description="盘前结束时间")
    after_market_open: Optional[str] = Field(None, max_length=8, description="盘后开始时间")
    after_market_close: Optional[str] = Field(None, max_length=8, description="盘后结束时间")
    holidays: Optional[List[str]] = Field(default_factory=list, description="休市日期列表")
    is_active: bool = Field(default=True, description="是否启用")

class MarketHoursCreate(MarketHoursBase):
    """创建市场交易时间"""
    pass

class MarketHoursResponse(MarketHoursBase):
    """市场交易时间响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class MarketDataRequest(BaseModel):
    """市场数据请求"""
    symbols: List[str] = Field(..., description="标的代码列表")
    data_types: List[str] = Field(..., description="数据类型列表")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    interval: Optional[str] = Field(None, description="时间间隔")
    limit: Optional[int] = Field(default=1000, description="数量限制")

class MarketDataResponse(BaseModel):
    """市场数据响应"""
    symbol: str
    data_type: str
    data: List[Dict[str, Any]]
    total_count: int
    has_more: bool

class DataProviderStatus(BaseModel):
    """数据提供商状态"""
    name: str
    is_connected: bool
    last_update: Optional[datetime]
    error_message: Optional[str]
    data_delay: int
    quality_score: Optional[Decimal]

class MarketStatus(BaseModel):
    """市场状态"""
    exchange: str
    market: str
    is_open: bool
    next_open: Optional[datetime]
    next_close: Optional[datetime]
    timezone: str
    current_session: Optional[str]  # pre_market, regular, after_market, closed

class SymbolSearch(BaseModel):
    """标的搜索"""
    query: str = Field(..., min_length=1, description="搜索关键词")
    asset_types: Optional[List[str]] = Field(None, description="资产类型筛选")
    exchanges: Optional[List[str]] = Field(None, description="交易所筛选")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量限制")

class SymbolSearchResult(BaseModel):
    """标的搜索结果"""
    symbols: List[SymbolResponse]
    total_count: int
    suggestions: Optional[List[str]] = None

# 自选股相关Schema
class WatchlistCreate(BaseModel):
    """创建自选股"""
    symbol_code: str = Field(..., description="标的代码")

class WatchlistUpdate(BaseModel):
    """更新自选股"""
    sort_order: Optional[int] = Field(None, description="排序")

class WatchlistResponse(BaseModel):
    """自选股响应"""
    id: int
    symbol: SymbolResponse
    quote: Optional[QuoteResponse] = None
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True

# 价格提醒相关Schema
class PriceAlertCreate(BaseModel):
    """创建价格提醒"""
    symbol_code: str = Field(..., description="标的代码")
    alert_type: str = Field(..., description="提醒类型")
    condition_value: float = Field(..., description="条件值")
    comparison_operator: str = Field(..., description="比较操作符")
    is_active: bool = Field(default=True, description="是否启用")
    is_repeatable: bool = Field(default=False, description="是否可重复触发")
    notification_methods: List[str] = Field(default=['websocket'], description="通知方式")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    note: Optional[str] = Field(None, description="备注")

class PriceAlertUpdate(BaseModel):
    """更新价格提醒"""
    condition_value: Optional[float] = Field(None, description="条件值")
    comparison_operator: Optional[str] = Field(None, description="比较操作符")
    is_active: Optional[bool] = Field(None, description="是否启用")
    is_repeatable: Optional[bool] = Field(None, description="是否可重复触发")
    notification_methods: Optional[List[str]] = Field(None, description="通知方式")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    note: Optional[str] = Field(None, description="备注")

class PriceAlertResponse(BaseModel):
    """价格提醒响应"""
    id: int
    symbol: SymbolResponse
    alert_type: str
    condition_value: float
    comparison_operator: str
    is_active: bool
    is_repeatable: bool
    notification_methods: List[str]
    triggered_at: Optional[datetime]
    triggered_price: Optional[float]
    trigger_count: int
    expires_at: Optional[datetime]
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# 市场深度相关Schema
class MarketDepthResponse(BaseModel):
    """市场深度响应"""
    symbol: str
    timestamp: float
    bids: List[Dict[str, float]]
    asks: List[Dict[str, float]]
    statistics: Dict[str, Any]

class MarketAnomalyResponse(BaseModel):
    """市场异动响应"""
    id: int
    symbol: SymbolResponse
    anomaly_type: str
    severity: str
    title: str
    description: str
    trigger_price: float
    price_change: float
    price_change_percent: float
    volume_ratio: float
    detected_at: datetime
    is_processed: bool
    is_notified: bool

    class Config:
        from_attributes = True