"""
风险偏好和投资配置Schema
"""
from typing import Optional, Dict, List, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from ..models.risk_profile import RiskToleranceLevel, InvestmentObjective, TimeHorizon

class RiskAssessmentAnswer(BaseModel):
    """风险评估答案"""
    question_id: int = Field(..., description="问题ID")
    answer: str = Field(..., description="答案")
    score: Optional[int] = Field(None, description="得分")

class RiskAssessmentRequest(BaseModel):
    """风险评估请求"""
    answers: List[RiskAssessmentAnswer] = Field(..., description="问卷答案")
    personal_info: Optional[Dict[str, Any]] = Field(None, description="个人信息")

class RiskProfileBase(BaseModel):
    """风险偏好基础模型"""
    risk_tolerance: RiskToleranceLevel = Field(..., description="风险承受能力")
    investment_objective: InvestmentObjective = Field(..., description="投资目标")
    time_horizon: TimeHorizon = Field(..., description="投资时间范围")
    age: Optional[int] = Field(None, ge=18, le=100, description="年龄")
    annual_income: Optional[Decimal] = Field(None, ge=0, description="年收入")
    net_worth: Optional[Decimal] = Field(None, ge=0, description="净资产")
    investment_experience_years: Optional[int] = Field(None, ge=0, description="投资经验年数")
    max_portfolio_loss_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="最大组合亏损百分比")
    max_single_position_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="单一持仓最大百分比")
    preferred_asset_classes: Optional[List[str]] = Field(default_factory=list, description="偏好资产类别")
    excluded_asset_classes: Optional[List[str]] = Field(default_factory=list, description="排除资产类别")

class RiskProfileCreate(RiskProfileBase):
    """创建风险偏好"""
    questionnaire_answers: Optional[Dict[str, Any]] = Field(None, description="问卷答案")
    questionnaire_version: Optional[str] = Field(None, description="问卷版本")

class RiskProfileUpdate(BaseModel):
    """更新风险偏好"""
    risk_tolerance: Optional[RiskToleranceLevel] = Field(None, description="风险承受能力")
    investment_objective: Optional[InvestmentObjective] = Field(None, description="投资目标")
    time_horizon: Optional[TimeHorizon] = Field(None, description="投资时间范围")
    max_portfolio_loss_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="最大组合亏损百分比")
    max_single_position_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="单一持仓最大百分比")
    preferred_asset_classes: Optional[List[str]] = Field(None, description="偏好资产类别")
    excluded_asset_classes: Optional[List[str]] = Field(None, description="排除资产类别")

class RiskProfileResponse(RiskProfileBase):
    """风险偏好响应"""
    id: int
    user_id: int
    risk_score: int
    is_active: bool
    last_assessment_date: Optional[datetime]
    next_review_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class PortfolioConfigurationBase(BaseModel):
    """投资组合配置基础模型"""
    name: str = Field(..., max_length=100, description="配置名称")
    description: Optional[str] = Field(None, description="配置描述")
    asset_allocation: Dict[str, Decimal] = Field(..., description="资产分配")
    rebalance_threshold: Optional[Decimal] = Field(default=Decimal('5.0'), ge=0, le=50, description="再平衡阈值(%)")
    max_drawdown_limit: Optional[Decimal] = Field(None, ge=0, le=100, description="最大回撤限制(%)")
    stop_loss_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="止损百分比")
    take_profit_percentage: Optional[Decimal] = Field(None, ge=0, le=1000, description="止盈百分比")
    min_cash_percentage: Optional[Decimal] = Field(default=Decimal('5.0'), ge=0, le=100, description="最小现金比例(%)")
    max_leverage_ratio: Optional[Decimal] = Field(default=Decimal('1.0'), ge=0, le=10, description="最大杠杆比例")
    allowed_instruments: Optional[List[str]] = Field(default_factory=list, description="允许的投资工具")
    forbidden_instruments: Optional[List[str]] = Field(default_factory=list, description="禁止的投资工具")
    rebalance_frequency: Optional[str] = Field(default="monthly", description="再平衡频率")
    auto_rebalance: Optional[bool] = Field(default=False, description="自动再平衡")
    
    @validator('asset_allocation')
    def validate_allocation_sum(cls, v):
        """验证资产分配总和"""
        total = sum(v.values())
        if abs(total - 100) > 0.01:  # 允许0.01%的误差
            raise ValueError('资产分配总和必须等于100%')
        return v

class PortfolioConfigurationCreate(PortfolioConfigurationBase):
    """创建投资组合配置"""
    pass

class PortfolioConfigurationUpdate(BaseModel):
    """更新投资组合配置"""
    name: Optional[str] = Field(None, max_length=100, description="配置名称")
    description: Optional[str] = Field(None, description="配置描述")
    asset_allocation: Optional[Dict[str, Decimal]] = Field(None, description="资产分配")
    rebalance_threshold: Optional[Decimal] = Field(None, ge=0, le=50, description="再平衡阈值(%)")
    max_drawdown_limit: Optional[Decimal] = Field(None, ge=0, le=100, description="最大回撤限制(%)")
    stop_loss_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="止损百分比")
    take_profit_percentage: Optional[Decimal] = Field(None, ge=0, le=1000, description="止盈百分比")
    auto_rebalance: Optional[bool] = Field(None, description="自动再平衡")

class PortfolioConfigurationResponse(PortfolioConfigurationBase):
    """投资组合配置响应"""
    id: int
    user_id: int
    risk_profile_id: int
    is_default: bool
    is_active: bool
    target_allocation: Optional[Dict[str, Any]]
    last_rebalance_date: Optional[datetime]
    next_rebalance_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class InvestmentRecommendationBase(BaseModel):
    """投资建议基础模型"""
    title: str = Field(..., max_length=200, description="建议标题")
    description: Optional[str] = Field(None, description="建议描述")
    recommendation_type: str = Field(..., description="建议类型")
    priority: Optional[str] = Field(default="medium", description="优先级")
    recommended_action: Optional[str] = Field(None, description="建议操作")
    target_symbol: Optional[str] = Field(None, description="目标标的")
    target_allocation: Optional[Decimal] = Field(None, ge=0, le=100, description="目标分配比例")
    reasoning: Optional[str] = Field(None, description="建议理由")
    expected_return: Optional[Decimal] = Field(None, description="预期收益率")
    risk_level: Optional[str] = Field(None, description="风险等级")
    confidence_score: Optional[Decimal] = Field(None, ge=0, le=100, description="置信度评分")
    valid_from: Optional[datetime] = Field(None, description="有效开始时间")
    valid_until: Optional[datetime] = Field(None, description="有效结束时间")

class InvestmentRecommendationResponse(InvestmentRecommendationBase):
    """投资建议响应"""
    id: int
    user_id: int
    risk_profile_id: int
    status: str
    is_read: bool
    is_accepted: Optional[bool]
    executed_at: Optional[datetime]
    execution_result: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class RiskAssessmentQuestionResponse(BaseModel):
    """风险评估问题响应"""
    id: int
    question_text: str
    question_type: str
    category: Optional[str]
    options: List[Dict[str, Any]]
    order_index: Optional[int]
    
    class Config:
        orm_mode = True

class AssetAllocationSuggestion(BaseModel):
    """资产分配建议"""
    asset_class: str = Field(..., description="资产类别")
    suggested_percentage: Decimal = Field(..., ge=0, le=100, description="建议分配比例")
    min_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="最小比例")
    max_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="最大比例")
    reasoning: Optional[str] = Field(None, description="建议理由")
    expected_return: Optional[Decimal] = Field(None, description="预期收益率")
    expected_volatility: Optional[Decimal] = Field(None, description="预期波动率")

class PortfolioOptimizationRequest(BaseModel):
    """投资组合优化请求"""
    target_return: Optional[Decimal] = Field(None, description="目标收益率")
    max_volatility: Optional[Decimal] = Field(None, description="最大波动率")
    constraints: Optional[Dict[str, Any]] = Field(None, description="约束条件")
    optimization_method: Optional[str] = Field(default="mean_variance", description="优化方法")

class PortfolioOptimizationResponse(BaseModel):
    """投资组合优化响应"""
    optimized_allocation: Dict[str, Decimal] = Field(..., description="优化后分配")
    expected_return: Decimal = Field(..., description="预期收益率")
    expected_volatility: Decimal = Field(..., description="预期波动率")
    sharpe_ratio: Decimal = Field(..., description="夏普比率")
    optimization_score: Decimal = Field(..., description="优化评分")
    suggestions: List[AssetAllocationSuggestion] = Field(..., description="分配建议")

class RiskAlertBase(BaseModel):
    """风险提醒基础模型"""
    alert_type: str = Field(..., description="提醒类型")
    title: str = Field(..., max_length=200, description="提醒标题")
    message: str = Field(..., description="提醒消息")
    severity: Optional[str] = Field(default="medium", description="严重程度")
    related_symbol: Optional[str] = Field(None, description="相关标的")
    related_portfolio: Optional[str] = Field(None, description="相关组合")

class RiskAlertResponse(RiskAlertBase):
    """风险提醒响应"""
    id: int
    user_id: int
    trigger_condition: Optional[Dict[str, Any]]
    trigger_value: Optional[Decimal]
    current_value: Optional[Decimal]
    status: str
    is_read: bool
    is_acknowledged: bool
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    resolution_note: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class RiskToleranceLevelInfo(BaseModel):
    """风险承受能力等级信息"""
    level: RiskToleranceLevel
    name: str
    description: str
    characteristics: List[str]
    suitable_investments: List[str]
    max_loss_tolerance: Decimal
    typical_allocation: Dict[str, Decimal]

class InvestmentObjectiveInfo(BaseModel):
    """投资目标信息"""
    objective: InvestmentObjective
    name: str
    description: str
    time_horizon: List[TimeHorizon]
    risk_tolerance: List[RiskToleranceLevel]
    typical_allocation: Dict[str, Decimal]

class MarketRegimeResponse(BaseModel):
    """市场环境响应"""
    id: int
    regime_name: str
    description: Optional[str]
    volatility_level: Optional[str]
    trend_direction: Optional[str]
    market_sentiment: Optional[str]
    is_current: bool
    confidence_level: Optional[Decimal]
    recommended_allocations: Optional[Dict[str, Any]]
    risk_adjustments: Optional[Dict[str, Any]]
    effective_from: Optional[datetime]
    effective_until: Optional[datetime]
    
    class Config:
        orm_mode = True

class RiskProfileAnalysis(BaseModel):
    """风险偏好分析"""
    current_profile: RiskProfileResponse
    risk_level_info: RiskToleranceLevelInfo
    objective_info: InvestmentObjectiveInfo
    recommended_allocation: Dict[str, Decimal]
    portfolio_suggestions: List[AssetAllocationSuggestion]
    next_review_date: datetime
    improvement_suggestions: List[str]