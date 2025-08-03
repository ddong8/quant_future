"""
WebSocket连接管理器
"""

import logging
import json
from typing import Dict, List, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储活跃连接 {user_id: [websocket1, websocket2, ...]}
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # 存储连接信息 {websocket: {'user_id': int, 'connected_at': datetime}}
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """接受WebSocket连接"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        self.connection_info[websocket] = {
            'user_id': user_id,
            'connected_at': datetime.now()
        }
        
        logger.info(f"用户 {user_id} 建立WebSocket连接")
    
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.connection_info:
            user_id = self.connection_info[websocket]['user_id']
            
            # 从用户连接列表中移除
            if user_id in self.active_connections:
                if websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)
                
                # 如果用户没有其他连接，移除用户记录
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # 移除连接信息
            del self.connection_info[websocket]
            
            logger.info(f"用户 {user_id} 断开WebSocket连接")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"发送个人消息失败: {str(e)}")
            self.disconnect(websocket)
    
    async def send_to_user(self, user_id: int, message: Dict[str, Any]):
        """发送消息给指定用户的所有连接"""
        if user_id not in self.active_connections:
            return
        
        message_str = json.dumps(message, ensure_ascii=False)
        disconnected_connections = []
        
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.error(f"发送用户消息失败: {str(e)}")
                disconnected_connections.append(websocket)
        
        # 清理断开的连接
        for websocket in disconnected_connections:
            self.disconnect(websocket)
    
    def send_to_user_sync(self, user_id: int, message: Dict[str, Any]):
        """同步方式发送消息给用户（用于非异步环境）"""
        if user_id not in self.active_connections:
            return
        
        # 创建异步任务
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # 如果没有运行的事件循环，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # 如果循环正在运行，创建任务
            asyncio.create_task(self.send_to_user(user_id, message))
        else:
            # 如果循环没有运行，直接运行
            loop.run_until_complete(self.send_to_user(user_id, message))
    
    async def broadcast(self, message: Dict[str, Any]):
        """广播消息给所有连接"""
        message_str = json.dumps(message, ensure_ascii=False)
        disconnected_connections = []
        
        for websocket in self.connection_info.keys():
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.error(f"广播消息失败: {str(e)}")
                disconnected_connections.append(websocket)
        
        # 清理断开的连接
        for websocket in disconnected_connections:
            self.disconnect(websocket)
    
    def get_user_connections(self, user_id: int) -> List[WebSocket]:
        """获取用户的所有连接"""
        return self.active_connections.get(user_id, [])
    
    def get_connection_count(self) -> int:
        """获取总连接数"""
        return len(self.connection_info)
    
    def get_user_count(self) -> int:
        """获取在线用户数"""
        return len(self.active_connections)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        return {
            'total_connections': self.get_connection_count(),
            'online_users': self.get_user_count(),
            'connections_per_user': {
                user_id: len(connections) 
                for user_id, connections in self.active_connections.items()
            },
            'timestamp': datetime.now().isoformat()
        }
    
    async def ping_all_connections(self):
        """向所有连接发送ping消息"""
        ping_message = {
            'type': 'ping',
            'timestamp': datetime.now().isoformat()
        }
        await self.broadcast(ping_message)
    
    async def send_system_notification(self, message: str, level: str = 'info'):
        """发送系统通知"""
        notification = {
            'type': 'system_notification',
            'level': level,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        await self.broadcast(notification)


# 全局WebSocket管理器实例
websocket_manager = ConnectionManager()


class WebSocketHandler:
    """WebSocket消息处理器"""
    
    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self.message_handlers = {
            'ping': self._handle_ping,
            'subscribe': self._handle_subscribe,
            'unsubscribe': self._handle_unsubscribe,
            'get_status': self._handle_get_status
        }
    
    async def handle_message(self, websocket: WebSocket, message: str):
        """处理WebSocket消息"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](websocket, data)
            else:
                await self._handle_unknown_message(websocket, data)
                
        except json.JSONDecodeError:
            await self._send_error(websocket, "Invalid JSON format")
        except Exception as e:
            logger.error(f"处理WebSocket消息失败: {str(e)}")
            await self._send_error(websocket, "Internal server error")
    
    async def _handle_ping(self, websocket: WebSocket, data: Dict[str, Any]):
        """处理ping消息"""
        pong_message = {
            'type': 'pong',
            'timestamp': datetime.now().isoformat()
        }
        await self.manager.send_personal_message(
            json.dumps(pong_message), websocket
        )
    
    async def _handle_subscribe(self, websocket: WebSocket, data: Dict[str, Any]):
        """处理订阅消息"""
        # 这里可以实现特定主题的订阅逻辑
        topic = data.get('topic')
        response = {
            'type': 'subscription_confirmed',
            'topic': topic,
            'timestamp': datetime.now().isoformat()
        }
        await self.manager.send_personal_message(
            json.dumps(response), websocket
        )
    
    async def _handle_unsubscribe(self, websocket: WebSocket, data: Dict[str, Any]):
        """处理取消订阅消息"""
        topic = data.get('topic')
        response = {
            'type': 'unsubscription_confirmed',
            'topic': topic,
            'timestamp': datetime.now().isoformat()
        }
        await self.manager.send_personal_message(
            json.dumps(response), websocket
        )
    
    async def _handle_get_status(self, websocket: WebSocket, data: Dict[str, Any]):
        """处理获取状态消息"""
        stats = self.manager.get_connection_stats()
        response = {
            'type': 'status_response',
            'data': stats
        }
        await self.manager.send_personal_message(
            json.dumps(response), websocket
        )
    
    async def _handle_unknown_message(self, websocket: WebSocket, data: Dict[str, Any]):
        """处理未知消息类型"""
        await self._send_error(websocket, f"Unknown message type: {data.get('type')}")
    
    async def _send_error(self, websocket: WebSocket, error_message: str):
        """发送错误消息"""
        error_response = {
            'type': 'error',
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        }
        await self.manager.send_personal_message(
            json.dumps(error_response), websocket
        )


# 全局WebSocket处理器实例
websocket_handler = WebSocketHandler(websocket_manager)