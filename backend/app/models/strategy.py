"""
策略相关数据模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid

from ..core.database import Base


class StrategyStatus(str, PyEnum):
    """策略状态枚举"""
    DRAFT = "draft"          # 草稿
    ACTIVE = "active"        # 活跃
    INACTIVE = "inactive"    # 已停用
    TESTING = "testing"      # 测试中
    ERROR = "error"          # 错误状态


class StrategyType(str, PyEnum):
    """策略类型枚举"""
    TREND_FOLLOWING = "trend_following"      # 趋势跟踪
    MEAN_REVERSION = "mean_reversion"        # 均值回归
    ARBITRAGE = "arbitrage"                  # 套利
    MARKET_MAKING = "market_making"          # 做市
    MOMENTUM = "momentum"                    # 动量
    STATISTICAL = "statistical"             # 统计套利
    CUSTOM = "custom"                        # 自定义


class Strategy(Base):
    """策略模型"""
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # 基本信息
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    strategy_type = Column(Enum(StrategyType), default=StrategyType.CUSTOM)
    status = Column(Enum(StrategyStatus), default=StrategyStatus.DRAFT, index=True)
    
    # 代码相关
    code = Column(Text, nullable=False)
    entry_point = Column(String(100), default="main")  # 入口函数名
    language = Column(String(20), default="python")
    
    # 配置参数
    parameters = Column(JSON, default=dict)  # 策略参数配置
    symbols = Column(JSON, default=list)     # 交易标的
    timeframe = Column(String(20))           # 时间周期
    
    # 风险控制
    max_position_size = Column(Float)        # 最大持仓规模
    max_drawdown = Column(Float)             # 最大回撤限制
    stop_loss = Column(Float)                # 止损比例
    take_profit = Column(Float)              # 止盈比例
    
    # 统计信息
    total_returns = Column(Float, default=0.0)      # 总收益率
    sharpe_ratio = Column(Float)                     # 夏普比率
    max_drawdown_pct = Column(Float)                 # 历史最大回撤
    win_rate = Column(Float)                         # 胜率
    total_trades = Column(Integer, default=0)        # 总交易次数
    
    # 运行状态
    is_running = Column(Boolean, default=False)      # 是否正在运行
    last_run_at = Column(DateTime)                   # 最后运行时间
    last_error = Column(Text)                        # 最后错误信息
    
    # 版本控制
    version = Column(Integer, default=1)             # 当前版本号
    
    # 元数据
    tags = Column(JSON, default=list)                # 标签
    is_public = Column(Boolean, default=False)       # 是否公开
    is_template = Column(Boolean, default=False)     # 是否为模板
    
    # 关联关系
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="strategies")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 版本历史
    versions = relationship("StrategyVersion", back_populates="strategy", cascade="all, delete-orphan")
    
    # 回测记录
    backtests = relationship("Backtest", back_populates="strategy", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Strategy(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'description': self.description,
            'strategy_type': self.strategy_type,
            'status': self.status,
            'code': self.code,
            'entry_point': self.entry_point,
            'language': self.language,
            'parameters': self.parameters,
            'symbols': self.symbols,
            'timeframe': self.timeframe,
            'max_position_size': self.max_position_size,
            'max_drawdown': self.max_drawdown,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'total_returns': self.total_returns,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown_pct': self.max_drawdown_pct,
            'win_rate': self.win_rate,
            'total_trades': self.total_trades,
            'is_running': self.is_running,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'last_error': self.last_error,
            'version': self.version,
            'tags': self.tags,
            'is_public': self.is_public,
            'is_template': self.is_template,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class StrategyVersion(Base):
    """策略版本模型"""
    __tablename__ = "strategy_versions"

    id = Column(Integer, primary_key=True, index=True)
    
    # 版本信息
    version_number = Column(Integer, nullable=False)
    version_name = Column(String(100))
    description = Column(Text)
    
    # 代码快照
    code = Column(Text, nullable=False)
    entry_point = Column(String(100), default="main")
    parameters = Column(JSON, default=dict)
    
    # 变更信息
    change_log = Column(Text)
    is_major_version = Column(Boolean, default=False)
    
    # 性能数据（该版本的回测结果）
    performance_data = Column(JSON, default=dict)
    
    # 关联关系
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    strategy = relationship("Strategy", back_populates="versions")
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<StrategyVersion(id={self.id}, strategy_id={self.strategy_id}, version={self.version_number})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'version_number': self.version_number,
            'version_name': self.version_name,
            'description': self.description,
            'code': self.code,
            'entry_point': self.entry_point,
            'parameters': self.parameters,
            'change_log': self.change_log,
            'is_major_version': self.is_major_version,
            'performance_data': self.performance_data,
            'strategy_id': self.strategy_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class StrategyTemplate(Base):
    """策略模板模型"""
    __tablename__ = "strategy_templates"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # 基本信息
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    strategy_type = Column(Enum(StrategyType), default=StrategyType.CUSTOM)
    category = Column(String(50))  # 模板分类
    
    # 模板代码
    code_template = Column(Text, nullable=False)
    default_parameters = Column(JSON, default=dict)
    
    # 使用统计
    usage_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    
    # 元数据
    tags = Column(JSON, default=list)
    is_official = Column(Boolean, default=False)  # 是否为官方模板
    is_active = Column(Boolean, default=True)
    
    # 创建者
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<StrategyTemplate(id={self.id}, name='{self.name}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'description': self.description,
            'strategy_type': self.strategy_type,
            'category': self.category,
            'code_template': self.code_template,
            'default_parameters': self.default_parameters,
            'usage_count': self.usage_count,
            'rating': self.rating,
            'tags': self.tags,
            'is_official': self.is_official,
            'is_active': self.is_active,
            'author_id': self.author_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }