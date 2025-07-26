"""
市场数据相关的Pydantic模型
"""
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class InstrumentInfo(BaseModel):
    """合约信息模型"""
    symbol: str
    exchange: str
    name: str
    product_id: str
    volume_multiple: int
    price_tick: float
    margin_rate: float
    commission_rate: float
    expired: bool
    trading_time: Dict[str, Any]


class QuoteData(BaseModel):
    """行情数据模型"""
    symbol: str
    last_price: float
    bid_price: float
    ask_price: float
    bid_volume: int
    ask_volume: int
    volume: int
    open_interest: int
    open: float
    high: float
    low: float
    pre_close: float
    upper_limit: float
    lower_limit: float
    datetime: str


class KlineData(BaseModel):
    """K线数据模型"""
    datetime: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    open_interest: int


class KlineRequest(BaseModel):
    """K线数据请求模型"""
    symbol: str
    duration: int = 60  # 秒
    data_length: int = 200
    
    @validator('duration')
    def validate_duration(cls, v):
        allowed_durations = [60, 300, 900, 1800, 3600, 86400]  # 1分钟到1天
        if v not in allowed_durations:
            raise ValueError(f'时间周期必须是: {allowed_durations}')
        return v
    
    @validator('data_length')
    def validate_data_length(cls, v):
        if v < 1 or v > 8000:
            raise ValueError('数据长度必须在1-8000之间')
        return v


class QuoteSubscription(BaseModel):
    """行情订阅模型"""
    symbols: List[str]
    
    @validator('symbols')
    def validate_symbols(cls, v):
        if not v:
            raise ValueError('合约列表不能为空')
        if len(v) > 100:
            raise ValueError('单次订阅合约数量不能超过100个')
        return v


class MarketDataFilter(BaseModel):
    """市场数据过滤模型"""
    exchange: Optional[str] = None
    product_id: Optional[str] = None
    expired: Optional[bool] = None
    keyword: Optional[str] = None


class TradingTimeInfo(BaseModel):
    """交易时间信息模型"""
    symbol: str
    trading_time: Dict[str, List[List[str]]]
    is_trading: bool
    next_trading_time: Optional[str] = None


class MarketStatus(BaseModel):
    """市场状态模型"""
    is_trading_time: bool
    current_session: Optional[str] = None
    next_session_start: Optional[str] = None
    market_date: str


class PriceLimit(BaseModel):
    """涨跌停价格模型"""
    symbol: str
    upper_limit: float
    lower_limit: float
    limit_ratio: float


class MarketDepth(BaseModel):
    """市场深度数据模型"""
    symbol: str
    bids: List[List[float]]  # [[价格, 数量], ...]
    asks: List[List[float]]  # [[价格, 数量], ...]
    datetime: str


class TickData(BaseModel):
    """逐笔成交数据模型"""
    symbol: str
    price: float
    volume: int
    direction: str  # "B"买入, "S"卖出, "N"中性
    datetime: str


class MarketSummary(BaseModel):
    """市场概况模型"""
    total_instruments: int
    active_instruments: int
    total_volume: int
    total_turnover: float
    up_count: int
    down_count: int
    unchanged_count: int
    limit_up_count: int
    limit_down_count: int


class InstrumentSearch(BaseModel):
    """合约搜索请求模型"""
    keyword: Optional[str] = None
    exchange: Optional[str] = None
    product_id: Optional[str] = None
    expired: Optional[bool] = False
    
    @validator('keyword')
    def validate_keyword(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError('搜索关键词至少需要2个字符')
        return v.strip() if v else None


class ConnectionStatus(BaseModel):
    """连接状态模型"""
    is_connected: bool
    is_sim_trading: bool
    reconnect_attempts: int
    tqsdk_available: bool
    last_heartbeat: Optional[str] = None
    connection_time: Optional[str] = None


class MarketDataStats(BaseModel):
    """市场数据统计模型"""
    quote_count: int
    kline_count: int
    subscription_count: int
    cache_hit_rate: float
    last_update: str