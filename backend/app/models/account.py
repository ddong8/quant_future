"""
账户管理数据模型
"""
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Boolean, ForeignKey, Enum, Text, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Dict, Any, Optional

from ..core.database import Base


class AccountType(PyEnum):
    """账户类型"""
    CASH = "CASH"           # 现金账户
    MARGIN = "MARGIN"       # 保证金账户
    FUTURES = "FUTURES"     # 期货账户
    OPTIONS = "OPTIONS"     # 期权账户


class AccountStatus(PyEnum):
    """账户状态"""
    ACTIVE = "ACTIVE"       # 活跃
    INACTIVE = "INACTIVE"   # 非活跃
    SUSPENDED = "SUSPENDED" # 暂停
    CLOSED = "CLOSED"       # 关闭


class TransactionType(PyEnum):
    """交易类型"""
    DEPOSIT = "DEPOSIT"         # 入金
    WITHDRAWAL = "WITHDRAWAL"   # 出金
    TRADE_BUY = "TRADE_BUY"    # 买入交易
    TRADE_SELL = "TRADE_SELL"  # 卖出交易
    DIVIDEND = "DIVIDEND"       # 股息
    INTEREST = "INTEREST"       # 利息
    FEE = "FEE"                # 手续费
    TAX = "TAX"                # 税费
    ADJUSTMENT = "ADJUSTMENT"   # 调整
    TRANSFER_IN = "TRANSFER_IN"   # 转入
    TRANSFER_OUT = "TRANSFER_OUT" # 转出


class TransactionStatus(PyEnum):
    """交易状态"""
    PENDING = "PENDING"         # 待处理
    PROCESSING = "PROCESSING"   # 处理中
    COMPLETED = "COMPLETED"     # 已完成
    FAILED = "FAILED"          # 失败
    CANCELLED = "CANCELLED"     # 已取消


class Account(Base):
    """账户模型"""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 账户基本信息 - 兼容现有数据库结构
    account_id = Column(String(50), unique=True, nullable=False, index=True)  # 主要账户标识
    account_name = Column(String(100), nullable=True)  # 允许为空以兼容现有数据
    broker = Column(String(50), nullable=True)  # 券商信息
    is_active = Column(Boolean, default=True, nullable=True)  # 账户状态
    
    # 资金信息 - 兼容现有数据库结构
    balance = Column(Float, nullable=True)  # 总余额
    available = Column(Float, nullable=True)  # 可用资金
    margin = Column(Float, nullable=True)  # 保证金
    frozen = Column(Float, nullable=True)  # 冻结资金
    
    # 盈亏信息 - 兼容现有数据库结构
    realized_pnl = Column(Float, nullable=True)  # 已实现盈亏
    unrealized_pnl = Column(Float, nullable=True)  # 未实现盈亏
    total_pnl = Column(Float, nullable=True)  # 总盈亏
    risk_ratio = Column(Float, nullable=True)  # 风险比率
    
    # 时间戳 - 兼容现有数据库结构
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Account(id={self.id}, account_id='{self.account_id}', user_id={self.user_id})>"
    
    def update_balances(self):
        """更新账户余额"""
        try:
            # 计算可用现金
            self.available_cash = self.cash_balance - self.frozen_cash
            
            # 计算净资产
            self.net_assets = self.total_assets - self.total_liabilities
            
            # 计算总盈亏
            self.total_pnl = self.realized_pnl + self.unrealized_pnl
            
            # 更新保证金比率
            if self.account_type == AccountType.MARGIN and self.maintenance_margin > 0:
                self.margin_ratio = self.margin_balance / self.maintenance_margin
            
            # 更新最后活动时间
            self.last_activity_at = datetime.now()
            
        except Exception as e:
            import logging
            logging.error(f"更新账户余额失败: {e}")
    
    def can_trade(self, required_amount: Decimal) -> bool:
        """检查是否可以交易"""
        if self.status != AccountStatus.ACTIVE:
            return False
        
        if self.available_cash < required_amount:
            return False
        
        # 保证金账户检查
        if self.account_type == AccountType.MARGIN:
            if self.margin_ratio < Decimal('1.0'):  # 保证金不足
                return False
        
        return True
    
    def freeze_cash(self, amount: Decimal) -> bool:
        """冻结资金"""
        if amount <= 0:
            return False
        
        if self.available_cash < amount:
            return False
        
        self.frozen_cash += amount
        self.available_cash -= amount
        return True
    
    def unfreeze_cash(self, amount: Decimal) -> bool:
        """解冻资金"""
        if amount <= 0:
            return False
        
        if self.frozen_cash < amount:
            return False
        
        self.frozen_cash -= amount
        self.available_cash += amount
        return True
    
    def add_cash(self, amount: Decimal, update_total: bool = True):
        """增加现金"""
        if amount > 0:
            self.cash_balance += amount
            self.available_cash += amount
            
            if update_total:
                self.total_assets += amount
    
    def subtract_cash(self, amount: Decimal, update_total: bool = True):
        """减少现金"""
        if amount > 0 and self.cash_balance >= amount:
            self.cash_balance -= amount
            self.available_cash = max(Decimal('0'), self.available_cash - amount)
            
            if update_total:
                self.total_assets = max(Decimal('0'), self.total_assets - amount)
    
    def calculate_buying_power(self) -> Decimal:
        """计算购买力"""
        if self.account_type == AccountType.CASH:
            return self.available_cash
        elif self.account_type == AccountType.MARGIN:
            # 保证金账户的购买力 = 可用现金 + 可用保证金
            return self.available_cash + max(Decimal('0'), self.margin_balance - self.maintenance_margin)
        else:
            return self.available_cash
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_number': self.account_number,
            'account_name': self.account_name,
            'account_type': self.account_type.value,
            'status': self.status.value,
            'base_currency': self.base_currency,
            'cash_balance': float(self.cash_balance),
            'available_cash': float(self.available_cash),
            'frozen_cash': float(self.frozen_cash),
            'margin_balance': float(self.margin_balance) if self.margin_balance else None,
            'maintenance_margin': float(self.maintenance_margin) if self.maintenance_margin else None,
            'initial_margin': float(self.initial_margin) if self.initial_margin else None,
            'margin_ratio': float(self.margin_ratio) if self.margin_ratio else None,
            'total_assets': float(self.total_assets),
            'total_liabilities': float(self.total_liabilities),
            'net_assets': float(self.net_assets),
            'market_value': float(self.market_value),
            'realized_pnl': float(self.realized_pnl),
            'unrealized_pnl': float(self.unrealized_pnl),
            'total_pnl': float(self.total_pnl),
            'total_deposits': float(self.total_deposits),
            'total_withdrawals': float(self.total_withdrawals),
            'total_fees': float(self.total_fees),
            'buying_power': float(self.calculate_buying_power()),
            'risk_level': self.risk_level,
            'settings': self.settings,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_activity_at': self.last_activity_at.isoformat() if self.last_activity_at else None
        }


class Transaction(Base):
    """资金流水模型"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    
    # 交易基本信息
    transaction_id = Column(String(100), unique=True, nullable=False, index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False, index=True)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, index=True)
    
    # 金额信息
    amount = Column(DECIMAL(20, 8), nullable=False)  # 交易金额
    currency = Column(String(10), default="USD", nullable=False)
    exchange_rate = Column(DECIMAL(20, 8), default=Decimal('1'))  # 汇率
    
    # 余额信息
    balance_before = Column(DECIMAL(20, 8))  # 交易前余额
    balance_after = Column(DECIMAL(20, 8))   # 交易后余额
    
    # 关联信息
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)  # 关联订单
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)  # 关联持仓
    symbol = Column(String(20), nullable=True)  # 交易标的
    
    # 描述信息
    description = Column(Text)  # 交易描述
    reference_id = Column(String(100))  # 外部参考ID
    
    # 手续费信息
    fee_amount = Column(DECIMAL(20, 8), default=Decimal('0'))  # 手续费
    tax_amount = Column(DECIMAL(20, 8), default=Decimal('0'))  # 税费
    
    # 附加数据
    account_model_metadata = Column(JSON, default=dict)  # 元数据
    
    # 时间戳
    transaction_time = Column(DateTime, default=func.now(), index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    account = relationship("Account", back_populates="transactions")
    order = relationship("Order")
    position = relationship("Position")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, type='{self.transaction_type}', amount={self.amount})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'account_id': self.account_id,
            'transaction_id': self.transaction_id,
            'transaction_type': self.transaction_type.value,
            'status': self.status.value,
            'amount': float(self.amount),
            'currency': self.currency,
            'exchange_rate': float(self.exchange_rate),
            'balance_before': float(self.balance_before) if self.balance_before else None,
            'balance_after': float(self.balance_after) if self.balance_after else None,
            'order_id': self.order_id,
            'position_id': self.position_id,
            'symbol': self.symbol,
            'description': self.description,
            'reference_id': self.reference_id,
            'fee_amount': float(self.fee_amount),
            'tax_amount': float(self.tax_amount),
            'metadata': self.model_metadata,
            'transaction_time': self.transaction_time.isoformat() if self.transaction_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AccountBalance(Base):
    """账户余额快照模型"""
    __tablename__ = "account_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    
    # 快照时间
    snapshot_date = Column(DateTime, nullable=False, index=True)
    snapshot_type = Column(String(20), default="daily")  # daily, weekly, monthly
    
    # 余额快照
    cash_balance = Column(DECIMAL(20, 8), nullable=False)
    available_cash = Column(DECIMAL(20, 8), nullable=False)
    frozen_cash = Column(DECIMAL(20, 8), nullable=False)
    total_assets = Column(DECIMAL(20, 8), nullable=False)
    total_liabilities = Column(DECIMAL(20, 8), nullable=False)
    net_assets = Column(DECIMAL(20, 8), nullable=False)
    market_value = Column(DECIMAL(20, 8), nullable=False)
    
    # 盈亏快照
    realized_pnl = Column(DECIMAL(20, 8), nullable=False)
    unrealized_pnl = Column(DECIMAL(20, 8), nullable=False)
    total_pnl = Column(DECIMAL(20, 8), nullable=False)
    daily_pnl = Column(DECIMAL(20, 8), default=Decimal('0'))  # 当日盈亏
    
    # 统计信息
    total_deposits = Column(DECIMAL(20, 8), nullable=False)
    total_withdrawals = Column(DECIMAL(20, 8), nullable=False)
    total_fees = Column(DECIMAL(20, 8), nullable=False)
    
    # 创建时间
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    account = relationship("Account")
    
    def __repr__(self):
        return f"<AccountBalance(id={self.id}, account_id={self.account_id}, date='{self.snapshot_date}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'account_id': self.account_id,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None,
            'snapshot_type': self.snapshot_type,
            'cash_balance': float(self.cash_balance),
            'available_cash': float(self.available_cash),
            'frozen_cash': float(self.frozen_cash),
            'total_assets': float(self.total_assets),
            'total_liabilities': float(self.total_liabilities),
            'net_assets': float(self.net_assets),
            'market_value': float(self.market_value),
            'realized_pnl': float(self.realized_pnl),
            'unrealized_pnl': float(self.unrealized_pnl),
            'total_pnl': float(self.total_pnl),
            'daily_pnl': float(self.daily_pnl),
            'total_deposits': float(self.total_deposits),
            'total_withdrawals': float(self.total_withdrawals),
            'total_fees': float(self.total_fees),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }