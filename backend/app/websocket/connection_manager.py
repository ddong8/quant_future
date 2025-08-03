"""
WebSocket连接管理器
负责管理WebSocket连接、订阅和消息分发
"""

import json
import asyncio
import logging
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 活跃连接：{connection_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # 用户连接映射：{user_id: set(connection_ids)}
        self.user_connections: Dict[int, Set[str]] = {}
        
        # 订阅管理：{topic: set(connection_ids)}
        self.subscriptions: Dict[str, Set[str]] = {}
        
        # 连接信息：{connection_id: connection_info}
        self.connection_info: Dict[str, Dict[str, Any]] = {}
        
        # 心跳管理
        self.heartbeat_interval = 30  # 30秒心跳间隔
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket, user_id: Optional[int] = None) -> str:
        """建立WebSocket连接"""
        await websocket.accept()
        
        # 生成连接ID
        connection_id = str(uuid.uuid4())
        
        # 存储连接
        self.active_connections[connection_id] = websocket
        
        # 存储连接信息
        self.connection_info[connection_id] = {
            'user_id': user_id,
            'connected_at': datetime.now(),
            'last_heartbeat': datetime.now(),
            'subscriptions': set()
        }
        
        # 用户连接映射
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        # 启动心跳任务
        self.heartbeat_tasks[connection_id] = asyncio.create_task(
            self._heartbeat_task(connection_id)
        )
        
        logger.info(f"WebSocket连接建立: {connection_id}, 用户: {user_id}")
        
        # 发送连接确认消息
        await self.send_personal_message(connection_id, {
            'type': 'connection_established',
            'connection_id': connection_id,
            'timestamp': datetime.now().isoformat()
        })
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """断开WebSocket连接"""
        if connection_id not in self.active_connections:
            return
        
        # 获取连接信息
        conn_info = self.connection_info.get(connection_id, {})
        user_id = conn_info.get('user_id')
        subscriptions = conn_info.get('subscriptions', set())
        
        # 取消所有订阅
        for topic in subscriptions:
            await self._unsubscribe_internal(connection_id, topic)
        
        # 移除用户连接映射
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # 取消心跳任务
        if connection_id in self.heartbeat_tasks:
            self.heartbeat_tasks[connection_id].cancel()
            del self.heartbeat_tasks[connection_id]
        
        # 移除连接
        del self.active_connections[connection_id]
        del self.connection_info[connection_id]
        
        logger.info(f"WebSocket连接断开: {connection_id}, 用户: {user_id}")
    
    async def send_personal_message(self, connection_id: str, message: Dict[str, Any]):
        """发送个人消息"""
        if connection_id not in self.active_connections:
            return False
        
        try:
            websocket = self.active_connections[connection_id]
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
            return True
        except Exception as e:
            logger.error(f"发送个人消息失败: {connection_id}, 错误: {e}")
            await self.disconnect(connection_id)
            return False
    
    async def send_user_message(self, user_id: int, message: Dict[str, Any]):
        """发送用户消息（所有连接）"""
        if user_id not in self.user_connections:
            return 0
        
        sent_count = 0
        connection_ids = list(self.user_connections[user_id])
        
        for connection_id in connection_ids:
            if await self.send_personal_message(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """广播消息给所有连接"""
        sent_count = 0
        connection_ids = list(self.active_connections.keys())
        
        for connection_id in connection_ids:
            if await self.send_personal_message(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    async def send_topic_message(self, topic: str, message: Dict[str, Any]):
        """发送主题消息给订阅者"""
        if topic not in self.subscriptions:
            return 0
        
        sent_count = 0
        connection_ids = list(self.subscriptions[topic])
        
        # 添加主题信息到消息
        message['topic'] = topic
        
        for connection_id in connection_ids:
            if await self.send_personal_message(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    async def subscribe(self, connection_id: str, topic: str) -> bool:
        """订阅主题"""
        if connection_id not in self.active_connections:
            return False
        
        # 添加到订阅列表
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        self.subscriptions[topic].add(connection_id)
        
        # 更新连接信息
        if connection_id in self.connection_info:
            self.connection_info[connection_id]['subscriptions'].add(topic)
        
        logger.info(f"连接 {connection_id} 订阅主题: {topic}")
        
        # 发送订阅确认
        await self.send_personal_message(connection_id, {
            'type': 'subscription_confirmed',
            'topic': topic,
            'timestamp': datetime.now().isoformat()
        })
        
        return True
    
    async def unsubscribe(self, connection_id: str, topic: str) -> bool:
        """取消订阅主题"""
        if connection_id not in self.active_connections:
            return False
        
        await self._unsubscribe_internal(connection_id, topic)
        
        # 发送取消订阅确认
        await self.send_personal_message(connection_id, {
            'type': 'unsubscription_confirmed',
            'topic': topic,
            'timestamp': datetime.now().isoformat()
        })
        
        return True
    
    async def _unsubscribe_internal(self, connection_id: str, topic: str):
        """内部取消订阅方法"""
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(connection_id)
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]
        
        # 更新连接信息
        if connection_id in self.connection_info:
            self.connection_info[connection_id]['subscriptions'].discard(topic)
        
        logger.info(f"连接 {connection_id} 取消订阅主题: {topic}")
    
    async def handle_message(self, connection_id: str, message: str):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # 心跳响应
                await self.send_personal_message(connection_id, {
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                })
                
                # 更新心跳时间
                if connection_id in self.connection_info:
                    self.connection_info[connection_id]['last_heartbeat'] = datetime.now()
            
            elif message_type == 'subscribe':
                # 订阅主题
                topic = data.get('topic')
                if topic:
                    await self.subscribe(connection_id, topic)
            
            elif message_type == 'unsubscribe':
                # 取消订阅
                topic = data.get('topic')
                if topic:
                    await self.unsubscribe(connection_id, topic)
            
            elif message_type == 'get_subscriptions':
                # 获取订阅列表
                subscriptions = list(self.connection_info.get(connection_id, {}).get('subscriptions', set()))
                await self.send_personal_message(connection_id, {
                    'type': 'subscriptions_list',
                    'subscriptions': subscriptions,
                    'timestamp': datetime.now().isoformat()
                })
            
            else:
                logger.warning(f"未知消息类型: {message_type}")
        
        except json.JSONDecodeError:
            logger.error(f"无效的JSON消息: {message}")
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
    
    async def _heartbeat_task(self, connection_id: str):
        """心跳任务"""
        try:
            while connection_id in self.active_connections:
                await asyncio.sleep(self.heartbeat_interval)
                
                # 检查连接是否还活跃
                if connection_id not in self.connection_info:
                    break
                
                last_heartbeat = self.connection_info[connection_id]['last_heartbeat']
                now = datetime.now()
                
                # 如果超过2个心跳间隔没有收到心跳，断开连接
                if (now - last_heartbeat).total_seconds() > self.heartbeat_interval * 2:
                    logger.warning(f"连接 {connection_id} 心跳超时，断开连接")
                    await self.disconnect(connection_id)
                    break
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"心跳任务出错: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        return {
            'total_connections': len(self.active_connections),
            'total_users': len(self.user_connections),
            'total_subscriptions': sum(len(subs) for subs in self.subscriptions.values()),
            'topics': list(self.subscriptions.keys()),
            'connections_per_user': {
                user_id: len(connections) 
                for user_id, connections in self.user_connections.items()
            }
        }
    
    def get_topic_stats(self) -> Dict[str, int]:
        """获取主题统计信息"""
        return {
            topic: len(connections) 
            for topic, connections in self.subscriptions.items()
        }


# 全局连接管理器实例
connection_manager = ConnectionManager()