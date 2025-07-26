"""
实时数据推送服务
"""
import asyncio
import json
import logging
from typing import Dict, List, Set, Optional, Callable, Any
from datetime import datetime
from fastapi import WebSocket
from collections import defaultdict
import weakref

from ..core.exceptions import ValidationError
from ..services.tqsdk_adapter import tqsdk_adapter
from ..services.market_service import market_service
from ..core.database import get_redis_client
from ..schemas.market import QuoteData, KlineData

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """WebSocket连接封装"""
    
    def __init__(self, websocket: WebSocket, user_id: int, connection_id: str):
        self.websocket = websocket
        self.user_id = user_id
        self.connection_id = connection_id
        self.subscribed_symbols: Set[str] = set()
        self.is_active = True
        self.created_at = datetime.now()
        self.last_ping = datetime.now()
    
    async def send_message(self, message: Dict[str, Any]):
        """发送消息"""
        try:
            if self.is_active:
                await self.websocket.send_text(json.dumps(message, default=str))
                return True
        except Exception as e:
            logger.warning(f"发送消息失败 {self.connection_id}: {e}")
            self.is_active = False
        return False
    
    async def close(self):
        """关闭连接"""
        try:
            if self.is_active:
                await self.websocket.close()
        except:
            pass
        finally:
            self.is_active = False


class RealtimeDataService:
    """实时数据推送服务"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.symbol_subscribers: Dict[str, Set[str]] = defaultdict(set)  # symbol -> connection_ids
        self.user_connections: Dict[int, Set[str]] = defaultdict(set)  # user_id -> connection_ids
        self.redis_client = get_redis_client()
        self.is_running = False
        self.data_push_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        
        # 数据缓存
        self._quote_cache: Dict[str, QuoteData] = {}
        self._last_push_time: Dict[str, datetime] = {}
        
        # 推送频率控制
        self.quote_push_interval = 0.5  # 500ms推送一次行情
        self.heartbeat_interval = 30  # 30秒心跳检测
        
        # 统计信息
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "total_subscriptions": 0,
            "messages_sent": 0,
            "errors": 0,
        }
    
    async def start(self):
        """启动实时数据服务"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 启动数据推送任务
        self.data_push_task = asyncio.create_task(self._data_push_loop())
        
        # 启动心跳检测任务
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        logger.info("实时数据推送服务已启动")
    
    async def stop(self):
        """停止实时数据服务"""
        self.is_running = False
        
        # 取消任务
        if self.data_push_task:
            self.data_push_task.cancel()
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        # 关闭所有连接
        for connection in list(self.connections.values()):
            await connection.close()
        
        self.connections.clear()
        self.symbol_subscribers.clear()
        self.user_connections.clear()
        
        logger.info("实时数据推送服务已停止")
    
    async def add_connection(
        self,
        websocket: WebSocket,
        user_id: int,
        connection_id: str
    ) -> WebSocketConnection:
        """添加WebSocket连接"""
        try:
            await websocket.accept()
            
            connection = WebSocketConnection(websocket, user_id, connection_id)
            
            self.connections[connection_id] = connection
            self.user_connections[user_id].add(connection_id)
            
            self.stats["total_connections"] += 1
            self.stats["active_connections"] += 1
            
            logger.info(f"新增WebSocket连接: {connection_id}, 用户: {user_id}")
            
            # 发送连接确认消息
            await connection.send_message({
                "type": "connection_established",
                "connection_id": connection_id,
                "timestamp": datetime.now().isoformat(),
            })
            
            return connection
            
        except Exception as e:
            logger.error(f"添加WebSocket连接失败: {e}")
            raise
    
    async def remove_connection(self, connection_id: str):
        """移除WebSocket连接"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        # 取消所有订阅
        for symbol in list(connection.subscribed_symbols):
            await self._unsubscribe_symbol(connection_id, symbol)
        
        # 从用户连接列表中移除
        self.user_connections[connection.user_id].discard(connection_id)
        if not self.user_connections[connection.user_id]:
            del self.user_connections[connection.user_id]
        
        # 关闭连接
        await connection.close()
        
        # 从连接列表中移除
        del self.connections[connection_id]
        
        self.stats["active_connections"] -= 1
        
        logger.info(f"移除WebSocket连接: {connection_id}")
    
    async def subscribe_quotes(
        self,
        connection_id: str,
        symbols: List[str]
    ) -> bool:
        """订阅行情"""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        
        try:
            # 验证合约代码
            valid_symbols = []
            for symbol in symbols:
                instrument = await market_service.get_instrument_by_symbol(symbol)
                if instrument:
                    valid_symbols.append(symbol)
                else:
                    logger.warning(f"无效的合约代码: {symbol}")
            
            if not valid_symbols:
                await connection.send_message({
                    "type": "error",
                    "message": "没有有效的合约代码",
                    "timestamp": datetime.now().isoformat(),
                })
                return False
            
            # 添加订阅
            for symbol in valid_symbols:
                connection.subscribed_symbols.add(symbol)
                self.symbol_subscribers[symbol].add(connection_id)
            
            # 通过市场服务订阅行情
            from ..schemas.market import QuoteSubscription
            subscription = QuoteSubscription(symbols=valid_symbols)
            await market_service.subscribe_quotes(subscription)
            
            self.stats["total_subscriptions"] += len(valid_symbols)
            
            # 发送订阅确认
            await connection.send_message({
                "type": "subscription_confirmed",
                "symbols": valid_symbols,
                "timestamp": datetime.now().isoformat(),
            })
            
            # 立即推送当前行情
            await self._push_current_quotes(connection_id, valid_symbols)
            
            logger.info(f"连接 {connection_id} 订阅行情: {valid_symbols}")
            return True
            
        except Exception as e:
            logger.error(f"订阅行情失败: {e}")
            await connection.send_message({
                "type": "error",
                "message": f"订阅失败: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            })
            return False
    
    async def unsubscribe_quotes(
        self,
        connection_id: str,
        symbols: List[str]
    ) -> bool:
        """取消订阅行情"""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        
        try:
            unsubscribed_symbols = []
            
            for symbol in symbols:
                if symbol in connection.subscribed_symbols:
                    await self._unsubscribe_symbol(connection_id, symbol)
                    unsubscribed_symbols.append(symbol)
            
            if unsubscribed_symbols:
                # 发送取消订阅确认
                await connection.send_message({
                    "type": "unsubscription_confirmed",
                    "symbols": unsubscribed_symbols,
                    "timestamp": datetime.now().isoformat(),
                })
                
                logger.info(f"连接 {connection_id} 取消订阅: {unsubscribed_symbols}")
            
            return True
            
        except Exception as e:
            logger.error(f"取消订阅失败: {e}")
            return False
    
    async def _unsubscribe_symbol(self, connection_id: str, symbol: str):
        """取消单个合约订阅"""
        if connection_id in self.connections:
            self.connections[connection_id].subscribed_symbols.discard(symbol)
        
        self.symbol_subscribers[symbol].discard(connection_id)
        
        # 如果没有其他连接订阅此合约，取消市场服务订阅
        if not self.symbol_subscribers[symbol]:
            await market_service.unsubscribe_quotes([symbol])
            del self.symbol_subscribers[symbol]
    
    async def _push_current_quotes(self, connection_id: str, symbols: List[str]):
        """推送当前行情"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        try:
            quotes = await market_service.get_quotes(symbols)
            
            if quotes:
                await connection.send_message({
                    "type": "quotes_snapshot",
                    "data": {symbol: quote.dict() for symbol, quote in quotes.items()},
                    "timestamp": datetime.now().isoformat(),
                })
                
                self.stats["messages_sent"] += 1
                
        except Exception as e:
            logger.error(f"推送当前行情失败: {e}")
            self.stats["errors"] += 1
    
    async def _data_push_loop(self):
        """数据推送循环"""
        while self.is_running:
            try:
                await asyncio.sleep(self.quote_push_interval)
                
                if not self.symbol_subscribers:
                    continue
                
                # 获取所有订阅的合约行情
                all_symbols = list(self.symbol_subscribers.keys())
                if not all_symbols:
                    continue
                
                quotes = await market_service.get_quotes(all_symbols)
                
                if not quotes:
                    continue
                
                # 按合约推送行情
                for symbol, quote in quotes.items():
                    await self._broadcast_quote(symbol, quote)
                
            except Exception as e:
                logger.error(f"数据推送循环异常: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(1)
    
    async def _broadcast_quote(self, symbol: str, quote: QuoteData):
        """广播行情数据"""
        if symbol not in self.symbol_subscribers:
            return
        
        # 检查是否需要推送（避免重复推送相同数据）
        current_time = datetime.now()
        last_push = self._last_push_time.get(symbol)
        
        if (last_push and 
            (current_time - last_push).total_seconds() < self.quote_push_interval):
            return
        
        message = {
            "type": "quote_update",
            "symbol": symbol,
            "data": quote.dict(),
            "timestamp": current_time.isoformat(),
        }
        
        # 向所有订阅此合约的连接推送
        connection_ids = list(self.symbol_subscribers[symbol])
        
        for connection_id in connection_ids:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                success = await connection.send_message(message)
                
                if success:
                    self.stats["messages_sent"] += 1
                else:
                    # 连接已断开，移除
                    await self.remove_connection(connection_id)
                    self.stats["errors"] += 1
        
        self._last_push_time[symbol] = current_time
    
    async def _heartbeat_loop(self):
        """心跳检测循环"""
        while self.is_running:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                current_time = datetime.now()
                disconnected_connections = []
                
                for connection_id, connection in self.connections.items():
                    # 发送心跳
                    success = await connection.send_message({
                        "type": "heartbeat",
                        "timestamp": current_time.isoformat(),
                    })
                    
                    if success:
                        connection.last_ping = current_time
                    else:
                        disconnected_connections.append(connection_id)
                
                # 移除断开的连接
                for connection_id in disconnected_connections:
                    await self.remove_connection(connection_id)
                
            except Exception as e:
                logger.error(f"心跳检测异常: {e}")
                await asyncio.sleep(5)
    
    async def broadcast_message(self, message: Dict[str, Any], user_ids: Optional[List[int]] = None):
        """广播消息"""
        target_connections = []
        
        if user_ids:
            # 向指定用户广播
            for user_id in user_ids:
                if user_id in self.user_connections:
                    for connection_id in self.user_connections[user_id]:
                        if connection_id in self.connections:
                            target_connections.append(self.connections[connection_id])
        else:
            # 向所有连接广播
            target_connections = list(self.connections.values())
        
        for connection in target_connections:
            await connection.send_message(message)
            self.stats["messages_sent"] += 1
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        return {
            **self.stats,
            "subscribed_symbols": len(self.symbol_subscribers),
            "active_symbols": len([s for s in self.symbol_subscribers if self.symbol_subscribers[s]]),
        }
    
    def get_user_connections(self, user_id: int) -> List[str]:
        """获取用户的连接列表"""
        return list(self.user_connections.get(user_id, set()))
    
    async def disconnect_user(self, user_id: int):
        """断开用户的所有连接"""
        if user_id in self.user_connections:
            connection_ids = list(self.user_connections[user_id])
            for connection_id in connection_ids:
                await self.remove_connection(connection_id)


# 创建全局实时数据服务实例
realtime_service = RealtimeDataService()