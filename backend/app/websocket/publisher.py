"""
WebSocket消息发布器
负责向WebSocket客户端推送各种类型的消息
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from .connection_manager import connection_manager

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """消息类型枚举"""
    # 市场数据
    MARKET_DATA = "market_data"
    PRICE_UPDATE = "price_update"
    DEPTH_UPDATE = "depth_update"
    
    # 订单相关
    ORDER_UPDATE = "order_update"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    
    # 持仓相关
    POSITION_UPDATE = "position_update"
    PNL_UPDATE = "pnl_update"
    
    # 账户相关
    ACCOUNT_UPDATE = "account_update"
    BALANCE_UPDATE = "balance_update"
    
    # 策略相关
    STRATEGY_UPDATE = "strategy_update"
    BACKTEST_UPDATE = "backtest_update"
    
    # 风险控制
    RISK_ALERT = "risk_alert"
    RISK_WARNING = "risk_warning"
    
    # 系统通知
    SYSTEM_NOTIFICATION = "system_notification"
    USER_NOTIFICATION = "user_notification"
    
    # 错误和异常
    ERROR = "error"
    WARNING = "warning"


class WebSocketPublisher:
    """WebSocket消息发布器"""
    
    def __init__(self):
        self.manager = connection_manager
    
    async def publish_market_data(self, symbol: str, data: Dict[str, Any]):
        """发布市场数据"""
        message = {
            'type': MessageType.MARKET_DATA,
            'symbol': symbol,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        # 发送到市场数据主题
        topic = f"market_data.{symbol}"
        await self.manager.send_topic_message(topic, message)
        
        # 发送到通用市场数据主题
        await self.manager.send_topic_message("market_data", message)
    
    async def publish_price_update(self, symbol: str, price: float, change: float = None):
        """发布价格更新"""
        message = {
            'type': MessageType.PRICE_UPDATE,
            'symbol': symbol,
            'price': price,
            'change': change,
            'timestamp': datetime.now().isoformat()
        }
        
        topic = f"price.{symbol}"
        await self.manager.send_topic_message(topic, message)
    
    async def publish_depth_update(self, symbol: str, bids: List[List[float]], asks: List[List[float]]):
        """发布深度数据更新"""
        message = {
            'type': MessageType.DEPTH_UPDATE,
            'symbol': symbol,
            'bids': bids,
            'asks': asks,
            'timestamp': datetime.now().isoformat()
        }
        
        topic = f"depth.{symbol}"
        await self.manager.send_topic_message(topic, message)
    
    async def publish_order_update(self, user_id: int, order_data: Dict[str, Any]):
        """发布订单更新"""
        message = {
            'type': MessageType.ORDER_UPDATE,
            'data': order_data,
            'timestamp': datetime.now().isoformat()
        }
        
        # 发送给特定用户
        await self.manager.send_user_message(user_id, message)
        
        # 发送到用户订单主题
        topic = f"orders.{user_id}"
        await self.manager.send_topic_message(topic, message)
    
    async def publish_order_filled(self, user_id: int, order_id: str, fill_data: Dict[str, Any]):
        """发布订单成交"""
        message = {
            'type': MessageType.ORDER_FILLED,
            'order_id': order_id,
            'data': fill_data,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.manager.send_user_message(user_id, message)
    
    async def publish_position_update(self, user_id: int, position_data: Dict[str, Any]):
        """发布持仓更新"""
        message = {
            'type': MessageType.POSITION_UPDATE,
            'data': position_data,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.manager.send_user_message(user_id, message)
        
        # 发送到用户持仓主题
        topic = f"positions.{user_id}"
        await self.manager.send_topic_message(topic, message)
    
    async def publish_pnl_update(self, user_id: int, pnl_data: Dict[str, Any]):
        """发布盈亏更新"""
        message = {
            'type': MessageType.PNL_UPDATE,
            'data': pnl_data,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.manager.send_user_message(user_id, message)
    
    async def publish_account_update(self, user_id: int, account_data: Dict[str, Any]):
        """发布账户更新"""
        message = {
            'type': MessageType.ACCOUNT_UPDATE,
            'data': account_data,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.manager.send_user_message(user_id, message)
    
    async def publish_balance_update(self, user_id: int, balance_data: Dict[str, Any]):
        """发布余额更新"""
        message = {
            'type': MessageType.BALANCE_UPDATE,
            'data': balance_data,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.manager.send_user_message(user_id, message)
    
    async def publish_strategy_update(self, user_id: int, strategy_data: Dict[str, Any]):
        """发布策略更新"""
        message = {
            'type': MessageType.STRATEGY_UPDATE,
            'data': strategy_data,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.manager.send_user_message(user_id, message)
        
        # 发送到用户策略主题
        topic = f"strategies.{user_id}"
        await self.manager.send_topic_message(topic, message)
    
    async def publish_backtest_update(self, user_id: int, backtest_data: Dict[str, Any]):
        """发布回测更新"""
        message = {
            'type': MessageType.BACKTEST_UPDATE,
            'data': backtest_data,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.manager.send_user_message(user_id, message)
        
        # 发送到用户回测主题
        topic = f"backtests.{user_id}"
        await self.manager.send_topic_message(topic, message)
    
    async def publish_risk_alert(self, user_id: int, alert_data: Dict[str, Any]):
        """发布风险警报"""
        message = {
            'type': MessageType.RISK_ALERT,
            'data': alert_data,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.manager.send_user_message(user_id, message)
        
        # 发送到风险主题
        topic = f"risk.{user_id}"
        await self.manager.send_topic_message(topic, message)
    
    async def publish_risk_warning(self, user_id: int, warning_data: Dict[str, Any]):
        """发布风险警告"""
        message = {
            'type': MessageType.RISK_WARNING,
            'data': warning_data,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.manager.send_user_message(user_id, message)
    
    async def publish_system_notification(self, notification_data: Dict[str, Any], target_users: Optional[List[int]] = None):
        """发布系统通知"""
        message = {
            'type': MessageType.SYSTEM_NOTIFICATION,
            'data': notification_data,
            'timestamp': datetime.now().isoformat()
        }
        
        if target_users:
            # 发送给指定用户
            for user_id in target_users:
                await self.manager.send_user_message(user_id, message)
        else:
            # 广播给所有用户
            await self.manager.broadcast_message(message)
    
    async def publish_user_notification(self, user_id: int, notification_data: Dict[str, Any]):
        """发布用户通知"""
        message = {
            'type': MessageType.USER_NOTIFICATION,
            'data': notification_data,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.manager.send_user_message(user_id, message)
        
        # 发送到用户通知主题
        topic = f"notifications.{user_id}"
        await self.manager.send_topic_message(topic, message)
    
    async def publish_error(self, user_id: int, error_data: Dict[str, Any]):
        """发布错误消息"""
        message = {
            'type': MessageType.ERROR,
            'data': error_data,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.manager.send_user_message(user_id, message)
    
    async def publish_warning(self, user_id: int, warning_data: Dict[str, Any]):
        """发布警告消息"""
        message = {
            'type': MessageType.WARNING,
            'data': warning_data,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.manager.send_user_message(user_id, message)
    
    async def publish_custom_message(self, topic: str, message_data: Dict[str, Any]):
        """发布自定义消息到指定主题"""
        message = {
            'data': message_data,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.manager.send_topic_message(topic, message)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取发布器统计信息"""
        return self.manager.get_connection_stats()


# 全局发布器实例
publisher = WebSocketPublisher()


# 便捷函数
async def publish_to_user(user_id: int, message_type: str, data: Dict[str, Any]):
    """向用户发布消息的便捷函数"""
    message = {
        'type': message_type,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }
    await connection_manager.send_user_message(user_id, message)


async def publish_to_topic(topic: str, message_type: str, data: Dict[str, Any]):
    """向主题发布消息的便捷函数"""
    message = {
        'type': message_type,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }
    await connection_manager.send_topic_message(topic, message)


async def broadcast_message(message_type: str, data: Dict[str, Any]):
    """广播消息的便捷函数"""
    message = {
        'type': message_type,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }
    await connection_manager.broadcast_message(message)