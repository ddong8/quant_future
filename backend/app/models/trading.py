"""
交易相关数据模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..core.database import Base
from .enums import OrderDirection, OrderOffset, OrderStatus, PositionDirection


class Order(Base):
    """订单模型"""
    __tablename__ = "orders"
    
    id = Column(String(50), primary_key=True, index=True)  # 使用字符串ID以支持外部订单ID
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    
    # 订单基本信息
    symbol = Column(String(20), nullable=False, index=True)
    direction = Column(String(10), nullable=False)  # buy/sell
    offset = Column(String(20), nullable=False)  # open/close/close_today/close_yesterday
    volume = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    
    # 订单状态
    status = Column(String(20), default=OrderStatus.PENDING, nullable=False)
    filled_volume = Column(Integer, default=0)
    avg_fill_price = Column(Float, default=0.0)
    
    # 手续费和滑点
    commission = Column(Float, default=0.0)
    slippage = Column(Float, default=0.0)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    filled_at = Column(DateTime(timezone=True))
    
    # 备注信息
    notes = Column(Text)
    
    # 关系
    strategy = relationship("Strategy", back_populates="orders")
    
    def __repr__(self):
        return f"<Order(id='{self.id}', symbol='{self.symbol}', direction='{self.direction}', status='{self.status}')>"


class Position(Base):
    """持仓模型"""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    
    # 持仓基本信息
    symbol = Column(String(20), nullable=False, index=True)
    direction = Column(String(10), nullable=False)  # long/short
    volume = Column(Integer, nullable=False)
    avg_price = Column(Float, nullable=False)
    
    # 盈亏信息
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    
    # 保证金信息
    margin = Column(Float, nullable=False)
    margin_rate = Column(Float, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Position(id={self.id}, symbol='{self.symbol}', direction='{self.direction}', volume={self.volume})>"


class Account(Base):
    """账户模型"""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 账户基本信息
    account_id = Column(String(50), unique=True, nullable=False, index=True)
    account_name = Column(String(100))
    broker = Column(String(50))  # 券商名称
    
    # 资金信息
    balance = Column(Float, default=0.0)  # 账户余额
    available = Column(Float, default=0.0)  # 可用资金
    margin = Column(Float, default=0.0)  # 占用保证金
    frozen = Column(Float, default=0.0)  # 冻结资金
    
    # 盈亏信息
    realized_pnl = Column(Float, default=0.0)  # 已实现盈亏
    unrealized_pnl = Column(Float, default=0.0)  # 未实现盈亏
    total_pnl = Column(Float, default=0.0)  # 总盈亏
    
    # 风险指标
    risk_ratio = Column(Float, default=0.0)  # 风险度
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Account(id={self.id}, account_id='{self.account_id}', balance={self.balance})>"