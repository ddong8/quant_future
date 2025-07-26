"""
风险管理相关数据模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..core.database import Base
from .enums import RiskEventType


class RiskRule(Base):
    """风险规则模型"""
    __tablename__ = "risk_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 规则类型和配置
    rule_type = Column(String(50), nullable=False)  # daily_loss/position_limit/order_frequency等
    parameters = Column(JSON, nullable=False)  # 规则参数配置
    
    # 适用范围
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # 为空表示全局规则
    strategy_id = Column(Integer, ForeignKey("strategies.id"), index=True)  # 为空表示用户级规则
    
    # 规则状态
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0)  # 优先级，数字越大优先级越高
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<RiskRule(id={self.id}, name='{self.name}', type='{self.rule_type}')>"


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