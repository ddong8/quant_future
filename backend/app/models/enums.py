"""
数据模型枚举类型定义
"""
from enum import Enum


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    TRADER = "trader"
    VIEWER = "viewer"


class StrategyStatus(str, Enum):
    """策略状态枚举"""
    DRAFT = "draft"
    TESTING = "testing"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"


class OrderDirection(str, Enum):
    """订单方向枚举"""
    BUY = "buy"
    SELL = "sell"


class OrderOffset(str, Enum):
    """订单开平仓枚举"""
    OPEN = "open"
    CLOSE = "close"
    CLOSE_TODAY = "close_today"
    CLOSE_YESTERDAY = "close_yesterday"


class OrderStatus(str, Enum):
    """订单状态枚举"""
    PENDING = "pending"
    PARTIAL_FILLED = "partial_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class PositionDirection(str, Enum):
    """持仓方向枚举"""
    LONG = "long"
    SHORT = "short"


class BacktestStatus(str, Enum):
    """回测状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskEventType(str, Enum):
    """风险事件类型枚举"""
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    POSITION_LIMIT = "position_limit"
    ORDER_FREQUENCY_LIMIT = "order_frequency_limit"
    ABNORMAL_TRADING = "abnormal_trading"
    SYSTEM_ERROR = "system_error"


class NotificationType(str, Enum):
    """通知类型枚举"""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    IN_APP = "in_app"