"""
风险管理相关的数据模型
"""
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field

from .base import BaseResponse


class RiskRuleBase(BaseModel):
    """风险规则基础模型"""
    rule_type: str = Field(..., description="规则类型")
    symbol: Optional[str] = Field(None, description="品种代码")
    rule_value: Decimal = Field(..., description="规则值")
    description: Optional[str] = Field(None, description="描述")
    is_active: bool = Field(True, description="是否激活")


class RiskRuleCreateRequest(RiskRuleBase):
    """创建风险规则请求"""
    pass


class RiskRuleUpdateRequest(BaseModel):
    """更新风险规则请求"""
    rule_value: Optional[Decimal] = Field(None, description="规则值")
    description: Optional[str] = Field(None, description="描述")
    is_active: Optional[bool] = Field(None, description="是否激活")


class RiskRule(RiskRuleBase):
    """风险规则"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RiskRuleListData(BaseModel):
    """风险规则列表数据"""
    rules: List[RiskRule]
    total: int


class RiskEventBase(BaseModel):
    """风险事件基础模型"""
    event_type: str = Field(..., description="事件类型")
    severity: str = Field(..., description="严重程度")
    title: str = Field(..., description="标题")
    description: Optional[str] = Field(None, description="描述")
    event_data: Optional[Dict[str, Any]] = Field(None, description="事件数据")


class RiskEvent(RiskEventBase):
    """风险事件"""
    id: int
    user_id: int
    strategy_id: Optional[int]
    is_resolved: bool
    resolved_at: Optional[datetime]
    resolved_by: Optional[int]
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RiskEventListData(BaseModel):
    """风险事件列表数据"""
    events: List[RiskEvent]
    total: int
    page: int
    page_size: int


class RiskCheckRequest(BaseModel):
    """风险检查请求"""
    symbol: str = Field(..., description="品种代码")
    side: str = Field(..., description="订单方向")
    quantity: float = Field(..., gt=0, description="数量")
    price: Optional[float] = Field(None, description="价格")
    order_type: str = Field("MARKET", description="订单类型")


class RiskCheckResult(BaseModel):
    """风险检查结果"""
    passed: bool = Field(..., description="是否通过")
    message: str = Field(..., description="检查消息")
    risk_level: str = Field(..., description="风险等级")
    failed_checks: Optional[List[Dict[str, Any]]] = Field(None, description="失败的检查项")


class RiskMetrics(BaseModel):
    """风险指标"""
    total_assets: float = Field(..., description="总资产")
    available_balance: float = Field(..., description="可用余额")
    used_margin: float = Field(..., description="已用保证金")
    total_market_value: float = Field(..., description="总市值")
    total_unrealized_pnl: float = Field(..., description="总未实现盈亏")
    margin_ratio: float = Field(..., description="保证金比例")
    position_count: int = Field(..., description="持仓数量")
    max_single_position_ratio: float = Field(..., description="最大单一持仓比例")


class RiskDashboard(BaseModel):
    """风险管理仪表板"""
    risk_metrics: RiskMetrics
    active_rules_count: int = Field(..., description="活跃规则数量")
    total_rules_count: int = Field(..., description="总规则数量")
    recent_events_count: int = Field(..., description="最近事件数量")
    risk_level: str = Field(..., description="风险等级")
    last_update: str = Field(..., description="最后更新时间")


class RiskAlertSettings(BaseModel):
    """风险告警设置"""
    daily_loss_threshold: float = Field(..., description="日亏损阈值")
    position_concentration_threshold: float = Field(..., description="持仓集中度阈值")
    margin_ratio_threshold: float = Field(..., description="保证金比例阈值")
    enable_email_alerts: bool = Field(True, description="启用邮件告警")
    enable_sms_alerts: bool = Field(False, description="启用短信告警")
    alert_frequency_minutes: int = Field(30, description="告警频率(分钟)")


class RiskReport(BaseModel):
    """风险报告"""
    report_date: str = Field(..., description="报告日期")
    risk_score: float = Field(..., description="风险评分")
    risk_level: str = Field(..., description="风险等级")
    key_metrics: Dict[str, float] = Field(..., description="关键指标")
    risk_events: List[RiskEvent] = Field(..., description="风险事件")
    recommendations: List[str] = Field(..., description="建议")


class AutoRiskAction(BaseModel):
    """自动风险处理动作"""
    action_type: str = Field(..., description="动作类型")
    trigger_condition: Dict[str, Any] = Field(..., description="触发条件")
    action_parameters: Dict[str, Any] = Field(..., description="动作参数")
    is_enabled: bool = Field(True, description="是否启用")
    priority: int = Field(1, description="优先级")


# 响应模型
class RiskRuleResponse(BaseResponse):
    """风险规则响应"""
    data: RiskRule


class RiskRuleListResponse(BaseResponse):
    """风险规则列表响应"""
    data: RiskRuleListData


class RiskEventResponse(BaseResponse):
    """风险事件响应"""
    data: RiskEvent


class RiskEventListResponse(BaseResponse):
    """风险事件列表响应"""
    data: RiskEventListData


class RiskCheckResponse(BaseResponse):
    """风险检查响应"""
    data: RiskCheckResult


class RiskMetricsResponse(BaseResponse):
    """风险指标响应"""
    data: RiskMetrics


class RiskDashboardResponse(BaseResponse):
    """风险仪表板响应"""
    data: RiskDashboard


class RiskReportResponse(BaseResponse):
    """风险报告响应"""
    data: RiskReport