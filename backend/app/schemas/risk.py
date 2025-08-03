"""
风险管理数据模式
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from enum import Enum


class RiskLevelEnum(str, Enum):
    """风险等级枚举"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskEventStatusEnum(str, Enum):
    """风险事件状态枚举"""
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"
    ESCALATED = "ESCALATED"


class RiskRuleTypeEnum(str, Enum):
    """风险规则类型枚举"""
    POSITION_LIMIT = "POSITION_LIMIT"
    CONCENTRATION = "CONCENTRATION"
    VAR_LIMIT = "VAR_LIMIT"
    DRAWDOWN_LIMIT = "DRAWDOWN_LIMIT"
    LEVERAGE_LIMIT = "LEVERAGE_LIMIT"
    LOSS_LIMIT = "LOSS_LIMIT"
    VOLATILITY_LIMIT = "VOLATILITY_LIMIT"
    CORRELATION_LIMIT = "CORRELATION_LIMIT"
    LIQUIDITY_RISK = "LIQUIDITY_RISK"
    CUSTOM = "CUSTOM"


class ActionTypeEnum(str, Enum):
    """风险处置动作类型枚举"""
    ALERT = "ALERT"
    BLOCK_ORDER = "BLOCK_ORDER"
    FORCE_CLOSE = "FORCE_CLOSE"
    REDUCE_POSITION = "REDUCE_POSITION"
    SUSPEND_TRADING = "SUSPEND_TRADING"
    NOTIFY_ADMIN = "NOTIFY_ADMIN"
    CUSTOM_ACTION = "CUSTOM_ACTION"


# ==================== 风险规则相关 ====================

class RiskRuleBase(BaseModel):
    """风险规则基础模式"""
    name: str = Field(..., description="规则名称", max_length=100)
    description: Optional[str] = Field(None, description="规则描述")
    rule_type: RiskRuleTypeEnum = Field(..., description="规则类型")
    conditions: Dict[str, Any] = Field(..., description="触发条件")
    actions: List[Dict[str, Any]] = Field(..., description="处置动作")
    is_active: bool = Field(True, description="是否激活")
    priority: int = Field(0, description="优先级")
    risk_level: RiskLevelEnum = Field(RiskLevelEnum.MEDIUM, description="风险等级")
    user_id: Optional[int] = Field(None, description="适用用户ID")
    strategy_id: Optional[int] = Field(None, description="适用策略ID")
    symbol_pattern: Optional[str] = Field(None, description="标的模式匹配", max_length=100)
    effective_from: Optional[datetime] = Field(None, description="生效开始时间")
    effective_to: Optional[datetime] = Field(None, description="生效结束时间")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")

    @validator('conditions')
    def validate_conditions(cls, v, values):
        """验证条件配置"""
        rule_type = values.get('rule_type')
        if not v:
            raise ValueError("条件配置不能为空")
        
        # 根据规则类型验证必要的条件参数
        if rule_type == RiskRuleTypeEnum.POSITION_LIMIT:
            if 'max_position' not in v:
                raise ValueError("持仓限制规则必须包含 max_position 参数")
        elif rule_type == RiskRuleTypeEnum.CONCENTRATION:
            if 'max_concentration' not in v:
                raise ValueError("集中度规则必须包含 max_concentration 参数")
        elif rule_type == RiskRuleTypeEnum.VAR_LIMIT:
            if 'max_var' not in v:
                raise ValueError("VaR限制规则必须包含 max_var 参数")
        elif rule_type == RiskRuleTypeEnum.DRAWDOWN_LIMIT:
            if 'max_drawdown' not in v:
                raise ValueError("回撤限制规则必须包含 max_drawdown 参数")
        elif rule_type == RiskRuleTypeEnum.LEVERAGE_LIMIT:
            if 'max_leverage' not in v:
                raise ValueError("杠杆限制规则必须包含 max_leverage 参数")
        elif rule_type == RiskRuleTypeEnum.LOSS_LIMIT:
            if 'max_loss' not in v:
                raise ValueError("亏损限制规则必须包含 max_loss 参数")
        
        return v

    @validator('actions')
    def validate_actions(cls, v):
        """验证动作配置"""
        if not v:
            raise ValueError("动作配置不能为空")
        
        valid_action_types = [action.value for action in ActionTypeEnum]
        
        for action in v:
            if 'type' not in action:
                raise ValueError("动作必须包含 type 字段")
            
            if action['type'] not in valid_action_types:
                raise ValueError(f"无效的动作类型: {action['type']}")
        
        return v

    @validator('effective_to')
    def validate_effective_period(cls, v, values):
        """验证生效时间范围"""
        effective_from = values.get('effective_from')
        if effective_from and v and v <= effective_from:
            raise ValueError("生效结束时间必须晚于开始时间")
        return v


class RiskRuleCreate(RiskRuleBase):
    """创建风险规则"""
    pass


class RiskRuleUpdate(BaseModel):
    """更新风险规则"""
    name: Optional[str] = Field(None, description="规则名称", max_length=100)
    description: Optional[str] = Field(None, description="规则描述")
    conditions: Optional[Dict[str, Any]] = Field(None, description="触发条件")
    actions: Optional[List[Dict[str, Any]]] = Field(None, description="处置动作")
    is_active: Optional[bool] = Field(None, description="是否激活")
    priority: Optional[int] = Field(None, description="优先级")
    risk_level: Optional[RiskLevelEnum] = Field(None, description="风险等级")
    user_id: Optional[int] = Field(None, description="适用用户ID")
    strategy_id: Optional[int] = Field(None, description="适用策略ID")
    symbol_pattern: Optional[str] = Field(None, description="标的模式匹配", max_length=100)
    effective_from: Optional[datetime] = Field(None, description="生效开始时间")
    effective_to: Optional[datetime] = Field(None, description="生效结束时间")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class RiskRuleResponse(RiskRuleBase):
    """风险规则响应"""
    id: int = Field(..., description="规则ID")
    trigger_count: int = Field(..., description="触发次数")
    last_triggered_at: Optional[datetime] = Field(None, description="最后触发时间")
    created_by: Optional[int] = Field(None, description="创建者ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# ==================== 风险事件相关 ====================

class RiskEventBase(BaseModel):
    """风险事件基础模式"""
    event_type: str = Field(..., description="事件类型", max_length=50)
    severity: RiskLevelEnum = Field(..., description="严重程度")
    status: RiskEventStatusEnum = Field(RiskEventStatusEnum.ACTIVE, description="事件状态")
    title: str = Field(..., description="事件标题", max_length=200)
    message: str = Field(..., description="事件消息")
    data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="事件数据")


class RiskEventUpdate(BaseModel):
    """更新风险事件"""
    resolution_notes: Optional[str] = Field(None, description="解决备注")


class RiskEventResponse(RiskEventBase):
    """风险事件响应"""
    id: int = Field(..., description="事件ID")
    rule_id: int = Field(..., description="规则ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    strategy_id: Optional[int] = Field(None, description="策略ID")
    position_id: Optional[int] = Field(None, description="持仓ID")
    order_id: Optional[int] = Field(None, description="订单ID")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")
    resolved_by: Optional[int] = Field(None, description="解决者ID")
    resolution_notes: Optional[str] = Field(None, description="解决备注")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# ==================== 风险指标相关 ====================

class RiskMetricsBase(BaseModel):
    """风险指标基础模式"""
    user_id: int = Field(..., description="用户ID")
    strategy_id: Optional[int] = Field(None, description="策略ID")
    date: datetime = Field(..., description="日期")
    period_type: str = Field("daily", description="周期类型")
    
    # 基础指标
    portfolio_value: Optional[Decimal] = Field(None, description="组合价值")
    cash_balance: Optional[Decimal] = Field(None, description="现金余额")
    total_exposure: Optional[Decimal] = Field(None, description="总敞口")
    net_exposure: Optional[Decimal] = Field(None, description="净敞口")
    
    # 收益指标
    daily_return: Optional[Decimal] = Field(None, description="日收益率")
    cumulative_return: Optional[Decimal] = Field(None, description="累计收益率")
    
    # 风险指标
    volatility: Optional[Decimal] = Field(None, description="波动率")
    max_drawdown: Optional[Decimal] = Field(None, description="最大回撤")
    current_drawdown: Optional[Decimal] = Field(None, description="当前回撤")
    var_95: Optional[Decimal] = Field(None, description="95% VaR")
    var_99: Optional[Decimal] = Field(None, description="99% VaR")
    cvar_95: Optional[Decimal] = Field(None, description="95% CVaR")
    
    # 杠杆和集中度
    leverage_ratio: Optional[Decimal] = Field(None, description="杠杆率")
    concentration_ratio: Optional[Decimal] = Field(None, description="集中度比率")
    
    # 流动性指标
    liquidity_ratio: Optional[Decimal] = Field(None, description="流动性比率")
    
    # 其他指标
    sharpe_ratio: Optional[Decimal] = Field(None, description="夏普比率")
    sortino_ratio: Optional[Decimal] = Field(None, description="索提诺比率")
    calmar_ratio: Optional[Decimal] = Field(None, description="卡玛比率")
    
    # 元数据
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")


class RiskMetricsResponse(RiskMetricsBase):
    """风险指标响应"""
    id: int = Field(..., description="指标ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# ==================== 风险限额相关 ====================

class RiskLimitBase(BaseModel):
    """风险限额基础模式"""
    user_id: int = Field(..., description="用户ID")
    strategy_id: Optional[int] = Field(None, description="策略ID")
    limit_type: str = Field(..., description="限额类型", max_length=50)
    limit_name: str = Field(..., description="限额名称", max_length=100)
    description: Optional[str] = Field(None, description="限额描述")
    limit_value: Decimal = Field(..., description="限额值")
    is_hard_limit: bool = Field(True, description="是否硬限制")
    warning_threshold: Decimal = Field(Decimal('0.8'), description="预警阈值")
    reset_frequency: str = Field("daily", description="重置频率")
    is_active: bool = Field(True, description="是否激活")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")

    @validator('warning_threshold')
    def validate_warning_threshold(cls, v):
        """验证预警阈值"""
        if v < 0 or v > 1:
            raise ValueError("预警阈值必须在0-1之间")
        return v

    @validator('reset_frequency')
    def validate_reset_frequency(cls, v):
        """验证重置频率"""
        valid_frequencies = ['daily', 'weekly', 'monthly', 'never']
        if v not in valid_frequencies:
            raise ValueError(f"重置频率必须是以下之一: {valid_frequencies}")
        return v


class RiskLimitCreate(RiskLimitBase):
    """创建风险限额"""
    pass


class RiskLimitUpdate(BaseModel):
    """更新风险限额"""
    limit_name: Optional[str] = Field(None, description="限额名称", max_length=100)
    description: Optional[str] = Field(None, description="限额描述")
    limit_value: Optional[Decimal] = Field(None, description="限额值")
    is_hard_limit: Optional[bool] = Field(None, description="是否硬限制")
    warning_threshold: Optional[Decimal] = Field(None, description="预警阈值")
    reset_frequency: Optional[str] = Field(None, description="重置频率")
    is_active: Optional[bool] = Field(None, description="是否激活")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class RiskLimitResponse(RiskLimitBase):
    """风险限额响应"""
    id: int = Field(..., description="限额ID")
    current_value: Optional[Decimal] = Field(None, description="当前值")
    utilization_ratio: Optional[Decimal] = Field(None, description="使用率")
    is_breached: bool = Field(..., description="是否违反")
    breach_count: int = Field(..., description="违反次数")
    last_breach_at: Optional[datetime] = Field(None, description="最后违反时间")
    last_reset_at: Optional[datetime] = Field(None, description="最后重置时间")
    created_by: Optional[int] = Field(None, description="创建者ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# ==================== 风险检查相关 ====================

class RiskCheckContext(BaseModel):
    """风险检查上下文"""
    user_id: int = Field(..., description="用户ID")
    strategy_id: Optional[int] = Field(None, description="策略ID")
    position_id: Optional[int] = Field(None, description="持仓ID")
    order_id: Optional[int] = Field(None, description="订单ID")
    symbol: Optional[str] = Field(None, description="标的代码")
    
    # 风险指标
    position_value: Optional[float] = Field(None, description="持仓价值")
    concentration: Optional[float] = Field(None, description="集中度")
    var_value: Optional[float] = Field(None, description="VaR值")
    drawdown: Optional[float] = Field(None, description="回撤")
    leverage: Optional[float] = Field(None, description="杠杆率")
    loss: Optional[float] = Field(None, description="亏损")
    volatility: Optional[float] = Field(None, description="波动率")
    correlation: Optional[float] = Field(None, description="相关性")
    liquidity_ratio: Optional[float] = Field(None, description="流动性比率")
    
    # 其他数据
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他数据")


class RiskCheckResponse(BaseModel):
    """风险检查响应"""
    message: str = Field(..., description="检查结果消息")
    events_count: int = Field(..., description="触发事件数量")
    events: List[Dict[str, Any]] = Field(..., description="触发的事件列表")


# ==================== 风险报告相关 ====================

class RiskSummaryResponse(BaseModel):
    """风险摘要响应"""
    latest_metrics: Optional[Dict[str, Any]] = Field(None, description="最新风险指标")
    active_events_count: int = Field(..., description="活跃事件数量")
    active_events: List[Dict[str, Any]] = Field(..., description="活跃事件列表")
    risk_limits: List[Dict[str, Any]] = Field(..., description="风险限额列表")
    summary: Dict[str, Any] = Field(..., description="摘要统计")


# ==================== 风险配置模板 ====================

class RiskRuleTemplate(BaseModel):
    """风险规则模板"""
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    rule_type: RiskRuleTypeEnum = Field(..., description="规则类型")
    default_conditions: Dict[str, Any] = Field(..., description="默认条件")
    default_actions: List[Dict[str, Any]] = Field(..., description="默认动作")
    parameters: List[Dict[str, Any]] = Field(..., description="可配置参数")


# ==================== 风险控制自动化执行相关 ====================

class RiskAction(BaseModel):
    """风险控制动作"""
    action_type: str = Field(..., description="动作类型")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="动作参数")
    reason: str = Field(..., description="执行原因")


class RiskCheckRequest(BaseModel):
    """风险检查请求"""
    user_id: int = Field(..., description="用户ID")
    order_data: Dict[str, Any] = Field(..., description="订单数据")


class RiskCheckResult(BaseModel):
    """风险检查结果"""
    passed: bool = Field(..., description="是否通过检查")
    risk_level: str = Field(..., description="风险级别")
    message: str = Field(..., description="检查消息")
    actions: List[RiskAction] = Field(default_factory=list, description="建议的风险控制动作")


class RiskControlActionRequest(BaseModel):
    """风险控制动作请求"""
    user_id: int = Field(..., description="用户ID")
    action: str = Field(..., description="动作类型")
    context: Dict[str, Any] = Field(default_factory=dict, description="执行上下文")


class RiskControlActionResult(BaseModel):
    """风险控制动作结果"""
    success: bool = Field(..., description="是否执行成功")
    action: str = Field(..., description="动作类型")
    user_id: int = Field(..., description="用户ID")
    executed_at: datetime = Field(..., description="执行时间")
    message: str = Field(..., description="执行消息")


class EmergencyRiskControlRequest(BaseModel):
    """紧急风险控制请求"""
    user_id: int = Field(..., description="用户ID")
    reason: str = Field(..., description="触发原因")


class RiskMonitoringStatus(BaseModel):
    """风险监控状态"""
    user_id: int = Field(..., description="用户ID")
    is_monitoring: bool = Field(..., description="是否正在监控")
    last_check_time: Optional[datetime] = Field(None, description="最后检查时间")
    risk_level: str = Field(..., description="当前风险级别")
    active_rules_count: int = Field(..., description="活跃规则数量")
    triggered_actions_count: int = Field(..., description="触发动作数量")


class RiskControlConfig(BaseModel):
    """风险控制配置"""
    max_position_size_ratio: float = Field(..., description="最大持仓占比")
    max_daily_loss_ratio: float = Field(..., description="最大日亏损比例")
    margin_call_ratio: float = Field(..., description="保证金追缴比例")
    liquidation_ratio: float = Field(..., description="强制平仓比例")
    max_order_value_ratio: float = Field(..., description="最大订单价值比例")
    auto_risk_control_enabled: bool = Field(True, description="是否启用自动风险控制")
    emergency_control_enabled: bool = Field(True, description="是否启用紧急风险控制")


# ==================== 风险报告相关 ====================

class RiskReportRequest(BaseModel):
    """风险报告请求"""
    user_id: int = Field(..., description="用户ID")
    report_type: str = Field(..., description="报告类型")
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="自定义配置")


class RiskReportResponse(BaseModel):
    """风险报告响应"""
    report_id: str = Field(..., description="报告ID")
    user_id: int = Field(..., description="用户ID")
    report_type: str = Field(..., description="报告类型")
    generated_at: datetime = Field(..., description="生成时间")
    executive_summary: Dict[str, Any] = Field(..., description="执行摘要")
    risk_metrics: Dict[str, Any] = Field(..., description="风险指标")
    recommendations: List[Dict[str, Any]] = Field(..., description="改进建议")


class RiskAnalysisRequest(BaseModel):
    """风险分析请求"""
    user_id: int = Field(..., description="用户ID")
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    analysis_types: List[str] = Field(..., description="分析类型列表")


class RiskAnalysisResponse(BaseModel):
    """风险分析响应"""
    analysis_id: str = Field(..., description="分析ID")
    user_id: int = Field(..., description="用户ID")
    results: Dict[str, Any] = Field(..., description="分析结果")
    generated_at: datetime = Field(..., description="生成时间")


class ReportScheduleConfig(BaseModel):
    """报告调度配置"""
    user_id: int = Field(..., description="用户ID")
    daily_enabled: bool = Field(False, description="是否启用日报")
    weekly_enabled: bool = Field(False, description="是否启用周报")
    monthly_enabled: bool = Field(False, description="是否启用月报")
    email_delivery: bool = Field(True, description="是否邮件发送")
    notification_delivery: bool = Field(True, description="是否站内通知")
    custom_schedule: Optional[str] = Field(None, description="自定义调度表达式")


# 预定义的风险规则模板
RISK_RULE_TEMPLATES = [
    RiskRuleTemplate(
        name="单一持仓限制",
        description="限制单一标的的最大持仓价值",
        rule_type=RiskRuleTypeEnum.POSITION_LIMIT,
        default_conditions={"max_position": 100000},
        default_actions=[{"type": "ALERT", "params": {}}],
        parameters=[
            {"name": "max_position", "type": "number", "description": "最大持仓价值", "default": 100000}
        ]
    ),
    RiskRuleTemplate(
        name="集中度控制",
        description="控制单一标的在组合中的最大占比",
        rule_type=RiskRuleTypeEnum.CONCENTRATION,
        default_conditions={"max_concentration": 0.2},
        default_actions=[{"type": "ALERT", "params": {}}],
        parameters=[
            {"name": "max_concentration", "type": "number", "description": "最大集中度", "default": 0.2}
        ]
    ),
    RiskRuleTemplate(
        name="最大回撤控制",
        description="控制组合的最大回撤幅度",
        rule_type=RiskRuleTypeEnum.DRAWDOWN_LIMIT,
        default_conditions={"max_drawdown": 0.1},
        default_actions=[{"type": "ALERT", "params": {}}, {"type": "SUSPEND_TRADING", "params": {"duration_minutes": 60}}],
        parameters=[
            {"name": "max_drawdown", "type": "number", "description": "最大回撤", "default": 0.1}
        ]
    ),
    RiskRuleTemplate(
        name="杠杆率限制",
        description="限制组合的最大杠杆率",
        rule_type=RiskRuleTypeEnum.LEVERAGE_LIMIT,
        default_conditions={"max_leverage": 3.0},
        default_actions=[{"type": "BLOCK_ORDER", "params": {}}],
        parameters=[
            {"name": "max_leverage", "type": "number", "description": "最大杠杆率", "default": 3.0}
        ]
    ),
    RiskRuleTemplate(
        name="VaR限制",
        description="限制组合的风险价值",
        rule_type=RiskRuleTypeEnum.VAR_LIMIT,
        default_conditions={"max_var": 50000},
        default_actions=[{"type": "ALERT", "params": {}}, {"type": "REDUCE_POSITION", "params": {"reduce_ratio": 0.3}}],
        parameters=[
            {"name": "max_var", "type": "number", "description": "最大VaR值", "default": 50000}
        ]
    )
]