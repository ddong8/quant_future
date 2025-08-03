"""
WebSocket性能优化服务
"""
import asyncio
import json
import time
import logging
from typing import Dict, List, Set, Any, Optional, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import weakref
import gzip
import zlib

logger = logging.getLogger(__name__)

@dataclass
class ConnectionMetrics:
    """连接指标"""
    connection_id: str
    connected_at: datetime
    last_activity: datetime
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    errors: int = 0
    latency_samples: List[float] = None
    
    def __post_init__(self):
        if self.latency_samples is None:
            self.latency_samples = deque(maxlen=100)
    
    @property
    def avg_latency(self) -> float:
        """平均延迟"""
        if not self.latency_samples:
            return 0.0
        return sum(self.latency_samples) / len(self.latency_samples)
    
    @property
    def connection_duration(self) -> timedelta:
        """连接持续时间"""
        return datetime.now() - self.connected_at

@dataclass
class MessageBatch:
    """消息批次"""
    messages: List[Dict[str, Any]]
    created_at: datetime
    target_connections: Set[str]
    
    def add_message(self, message: Dict[str, Any]):
        """添加消息到批次"""
        self.messages.append(message)
    
    def is_ready_to_send(self, batch_size: int = 10, max_wait_time: float = 0.1) -> bool:
        """检查是否准备发送"""
        return (
            len(self.messages) >= batch_size or
            (datetime.now() - self.created_at).total_seconds() >= max_wait_time
        )

class WebSocketOptimizationService:
    """WebSocket性能优化服务"""
    
    def __init__(self):
        self.connections: Dict[str, Any] = {}  # connection_id -> websocket
        self.connection_metrics: Dict[str, ConnectionMetrics] = {}
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)  # topic -> connection_ids
        self.message_batches: Dict[str, MessageBatch] = {}  # topic -> batch
        self.rate_limiters: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.compression_enabled = True
        self.batch_enabled = True
        self.heartbeat_interval = 30  # 秒
        self.max_connections_per_user = 5
        self.user_connections: Dict[int, Set[str]] = defaultdict(set)
        
        # 性能配置
        self.config = {
            "max_message_size": 1024 * 1024,  # 1MB
            "batch_size": 10,
            "batch_timeout": 0.1,  # 100ms
            "rate_limit_per_second": 100,
            "compression_threshold": 1024,  # 1KB
            "heartbeat_timeout": 60,
            "cleanup_interval": 300,  # 5分钟
        }
        
        # 启动后台任务
        asyncio.create_task(self._background_tasks())
    
    async def register_connection(
        self, 
        connection_id: str, 
        websocket: Any, 
        user_id: Optional[int] = None
    ):
        """注册WebSocket连接"""
        
        # 检查用户连接数限制
        if user_id and len(self.user_connections[user_id]) >= self.max_connections_per_user:
            oldest_connection = min(
                self.user_connections[user_id],
                key=lambda cid: self.connection_metrics[cid].connected_at
            )
            await self.disconnect_connection(oldest_connection, "Connection limit exceeded")
        
        # 注册连接
        self.connections[connection_id] = websocket
        self.connection_metrics[connection_id] = ConnectionMetrics(
            connection_id=connection_id,
            connected_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        if user_id:
            self.user_connections[user_id].add(connection_id)
        
        logger.info(f"WebSocket connection registered: {connection_id}")
    
    async def unregister_connection(self, connection_id: str):
        """注销WebSocket连接"""
        
        if connection_id in self.connections:
            del self.connections[connection_id]
        
        if connection_id in self.connection_metrics:
            del self.connection_metrics[connection_id]
        
        # 从订阅中移除
        for topic, subscribers in self.subscriptions.items():
            subscribers.discard(connection_id)
        
        # 从用户连接中移除
        for user_id, connections in self.user_connections.items():
            connections.discard(connection_id)
        
        logger.info(f"WebSocket connection unregistered: {connection_id}")
    
    async def disconnect_connection(self, connection_id: str, reason: str = ""):
        """断开连接"""
        
        if connection_id in self.connections:
            try:
                websocket = self.connections[connection_id]
                await websocket.close(code=1000, reason=reason)
            except Exception as e:
                logger.error(f"Error closing connection {connection_id}: {e}")
            finally:
                await self.unregister_connection(connection_id)
    
    def subscribe_to_topic(self, connection_id: str, topic: str):
        """订阅主题"""
        
        if connection_id not in self.connections:
            return False
        
        self.subscriptions[topic].add(connection_id)
        logger.debug(f"Connection {connection_id} subscribed to {topic}")
        return True
    
    def unsubscribe_from_topic(self, connection_id: str, topic: str):
        """取消订阅主题"""
        
        self.subscriptions[topic].discard(connection_id)
        logger.debug(f"Connection {connection_id} unsubscribed from {topic}")
    
    async def send_message_to_connection(
        self, 
        connection_id: str, 
        message: Dict[str, Any],
        compress: bool = None
    ):
        """发送消息到指定连接"""
        
        if connection_id not in self.connections:
            return False
        
        try:
            websocket = self.connections[connection_id]
            metrics = self.connection_metrics[connection_id]
            
            # 序列化消息
            message_data = json.dumps(message, ensure_ascii=False)
            message_bytes = message_data.encode('utf-8')
            
            # 压缩处理
            if compress is None:
                compress = (
                    self.compression_enabled and 
                    len(message_bytes) > self.config["compression_threshold"]
                )
            
            if compress:
                message_bytes = gzip.compress(message_bytes)
                message["_compressed"] = True
            
            # 检查消息大小
            if len(message_bytes) > self.config["max_message_size"]:
                logger.warning(f"Message too large: {len(message_bytes)} bytes")
                return False
            
            # 发送消息
            start_time = time.time()
            await websocket.send_bytes(message_bytes)
            
            # 更新指标
            latency = time.time() - start_time
            metrics.messages_sent += 1
            metrics.bytes_sent += len(message_bytes)
            metrics.latency_samples.append(latency)
            metrics.last_activity = datetime.now()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            metrics.errors += 1
            await self.unregister_connection(connection_id)
            return False
    
    async def broadcast_to_topic(
        self, 
        topic: str, 
        message: Dict[str, Any],
        exclude_connections: Set[str] = None
    ):
        """广播消息到主题订阅者"""
        
        if topic not in self.subscriptions:
            return 0
        
        subscribers = self.subscriptions[topic].copy()
        if exclude_connections:
            subscribers -= exclude_connections
        
        if not subscribers:
            return 0
        
        # 批量发送优化
        if self.batch_enabled and len(subscribers) > 1:
            await self._add_to_batch(topic, message, subscribers)
            return len(subscribers)
        
        # 并发发送
        tasks = [
            self.send_message_to_connection(connection_id, message)
            for connection_id in subscribers
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = sum(1 for result in results if result is True)
        
        logger.debug(f"Broadcast to {topic}: {success_count}/{len(subscribers)} successful")
        return success_count
    
    async def _add_to_batch(
        self, 
        topic: str, 
        message: Dict[str, Any], 
        target_connections: Set[str]
    ):
        """添加消息到批次"""
        
        if topic not in self.message_batches:
            self.message_batches[topic] = MessageBatch(
                messages=[],
                created_at=datetime.now(),
                target_connections=target_connections.copy()
            )
        
        batch = self.message_batches[topic]
        batch.add_message(message)
        batch.target_connections.update(target_connections)
        
        # 检查是否需要立即发送
        if batch.is_ready_to_send(
            self.config["batch_size"], 
            self.config["batch_timeout"]
        ):
            await self._send_batch(topic)
    
    async def _send_batch(self, topic: str):
        """发送批次消息"""
        
        if topic not in self.message_batches:
            return
        
        batch = self.message_batches[topic]
        del self.message_batches[topic]
        
        if not batch.messages:
            return
        
        # 创建批次消息
        batch_message = {
            "type": "batch",
            "topic": topic,
            "messages": batch.messages,
            "timestamp": datetime.now().isoformat()
        }
        
        # 并发发送到所有目标连接
        tasks = [
            self.send_message_to_connection(connection_id, batch_message)
            for connection_id in batch.target_connections
            if connection_id in self.connections
        ]
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for result in results if result is True)
            logger.debug(f"Batch sent to {topic}: {success_count}/{len(tasks)} successful")
    
    def check_rate_limit(self, connection_id: str) -> bool:
        """检查速率限制"""
        
        now = time.time()
        rate_limiter = self.rate_limiters[connection_id]
        
        # 清理过期的时间戳
        while rate_limiter and rate_limiter[0] < now - 1:
            rate_limiter.popleft()
        
        # 检查是否超过限制
        if len(rate_limiter) >= self.config["rate_limit_per_second"]:
            return False
        
        # 添加当前时间戳
        rate_limiter.append(now)
        return True
    
    async def handle_message(
        self, 
        connection_id: str, 
        message: Dict[str, Any]
    ):
        """处理接收到的消息"""
        
        if connection_id not in self.connections:
            return
        
        # 检查速率限制
        if not self.check_rate_limit(connection_id):
            await self.send_message_to_connection(
                connection_id,
                {"type": "error", "message": "Rate limit exceeded"}
            )
            return
        
        # 更新指标
        metrics = self.connection_metrics[connection_id]
        metrics.messages_received += 1
        metrics.last_activity = datetime.now()
        
        # 处理不同类型的消息
        message_type = message.get("type")
        
        if message_type == "subscribe":
            topic = message.get("topic")
            if topic:
                self.subscribe_to_topic(connection_id, topic)
                await self.send_message_to_connection(
                    connection_id,
                    {"type": "subscribed", "topic": topic}
                )
        
        elif message_type == "unsubscribe":
            topic = message.get("topic")
            if topic:
                self.unsubscribe_from_topic(connection_id, topic)
                await self.send_message_to_connection(
                    connection_id,
                    {"type": "unsubscribed", "topic": topic}
                )
        
        elif message_type == "ping":
            await self.send_message_to_connection(
                connection_id,
                {"type": "pong", "timestamp": datetime.now().isoformat()}
            )
    
    async def send_heartbeat(self):
        """发送心跳消息"""
        
        heartbeat_message = {
            "type": "heartbeat",
            "timestamp": datetime.now().isoformat()
        }
        
        # 并发发送心跳到所有连接
        tasks = [
            self.send_message_to_connection(connection_id, heartbeat_message)
            for connection_id in list(self.connections.keys())
        ]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def cleanup_stale_connections(self):
        """清理过期连接"""
        
        now = datetime.now()
        stale_connections = []
        
        for connection_id, metrics in self.connection_metrics.items():
            if (now - metrics.last_activity).total_seconds() > self.config["heartbeat_timeout"]:
                stale_connections.append(connection_id)
        
        for connection_id in stale_connections:
            await self.disconnect_connection(connection_id, "Connection timeout")
        
        if stale_connections:
            logger.info(f"Cleaned up {len(stale_connections)} stale connections")
    
    async def _background_tasks(self):
        """后台任务"""
        
        while True:
            try:
                # 发送心跳
                await self.send_heartbeat()
                
                # 发送待处理的批次
                for topic in list(self.message_batches.keys()):
                    batch = self.message_batches[topic]
                    if batch.is_ready_to_send(
                        self.config["batch_size"], 
                        self.config["batch_timeout"]
                    ):
                        await self._send_batch(topic)
                
                # 清理过期连接
                await self.cleanup_stale_connections()
                
                # 等待下一次执行
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Error in background tasks: {e}")
                await asyncio.sleep(5)
    
    def get_connection_metrics(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """获取连接指标"""
        
        if connection_id not in self.connection_metrics:
            return None
        
        metrics = self.connection_metrics[connection_id]
        return {
            "connection_id": metrics.connection_id,
            "connected_at": metrics.connected_at.isoformat(),
            "last_activity": metrics.last_activity.isoformat(),
            "connection_duration": str(metrics.connection_duration),
            "messages_sent": metrics.messages_sent,
            "messages_received": metrics.messages_received,
            "bytes_sent": metrics.bytes_sent,
            "bytes_received": metrics.bytes_received,
            "errors": metrics.errors,
            "avg_latency": metrics.avg_latency
        }
    
    def get_global_metrics(self) -> Dict[str, Any]:
        """获取全局指标"""
        
        total_connections = len(self.connections)
        total_subscriptions = sum(len(subs) for subs in self.subscriptions.values())
        total_messages_sent = sum(m.messages_sent for m in self.connection_metrics.values())
        total_messages_received = sum(m.messages_received for m in self.connection_metrics.values())
        total_bytes_sent = sum(m.bytes_sent for m in self.connection_metrics.values())
        total_bytes_received = sum(m.bytes_received for m in self.connection_metrics.values())
        total_errors = sum(m.errors for m in self.connection_metrics.values())
        
        avg_latency = 0
        if self.connection_metrics:
            avg_latency = sum(m.avg_latency for m in self.connection_metrics.values()) / len(self.connection_metrics)
        
        return {
            "total_connections": total_connections,
            "total_subscriptions": total_subscriptions,
            "total_messages_sent": total_messages_sent,
            "total_messages_received": total_messages_received,
            "total_bytes_sent": total_bytes_sent,
            "total_bytes_received": total_bytes_received,
            "total_errors": total_errors,
            "avg_latency": avg_latency,
            "active_topics": len(self.subscriptions),
            "pending_batches": len(self.message_batches)
        }
    
    def get_topic_metrics(self) -> Dict[str, Dict[str, Any]]:
        """获取主题指标"""
        
        topic_metrics = {}
        
        for topic, subscribers in self.subscriptions.items():
            topic_metrics[topic] = {
                "subscriber_count": len(subscribers),
                "active_subscribers": len([
                    cid for cid in subscribers 
                    if cid in self.connections
                ]),
                "has_pending_batch": topic in self.message_batches
            }
        
        return topic_metrics

# 创建全局实例
websocket_optimization_service = WebSocketOptimizationService()