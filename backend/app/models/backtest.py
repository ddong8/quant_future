"""
回测相关数据模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..core.database import Base
from .enums import BacktestStatus


class Backtest(Base):
    """回测模型"""
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 关联策略和用户
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 回测配置
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    initial_capital = Column(Float, nullable=False)
    symbols = Column(JSON)  # 回测合约列表
    parameters = Column(JSON)  # 策略参数
    
    # 回测状态
    status = Column(String(20), default=BacktestStatus.PENDING, nullable=False)
    progress = Column(Float, default=0.0)  # 回测进度 0-100
    
    # 回测结果 - 基础指标
    final_capital = Column(Float, default=0.0)
    total_return = Column(Float, default=0.0)  # 总收益率
    annual_return = Column(Float, default=0.0)  # 年化收益率
    max_drawdown = Column(Float, default=0.0)  # 最大回撤
    sharpe_ratio = Column(Float, default=0.0)  # 夏普比率
    sortino_ratio = Column(Float, default=0.0)  # 索提诺比率
    
    # 交易统计
    total_trades = Column(Integer, default=0)  # 总交易次数
    winning_trades = Column(Integer, default=0)  # 盈利交易次数
    losing_trades = Column(Integer, default=0)  # 亏损交易次数
    win_rate = Column(Float, default=0.0)  # 胜率
    avg_win = Column(Float, default=0.0)  # 平均盈利
    avg_loss = Column(Float, default=0.0)  # 平均亏损
    profit_factor = Column(Float, default=0.0)  # 盈亏比
    
    # 详细结果数据
    equity_curve = Column(JSON)  # 资金曲线数据
    trade_records = Column(JSON)  # 交易记录
    daily_returns = Column(JSON)  # 日收益率
    
    # 错误信息
    error_message = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # 关系
    strategy = relationship("Strategy", back_populates="backtests")
    user = relationship("User", back_populates="backtests")
    reports = relationship("BacktestReport", foreign_keys="BacktestReport.backtest_id", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Backtest(id={self.id}, name='{self.name}', status='{self.status}')>"


class BacktestTemplate(Base):
    """回测模板模型"""
    __tablename__ = "backtest_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 模板配置
    config = Column(JSON, nullable=False)  # 模板配置JSON
    parameters = Column(JSON)  # 默认参数
    
    # 模板属性
    is_public = Column(Boolean, default=False)  # 是否公开
    is_system = Column(Boolean, default=False)  # 是否系统模板
    
    # 创建者
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<BacktestTemplate(id={self.id}, name='{self.name}')>"


class BacktestComparison(Base):
    """回测对比模型"""
    __tablename__ = "backtest_comparisons"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 对比的回测ID列表
    backtest_ids = Column(JSON, nullable=False)  # 回测ID列表
    
    # 对比结果
    comparison_data = Column(JSON)  # 对比数据JSON
    
    # 创建者
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<BacktestComparison(id={self.id}, name='{self.name}')>"


class BacktestReport(Base):
    """回测报告模型"""
    __tablename__ = "backtest_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id"), nullable=False, index=True)
    
    # 报告内容
    report_type = Column(String(50), nullable=False)  # summary/detailed/comparison
    content = Column(JSON, nullable=False)  # 报告内容JSON
    
    # 报告文件
    file_path = Column(String(255))  # 报告文件路径
    file_format = Column(String(20))  # pdf/html/excel
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    backtest = relationship("Backtest", foreign_keys=[backtest_id])
    
    def __repr__(self):
        return f"<BacktestReport(id={self.id}, backtest_id={self.backtest_id}, type='{self.report_type}')>"