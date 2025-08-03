"""
市场数据管理器
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..adapters.market_data_adapter import MarketDataAdapter, MarketDataAdapterFactory
from ..services.market_data_service import MarketDataService
from ..core.database import get_db

logger = logging.getLogger(__name__)

class MarketDataManager:
    """市场数据管理器"""
    
    def __init__(self):
        self.adapters: Dict[str, MarketDataAdapter] = {}
        self.subscriptions: Dict[str, List[str]] = {}  # provider -> symbols
        self.is_running = False
        self.tasks: List[asyncio.Task] = []
    
    async def initialize(self, providers_config: List[Dict[str, Any]]):
        """初始化数据管理器"""
        try:
            # 创建数据适配器
            for config in providers_config:
                provider_name = config['name']
                adapter = MarketDataAdapterFactory.create_adapter(provider_name, config)
                
                # 连接到数据源
                if await adapter.connect():
                    self.adapters[provider_name] = adapter
                    self.subscriptions[provider_name] = []
                    logger.info(f"数据提供商初始化成功: {provider_name}")
                else:
                    logger.error(f"数据提供商连接失败: {provider_name}")
            
            logger.info(f"市场数据管理器初始化完成，共{len(self.adapters)}个提供商")
            
        except Exception as e:
            logger.error(f"市场数据管理器初始化失败: {e}")
            raise
    
    async def start(self):
        """启动数据管理器"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 启动数据订阅任务
        for provider_name, adapter in self.adapters.items():
            if self.subscriptions[provider_name]:
                # 启动报价订阅
                task = asyncio.create_task(
                    self._handle_quote_subscription(provider_name, adapter)
                )
                self.tasks.append(task)
                
                # 启动成交数据订阅
                task = asyncio.create_task(
                    self._handle_trade_subscription(provider_name, adapter)
                )
                self.tasks.append(task)
                
                # 启动深度数据订阅
                task = asyncio.create_task(
                    self._handle_depth_subscription(provider_name, adapter)
                )
                self.tasks.append(task)
        
        # 启动数据质量监控任务
        task = asyncio.create_task(self._monitor_data_quality())
        self.tasks.append(task)
        
        logger.info("市场数据管理器启动成功")
    
    async def stop(self):
        """停止数据管理器"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 取消所有任务
        for task in self.tasks:
            task.cancel()
        
        # 等待任务完成
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks.clear()
        
        # 断开所有连接
        for adapter in self.adapters.values():
            await adapter.disconnect()
        
        logger.info("市场数据管理器已停止")
    
    async def subscribe_symbol(self, provider_name: str, symbol: str):
        """订阅标的数据"""
        if provider_name not in self.adapters:
            raise ValueError(f"数据提供商不存在: {provider_name}")
        
        if symbol not in self.subscriptions[provider_name]:
            self.subscriptions[provider_name].append(symbol)
            logger.info(f"订阅标的成功: {provider_name} - {symbol}")
    
    async def unsubscribe_symbol(self, provider_name: str, symbol: str):
        """取消订阅标的数据"""
        if provider_name in self.subscriptions:
            if symbol in self.subscriptions[provider_name]:
                self.subscriptions[provider_name].remove(symbol)
                logger.info(f"取消订阅标的成功: {provider_name} - {symbol}")
    
    async def get_quote(self, symbol: str, provider_name: str = None) -> Optional[Dict[str, Any]]:
        """获取实时报价"""
        try:
            if provider_name:
                # 指定提供商
                if provider_name in self.adapters:
                    return await self.adapters[provider_name].get_quote(symbol)
            else:
                # 尝试所有提供商
                for adapter in self.adapters.values():
                    quote = await adapter.get_quote(symbol)
                    if quote:
                        return quote
            
            return None
            
        except Exception as e:
            logger.error(f"获取报价失败: {symbol}, {e}")
            return None
    
    async def get_klines(self, symbol: str, interval: str, 
                        start_time: datetime = None, end_time: datetime = None,
                        limit: int = 1000, provider_name: str = None) -> List[Dict[str, Any]]:
        """获取K线数据"""
        try:
            if provider_name:
                # 指定提供商
                if provider_name in self.adapters:
                    return await self.adapters[provider_name].get_klines(
                        symbol, interval, start_time, end_time, limit
                    )
            else:
                # 尝试所有提供商
                for adapter in self.adapters.values():
                    klines = await adapter.get_klines(symbol, interval, start_time, end_time, limit)
                    if klines:
                        return klines
            
            return []
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {symbol}, {e}")
            return []
    
    async def get_trades(self, symbol: str, limit: int = 1000, 
                        provider_name: str = None) -> List[Dict[str, Any]]:
        """获取成交数据"""
        try:
            if provider_name:
                # 指定提供商
                if provider_name in self.adapters:
                    return await self.adapters[provider_name].get_trades(symbol, limit)
            else:
                # 尝试所有提供商
                for adapter in self.adapters.values():
                    trades = await adapter.get_trades(symbol, limit)
                    if trades:
                        return trades
            
            return []
            
        except Exception as e:
            logger.error(f"获取成交数据失败: {symbol}, {e}")
            return []
    
    async def get_depth(self, symbol: str, limit: int = 20, 
                       provider_name: str = None) -> Optional[Dict[str, Any]]:
        """获取深度数据"""
        try:
            if provider_name:
                # 指定提供商
                if provider_name in self.adapters:
                    return await self.adapters[provider_name].get_depth(symbol, limit)
            else:
                # 尝试所有提供商
                for adapter in self.adapters.values():
                    depth = await adapter.get_depth(symbol, limit)
                    if depth:
                        return depth
            
            return None
            
        except Exception as e:
            logger.error(f"获取深度数据失败: {symbol}, {e}")
            return None
    
    def get_provider_status(self) -> List[Dict[str, Any]]:
        """获取提供商状态"""
        status_list = []
        
        for provider_name, adapter in self.adapters.items():
            status_list.append({
                'name': provider_name,
                'is_connected': adapter.is_connected,
                'last_error': adapter.last_error,
                'is_realtime': adapter.is_realtime(),
                'delay_seconds': adapter.get_delay_seconds(),
                'subscribed_symbols': len(self.subscriptions.get(provider_name, []))
            })
        
        return status_list
    
    async def _handle_quote_subscription(self, provider_name: str, adapter: MarketDataAdapter):
        """处理报价订阅"""
        try:
            symbols = self.subscriptions[provider_name]
            if not symbols:
                return
            
            async for quote_data in adapter.subscribe_quotes(symbols):
                if not self.is_running:
                    break
                
                # 保存报价数据到数据库
                await self._save_quote_data(quote_data)
                
        except asyncio.CancelledError:
            logger.info(f"报价订阅任务已取消: {provider_name}")
        except Exception as e:
            logger.error(f"报价订阅处理失败: {provider_name}, {e}")
    
    async def _handle_trade_subscription(self, provider_name: str, adapter: MarketDataAdapter):
        """处理成交数据订阅"""
        try:
            symbols = self.subscriptions[provider_name]
            if not symbols:
                return
            
            async for trade_data in adapter.subscribe_trades(symbols):
                if not self.is_running:
                    break
                
                # 保存成交数据到数据库
                await self._save_trade_data(trade_data)
                
        except asyncio.CancelledError:
            logger.info(f"成交数据订阅任务已取消: {provider_name}")
        except Exception as e:
            logger.error(f"成交数据订阅处理失败: {provider_name}, {e}")
    
    async def _handle_depth_subscription(self, provider_name: str, adapter: MarketDataAdapter):
        """处理深度数据订阅"""
        try:
            symbols = self.subscriptions[provider_name]
            if not symbols:
                return
            
            async for depth_data in adapter.subscribe_depth(symbols):
                if not self.is_running:
                    break
                
                # 保存深度数据到数据库
                await self._save_depth_data(depth_data)
                
        except asyncio.CancelledError:
            logger.info(f"深度数据订阅任务已取消: {provider_name}")
        except Exception as e:
            logger.error(f"深度数据订阅处理失败: {provider_name}, {e}")
    
    async def _save_quote_data(self, quote_data: Dict[str, Any]):
        """保存报价数据"""
        try:
            # 获取数据库会话
            db = next(get_db())
            service = MarketDataService(db)
            
            # 获取标的ID
            symbol = service.get_symbol(quote_data['symbol'])
            if not symbol:
                logger.warning(f"标的不存在: {quote_data['symbol']}")
                return
            
            # 准备报价数据
            quote_data['symbol_id'] = symbol.id
            
            # 保存到数据库
            service.save_quote(quote_data)
            
        except Exception as e:
            logger.error(f"保存报价数据失败: {e}")
    
    async def _save_trade_data(self, trade_data: Dict[str, Any]):
        """保存成交数据"""
        try:
            # 获取数据库会话
            db = next(get_db())
            service = MarketDataService(db)
            
            # 获取标的ID
            symbol = service.get_symbol(trade_data['symbol'])
            if not symbol:
                logger.warning(f"标的不存在: {trade_data['symbol']}")
                return
            
            # 准备成交数据
            trade_data['symbol_id'] = symbol.id
            
            # 保存到数据库
            service.save_trade(trade_data)
            
        except Exception as e:
            logger.error(f"保存成交数据失败: {e}")
    
    async def _save_depth_data(self, depth_data: Dict[str, Any]):
        """保存深度数据"""
        try:
            # 获取数据库会话
            db = next(get_db())
            service = MarketDataService(db)
            
            # 获取标的ID
            symbol = service.get_symbol(depth_data['symbol'])
            if not symbol:
                logger.warning(f"标的不存在: {depth_data['symbol']}")
                return
            
            # 准备深度数据
            depth_data['symbol_id'] = symbol.id
            
            # 保存到数据库
            service.save_depth_data(depth_data)
            
        except Exception as e:
            logger.error(f"保存深度数据失败: {e}")
    
    async def _monitor_data_quality(self):
        """监控数据质量"""
        try:
            while self.is_running:
                # 获取数据库会话
                db = next(get_db())
                service = MarketDataService(db)
                
                # 为每个提供商计算数据质量
                for provider_name in self.adapters.keys():
                    try:
                        # 计算报价数据质量
                        service.calculate_data_quality(provider_name, data_type='QUOTE')
                        
                        # 计算K线数据质量
                        service.calculate_data_quality(provider_name, data_type='KLINE')
                        
                    except Exception as e:
                        logger.error(f"计算数据质量失败: {provider_name}, {e}")
                
                # 每小时检查一次
                await asyncio.sleep(3600)
                
        except asyncio.CancelledError:
            logger.info("数据质量监控任务已取消")
        except Exception as e:
            logger.error(f"数据质量监控失败: {e}")

# 全局市场数据管理器实例
market_data_manager = MarketDataManager()