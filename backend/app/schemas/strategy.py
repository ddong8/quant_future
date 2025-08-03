"""
策略相关的Pydantic模式
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from ..models.strategy import StrategyStatus, StrategyType


class StrategyBase(BaseModel):
    """策略基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    strategy_type: StrategyType = Field(StrategyType.CUSTOM, description="策略类型")
    code: str = Field(..., min_length=1, description="策略代码")
    entry_point: str = Field("main", description="入口函数名")
    language: str = Field("python", description="编程语言")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="策略参数")
    symbols: List[str] = Field(default_factory=list, description="交易标的")
    timeframe: Optional[str] = Field(None, description="时间周期")
    max_position_size: Optional[float] = Field(None, ge=0, description="最大持仓规模")
    max_drawdown: Optional[float] = Field(None, ge=0, le=1, description="最大回撤限制")
    stop_loss: Optional[float] = Field(None, ge=0, le=1, description="止损比例")
    take_profit: Optional[float] = Field(None, ge=0, description="止盈比例")
    tags: List[str] = Field(default_factory=list, description="标签")
    is_public: bool = Field(False, description="是否公开")

    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('策略名称不能为空')
        return v.strip()

    @validator('symbols')
    def validate_symbols(cls, v):
        if v:
            # 验证交易标的格式
            for symbol in v:
                if not isinstance(symbol, str) or not symbol.strip():
                    raise ValueError('交易标的格式不正确')
        return v

    @validator('parameters')
    def validate_parameters(cls, v):
        if v:
            # 验证参数值类型
            for key, value in v.items():
                if not isinstance(key, str):
                    raise ValueError('参数名必须为字符串')
        return v


class StrategyCreate(StrategyBase):
    """创建策略模式"""
    pass


class StrategyUpdate(BaseModel):
    """更新策略模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    strategy_type: Optional[StrategyType] = None
    code: Optional[str] = Field(None, min_length=1)
    entry_point: Optional[str] = None
    language: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    symbols: Optional[List[str]] = None
    timeframe: Optional[str] = None
    max_position_size: Optional[float] = Field(None, ge=0)
    max_drawdown: Optional[float] = Field(None, ge=0, le=1)
    stop_loss: Optional[float] = Field(None, ge=0, le=1)
    take_profit: Optional[float] = Field(None, ge=0)
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    status: Optional[StrategyStatus] = None


class StrategyStatusUpdate(BaseModel):
    """策略状态更新模式"""
    status: StrategyStatus = Field(..., description="策略状态")
    reason: Optional[str] = Field(None, description="状态变更原因")


class StrategyResponse(StrategyBase):
    """策略响应模式"""
    id: int
    uuid: str
    status: StrategyStatus
    version: int
    total_returns: float
    sharpe_ratio: Optional[float]
    max_drawdown_pct: Optional[float]
    win_rate: Optional[float]
    total_trades: int
    is_running: bool
    last_run_at: Optional[datetime]
    last_error: Optional[str]
    is_template: bool
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StrategySearchRequest(BaseModel):
    """策略搜索请求模式"""
    query: Optional[str] = Field(None, description="搜索关键词")
    strategy_type: Optional[StrategyType] = Field(None, description="策略类型")
    status: Optional[StrategyStatus] = Field(None, description="策略状态")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    is_public: Optional[bool] = Field(None, description="是否公开")
    is_template: Optional[bool] = Field(None, description="是否为模板")
    min_returns: Optional[float] = Field(None, description="最小收益率")
    max_drawdown: Optional[float] = Field(None, description="最大回撤")
    min_sharpe_ratio: Optional[float] = Field(None, description="最小夏普比率")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向")


class StrategyListResponse(BaseModel):
    """策略列表响应模式"""
    id: int
    uuid: str
    name: str
    description: Optional[str]
    strategy_type: StrategyType
    status: StrategyStatus
    version: int
    total_returns: float
    sharpe_ratio: Optional[float]
    win_rate: Optional[float]
    total_trades: int
    is_running: bool
    last_run_at: Optional[datetime]
    tags: List[str]
    is_public: bool
    is_template: bool
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StrategyVersionBase(BaseModel):
    """策略版本基础模式"""
    version_name: Optional[str] = Field(None, max_length=100, description="版本名称")
    description: Optional[str] = Field(None, description="版本描述")
    change_log: Optional[str] = Field(None, description="变更日志")
    is_major_version: bool = Field(False, description="是否为主要版本")


class StrategyVersionCreate(StrategyVersionBase):
    """创建策略版本模式"""
    code: str = Field(..., min_length=1, description="策略代码")
    entry_point: str = Field("main", description="入口函数名")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="策略参数")


class StrategyVersionResponse(StrategyVersionBase):
    """策略版本响应模式"""
    id: int
    version_number: int
    code: str
    entry_point: str
    parameters: Dict[str, Any]
    performance_data: Dict[str, Any]
    strategy_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class StrategyTemplateBase(BaseModel):
    """策略模板基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    strategy_type: StrategyType = Field(StrategyType.CUSTOM, description="策略类型")
    category: Optional[str] = Field(None, max_length=50, description="模板分类")
    code_template: str = Field(..., min_length=1, description="模板代码")
    default_parameters: Dict[str, Any] = Field(default_factory=dict, description="默认参数")
    tags: List[str] = Field(default_factory=list, description="标签")


class StrategyTemplateCreate(StrategyTemplateBase):
    """创建策略模板模式"""
    pass


class StrategyTemplateUpdate(BaseModel):
    """更新策略模板模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    strategy_type: Optional[StrategyType] = None
    category: Optional[str] = Field(None, max_length=50)
    code_template: Optional[str] = Field(None, min_length=1)
    default_parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class StrategyTemplateResponse(StrategyTemplateBase):
    """策略模板响应模式"""
    id: int
    uuid: str
    usage_count: int
    rating: float
    is_official: bool
    is_active: bool
    author_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StrategySearchParams(BaseModel):
    """策略搜索参数"""
    keyword: Optional[str] = Field(None, description="关键词搜索")
    strategy_type: Optional[StrategyType] = Field(None, description="策略类型")
    status: Optional[StrategyStatus] = Field(None, description="策略状态")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    is_public: Optional[bool] = Field(None, description="是否公开")
    is_template: Optional[bool] = Field(None, description="是否为模板")
    is_running: Optional[bool] = Field(None, description="是否正在运行")
    created_after: Optional[datetime] = Field(None, description="创建时间起始")
    created_before: Optional[datetime] = Field(None, description="创建时间结束")
    sort_by: Optional[str] = Field("updated_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")

    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = [
            'name', 'created_at', 'updated_at', 'total_returns', 
            'sharpe_ratio', 'win_rate', 'total_trades'
        ]
        if v not in allowed_fields:
            raise ValueError(f'排序字段必须是: {", ".join(allowed_fields)}')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('排序方向必须是 asc 或 desc')
        return v.lower()


class StrategyStatsResponse(BaseModel):
    """策略统计响应模式"""
    total_strategies: int
    active_strategies: int
    running_strategies: int
    draft_strategies: int
    public_strategies: int
    template_strategies: int
    avg_returns: float
    avg_sharpe_ratio: float
    avg_win_rate: float
    total_trades: int

    class Config:
        from_attributes = True


class StrategyExecutionRequest(BaseModel):
    """策略执行请求模式"""
    action: str = Field(..., description="执行动作: start, stop, pause, resume")
    parameters: Optional[Dict[str, Any]] = Field(None, description="执行参数")

    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['start', 'stop', 'pause', 'resume']
        if v not in allowed_actions:
            raise ValueError(f'执行动作必须是: {", ".join(allowed_actions)}')
        return v


class StrategyExecutionResponse(BaseModel):
    """策略执行响应模式"""
    strategy_id: int
    action: str
    success: bool
    message: str
    execution_id: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class StrategyStatsResponse(BaseModel):
    """策略统计响应模式"""
    total_strategies: int
    active_strategies: int
    draft_strategies: int
    public_strategies: int
    template_strategies: int
    avg_returns: float
    avg_sharpe_ratio: Optional[float]
    top_performers: List[StrategyListResponse]


class StrategyCloneRequest(BaseModel):
    """策略克隆请求模式"""
    name: str = Field(..., min_length=1, max_length=100, description="新策略名称")
    description: Optional[str] = Field(None, description="新策略描述")
    is_public: bool = Field(False, description="是否公开")


class BatchStrategyOperation(BaseModel):
    """批量策略操作模式"""
    strategy_ids: List[int] = Field(..., description="策略ID列表")
    operation: str = Field(..., description="操作类型")
    parameters: Optional[Dict[str, Any]] = Field(None, description="操作参数")


class StrategyTemplate(BaseModel):
    """策略模板模式"""
    id: int
    name: str
    description: Optional[str]
    category: str
    code_template: str
    parameters_template: Dict[str, Any]
    is_system: bool
    created_at: datetime

    class Config:
        from_attributes = True