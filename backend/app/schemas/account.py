"""
账户管理数据模式
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from enum import Enum


class AccountTypeEnum(str, Enum):
    """账户类型枚举"""
    CASH = "CASH"
    MARGIN = "MARGIN"
    FUTURES = "FUTURES"
    OPTIONS = "OPTIONS"


class AccountStatusEnum(str, Enum):
    """账户状态枚举"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class TransactionTypeEnum(str, Enum):
    """交易类型枚举"""
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRADE_BUY = "TRADE_BUY"
    TRADE_SELL = "TRADE_SELL"
    DIVIDEND = "DIVIDEND"
    INTEREST = "INTEREST"
    FEE = "FEE"
    TAX = "TAX"
    ADJUSTMENT = "ADJUSTMENT"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"


class TransactionStatusEnum(str, Enum):
    """交易状态枚举"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# ==================== 账户相关模式 ====================

class AccountBase(BaseModel):
    """账户基础模式"""
    account_name: str = Field(..., description="账户名称", max_length=100)
    account_type: AccountTypeEnum = Field(..., description="账户类型")
    base_currency: str = Field("USD", description="基础货币", max_length=10)
    risk_level: str = Field("MEDIUM", description="风险等级")
    max_position_value: Optional[Decimal] = Field(None, description="最大持仓价值限制")
    max_daily_loss: Optional[Decimal] = Field(None, description="最大日亏损限制")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="账户设置")

    @validator('risk_level')
    def validate_risk_level(cls, v):
        if v not in ['LOW', 'MEDIUM', 'HIGH']:
            raise ValueError('风险等级必须是 LOW, MEDIUM 或 HIGH')
        return v

    @validator('max_position_value', 'max_daily_loss')
    def validate_limits(cls, v):
        if v is not None and v <= 0:
            raise ValueError('限制值必须大于0')
        return v


class AccountCreate(AccountBase):
    """创建账户"""
    pass


class AccountUpdate(BaseModel):
    """更新账户"""
    account_name: Optional[str] = Field(None, description="账户名称", max_length=100)
    risk_level: Optional[str] = Field(None, description="风险等级")
    max_position_value: Optional[Decimal] = Field(None, description="最大持仓价值限制")
    max_daily_loss: Optional[Decimal] = Field(None, description="最大日亏损限制")
    settings: Optional[Dict[str, Any]] = Field(None, description="账户设置")


class AccountResponse(AccountBase):
    """账户响应"""
    id: int = Field(..., description="账户ID")
    user_id: int = Field(..., description="用户ID")
    account_number: str = Field(..., description="账户号")
    status: AccountStatusEnum = Field(..., description="账户状态")
    
    # 资金信息
    cash_balance: Decimal = Field(..., description="现金余额")
    available_cash: Decimal = Field(..., description="可用现金")
    frozen_cash: Decimal = Field(..., description="冻结资金")
    
    # 保证金信息
    margin_balance: Optional[Decimal] = Field(None, description="保证金余额")
    maintenance_margin: Optional[Decimal] = Field(None, description="维持保证金")
    initial_margin: Optional[Decimal] = Field(None, description="初始保证金")
    margin_ratio: Optional[Decimal] = Field(None, description="保证金比率")
    
    # 资产信息
    total_assets: Decimal = Field(..., description="总资产")
    total_liabilities: Decimal = Field(..., description="总负债")
    net_assets: Decimal = Field(..., description="净资产")
    market_value: Decimal = Field(..., description="市值")
    
    # 盈亏信息
    realized_pnl: Decimal = Field(..., description="已实现盈亏")
    unrealized_pnl: Decimal = Field(..., description="未实现盈亏")
    total_pnl: Decimal = Field(..., description="总盈亏")
    
    # 统计信息
    total_deposits: Decimal = Field(..., description="总入金")
    total_withdrawals: Decimal = Field(..., description="总出金")
    total_fees: Decimal = Field(..., description="总手续费")
    buying_power: Decimal = Field(..., description="购买力")
    
    # 时间信息
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    last_activity_at: Optional[datetime] = Field(None, description="最后活动时间")

    class Config:
        from_attributes = True


# ==================== 交易流水相关模式 ====================

class TransactionBase(BaseModel):
    """交易流水基础模式"""
    transaction_type: TransactionTypeEnum = Field(..., description="交易类型")
    amount: Decimal = Field(..., description="交易金额")
    currency: str = Field("USD", description="货币", max_length=10)
    description: Optional[str] = Field(None, description="交易描述")
    reference_id: Optional[str] = Field(None, description="外部参考ID", max_length=100)

    @validator('amount')
    def validate_amount(cls, v):
        if v == 0:
            raise ValueError('交易金额不能为0')
        return v


class DepositRequest(BaseModel):
    """入金请求"""
    amount: Decimal = Field(..., description="入金金额", gt=0)
    description: Optional[str] = Field(None, description="入金描述")
    reference_id: Optional[str] = Field(None, description="外部参考ID")


class WithdrawalRequest(BaseModel):
    """出金请求"""
    amount: Decimal = Field(..., description="出金金额", gt=0)
    description: Optional[str] = Field(None, description="出金描述")
    reference_id: Optional[str] = Field(None, description="外部参考ID")


class TransactionResponse(TransactionBase):
    """交易流水响应"""
    id: int = Field(..., description="交易ID")
    account_id: int = Field(..., description="账户ID")
    transaction_id: str = Field(..., description="交易流水号")
    status: TransactionStatusEnum = Field(..., description="交易状态")
    
    exchange_rate: Decimal = Field(..., description="汇率")
    balance_before: Optional[Decimal] = Field(None, description="交易前余额")
    balance_after: Optional[Decimal] = Field(None, description="交易后余额")
    
    # 关联信息
    order_id: Optional[int] = Field(None, description="关联订单ID")
    position_id: Optional[int] = Field(None, description="关联持仓ID")
    symbol: Optional[str] = Field(None, description="交易标的")
    
    # 费用信息
    fee_amount: Decimal = Field(..., description="手续费")
    tax_amount: Decimal = Field(..., description="税费")
    
    # 附加数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    # 时间信息
    transaction_time: Optional[datetime] = Field(None, description="交易时间")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


# ==================== 余额快照相关模式 ====================

class AccountBalanceResponse(BaseModel):
    """账户余额快照响应"""
    id: int = Field(..., description="快照ID")
    account_id: int = Field(..., description="账户ID")
    snapshot_date: datetime = Field(..., description="快照时间")
    snapshot_type: str = Field(..., description="快照类型")
    
    # 余额快照
    cash_balance: Decimal = Field(..., description="现金余额")
    available_cash: Decimal = Field(..., description="可用现金")
    frozen_cash: Decimal = Field(..., description="冻结资金")
    total_assets: Decimal = Field(..., description="总资产")
    total_liabilities: Decimal = Field(..., description="总负债")
    net_assets: Decimal = Field(..., description="净资产")
    market_value: Decimal = Field(..., description="市值")
    
    # 盈亏快照
    realized_pnl: Decimal = Field(..., description="已实现盈亏")
    unrealized_pnl: Decimal = Field(..., description="未实现盈亏")
    total_pnl: Decimal = Field(..., description="总盈亏")
    daily_pnl: Decimal = Field(..., description="当日盈亏")
    
    # 统计信息
    total_deposits: Decimal = Field(..., description="总入金")
    total_withdrawals: Decimal = Field(..., description="总出金")
    total_fees: Decimal = Field(..., description="总手续费")
    
    created_at: Optional[datetime] = Field(None, description="创建时间")

    class Config:
        from_attributes = True


# ==================== 统计分析相关模式 ====================

class TransactionSummaryResponse(BaseModel):
    """交易汇总响应"""
    period: str = Field(..., description="统计周期")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    total_transactions: int = Field(..., description="总交易数")
    deposits: float = Field(..., description="总入金")
    withdrawals: float = Field(..., description="总出金")
    trade_amount: float = Field(..., description="交易金额")
    fees: float = Field(..., description="总手续费")
    by_type: Dict[str, Dict[str, Any]] = Field(..., description="按类型统计")


class AccountConsistencyResponse(BaseModel):
    """账户一致性检查响应"""
    account_id: int = Field(..., description="账户ID")
    is_consistent: bool = Field(..., description="是否一致")
    issues: List[Dict[str, str]] = Field(..., description="发现的问题")
    checked_at: str = Field(..., description="检查时间")


class AccountTotalsResponse(BaseModel):
    """账户总资产响应"""
    cash_balance: Decimal = Field(..., description="现金余额")
    market_value: Decimal = Field(..., description="市值")
    total_assets: Decimal = Field(..., description="总资产")
    unrealized_pnl: Decimal = Field(..., description="未实现盈亏")
    net_assets: Decimal = Field(..., description="净资产")


# ==================== 资金操作相关模式 ====================

class FreezeRequest(BaseModel):
    """冻结资金请求"""
    amount: Decimal = Field(..., description="冻结金额", gt=0)
    description: Optional[str] = Field(None, description="冻结原因")


class UnfreezeRequest(BaseModel):
    """解冻资金请求"""
    amount: Decimal = Field(..., description="解冻金额", gt=0)
    description: Optional[str] = Field(None, description="解冻原因")


class TradeTransactionRequest(BaseModel):
    """交易流水记录请求"""
    order_id: int = Field(..., description="订单ID")
    position_id: int = Field(..., description="持仓ID")
    amount: Decimal = Field(..., description="交易金额")
    fee: Decimal = Field(Decimal('0'), description="手续费", ge=0)
    symbol: Optional[str] = Field(None, description="交易标的")
    description: Optional[str] = Field(None, description="交易描述")