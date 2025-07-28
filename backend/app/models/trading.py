"""
交易相关数据模型
"""
from sqlalchemy import Column, Integer, String, Decimal, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime

from ..core.database import Base
from .enums import OrderStatus, OrderType, OrderSide, PositionSide, TransactionType


class Order(Base):
    """订单模型"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("trading_accounts.id"), nullable=False, index=True)
    
    # 订单基本信息
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(SQLEnum(OrderSide), nullable=False)
    order_type = Column(SQLEnum(OrderType), nullable=False)
    quantity = Column(Decimal(precision=18, scale=8), nullable=False)
    price = Column(Decimal(precision=18, scale=8), nullable=True)
    stop_price = Column(Decimal(precision=18, scale=8), nullable=True)
    time_in_force = Column(String(10), default='GTC')
    
    # 订单状态和执行信息
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    filled_quantity = Column(Decimal(precision=18, scale=8), default=0)
    filled_amount = Column(Decimal(precision=18, scale=8), default=0)
    average_price = Column(Decimal(precision=18, scale=8), nullable=True)
    commission = Column(Decimal(precision=18, scale=8), default=0)
    realized_pnl = Column(Decimal(precision=18, scale=8), default=0)
    
    # 外部订单ID
    exchange_order_id = Column(String(100), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    last_fill_time = Column(DateTime, nullable=True)
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    
    # 备注
    notes = Column(Text, nullable=True)
    
    # 关系
    user = relationship("User", back_populates="orders")
    account = relationship("TradingAccount", back_populates="orders")
    
    def __repr__(self):
        return f"<Order(order_id='{self.order_id}', symbol='{self.symbol}', side='{self.side}', status='{self.status}')>"


class Position(Base):
    """持仓模型"""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 持仓基本信息
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(SQLEnum(PositionSide), nullable=False)
    quantity = Column(Decimal(precision=18, scale=8), nullable=False)
    average_price = Column(Decimal(precision=18, scale=8), nullable=False)
    
    # 市值和盈亏
    market_value = Column(Decimal(precision=18, scale=8), default=0)
    unrealized_pnl = Column(Decimal(precision=18, scale=8), default=0)
    realized_pnl = Column(Decimal(precision=18, scale=8), default=0)
    
    # 冻结数量
    frozen_quantity = Column(Decimal(precision=18, scale=8), default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="positions")
    
    def __repr__(self):
        return f"<Position(symbol='{self.symbol}', side='{self.side}', quantity={self.quantity})>"


class TradingAccount(Base):
    """交易账户模型"""
    __tablename__ = "trading_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    account_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # 资金信息
    total_balance = Column(Decimal(precision=18, scale=2), default=0)
    available_balance = Column(Decimal(precision=18, scale=2), default=0)
    used_margin = Column(Decimal(precision=18, scale=2), default=0)
    frozen_balance = Column(Decimal(precision=18, scale=2), default=0)
    
    # 盈亏和费用
    realized_pnl = Column(Decimal(precision=18, scale=2), default=0)
    unrealized_pnl = Column(Decimal(precision=18, scale=2), default=0)
    commission_paid = Column(Decimal(precision=18, scale=2), default=0)
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="trading_account")
    orders = relationship("Order", back_populates="account")
    transactions = relationship("AccountTransaction", back_populates="account")
    
    def __repr__(self):
        return f"<TradingAccount(account_id='{self.account_id}', balance={self.total_balance})>"


class AccountTransaction(Base):
    """账户交易流水模型"""
    __tablename__ = "account_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("trading_accounts.id"), nullable=False, index=True)
    
    # 交易信息
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    amount = Column(Decimal(precision=18, scale=2), nullable=False)
    description = Column(String(200), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    account = relationship("TradingAccount", back_populates="transactions")
    
    def __repr__(self):
        return f"<AccountTransaction(type='{self.transaction_type}', amount={self.amount})>"