"""
策略管理相关的Pydantic模型
"""
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.enums import StrategyStatus


class StrategyBase(BaseModel):
    """策略基础模型"""
    name: str
    description: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('策略名称至少需要2个字符')
        if len(v.strip()) > 100:
            raise ValueError('策略名称不能超过100个字符')
        return v.strip()


class StrategyCreate(StrategyBase):
    """创建策略模型"""
    code: str
    language: str = "python"
    parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    
    @validator('code')
    def validate_code(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('策略代码至少需要10个字符')
        return v.strip()
    
    @validator('language')
    def validate_language(cls, v):
        allowed_languages = ['python']
        if v not in allowed_languages:
            raise ValueError(f'编程语言必须是: {", ".join(allowed_languages)}')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            if len(v) > 10:
                raise ValueError('标签数量不能超过10个')
            for tag in v:
                if not isinstance(tag, str) or len(tag.strip()) < 1:
                    raise ValueError('标签必须是非空字符串')
                if len(tag.strip()) > 20:
                    raise ValueError('单个标签长度不能超过20个字符')
        return v


class StrategyUpdate(BaseModel):
    """更新策略模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v or len(v.strip()) < 2:
                raise ValueError('策略名称至少需要2个字符')
            if len(v.strip()) > 100:
                raise ValueError('策略名称不能超过100个字符')
        return v.strip() if v else None
    
    @validator('code')
    def validate_code(cls, v):
        if v is not None:
            if not v or len(v.strip()) < 10:
                raise ValueError('策略代码至少需要10个字符')
        return v.strip() if v else None
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            if len(v) > 10:
                raise ValueError('标签数量不能超过10个')
            for tag in v:
                if not isinstance(tag, str) or len(tag.strip()) < 1:
                    raise ValueError('标签必须是非空字符串')
                if len(tag.strip()) > 20:
                    raise ValueError('单个标签长度不能超过20个字符')
        return v


class StrategyResponse(BaseModel):
    """策略响应模型"""
    id: int
    name: str
    description: Optional[str]
    code: str
    language: str
    version: str
    user_id: int
    status: str
    parameters: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    created_at: datetime
    updated_at: Optional[datetime]
    last_run_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class StrategyListResponse(BaseModel):
    """策略列表响应模型"""
    id: int
    name: str
    description: Optional[str]
    language: str
    version: str
    user_id: int
    status: str
    tags: Optional[List[str]]
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    created_at: datetime
    updated_at: Optional[datetime]
    last_run_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class StrategySearchRequest(BaseModel):
    """策略搜索请求模型"""
    keyword: Optional[str] = None
    status: Optional[StrategyStatus] = None
    tags: Optional[List[str]] = None
    user_id: Optional[int] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    min_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    
    @validator('keyword')
    def validate_keyword(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError('搜索关键词至少需要2个字符')
        return v.strip() if v else None


class StrategyStatusUpdate(BaseModel):
    """策略状态更新模型"""
    status: StrategyStatus
    
    @validator('status')
    def validate_status(cls, v):
        # 只允许某些状态转换
        allowed_statuses = [
            StrategyStatus.DRAFT,
            StrategyStatus.TESTING,
            StrategyStatus.ACTIVE,
            StrategyStatus.PAUSED,
            StrategyStatus.STOPPED
        ]
        if v not in allowed_statuses:
            raise ValueError(f'状态必须是: {[s.value for s in allowed_statuses]}')
        return v


class StrategyVersionCreate(BaseModel):
    """创建策略版本模型"""
    version: str
    code: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    
    @validator('version')
    def validate_version(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('版本号不能为空')
        if len(v.strip()) > 20:
            raise ValueError('版本号不能超过20个字符')
        return v.strip()
    
    @validator('code')
    def validate_code(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('策略代码至少需要10个字符')
        return v.strip()


class StrategyVersionResponse(BaseModel):
    """策略版本响应模型"""
    id: int
    strategy_id: int
    version: str
    code: str
    description: Optional[str]
    parameters: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class StrategyStatsResponse(BaseModel):
    """策略统计响应模型"""
    total_strategies: int
    active_strategies: int
    draft_strategies: int
    testing_strategies: int
    paused_strategies: int
    stopped_strategies: int
    avg_return: float
    avg_sharpe_ratio: float
    top_performers: List[StrategyListResponse]


class StrategyCloneRequest(BaseModel):
    """策略克隆请求模型"""
    name: str
    description: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('策略名称至少需要2个字符')
        if len(v.strip()) > 100:
            raise ValueError('策略名称不能超过100个字符')
        return v.strip()


class StrategyExportRequest(BaseModel):
    """策略导出请求模型"""
    format: str = "json"
    include_versions: bool = False
    include_performance: bool = True
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['json', 'yaml', 'zip']
        if v not in allowed_formats:
            raise ValueError(f'导出格式必须是: {allowed_formats}')
        return v


class StrategyImportRequest(BaseModel):
    """策略导入请求模型"""
    data: Dict[str, Any]
    overwrite: bool = False
    
    @validator('data')
    def validate_data(cls, v):
        required_fields = ['name', 'code', 'language']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'导入数据缺少必需字段: {field}')
        return v


class BatchStrategyOperation(BaseModel):
    """批量策略操作模型"""
    strategy_ids: List[int]
    operation: str  # activate, pause, stop, delete
    
    @validator('strategy_ids')
    def validate_strategy_ids(cls, v):
        if not v:
            raise ValueError('策略ID列表不能为空')
        if len(v) > 50:
            raise ValueError('批量操作最多支持50个策略')
        return v
    
    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = ['activate', 'pause', 'stop', 'delete']
        if v not in allowed_operations:
            raise ValueError(f'操作类型必须是: {allowed_operations}')
        return v


class StrategyTemplate(BaseModel):
    """策略模板模型"""
    name: str
    description: str
    code: str
    language: str = "python"
    parameters: Dict[str, Any]
    tags: List[str]
    category: str
    
    @validator('category')
    def validate_category(cls, v):
        allowed_categories = [
            'trend_following', 'mean_reversion', 'arbitrage', 
            'momentum', 'volatility', 'other'
        ]
        if v not in allowed_categories:
            raise ValueError(f'策略分类必须是: {allowed_categories}')
        return v


class StrategyPerformanceMetrics(BaseModel):
    """策略性能指标模型"""
    strategy_id: int
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_return: float
    volatility: float
    beta: float
    alpha: float
    information_ratio: float
    calmar_ratio: float
    updated_at: datetime


class StrategyValidationRequest(BaseModel):
    """策略验证请求模型"""
    code: str
    check_syntax: bool = True
    check_security: bool = True
    check_structure: bool = True
    check_dependencies: bool = True
    
    @validator('code')
    def validate_code(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('策略代码不能为空且至少需要10个字符')
        return v.strip()


class StrategyValidationResponse(BaseModel):
    """策略验证响应模型"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    checks: Dict[str, bool]
    suggestions: Optional[List[str]] = None


class StrategyTestRequest(BaseModel):
    """策略测试请求模型"""
    strategy_id: int
    test_params: Optional[Dict[str, Any]] = None
    timeout: int = 30
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v < 1 or v > 300:
            raise ValueError('超时时间必须在1-300秒之间')
        return v


class StrategyTestResponse(BaseModel):
    """策略测试响应模型"""
    strategy_id: int
    strategy_name: str
    test_time: str
    overall_result: str  # PASS, FAIL, ERROR
    validation: Dict[str, Any]
    execution: Dict[str, Any]
    performance: Dict[str, Any]
    recommendations: List[str]
    error: Optional[str] = None


class StrategySandboxRequest(BaseModel):
    """策略沙盒执行请求模型"""
    code: str
    test_data: Optional[Dict[str, Any]] = None
    timeout: int = 30
    
    @validator('code')
    def validate_code(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('策略代码不能为空且至少需要10个字符')
        return v.strip()
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v < 1 or v > 300:
            raise ValueError('超时时间必须在1-300秒之间')
        return v


class StrategySandboxResponse(BaseModel):
    """策略沙盒执行响应模型"""
    success: bool
    output: str
    error: str
    execution_time: float
    memory_usage: float


class StrategyCodeAnalysis(BaseModel):
    """策略代码分析模型"""
    lines_of_code: int
    complexity_score: float
    functions_count: int
    imports_count: int
    security_score: float
    maintainability_score: float
    suggestions: List[str]


class StrategyDependencyInfo(BaseModel):
    """策略依赖信息模型"""
    module_name: str
    is_available: bool
    version: Optional[str] = None
    description: Optional[str] = None
    installation_command: Optional[str] = None


class StrategySecurityReport(BaseModel):
    """策略安全报告模型"""
    security_level: str  # HIGH, MEDIUM, LOW
    issues: List[Dict[str, str]]
    recommendations: List[str]
    safe_to_execute: bool