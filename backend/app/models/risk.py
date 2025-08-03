"""
风险管理相关数据模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean, Numeric, DECIMAL, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any

from ..core.database import Base
from .enums import RiskEventType, RiskRuleType


class RiskRule(Base):
    """风险规则模型"""
    __tablename__ = "risk_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 规则信息
    rule_type = Column(SQLEnum(RiskRuleType), nullable=False)
    symbol = Column(String(20), nullable=True, index=True)  # 品种代码，为空表示全局规则
    rule_value = Column(Numeric(precision=18, scale=8), nullable=False)
    description = Column(Text)
    
    # 规则状态
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<RiskRule(id={self.id}, type='{self.rule_type}', value={self.rule_value})>"


class RiskEvent(Base):
    """风险事件模型"""
    __tablename__ = "risk_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 事件基本信息
    event_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="medium")  # low/medium/high/critical
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # 关联信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), index=True)
    rule_id = Column(Integer, ForeignKey("risk_rules.id"), index=True)
    
    # 事件数据
    event_data = Column(JSON)  # 事件相关数据
    threshold_value = Column(Float)  # 阈值
    actual_value = Column(Float)  # 实际值
    
    # 处理状态
    is_resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)
    resolved_at = Column(DateTime(timezone=True))
    
    # 自动处理
    auto_action_taken = Column(String(100))  # 自动执行的动作
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="risk_events")
    strategy = relationship("Strategy", foreign_keys=[strategy_id])
    rule = relationship("RiskRule", foreign_keys=[rule_id])
    
    def __repr__(self):
        return f"<RiskEvent(id={self.id}, type='{self.event_type}', severity='{self.severity}')>"


class RiskMetric(Base):
    """风险指标模型"""
    __tablename__ = "risk_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), index=True)
    
    # 指标类型和值
    metric_type = Column(String(50), nullable=False)  # var/drawdown/concentration等
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))  # percent/amount/ratio等
    
    # 时间维度
    time_period = Column(String(20), nullable=False)  # daily/weekly/monthly
    calculation_date = Column(DateTime(timezone=True), nullable=False)
    
    # 基准和阈值
    benchmark_value = Column(Float)
    warning_threshold = Column(Float)
    critical_threshold = Column(Float)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<RiskMetric(id={self.id}, type='{self.metric_type}', value={self.metric_value})>"


class RiskMetrics(Base):
    """风险指标模型"""
    __tablename__ = "risk_metrics_daily"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey('strategies.id'), nullable=True, index=True)
    
    # 时间维度
    date = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(20), default='daily')  # daily, weekly, monthly
    
    # 基础指标
    portfolio_value = Column(DECIMAL(18, 8), nullable=False)
    cash_balance = Column(DECIMAL(18, 8), nullable=False)
    total_exposure = Column(DECIMAL(18, 8), nullable=False)
    net_exposure = Column(DECIMAL(18, 8), nullable=False)
    
    # 收益指标
    daily_return = Column(DECIMAL(10, 6), nullable=True)
    cumulative_return = Column(DECIMAL(10, 6), nullable=True)
    
    # 风险指标
    volatility = Column(DECIMAL(10, 6), nullable=True)
    max_drawdown = Column(DECIMAL(10, 6), nullable=True)
    current_drawdown = Column(DECIMAL(10, 6), nullable=True)
    var_95 = Column(DECIMAL(18, 8), nullable=True)  # 95% VaR
    var_99 = Column(DECIMAL(18, 8), nullable=True)  # 99% VaR
    cvar_95 = Column(DECIMAL(18, 8), nullable=True)  # 95% CVaR
    
    # 杠杆和集中度
    leverage_ratio = Column(DECIMAL(10, 6), nullable=True)
    concentration_ratio = Column(DECIMAL(10, 6), nullable=True)  # 最大持仓占比
    
    # 流动性指标
    liquidity_ratio = Column(DECIMAL(10, 6), nullable=True)
    
    # 其他指标
    sharpe_ratio = Column(DECIMAL(10, 6), nullable=True)
    sortino_ratio = Column(DECIMAL(10, 6), nullable=True)
    calmar_ratio = Column(DECIMAL(10, 6), nullable=True)
    
    # 元数据
    metrics_model_metadata = Column(JSON, default=dict)
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User")
    strategy = relationship("Strategy")
    
    def __repr__(self):
        return f"<RiskMetrics(id={self.id}, user_id={self.user_id}, date='{self.date}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'strategy_id': self.strategy_id,
            'date': self.date.isoformat() if self.date else None,
            'period_type': self.period_type,
            'portfolio_value': float(self.portfolio_value) if self.portfolio_value else None,
            'cash_balance': float(self.cash_balance) if self.cash_balance else None,
            'total_exposure': float(self.total_exposure) if self.total_exposure else None,
            'net_exposure': float(self.net_exposure) if self.net_exposure else None,
            'daily_return': float(self.daily_return) if self.daily_return else None,
            'cumulative_return': float(self.cumulative_return) if self.cumulative_return else None,
            'volatility': float(self.volatility) if self.volatility else None,
            'max_drawdown': float(self.max_drawdown) if self.max_drawdown else None,
            'current_drawdown': float(self.current_drawdown) if self.current_drawdown else None,
            'var_95': float(self.var_95) if self.var_95 else None,
            'var_99': float(self.var_99) if self.var_99 else None,
            'cvar_95': float(self.cvar_95) if self.cvar_95 else None,
            'leverage_ratio': float(self.leverage_ratio) if self.leverage_ratio else None,
            'concentration_ratio': float(self.concentration_ratio) if self.concentration_ratio else None,
            'liquidity_ratio': float(self.liquidity_ratio) if self.liquidity_ratio else None,
            'sharpe_ratio': float(self.sharpe_ratio) if self.sharpe_ratio else None,
            'sortino_ratio': float(self.sortino_ratio) if self.sortino_ratio else None,
            'calmar_ratio': float(self.calmar_ratio) if self.calmar_ratio else None,
            'metadata': self.metrics_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class RiskLimit(Base):
    """风险限额模型"""
    __tablename__ = "risk_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey('strategies.id'), nullable=True, index=True)
    
    # 限额类型和名称
    limit_type = Column(String(50), nullable=False, index=True)
    limit_name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 限额值
    limit_value = Column(DECIMAL(18, 8), nullable=False)
    current_value = Column(DECIMAL(18, 8), default=0)
    utilization_ratio = Column(DECIMAL(10, 6), default=0)  # 使用率
    
    # 限额配置
    is_hard_limit = Column(Boolean, default=True)  # 硬限制还是软限制
    warning_threshold = Column(DECIMAL(10, 6), default=0.8)  # 预警阈值
    
    # 时间配置
    reset_frequency = Column(String(20), default='daily')  # daily, weekly, monthly, never
    last_reset_at = Column(DateTime, nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_breached = Column(Boolean, default=False)
    breach_count = Column(Integer, default=0)
    last_breach_at = Column(DateTime, nullable=True)
    
    # 元数据
    limit_model_metadata = Column(JSON, default=dict)
    
    # 审计字段
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    strategy = relationship("Strategy")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<RiskLimit(id={self.id}, type='{self.limit_type}', value={self.limit_value})>"
    
    def check_breach(self, current_value: float) -> bool:
        """检查是否违反限额"""
        self.current_value = current_value
        self.utilization_ratio = current_value / float(self.limit_value) if self.limit_value > 0 else 0
        
        if current_value > float(self.limit_value):
            if not self.is_breached:
                self.is_breached = True
                self.breach_count += 1
                self.last_breach_at = datetime.now()
            return True
        else:
            self.is_breached = False
            return False
    
    def is_warning_level(self) -> bool:
        """检查是否达到预警水平"""
        return self.utilization_ratio >= self.warning_threshold
    
    def reset_if_needed(self):
        """根据重置频率重置限额"""
        if self.reset_frequency == 'never':
            return
        
        now = datetime.now()
        should_reset = False
        
        if not self.last_reset_at:
            should_reset = True
        elif self.reset_frequency == 'daily':
            should_reset = now.date() > self.last_reset_at.date()
        elif self.reset_frequency == 'weekly':
            should_reset = (now - self.last_reset_at).days >= 7
        elif self.reset_frequency == 'monthly':
            should_reset = now.month != self.last_reset_at.month or now.year != self.last_reset_at.year
        
        if should_reset:
            self.current_value = 0
            self.utilization_ratio = 0
            self.is_breached = False
            self.last_reset_at = now
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'strategy_id': self.strategy_id,
            'limit_type': self.limit_type,
            'limit_name': self.limit_name,
            'description': self.description,
            'limit_value': float(self.limit_value) if self.limit_value else None,
            'current_value': float(self.current_value) if self.current_value else None,
            'utilization_ratio': float(self.utilization_ratio) if self.utilization_ratio else None,
            'is_hard_limit': self.is_hard_limit,
            'warning_threshold': float(self.warning_threshold) if self.warning_threshold else None,
            'reset_frequency': self.reset_frequency,
            'last_reset_at': self.last_reset_at.isoformat() if self.last_reset_at else None,
            'is_active': self.is_active,
            'is_breached': self.is_breached,
            'breach_count': self.breach_count,
            'last_breach_at': self.last_breach_at.isoformat() if self.last_breach_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }