"""
市场数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from ..core.database import Base

class DataProvider(str, Enum):
    """数据提供商"""
    YAHOO_FINANCE = "YAHOO_FINANCE"
    ALPHA_VANTAGE = "ALPHA_VANTAGE"
    POLYGON = "POLYGON"
    IEX_CLOUD = "IEX_CLOUD"
    FINNHUB = "FINNHUB"
    QUANDL = "QUANDL"
    INTERNAL = "INTERNAL"

class DataType(str, Enum):
    """数据类型"""
    QUOTE = "QUOTE"           # 实时报价
    TRADE = "TRADE"           # 成交数据
    KLINE = "KLINE"           # K线数据
    DEPTH = "DEPTH"           # 深度数据
    NEWS = "NEWS"             # 新闻数据
    FUNDAMENTAL = "FUNDAMENTAL" # 基本面数据

class DataStatus(str, Enum):
    """数据状态"""
    ACTIVE = "ACTIVE"         # 活跃
    DELAYED = "DELAYED"       # 延迟
    STALE = "STALE"          # 过期
    ERROR = "ERROR"          # 错误

class Symbol(Base):
    """交易标的"""
    __tablename__ = "symbols"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    symbol = Column(String(20), nullable=False, unique=True, index=True, comment="标的代码")
    name = Column(String(200), nullable=False, comment="标的名称")
    exchange = Column(String(20), nullable=False, comment="交易所")
    market = Column(String(20), comment="市场")
    sector = Column(String(50), comment="行业")
    industry = Column(String(100), comment="子行业")
    
    # 分类信息
    asset_type = Column(String(20), nullable=False, comment="资产类型")  # stock, etf, crypto, forex, commodity
    currency = Column(String(10), default="USD", comment="计价货币")
    country = Column(String(10), comment="国家代码")
    
    # 交易信息
    is_tradable = Column(Boolean, default=True, comment="是否可交易")
    is_active = Column(Boolean, default=True, comment="是否活跃")
    lot_size = Column(Integer, default=1, comment="最小交易单位")
    tick_size = Column(Numeric(10, 6), comment="最小价格变动")
    
    # 元数据
    description = Column(Text, comment="描述")
    website = Column(String(200), comment="官网")
    model_metadata = Column(JSON, comment="其他元数据")
    
    # 时间信息
    listed_date = Column(DateTime, comment="上市日期")
    delisted_date = Column(DateTime, comment="退市日期")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    quotes = relationship("Quote", back_populates="symbol", cascade="all, delete-orphan")
    klines = relationship("Kline", back_populates="symbol", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="symbol", cascade="all, delete-orphan")
    depth_data = relationship("DepthData", back_populates="symbol", cascade="all, delete-orphan")
    watchlists = relationship("WatchlistItem", back_populates="symbol", cascade="all, delete-orphan")

class Quote(Base):
    """实时报价"""
    __tablename__ = "quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    
    # 价格信息
    price = Column(Numeric(15, 6), nullable=False, comment="当前价格")
    bid_price = Column(Numeric(15, 6), comment="买一价")
    ask_price = Column(Numeric(15, 6), comment="卖一价")
    bid_size = Column(Numeric(15, 2), comment="买一量")
    ask_size = Column(Numeric(15, 2), comment="卖一量")
    
    # 变动信息
    change = Column(Numeric(15, 6), comment="价格变动")
    change_percent = Column(Numeric(8, 4), comment="涨跌幅")
    
    # 交易信息
    volume = Column(Numeric(20, 2), comment="成交量")
    turnover = Column(Numeric(20, 2), comment="成交额")
    open_price = Column(Numeric(15, 6), comment="开盘价")
    high_price = Column(Numeric(15, 6), comment="最高价")
    low_price = Column(Numeric(15, 6), comment="最低价")
    prev_close = Column(Numeric(15, 6), comment="昨收价")
    
    # 数据质量
    data_provider = Column(String(20), nullable=False, comment="数据提供商")
    data_status = Column(String(20), default="ACTIVE", comment="数据状态")
    delay_seconds = Column(Integer, default=0, comment="延迟秒数")
    
    # 时间信息
    quote_time = Column(DateTime, nullable=False, index=True, comment="报价时间")
    received_at = Column(DateTime, server_default=func.now(), comment="接收时间")
    
    # 关系
    symbol = relationship("Symbol", back_populates="quotes")
    
    # 索引
    __table_args__ = (
        Index('ix_quotes_symbol_time', 'symbol_id', 'quote_time'),
        Index('ix_quotes_provider_status', 'data_provider', 'data_status'),
    )

class Kline(Base):
    """K线数据"""
    __tablename__ = "klines"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    
    # 时间信息
    interval = Column(String(10), nullable=False, comment="时间间隔")  # 1m, 5m, 15m, 1h, 1d, 1w, 1M
    open_time = Column(DateTime, nullable=False, index=True, comment="开始时间")
    close_time = Column(DateTime, nullable=False, comment="结束时间")
    
    # OHLCV数据
    open_price = Column(Numeric(15, 6), nullable=False, comment="开盘价")
    high_price = Column(Numeric(15, 6), nullable=False, comment="最高价")
    low_price = Column(Numeric(15, 6), nullable=False, comment="最低价")
    close_price = Column(Numeric(15, 6), nullable=False, comment="收盘价")
    volume = Column(Numeric(20, 2), nullable=False, comment="成交量")
    turnover = Column(Numeric(20, 2), comment="成交额")
    
    # 统计信息
    trade_count = Column(Integer, comment="成交笔数")
    vwap = Column(Numeric(15, 6), comment="成交量加权平均价")
    
    # 数据质量
    data_provider = Column(String(20), nullable=False, comment="数据提供商")
    is_final = Column(Boolean, default=False, comment="是否最终数据")
    
    # 时间信息
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    symbol = relationship("Symbol", back_populates="klines")
    
    # 索引和约束
    __table_args__ = (
        Index('ix_klines_symbol_interval_time', 'symbol_id', 'interval', 'open_time'),
        Index('ix_klines_provider', 'data_provider'),
    )

class Trade(Base):
    """成交数据"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    
    # 成交信息
    trade_id = Column(String(50), comment="成交ID")
    price = Column(Numeric(15, 6), nullable=False, comment="成交价格")
    quantity = Column(Numeric(15, 2), nullable=False, comment="成交数量")
    amount = Column(Numeric(20, 2), comment="成交金额")
    
    # 方向信息
    side = Column(String(10), comment="买卖方向")  # BUY, SELL, UNKNOWN
    is_buyer_maker = Column(Boolean, comment="买方是否为挂单方")
    
    # 数据质量
    data_provider = Column(String(20), nullable=False, comment="数据提供商")
    
    # 时间信息
    trade_time = Column(DateTime, nullable=False, index=True, comment="成交时间")
    received_at = Column(DateTime, server_default=func.now(), comment="接收时间")
    
    # 关系
    symbol = relationship("Symbol", back_populates="trades")
    
    # 索引
    __table_args__ = (
        Index('ix_trades_symbol_time', 'symbol_id', 'trade_time'),
        Index('ix_trades_provider', 'data_provider'),
    )

class DepthData(Base):
    """深度数据"""
    __tablename__ = "depth_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    
    # 深度信息
    bids = Column(JSON, nullable=False, comment="买盘数据")  # [[price, quantity], ...]
    asks = Column(JSON, nullable=False, comment="卖盘数据")  # [[price, quantity], ...]
    
    # 统计信息
    bid_count = Column(Integer, comment="买盘档数")
    ask_count = Column(Integer, comment="卖盘档数")
    total_bid_quantity = Column(Numeric(20, 2), comment="买盘总量")
    total_ask_quantity = Column(Numeric(20, 2), comment="卖盘总量")
    spread = Column(Numeric(15, 6), comment="买卖价差")
    spread_percent = Column(Numeric(8, 4), comment="价差百分比")
    
    # 数据质量
    data_provider = Column(String(20), nullable=False, comment="数据提供商")
    depth_level = Column(Integer, default=20, comment="深度档数")
    
    # 时间信息
    snapshot_time = Column(DateTime, nullable=False, index=True, comment="快照时间")
    received_at = Column(DateTime, server_default=func.now(), comment="接收时间")
    
    # 关系
    symbol = relationship("Symbol", back_populates="depth_data")
    
    # 索引
    __table_args__ = (
        Index('ix_depth_data_symbol_time', 'symbol_id', 'snapshot_time'),
        Index('ix_depth_data_provider', 'data_provider'),
    )

class DataProvider(Base):
    """数据提供商配置"""
    __tablename__ = "data_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    name = Column(String(50), nullable=False, unique=True, comment="提供商名称")
    display_name = Column(String(100), comment="显示名称")
    description = Column(Text, comment="描述")
    
    # 配置信息
    api_endpoint = Column(String(200), comment="API端点")
    api_key = Column(String(200), comment="API密钥")
    api_secret = Column(String(200), comment="API密钥")
    rate_limit = Column(Integer, comment="速率限制")
    
    # 支持的数据类型
    supported_data_types = Column(JSON, comment="支持的数据类型")
    supported_symbols = Column(JSON, comment="支持的标的")
    supported_intervals = Column(JSON, comment="支持的时间间隔")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_realtime = Column(Boolean, default=False, comment="是否实时")
    delay_seconds = Column(Integer, default=0, comment="延迟秒数")
    
    # 质量指标
    reliability_score = Column(Numeric(5, 2), comment="可靠性评分")
    last_error = Column(Text, comment="最后错误")
    error_count = Column(Integer, default=0, comment="错误次数")
    
    # 时间信息
    last_connected_at = Column(DateTime, comment="最后连接时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

class DataSubscription(Base):
    """数据订阅"""
    __tablename__ = "data_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    
    # 订阅信息
    data_types = Column(JSON, nullable=False, comment="订阅的数据类型")
    intervals = Column(JSON, comment="订阅的时间间隔")
    
    # 配置信息
    is_active = Column(Boolean, default=True, comment="是否激活")
    priority = Column(Integer, default=1, comment="优先级")
    
    # 通知设置
    enable_alerts = Column(Boolean, default=False, comment="启用提醒")
    alert_conditions = Column(JSON, comment="提醒条件")
    
    # 时间信息
    subscribed_at = Column(DateTime, server_default=func.now(), comment="订阅时间")
    last_updated_at = Column(DateTime, comment="最后更新时间")
    
    # 关系
    user = relationship("User")
    symbol = relationship("Symbol")
    
    # 索引
    __table_args__ = (
        Index('ix_data_subscriptions_user_symbol', 'user_id', 'symbol_id'),
    )

class WatchlistItem(Base):
    """自选股项目"""
    __tablename__ = "watchlist_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    
    # 分组信息
    group_name = Column(String(50), default="默认", comment="分组名称")
    sort_order = Column(Integer, default=0, comment="排序")
    
    # 配置信息
    notes = Column(Text, comment="备注")
    tags = Column(JSON, comment="标签")
    
    # 提醒设置
    price_alerts = Column(JSON, comment="价格提醒")
    volume_alerts = Column(JSON, comment="成交量提醒")
    
    # 时间信息
    added_at = Column(DateTime, server_default=func.now(), comment="添加时间")
    last_viewed_at = Column(DateTime, comment="最后查看时间")
    
    # 关系
    user = relationship("User")
    symbol = relationship("Symbol", back_populates="watchlists")
    
    # 索引
    __table_args__ = (
        Index('ix_watchlist_items_user_group', 'user_id', 'group_name'),
    )

class DataQualityMetric(Base):
    """数据质量指标"""
    __tablename__ = "data_quality_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 标识信息
    data_provider = Column(String(20), nullable=False, comment="数据提供商")
    symbol_id = Column(Integer, ForeignKey("symbols.id"), index=True, comment="标的ID")
    data_type = Column(String(20), nullable=False, comment="数据类型")
    
    # 质量指标
    completeness_score = Column(Numeric(5, 2), comment="完整性评分")
    accuracy_score = Column(Numeric(5, 2), comment="准确性评分")
    timeliness_score = Column(Numeric(5, 2), comment="及时性评分")
    consistency_score = Column(Numeric(5, 2), comment="一致性评分")
    overall_score = Column(Numeric(5, 2), comment="综合评分")
    
    # 统计信息
    total_records = Column(Integer, comment="总记录数")
    missing_records = Column(Integer, comment="缺失记录数")
    duplicate_records = Column(Integer, comment="重复记录数")
    error_records = Column(Integer, comment="错误记录数")
    
    # 延迟统计
    avg_delay_seconds = Column(Numeric(10, 2), comment="平均延迟秒数")
    max_delay_seconds = Column(Integer, comment="最大延迟秒数")
    
    # 时间范围
    metric_date = Column(DateTime, nullable=False, index=True, comment="指标日期")
    start_time = Column(DateTime, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    
    # 时间信息
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关系
    symbol = relationship("Symbol")
    
    # 索引
    __table_args__ = (
        Index('ix_data_quality_provider_date', 'data_provider', 'metric_date'),
        Index('ix_data_quality_symbol_type', 'symbol_id', 'data_type'),
    )

class MarketHours(Base):
    """市场交易时间"""
    __tablename__ = "market_hours"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 市场信息
    exchange = Column(String(20), nullable=False, comment="交易所")
    market = Column(String(20), comment="市场")
    timezone = Column(String(50), nullable=False, comment="时区")
    
    # 交易时间
    open_time = Column(String(8), nullable=False, comment="开市时间")  # HH:MM:SS
    close_time = Column(String(8), nullable=False, comment="收市时间")  # HH:MM:SS
    
    # 特殊时间
    pre_market_open = Column(String(8), comment="盘前开始时间")
    pre_market_close = Column(String(8), comment="盘前结束时间")
    after_market_open = Column(String(8), comment="盘后开始时间")
    after_market_close = Column(String(8), comment="盘后结束时间")
    
    # 休市日期
    holidays = Column(JSON, comment="休市日期列表")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 时间信息
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
class Watchlist(Base):
    """用户自选股（简化版）"""
    __tablename__ = "watchlist"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False, comment="排序")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关系
    user = relationship("User", back_populates="watchlist")
    symbol = relationship("Symbol")
    
    # 索引和约束
    __table_args__ = (
        Index('ix_watchlist_user_symbol', 'user_id', 'symbol_id'),
    )


class PriceAlert(Base):
    """价格提醒"""
    __tablename__ = "price_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    
    # 提醒条件
    alert_type = Column(String(20), nullable=False, comment="提醒类型")  # PRICE_ABOVE, PRICE_BELOW, CHANGE_PERCENT, VOLUME
    condition_value = Column(Numeric(15, 6), nullable=False, comment="条件值")
    comparison_operator = Column(String(10), nullable=False, comment="比较操作符")  # >, <, >=, <=, =
    
    # 提醒设置
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    is_repeatable = Column(Boolean, default=False, nullable=False, comment="是否可重复触发")
    notification_methods = Column(JSON, comment="通知方式")  # ['email', 'sms', 'push', 'websocket']
    
    # 触发信息
    triggered_at = Column(DateTime, comment="触发时间")
    triggered_price = Column(Numeric(15, 6), comment="触发价格")
    trigger_count = Column(Integer, default=0, comment="触发次数")
    
    # 有效期
    expires_at = Column(DateTime, comment="过期时间")
    
    # 备注
    note = Column(Text, comment="备注")
    
    # 时间信息
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User")
    symbol = relationship("Symbol")
    
    # 索引
    __table_args__ = (
        Index('ix_price_alerts_user_symbol', 'user_id', 'symbol_id'),
        Index('ix_price_alerts_active', 'is_active', 'expires_at'),
    )

class MarketAnomaly(Base):
    """市场异动"""
    __tablename__ = "market_anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    
    # 异动信息
    anomaly_type = Column(String(20), nullable=False, comment="异动类型")  # PRICE_SPIKE, VOLUME_SURGE, GAP_UP, GAP_DOWN
    severity = Column(String(10), nullable=False, comment="严重程度")  # LOW, MEDIUM, HIGH, CRITICAL
    
    # 异动数据
    trigger_price = Column(Numeric(15, 6), comment="触发价格")
    price_change = Column(Numeric(15, 6), comment="价格变动")
    price_change_percent = Column(Numeric(8, 4), comment="价格变动百分比")
    volume_ratio = Column(Numeric(8, 2), comment="成交量倍数")
    
    # 描述信息
    title = Column(String(200), nullable=False, comment="异动标题")
    description = Column(Text, comment="异动描述")
    
    # 状态信息
    is_processed = Column(Boolean, default=False, comment="是否已处理")
    is_notified = Column(Boolean, default=False, comment="是否已通知")
    
    # 时间信息
    detected_at = Column(DateTime, nullable=False, comment="检测时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关系
    symbol = relationship("Symbol")
    
    # 索引
    __table_args__ = (
        Index('ix_market_anomalies_symbol_time', 'symbol_id', 'detected_at'),
        Index('ix_market_anomalies_severity', 'severity', 'is_processed'),
    )