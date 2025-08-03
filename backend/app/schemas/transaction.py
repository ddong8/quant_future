"""
交易流水数据模型Schema
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from ..models.account import TransactionType, TransactionStatus

class TransactionBase(BaseModel):
    """交易流水基础模型"""
    account_id: int = Field(..., description="账户ID")
    transaction_type: TransactionType = Field(..., description="交易类型")
    amount: Decimal = Field(..., description="交易金额")
    currency: str = Field(default="USD", description="货币类型")
    exchange_rate: Optional[Decimal] = Field(default=Decimal('1'), description="汇率")
    symbol: Optional[str] = Field(None, description="交易标的")
    description: Optional[str] = Field(None, description="交易描述")
    reference_id: Optional[str] = Field(None, description="关联ID")
    fee_amount: Optional[Decimal] = Field(default=Decimal('0'), description="手续费")
    tax_amount: Optional[Decimal] = Field(default=Decimal('0'), description="税费")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")

class TransactionCreate(TransactionBase):
    """创建交易流水"""
    transaction_id: Optional[str] = Field(None, description="交易ID")
    status: Optional[TransactionStatus] = Field(default=TransactionStatus.COMPLETED, description="交易状态")
    balance_before: Optional[Decimal] = Field(None, description="交易前余额")
    balance_after: Optional[Decimal] = Field(None, description="交易后余额")
    order_id: Optional[int] = Field(None, description="关联订单ID")
    position_id: Optional[int] = Field(None, description="关联持仓ID")
    transaction_time: Optional[datetime] = Field(None, description="交易时间")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v == 0:
            raise ValueError('交易金额不能为0')
        return v
    
    @validator('fee_amount', 'tax_amount')
    def validate_fees(cls, v):
        if v and v < 0:
            raise ValueError('费用不能为负数')
        return v

class TransactionUpdate(BaseModel):
    """更新交易流水"""
    status: Optional[TransactionStatus] = Field(None, description="交易状态")
    description: Optional[str] = Field(None, description="交易描述")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

class TransactionResponse(BaseModel):
    """交易流水响应"""
    id: int
    transaction_id: str
    account_id: int
    transaction_type: TransactionType
    status: TransactionStatus
    amount: Decimal
    currency: str
    exchange_rate: Decimal
    balance_before: Optional[Decimal]
    balance_after: Optional[Decimal]
    order_id: Optional[int]
    position_id: Optional[int]
    symbol: Optional[str]
    description: Optional[str]
    reference_id: Optional[str]
    fee_amount: Decimal
    tax_amount: Decimal
    metadata: Dict[str, Any]
    transaction_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None
        }

class TransactionSearch(BaseModel):
    """交易流水搜索"""
    account_ids: Optional[List[int]] = Field(None, description="账户ID列表")
    transaction_types: Optional[List[TransactionType]] = Field(None, description="交易类型列表")
    status_list: Optional[List[TransactionStatus]] = Field(None, description="状态列表")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    min_amount: Optional[Decimal] = Field(None, description="最小金额")
    max_amount: Optional[Decimal] = Field(None, description="最大金额")
    symbols: Optional[List[str]] = Field(None, description="标的列表")
    keyword: Optional[str] = Field(None, description="关键词")
    sort_field: str = Field(default="transaction_time", description="排序字段")
    sort_order: str = Field(default="desc", description="排序方向")
    skip: int = Field(default=0, ge=0, description="跳过数量")
    limit: int = Field(default=100, ge=1, le=1000, description="限制数量")

class TransactionStatistics(BaseModel):
    """交易统计"""
    period: str
    start_date: str
    end_date: str
    summary: Dict[str, Any]
    extremes: Dict[str, Any]
    daily_stats: List[Dict[str, Any]]
    type_breakdown: List[Dict[str, Any]]

class TransactionCategories(BaseModel):
    """交易分类统计"""
    by_type: List[Dict[str, Any]]
    by_status: List[Dict[str, Any]]
    by_currency: List[Dict[str, Any]]

class CashFlowAnalysis(BaseModel):
    """现金流分析"""
    period: str
    interval: str
    start_date: str
    end_date: str
    cash_flow_data: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    inflow_analysis: Dict[str, Any]
    outflow_analysis: Dict[str, Any]

class TransactionReport(BaseModel):
    """交易报表"""
    report_type: str
    period: Dict[str, str]
    generated_at: str
    # 其他字段根据报表类型动态添加

class TransactionExport(BaseModel):
    """交易导出"""
    export_format: str = Field(..., pattern="^(csv|excel|json)$", description="导出格式")
    filters: Optional[Dict[str, Any]] = Field(None, description="筛选条件")

class TransactionAudit(BaseModel):
    """交易审计"""
    audit_type: str
    total_issues: int
    issues: List[Dict[str, Any]]
    status: str
    audited_at: str

class SuspiciousTransaction(BaseModel):
    """可疑交易"""
    transaction_id: str
    transaction_time: Optional[str]
    amount: float
    transaction_type: str
    status: str
    description: Optional[str]
    suspicion_reasons: List[str]
    risk_level: int

class TransactionFilter(BaseModel):
    """交易筛选器"""
    account_id: Optional[int] = Field(None, description="账户ID")
    transaction_types: Optional[List[str]] = Field(None, description="交易类型")
    status: Optional[str] = Field(None, description="交易状态")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    min_amount: Optional[float] = Field(None, description="最小金额")
    max_amount: Optional[float] = Field(None, description="最大金额")
    symbol: Optional[str] = Field(None, description="交易标的")
    keyword: Optional[str] = Field(None, description="关键词搜索")

class TransactionSummary(BaseModel):
    """交易汇总"""
    total_count: int = Field(..., description="总交易数")
    total_income: float = Field(..., description="总收入")
    total_expense: float = Field(..., description="总支出")
    net_amount: float = Field(..., description="净额")
    total_fees: float = Field(..., description="总手续费")
    avg_amount: float = Field(..., description="平均金额")

class DailyTransactionStats(BaseModel):
    """每日交易统计"""
    date: str
    count: int
    total_amount: float
    total_volume: float

class TransactionTypeBreakdown(BaseModel):
    """交易类型分解"""
    type: str
    count: int
    total_amount: float
    total_fees: float
    percentage: float

class CashFlowMetrics(BaseModel):
    """现金流指标"""
    volatility: float = Field(..., description="现金流波动性")
    trend: float = Field(..., description="现金流趋势")
    positive_ratio: float = Field(..., description="正现金流比例")
    total_periods: int = Field(..., description="总周期数")

class TransactionValidation(BaseModel):
    """交易验证"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    @validator('errors', 'warnings', pre=True)
    def ensure_list(cls, v):
        if v is None:
            return []
        return v if isinstance(v, list) else [v]