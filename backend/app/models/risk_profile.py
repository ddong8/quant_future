"""
风险偏好和投资配置数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from ..core.database import Base

class RiskToleranceLevel(str, Enum):
    """风险承受能力等级"""
    CONSERVATIVE = "CONSERVATIVE"  # 保守型
    MODERATE = "MODERATE"         # 稳健型
    BALANCED = "BALANCED"         # 平衡型
    AGGRESSIVE = "AGGRESSIVE"     # 积极型
    SPECULATIVE = "SPECULATIVE"   # 投机型

class InvestmentObjective(str, Enum):
    """投资目标"""
    CAPITAL_PRESERVATION = "CAPITAL_PRESERVATION"  # 资本保值
    INCOME_GENERATION = "INCOME_GENERATION"        # 收益生成
    BALANCED_GROWTH = "BALANCED_GROWTH"            # 平衡增长
    CAPITAL_APPRECIATION = "CAPITAL_APPRECIATION"  # 资本增值
    SPECULATION = "SPECULATION"                    # 投机交易

class TimeHorizon(str, Enum):
    """投资时间范围"""
    SHORT_TERM = "SHORT_TERM"    # 短期（<1年）
    MEDIUM_TERM = "MEDIUM_TERM"  # 中期（1-5年）
    LONG_TERM = "LONG_TERM"      # 长期（>5年）

class RiskProfile(Base):
    """用户风险偏好档案"""
    __tablename__ = "risk_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # 风险评估结果
    risk_tolerance = Column(SQLEnum(RiskToleranceLevel), nullable=False, comment="风险承受能力")
    risk_score = Column(Integer, nullable=False, comment="风险评分(0-100)")
    
    # 投资目标和时间范围
    investment_objective = Column(SQLEnum(InvestmentObjective), nullable=False, comment="投资目标")
    time_horizon = Column(SQLEnum(TimeHorizon), nullable=False, comment="投资时间范围")
    
    # 个人信息
    age = Column(Integer, comment="年龄")
    annual_income = Column(Numeric(15, 2), comment="年收入")
    net_worth = Column(Numeric(15, 2), comment="净资产")
    investment_experience_years = Column(Integer, comment="投资经验年数")
    
    # 风险偏好设置
    max_portfolio_loss_percentage = Column(Numeric(5, 2), comment="最大组合亏损百分比")
    max_single_position_percentage = Column(Numeric(5, 2), comment="单一持仓最大百分比")
    preferred_asset_classes = Column(JSON, comment="偏好资产类别")
    excluded_asset_classes = Column(JSON, comment="排除资产类别")
    
    # 评估问卷答案
    questionnaire_answers = Column(JSON, comment="问卷答案")
    questionnaire_version = Column(String(10), comment="问卷版本")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否激活")
    last_assessment_date = Column(DateTime, comment="最后评估日期")
    next_review_date = Column(DateTime, comment="下次复评日期")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User", back_populates="risk_profile")
    portfolio_configs = relationship("PortfolioConfiguration", back_populates="risk_profile", cascade="all, delete-orphan")
    investment_recommendations = relationship("InvestmentRecommendation", back_populates="risk_profile", cascade="all, delete-orphan")

class PortfolioConfiguration(Base):
    """投资组合配置"""
    __tablename__ = "portfolio_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    risk_profile_id = Column(Integer, ForeignKey("risk_profiles.id"), nullable=False)
    
    # 配置基本信息
    name = Column(String(100), nullable=False, comment="配置名称")
    description = Column(Text, comment="配置描述")
    is_default = Column(Boolean, default=False, comment="是否默认配置")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 资产分配
    asset_allocation = Column(JSON, nullable=False, comment="资产分配")
    target_allocation = Column(JSON, comment="目标分配")
    rebalance_threshold = Column(Numeric(5, 2), default=5.0, comment="再平衡阈值(%)")
    
    # 风险控制参数
    max_drawdown_limit = Column(Numeric(5, 2), comment="最大回撤限制(%)")
    stop_loss_percentage = Column(Numeric(5, 2), comment="止损百分比")
    take_profit_percentage = Column(Numeric(5, 2), comment="止盈百分比")
    
    # 投资约束
    min_cash_percentage = Column(Numeric(5, 2), default=5.0, comment="最小现金比例(%)")
    max_leverage_ratio = Column(Numeric(5, 2), default=1.0, comment="最大杠杆比例")
    allowed_instruments = Column(JSON, comment="允许的投资工具")
    forbidden_instruments = Column(JSON, comment="禁止的投资工具")
    
    # 再平衡设置
    rebalance_frequency = Column(String(20), default="monthly", comment="再平衡频率")
    auto_rebalance = Column(Boolean, default=False, comment="自动再平衡")
    last_rebalance_date = Column(DateTime, comment="最后再平衡日期")
    next_rebalance_date = Column(DateTime, comment="下次再平衡日期")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User")
    risk_profile = relationship("RiskProfile", back_populates="portfolio_configs")
    allocation_history = relationship("AllocationHistory", back_populates="portfolio_config", cascade="all, delete-orphan")

class AllocationHistory(Base):
    """资产分配历史记录"""
    __tablename__ = "allocation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_config_id = Column(Integer, ForeignKey("portfolio_configurations.id"), nullable=False)
    
    # 分配信息
    allocation_date = Column(DateTime, nullable=False, comment="分配日期")
    allocation_data = Column(JSON, nullable=False, comment="分配数据")
    total_value = Column(Numeric(15, 2), comment="总价值")
    
    # 变更原因
    change_reason = Column(String(50), comment="变更原因")
    change_description = Column(Text, comment="变更描述")
    
    # 性能指标
    expected_return = Column(Numeric(8, 4), comment="预期收益率")
    expected_volatility = Column(Numeric(8, 4), comment="预期波动率")
    sharpe_ratio = Column(Numeric(8, 4), comment="夏普比率")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关系
    portfolio_config = relationship("PortfolioConfiguration", back_populates="allocation_history")

class InvestmentRecommendation(Base):
    """投资建议"""
    __tablename__ = "investment_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    risk_profile_id = Column(Integer, ForeignKey("risk_profiles.id"), nullable=False)
    
    # 建议基本信息
    title = Column(String(200), nullable=False, comment="建议标题")
    description = Column(Text, comment="建议描述")
    recommendation_type = Column(String(50), nullable=False, comment="建议类型")
    priority = Column(String(20), default="medium", comment="优先级")
    
    # 建议内容
    recommended_action = Column(String(50), comment="建议操作")
    target_symbol = Column(String(20), comment="目标标的")
    target_allocation = Column(Numeric(5, 2), comment="目标分配比例")
    reasoning = Column(Text, comment="建议理由")
    
    # 风险和收益预期
    expected_return = Column(Numeric(8, 4), comment="预期收益率")
    risk_level = Column(String(20), comment="风险等级")
    confidence_score = Column(Numeric(5, 2), comment="置信度评分")
    
    # 状态信息
    status = Column(String(20), default="active", comment="状态")
    is_read = Column(Boolean, default=False, comment="是否已读")
    is_accepted = Column(Boolean, comment="是否接受")
    
    # 有效期
    valid_from = Column(DateTime, comment="有效开始时间")
    valid_until = Column(DateTime, comment="有效结束时间")
    
    # 执行信息
    executed_at = Column(DateTime, comment="执行时间")
    execution_result = Column(JSON, comment="执行结果")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User")
    risk_profile = relationship("RiskProfile", back_populates="investment_recommendations")

class RiskAssessmentQuestion(Base):
    """风险评估问题"""
    __tablename__ = "risk_assessment_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 问题信息
    question_text = Column(Text, nullable=False, comment="问题文本")
    question_type = Column(String(20), nullable=False, comment="问题类型")
    category = Column(String(50), comment="问题分类")
    weight = Column(Numeric(5, 2), default=1.0, comment="权重")
    
    # 选项和评分
    options = Column(JSON, nullable=False, comment="选项列表")
    scoring_rules = Column(JSON, comment="评分规则")
    
    # 版本和状态
    version = Column(String(10), default="1.0", comment="版本")
    is_active = Column(Boolean, default=True, comment="是否激活")
    order_index = Column(Integer, comment="排序索引")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

class MarketRegime(Base):
    """市场环境"""
    __tablename__ = "market_regimes"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 市场环境信息
    regime_name = Column(String(50), nullable=False, comment="环境名称")
    description = Column(Text, comment="环境描述")
    
    # 市场指标
    volatility_level = Column(String(20), comment="波动率水平")
    trend_direction = Column(String(20), comment="趋势方向")
    market_sentiment = Column(String(20), comment="市场情绪")
    
    # 环境参数
    parameters = Column(JSON, comment="环境参数")
    
    # 推荐配置
    recommended_allocations = Column(JSON, comment="推荐分配")
    risk_adjustments = Column(JSON, comment="风险调整")
    
    # 状态信息
    is_current = Column(Boolean, default=False, comment="是否当前环境")
    confidence_level = Column(Numeric(5, 2), comment="置信水平")
    
    # 有效期
    effective_from = Column(DateTime, comment="生效开始时间")
    effective_until = Column(DateTime, comment="生效结束时间")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

class RiskAlert(Base):
    """风险提醒"""
    __tablename__ = "risk_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 提醒信息
    alert_type = Column(String(50), nullable=False, comment="提醒类型")
    title = Column(String(200), nullable=False, comment="提醒标题")
    message = Column(Text, nullable=False, comment="提醒消息")
    severity = Column(String(20), default="medium", comment="严重程度")
    
    # 触发条件
    trigger_condition = Column(JSON, comment="触发条件")
    trigger_value = Column(Numeric(15, 4), comment="触发值")
    current_value = Column(Numeric(15, 4), comment="当前值")
    
    # 相关信息
    related_symbol = Column(String(20), comment="相关标的")
    related_portfolio = Column(String(100), comment="相关组合")
    
    # 状态信息
    status = Column(String(20), default="active", comment="状态")
    is_read = Column(Boolean, default=False, comment="是否已读")
    is_acknowledged = Column(Boolean, default=False, comment="是否确认")
    
    # 处理信息
    acknowledged_at = Column(DateTime, comment="确认时间")
    resolved_at = Column(DateTime, comment="解决时间")
    resolution_note = Column(Text, comment="解决备注")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User")