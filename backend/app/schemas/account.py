"""
账户相关的数据模型
"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field

from .base import BaseResponse


class TradingAccountBase(BaseModel):
    """交易账户基础模型"""
    account_id: str = Field(..., description="账户ID")
    total_balance: Decimal = Field(..., description="总余额")
    available_balance: Decimal = Field(..., description="可用余额")
    used_margin: Decimal = Field(..., description="已用保证金")
    frozen_balance: Decimal = Field(..., description="冻结余额")
    commission_paid: Decimal = Field(..., description="已付手续费")
    realized_pnl: Decimal = Field(..., description="已实现盈亏")
    unrealized_pnl: Decimal = Field(..., description="未实现盈亏")


class TradingAccount(TradingAccountBase):
    """交易账户信息"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AccountMetrics(BaseModel):
    """账户指标"""
    account_id: str = Field(..., description="账户ID")
    total_balance: float = Field(..., description="总余额")
    available_balance: float = Field(..., description="可用余额")
    used_margin: float = Field(..., description="已用保证金")
    frozen_balance: float = Field(..., description="冻结余额")
    realized_pnl: float = Field(..., description="已实现盈亏")
    unrealized_pnl: float = Field(..., description="未实现盈亏")
    net_value: float = Field(..., description="净值")
    total_market_value: float = Field(..., description="总市值")
    margin_ratio: float = Field(..., description="保证金比例")
    available_ratio: float = Field(..., description="可用资金比例")
    today_pnl: float = Field(..., description="今日盈亏")
    commission_paid: float = Field(..., description="已付手续费")
    position_count: int = Field(..., description="持仓数量")
    last_update: str = Field(..., description="最后更新时间")


class AccountTransaction(BaseModel):
    """账户交易流水"""
    id: int
    account_id: int
    transaction_type: str = Field(..., description="交易类型")
    amount: Decimal = Field(..., description="金额")
    description: str = Field(..., description="描述")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class BalanceHistory(BaseModel):
    """余额历史"""
    date: str = Field(..., description="日期")
    balance: float = Field(..., description="余额")
    change: float = Field(..., description="变化金额")


class RiskIndicators(BaseModel):
    """风险指标"""
    risk_ratio: float = Field(..., description="风险度")
    fund_usage_ratio: float = Field(..., description="资金使用率")
    pnl_ratio: float = Field(..., description="盈亏比例(%)")
    risk_level: str = Field(..., description="风险等级")
    margin_call_threshold: float = Field(..., description="保证金追缴阈值")
    force_close_threshold: float = Field(..., description="强制平仓阈值")
    available_margin: float = Field(..., description="可用保证金")


class DepositRequest(BaseModel):
    """充值请求"""
    amount: float = Field(..., gt=0, description="充值金额")
    description: Optional[str] = Field(None, description="描述")


class WithdrawRequest(BaseModel):
    """提现请求"""
    amount: float = Field(..., gt=0, description="提现金额")
    description: Optional[str] = Field(None, description="描述")


class TransactionHistoryRequest(BaseModel):
    """交易流水查询请求"""
    transaction_type: Optional[str] = Field(None, description="交易类型")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")


class TransactionHistoryData(BaseModel):
    """交易流水数据"""
    transactions: List[AccountTransaction]
    total: int
    page: int
    page_size: int


class TransactionData(BaseModel):
    """交易数据"""
    account_id: str = Field(..., description="账户ID")
    total_balance: float = Field(..., description="总余额")
    available_balance: float = Field(..., description="可用余额")
    transaction_amount: float = Field(..., description="交易金额")


class FreezeBalanceRequest(BaseModel):
    """冻结资金请求"""
    amount: float = Field(..., gt=0, description="冻结金额")
    description: str = Field("", description="描述")


class UnfreezeBalanceRequest(BaseModel):
    """解冻资金请求"""
    amount: float = Field(..., gt=0, description="解冻金额")
    description: str = Field("", description="描述")


class MarginUpdateRequest(BaseModel):
    """保证金更新请求"""
    used_margin: float = Field(..., ge=0, description="已用保证金")


class UnrealizedPnlUpdateRequest(BaseModel):
    """未实现盈亏更新请求"""
    unrealized_pnl: float = Field(..., description="未实现盈亏")


# 响应模型
class AccountResponse(BaseResponse):
    """账户响应"""
    data: TradingAccount


class AccountMetricsResponse(BaseResponse):
    """账户指标响应"""
    data: AccountMetrics


class TransactionHistoryResponse(BaseResponse):
    """交易流水响应"""
    data: TransactionHistoryData


class BalanceHistoryResponse(BaseResponse):
    """余额历史响应"""
    data: List[BalanceHistory]


class RiskIndicatorsResponse(BaseResponse):
    """风险指标响应"""
    data: RiskIndicators


class TransactionResponse(BaseResponse):
    """交易响应"""
    data: TransactionData