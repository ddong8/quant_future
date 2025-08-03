"""
交易相关数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime

from ..core.database import Base
from .enums import OrderStatus, OrderType, OrderSide, PositionSide, TransactionType




class TradingAccount(Base):
    """交易账户模型"""
    __tablename__ = "trading_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    account_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # 资金信息
    total_balance = Column(Numeric(precision=18, scale=2), default=0)
    available_balance = Column(Numeric(precision=18, scale=2), default=0)
    used_margin = Column(Numeric(precision=18, scale=2), default=0)
    frozen_balance = Column(Numeric(precision=18, scale=2), default=0)
    
    # 盈亏和费用
    realized_pnl = Column(Numeric(precision=18, scale=2), default=0)
    unrealized_pnl = Column(Numeric(precision=18, scale=2), default=0)
    commission_paid = Column(Numeric(precision=18, scale=2), default=0)
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="trading_account")
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
    amount = Column(Numeric(precision=18, scale=2), nullable=False)
    description = Column(String(200), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    account = relationship("TradingAccount", back_populates="transactions")
    
    def __repr__(self):
        return f"<AccountTransaction(type='{self.transaction_type}', amount={self.amount})>"