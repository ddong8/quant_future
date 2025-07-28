"""
回测相关的Pydantic模型
"""
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.enums import BacktestStatus


class BacktestBase(BaseModel):
    """回测基础模型"""
    name: str
    description: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('回测名称至少需要2个字符')
        if len(v.strip()) > 100:
            raise ValueError('回测名称不能超过100个字符')
        return v.strip()


class BacktestCreate(BacktestBase):
    """创建回测模型"""
    strategy_id: int
    start_date: datetime
    end_date: datetime
    initial_capital: float
    symbols: List[str]
    parameters: Optional[Dict[str, Any]] = None
    
    @validator('strategy_id')
    def validate_strategy_id(cls, v):
        if v <= 0:
            raise ValueError('策略ID必须大于0')
        return v
    
    @validator('start_date', 'end_date')
    def validate_dates(cls, v):
        if v > datetime.utcnow():
            raise ValueError('日期不能超过当前时间')
        return v
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('结束日期必须晚于开始日期')
        return v
    
    @validator('initial_capital')
    def validate_initial_capital(cls, v):
        if v <= 0:
            raise ValueError('初始资金必须大于0')
        if v > 1000000000:  # 10亿
            raise ValueError('初始资金不能超过10亿')
        return v
    
    @validator('symbols')
    def validate_symbols(cls, v):
        if not v:
            raise ValueError('必须指定至少一个交易品种')
        if len(v) > 50:
            raise ValueError('交易品种数量不能超过50个')
        
        for symbol in v:
            if not isinstance(symbol, str) or len(symbol.strip()) < 1:
                raise ValueError('交易品种必须是非空字符串')
        
        return v


class BacktestUpdate(BaseModel):
    """更新回测模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    initial_capital: Optional[float] = None
    symbols: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v or len(v.strip()) < 2:
                raise ValueError('回测名称至少需要2个字符')
            if len(v.strip()) > 100:
                raise ValueError('回测名称不能超过100个字符')
        return v.strip() if v else None
    
    @validator('start_date', 'end_date')
    def validate_dates(cls, v):
        if v is not None and v > datetime.utcnow():
            raise ValueError('日期不能超过当前时间')
        return v
    
    @validator('initial_capital')
    def validate_initial_capital(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError('初始资金必须大于0')
            if v > 1000000000:
                raise ValueError('初始资金不能超过10亿')
        return v
    
    @validator('symbols')
    def validate_symbols(cls, v):
        if v is not None:
            if not v:
                raise ValueError('必须指定至少一个交易品种')
            if len(v) > 50:
                raise ValueError('交易品种数量不能超过50个')
        return v


class BacktestResponse(BaseModel):
    """回测响应模型"""
    id: int
    name: str
    description: Optional[str]
    strategy_id: int
    user_id: int
    start_date: datetime
    end_date: datetime
    initial_capital: float
    symbols: List[str]
    parameters: Optional[Dict[str, Any]]
    status: str
    progress: float
    
    # 回测结果
    final_capital: Optional[float] = None
    total_return: Optional[float] = None
    annual_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    
    # 交易统计
    total_trades: Optional[int] = None
    winning_trades: Optional[int] = None
    losing_trades: Optional[int] = None
    win_rate: Optional[float] = None
    avg_win: Optional[float] = None
    avg_loss: Optional[float] = None
    profit_factor: Optional[float] = None
    
    # 错误信息
    error_message: Optional[str] = None
    
    # 时间戳
    created_at: datetime
    updated_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class BacktestListResponse(BaseModel):
    """回测列表响应模型"""
    id: int
    name: str
    description: Optional[str]
    strategy_id: int
    status: str
    progress: float
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: Optional[float] = None
    total_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class BacktestProgressResponse(BaseModel):
    """回测进度响应模型"""
    backtest_id: int
    status: str
    progress: float
    started_at: Optional[datetime] = None
    eta: Optional[datetime] = None
    error_message: Optional[str] = None


class BacktestResultsResponse(BaseModel):
    """回测结果响应模型"""
    backtest_id: int
    name: str
    strategy_id: int
    start_date: datetime
    end_date: datetime
    initial_capital: float
    symbols: List[str]
    parameters: Optional[Dict[str, Any]]
    
    # 基础指标
    final_capital: float
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    
    # 交易统计
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    
    # 详细数据
    equity_curve: Optional[List[Dict[str, Any]]] = None
    trade_records: Optional[List[Dict[str, Any]]] = None
    daily_returns: Optional[List[Dict[str, Any]]] = None
    
    # 时间信息
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class BacktestStatsResponse(BaseModel):
    """回测统计响应模型"""
    total_backtests: int
    completed_backtests: int
    running_backtests: int
    failed_backtests: int
    success_rate: float
    
    avg_return: float
    avg_sharpe_ratio: float
    avg_max_drawdown: float
    
    best_return_backtest: Optional[Dict[str, Any]] = None
    best_sharpe_backtest: Optional[Dict[str, Any]] = None


class BacktestSearchRequest(BaseModel):
    """回测搜索请求模型"""
    strategy_id: Optional[int] = None
    status: Optional[BacktestStatus] = None
    keyword: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_return: Optional[float] = None
    max_return: Optional[float] = None
    min_sharpe: Optional[float] = None
    max_drawdown: Optional[float] = None
    
    @validator('keyword')
    def validate_keyword(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError('搜索关键词至少需要2个字符')
        return v.strip() if v else None


class BacktestCloneRequest(BaseModel):
    """回测克隆请求模型"""
    name: str
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('回测名称至少需要2个字符')
        if len(v.strip()) > 100:
            raise ValueError('回测名称不能超过100个字符')
        return v.strip()


class BacktestComparisonRequest(BaseModel):
    """回测比较请求模型"""
    backtest_ids: List[int]
    
    @validator('backtest_ids')
    def validate_backtest_ids(cls, v):
        if len(v) < 2:
            raise ValueError('至少需要选择2个回测进行比较')
        if len(v) > 10:
            raise ValueError('最多只能比较10个回测')
        if len(set(v)) != len(v):
            raise ValueError('不能包含重复的回测ID')
        return v


class BacktestComparisonResponse(BaseModel):
    """回测比较响应模型"""
    backtests: List[Dict[str, Any]]
    metrics_comparison: Dict[str, Any]
    ranking: Dict[str, List[int]]


class BacktestOrderRecord(BaseModel):
    """回测订单记录模型"""
    id: str
    symbol: str
    side: str
    type: str
    quantity: float
    price: Optional[float]
    filled_price: Optional[float]
    filled_quantity: float
    commission: float
    created_time: Optional[datetime]
    filled_time: Optional[datetime]
    status: str


class BacktestEquityPoint(BaseModel):
    """回测资金曲线点模型"""
    timestamp: datetime
    total_value: float
    available_cash: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float


class BacktestDailyReturn(BaseModel):
    """回测日收益率模型"""
    date: datetime
    return_rate: float
    cumulative_return: float


class BacktestPerformanceMetrics(BaseModel):
    """回测性能指标模型"""
    # 收益指标
    total_return: float
    annual_return: float
    monthly_return: float
    daily_return: float
    
    # 风险指标
    volatility: float
    max_drawdown: float
    max_drawdown_duration: int
    var_95: float  # 95% VaR
    cvar_95: float  # 95% CVaR
    
    # 风险调整收益指标
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    information_ratio: float
    
    # 交易指标
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    avg_trade_duration: float
    
    # 其他指标
    beta: Optional[float] = None
    alpha: Optional[float] = None
    correlation: Optional[float] = None
    tracking_error: Optional[float] = None


class BacktestRiskMetrics(BaseModel):
    """回测风险指标模型"""
    max_drawdown: float
    max_drawdown_duration: int
    volatility: float
    downside_volatility: float
    var_95: float
    cvar_95: float
    skewness: float
    kurtosis: float
    tail_ratio: float
    
    # 风险分解
    systematic_risk: Optional[float] = None
    idiosyncratic_risk: Optional[float] = None
    
    # 极端风险
    worst_day: float
    best_day: float
    worst_month: float
    best_month: float


class BacktestOptimizationRequest(BaseModel):
    """回测优化请求模型"""
    strategy_id: int
    start_date: datetime
    end_date: datetime
    initial_capital: float
    symbols: List[str]
    
    # 优化参数
    optimization_params: Dict[str, Dict[str, Any]]  # 参数名 -> {min, max, step}
    optimization_target: str = "sharpe_ratio"  # 优化目标
    max_iterations: int = 100
    
    @validator('optimization_target')
    def validate_optimization_target(cls, v):
        allowed_targets = [
            'total_return', 'annual_return', 'sharpe_ratio', 'sortino_ratio',
            'calmar_ratio', 'max_drawdown', 'profit_factor'
        ]
        if v not in allowed_targets:
            raise ValueError(f'优化目标必须是: {allowed_targets}')
        return v
    
    @validator('max_iterations')
    def validate_max_iterations(cls, v):
        if v < 1 or v > 1000:
            raise ValueError('最大迭代次数必须在1-1000之间')
        return v


class BacktestOptimizationResponse(BaseModel):
    """回测优化响应模型"""
    optimization_id: str
    status: str
    progress: float
    best_params: Optional[Dict[str, Any]] = None
    best_result: Optional[Dict[str, Any]] = None
    all_results: Optional[List[Dict[str, Any]]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class BacktestReportRequest(BaseModel):
    """回测报告请求模型"""
    backtest_id: int
    report_type: str = "detailed"  # summary/detailed/comparison
    include_charts: bool = True
    include_trades: bool = True
    format: str = "html"  # html/pdf/excel
    
    @validator('report_type')
    def validate_report_type(cls, v):
        allowed_types = ['summary', 'detailed', 'comparison']
        if v not in allowed_types:
            raise ValueError(f'报告类型必须是: {allowed_types}')
        return v
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['html', 'pdf', 'excel']
        if v not in allowed_formats:
            raise ValueError(f'报告格式必须是: {allowed_formats}')
        return v


class BacktestReportResponse(BaseModel):
    """回测报告响应模型"""
    report_id: int
    backtest_id: int
    report_type: str
    format: str
    file_path: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime