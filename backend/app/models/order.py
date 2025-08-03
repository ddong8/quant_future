"""
订单相关数据模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON, Float, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid
from decimal import Decimal
from datetime import datetime

from ..core.database import Base


class OrderType(str, PyEnum):
    """订单类型枚举"""
    MARKET = "market"           # 市价单
    LIMIT = "limit"             # 限价单
    STOP = "stop"               # 止损单
    STOP_LIMIT = "stop_limit"   # 止损限价单
    TRAILING_STOP = "trailing_stop"  # 跟踪止损单
    ICEBERG = "iceberg"         # 冰山单
    TWAP = "twap"               # 时间加权平均价格单
    VWAP = "vwap"               # 成交量加权平均价格单


class OrderSide(str, PyEnum):
    """订单方向枚举"""
    BUY = "buy"                 # 买入
    SELL = "sell"               # 卖出


class OrderStatus(str, PyEnum):
    """订单状态枚举"""
    PENDING = "pending"         # 待提交
    SUBMITTED = "submitted"     # 已提交
    ACCEPTED = "accepted"       # 已接受
    PARTIALLY_FILLED = "partially_filled"  # 部分成交
    FILLED = "filled"           # 完全成交
    CANCELLED = "cancelled"     # 已取消
    REJECTED = "rejected"       # 已拒绝
    EXPIRED = "expired"         # 已过期
    SUSPENDED = "suspended"     # 已暂停


class OrderTimeInForce(str, PyEnum):
    """订单有效期类型枚举"""
    DAY = "day"                 # 当日有效
    GTC = "gtc"                 # 撤销前有效 (Good Till Cancelled)
    IOC = "ioc"                 # 立即成交或取消 (Immediate Or Cancel)
    FOK = "fok"                 # 全部成交或取消 (Fill Or Kill)
    GTD = "gtd"                 # 指定日期前有效 (Good Till Date)


class OrderPriority(str, PyEnum):
    """订单优先级枚举"""
    LOW = "low"                 # 低优先级
    NORMAL = "normal"           # 普通优先级
    HIGH = "high"               # 高优先级
    URGENT = "urgent"           # 紧急优先级


class Order(Base):
    """订单模型"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # 基本信息
    symbol = Column(String(20), nullable=False, index=True)  # 交易标的
    order_type = Column(Enum(OrderType), nullable=False, index=True)
    side = Column(Enum(OrderSide), nullable=False, index=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, index=True)
    
    # 数量和价格
    quantity = Column(DECIMAL(20, 8), nullable=False)  # 订单数量
    price = Column(DECIMAL(20, 8))  # 订单价格（市价单可为空）
    stop_price = Column(DECIMAL(20, 8))  # 止损价格
    filled_quantity = Column(DECIMAL(20, 8), default=Decimal('0'))  # 已成交数量
    remaining_quantity = Column(DECIMAL(20, 8))  # 剩余数量
    avg_fill_price = Column(DECIMAL(20, 8))  # 平均成交价格
    
    # 订单属性
    time_in_force = Column(Enum(OrderTimeInForce), default=OrderTimeInForce.DAY)
    priority = Column(Enum(OrderPriority), default=OrderPriority.NORMAL)
    
    # 高级订单参数
    iceberg_quantity = Column(DECIMAL(20, 8))  # 冰山单显示数量
    trailing_amount = Column(DECIMAL(20, 8))   # 跟踪止损金额
    trailing_percent = Column(Float)           # 跟踪止损百分比
    
    # 时间相关
    expire_time = Column(DateTime)  # 过期时间
    submitted_at = Column(DateTime)  # 提交时间
    accepted_at = Column(DateTime)   # 接受时间
    filled_at = Column(DateTime)     # 完全成交时间
    cancelled_at = Column(DateTime)  # 取消时间
    
    # 成交信息
    commission = Column(DECIMAL(20, 8), default=Decimal('0'))  # 手续费
    commission_asset = Column(String(10))  # 手续费资产
    total_value = Column(DECIMAL(20, 8))   # 订单总价值
    
    # 风险控制
    max_position_size = Column(DECIMAL(20, 8))  # 最大持仓限制
    risk_check_passed = Column(Boolean, default=False)  # 风险检查是否通过
    risk_check_message = Column(Text)  # 风险检查消息
    
    # 策略关联
    strategy_id = Column(Integer, ForeignKey("strategies.id"), index=True)
    strategy = relationship("Strategy")
    
    # 回测关联
    backtest_id = Column(Integer, ForeignKey("backtests.id"), index=True)
    backtest = relationship("Backtest")
    
    # 父订单关联（用于算法订单拆分）
    parent_order_id = Column(Integer, ForeignKey("orders.id"), index=True)
    parent_order = relationship("Order", remote_side=[id], back_populates="child_orders")
    child_orders = relationship("Order", back_populates="parent_order")
    
    # 订单来源
    source = Column(String(50), default="manual")  # manual, strategy, algorithm
    source_id = Column(String(100))  # 来源标识
    
    # 执行信息
    broker = Column(String(50))  # 券商/交易所
    account_id = Column(String(100))  # 账户ID
    order_id_external = Column(String(100))  # 外部订单ID
    
    # 元数据
    tags = Column(JSON, default=list)  # 标签
    notes = Column(Text)  # 备注
    order_model_metadata = Column(JSON, default=dict)  # 元数据
    
    # 用户关联
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="orders")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 成交记录关联
    fills = relationship("OrderFill", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(id={self.id}, symbol='{self.symbol}', side='{self.side}', status='{self.status}')>"
    
    @property
    def is_buy(self) -> bool:
        """是否为买单"""
        return self.side == OrderSide.BUY
    
    @property
    def is_sell(self) -> bool:
        """是否为卖单"""
        return self.side == OrderSide.SELL
    
    @property
    def is_market_order(self) -> bool:
        """是否为市价单"""
        return self.order_type == OrderType.MARKET
    
    @property
    def is_limit_order(self) -> bool:
        """是否为限价单"""
        return self.order_type == OrderType.LIMIT
    
    @property
    def is_active(self) -> bool:
        """订单是否处于活跃状态"""
        return self.status in [
            OrderStatus.PENDING,
            OrderStatus.SUBMITTED,
            OrderStatus.ACCEPTED,
            OrderStatus.PARTIALLY_FILLED
        ]
    
    @property
    def is_finished(self) -> bool:
        """订单是否已结束"""
        return self.status in [
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED
        ]
    
    @property
    def fill_ratio(self) -> float:
        """成交比例"""
        if not self.quantity or self.quantity == 0:
            return 0.0
        return float(self.filled_quantity / self.quantity)
    
    def calculate_remaining_quantity(self):
        """计算剩余数量"""
        if self.quantity and self.filled_quantity:
            self.remaining_quantity = self.quantity - self.filled_quantity
        else:
            self.remaining_quantity = self.quantity
    
    def update_avg_fill_price(self):
        """更新平均成交价格"""
        if self.fills:
            total_value = sum(fill.quantity * fill.price for fill in self.fills)
            total_quantity = sum(fill.quantity for fill in self.fills)
            if total_quantity > 0:
                self.avg_fill_price = total_value / total_quantity
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'symbol': self.symbol,
            'order_type': self.order_type,
            'side': self.side,
            'status': self.status,
            'quantity': float(self.quantity) if self.quantity else None,
            'price': float(self.price) if self.price else None,
            'stop_price': float(self.stop_price) if self.stop_price else None,
            'filled_quantity': float(self.filled_quantity) if self.filled_quantity else 0,
            'remaining_quantity': float(self.remaining_quantity) if self.remaining_quantity else None,
            'avg_fill_price': float(self.avg_fill_price) if self.avg_fill_price else None,
            'time_in_force': self.time_in_force,
            'priority': self.priority,
            'iceberg_quantity': float(self.iceberg_quantity) if self.iceberg_quantity else None,
            'trailing_amount': float(self.trailing_amount) if self.trailing_amount else None,
            'trailing_percent': self.trailing_percent,
            'expire_time': self.expire_time.isoformat() if self.expire_time else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'filled_at': self.filled_at.isoformat() if self.filled_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'commission': float(self.commission) if self.commission else 0,
            'commission_asset': self.commission_asset,
            'total_value': float(self.total_value) if self.total_value else None,
            'max_position_size': float(self.max_position_size) if self.max_position_size else None,
            'risk_check_passed': self.risk_check_passed,
            'risk_check_message': self.risk_check_message,
            'strategy_id': self.strategy_id,
            'backtest_id': self.backtest_id,
            'parent_order_id': self.parent_order_id,
            'source': self.source,
            'source_id': self.source_id,
            'broker': self.broker,
            'account_id': self.account_id,
            'order_id_external': self.order_id_external,
            'tags': self.tags,
            'notes': self.notes,
            'metadata': self.order_metadata,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'fill_ratio': self.fill_ratio,
            'is_active': self.is_active,
            'is_finished': self.is_finished
        }


class OrderFill(Base):
    """订单成交记录模型"""
    __tablename__ = "order_fills"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # 订单关联
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    order = relationship("Order", back_populates="fills")
    
    # 成交信息
    fill_id_external = Column(String(100))  # 外部成交ID
    quantity = Column(DECIMAL(20, 8), nullable=False)  # 成交数量
    price = Column(DECIMAL(20, 8), nullable=False)     # 成交价格
    value = Column(DECIMAL(20, 8), nullable=False)     # 成交金额
    
    # 手续费信息
    commission = Column(DECIMAL(20, 8), default=Decimal('0'))
    commission_asset = Column(String(10))
    
    # 成交时间
    fill_time = Column(DateTime, nullable=False)
    
    # 成交来源
    liquidity = Column(String(10))  # maker/taker
    counterparty = Column(String(100))  # 对手方
    
    # 元数据
    fill_model_metadata = Column(JSON, default=dict)
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<OrderFill(id={self.id}, order_id={self.order_id}, quantity={self.quantity}, price={self.price})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'order_id': self.order_id,
            'fill_id_external': self.fill_id_external,
            'quantity': float(self.quantity),
            'price': float(self.price),
            'value': float(self.value),
            'commission': float(self.commission),
            'commission_asset': self.commission_asset,
            'fill_time': self.fill_time.isoformat(),
            'liquidity': self.liquidity,
            'counterparty': self.counterparty,
            'metadata': self.fill_metadata,
            'created_at': self.created_at.isoformat()
        }


class OrderTemplate(Base):
    """订单模板模型"""
    __tablename__ = "order_templates"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # 基本信息
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # 模板分类
    
    # 模板配置
    template_config = Column(JSON, nullable=False)  # 订单模板配置
    default_parameters = Column(JSON, default=dict)  # 默认参数
    
    # 使用统计
    usage_count = Column(Integer, default=0)
    
    # 元数据
    tags = Column(JSON, default=list)
    is_official = Column(Boolean, default=False)  # 是否为官方模板
    is_active = Column(Boolean, default=True)
    
    # 创建者
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<OrderTemplate(id={self.id}, name='{self.name}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'template_config': self.template_config,
            'default_parameters': self.default_parameters,
            'usage_count': self.usage_count,
            'tags': self.tags,
            'is_official': self.is_official,
            'is_active': self.is_active,
            'author_id': self.author_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }