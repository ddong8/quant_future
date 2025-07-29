"""
市场数据服务
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, time
import asyncio
import logging
import json

from ..services.tqsdk_adapter import tqsdk_adapter
from ..core.database import get_redis_client
from ..core.exceptions import ExternalServiceError, ValidationError
from ..core.influxdb import influx_manager
from ..schemas.market import (
    InstrumentInfo,
    QuoteData,
    KlineData,
    KlineRequest,
    QuoteSubscription,
    MarketDataFilter,
    TradingTimeInfo,
    MarketStatus,
    ConnectionStatus,
    MarketDataStats,
)

logger = logging.getLogger(__name__)


class MarketService:
    """市场数据服务类"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self._subscribed_symbols = set()
        self._quote_cache_ttl = 5  # 行情缓存5秒
        self._instrument_cache_ttl = 300  # 合约信息缓存5分钟
    
    async def initialize(self):
        """初始化市场数据服务"""
        try:
            # 检查是否有天勤配置
            from ..core.config import settings
            if not settings.TQSDK_AUTH:
                logger.warning("未配置天勤账户，跳过市场数据服务初始化")
                return True
            
            # 初始化tqsdk适配器
            await tqsdk_adapter.initialize(use_sim=True)
            
            # 启动数据更新任务
            asyncio.create_task(self._data_update_task())
            
            logger.info("市场数据服务初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"市场数据服务初始化失败: {e}")
            # 不抛出异常，允许应用继续启动
            logger.warning("市场数据服务初始化失败，但应用将继续启动")
            return False
    
    async def get_connection_status(self) -> ConnectionStatus:
        """获取连接状态"""
        status = tqsdk_adapter.get_connection_status()
        
        return ConnectionStatus(
            is_connected=status["is_connected"],
            is_sim_trading=status["is_sim_trading"],
            reconnect_attempts=status["reconnect_attempts"],
            tqsdk_available=status["tqsdk_available"],
            last_heartbeat=datetime.now().isoformat(),
        )
    
    async def get_instruments(
        self,
        filter_params: Optional[MarketDataFilter] = None
    ) -> List[InstrumentInfo]:
        """获取合约信息列表"""
        try:
            # 从适配器获取合约信息
            instruments_data = await tqsdk_adapter.get_instruments(
                exchange=filter_params.exchange if filter_params else None
            )
            
            instruments = []
            for data in instruments_data:
                # 应用过滤条件
                if filter_params:
                    if filter_params.product_id and data.get("product_id") != filter_params.product_id:
                        continue
                    if filter_params.expired is not None and data.get("expired") != filter_params.expired:
                        continue
                    if filter_params.keyword:
                        keyword = filter_params.keyword.lower()
                        if (keyword not in data.get("symbol", "").lower() and 
                            keyword not in data.get("name", "").lower()):
                            continue
                
                instrument = InstrumentInfo(**data)
                instruments.append(instrument)
            
            logger.info(f"获取到{len(instruments)}个合约信息")
            return instruments
            
        except Exception as e:
            logger.error(f"获取合约信息失败: {e}")
            raise ExternalServiceError(f"获取合约信息失败: {str(e)}")
    
    async def get_instrument_by_symbol(self, symbol: str) -> Optional[InstrumentInfo]:
        """根据合约代码获取合约信息"""
        try:
            instruments = await self.get_instruments()
            
            for instrument in instruments:
                if instrument.symbol == symbol:
                    return instrument
            
            return None
            
        except Exception as e:
            logger.error(f"获取合约信息失败 {symbol}: {e}")
            return None
    
    async def get_quote(self, symbol: str) -> Optional[QuoteData]:
        """获取实时行情"""
        try:
            # 检查缓存
            cache_key = f"quote:{symbol}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                quote_dict = json.loads(cached_data)
                return QuoteData(**quote_dict)
            
            # 从适配器获取行情
            quote_data = await tqsdk_adapter.get_quote(symbol)
            
            if not quote_data:
                return None
            
            quote = QuoteData(**quote_data)
            
            # 缓存行情数据
            self.redis_client.setex(
                cache_key,
                self._quote_cache_ttl,
                quote.json()
            )
            
            # 存储到InfluxDB
            await self._store_quote_to_influx(quote_data)
            
            return quote
            
        except Exception as e:
            logger.error(f"获取行情失败 {symbol}: {e}")
            return None
    
    async def get_quotes(self, symbols: List[str]) -> Dict[str, QuoteData]:
        """批量获取行情"""
        quotes = {}
        
        tasks = [self.get_quote(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, result in zip(symbols, results):
            if isinstance(result, QuoteData):
                quotes[symbol] = result
            elif isinstance(result, Exception):
                logger.warning(f"获取行情失败 {symbol}: {result}")
        
        return quotes
    
    async def get_klines(self, request: KlineRequest) -> List[KlineData]:
        """获取K线数据"""
        try:
            # 检查缓存
            cache_key = f"klines:{request.symbol}:{request.duration}:{request.data_length}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                klines_data = json.loads(cached_data)
                return [KlineData(**kline) for kline in klines_data]
            
            # 从适配器获取K线数据
            klines_data = await tqsdk_adapter.get_klines(
                request.symbol,
                request.duration,
                request.data_length
            )
            
            klines = [KlineData(**kline) for kline in klines_data]
            
            # 缓存K线数据（缓存时间根据周期调整）
            cache_ttl = min(request.duration, 300)  # 最多缓存5分钟
            self.redis_client.setex(
                cache_key,
                cache_ttl,
                json.dumps(klines_data)
            )
            
            # 存储到InfluxDB
            for kline_data in klines_data:
                await self._store_kline_to_influx(request.symbol, kline_data, request.duration)
            
            logger.info(f"获取K线数据成功 {request.symbol}: {len(klines)}条")
            return klines
            
        except Exception as e:
            logger.error(f"获取K线数据失败 {request.symbol}: {e}")
            raise ExternalServiceError(f"获取K线数据失败: {str(e)}")
    
    async def subscribe_quotes(self, subscription: QuoteSubscription) -> bool:
        """订阅行情"""
        try:
            # 添加到订阅列表
            self._subscribed_symbols.update(subscription.symbols)
            
            # 通过适配器订阅
            await tqsdk_adapter.subscribe_quotes(subscription.symbols)
            
            # 缓存订阅信息
            subscription_key = "market:subscriptions"
            self.redis_client.sadd(subscription_key, *subscription.symbols)
            
            logger.info(f"订阅行情成功: {subscription.symbols}")
            return True
            
        except Exception as e:
            logger.error(f"订阅行情失败: {e}")
            raise ExternalServiceError(f"订阅行情失败: {str(e)}")
    
    async def unsubscribe_quotes(self, symbols: List[str]) -> bool:
        """取消订阅行情"""
        try:
            # 从订阅列表移除
            self._subscribed_symbols.difference_update(symbols)
            
            # 通过适配器取消订阅
            await tqsdk_adapter.unsubscribe_quotes(symbols)
            
            # 更新缓存
            subscription_key = "market:subscriptions"
            self.redis_client.srem(subscription_key, *symbols)
            
            logger.info(f"取消订阅行情: {symbols}")
            return True
            
        except Exception as e:
            logger.error(f"取消订阅行情失败: {e}")
            return False
    
    async def get_subscribed_symbols(self) -> List[str]:
        """获取已订阅的合约列表"""
        subscription_key = "market:subscriptions"
        symbols = self.redis_client.smembers(subscription_key)
        return list(symbols)
    
    async def get_trading_time_info(self, symbol: str) -> Optional[TradingTimeInfo]:
        """获取交易时间信息"""
        try:
            instrument = await self.get_instrument_by_symbol(symbol)
            if not instrument:
                return None
            
            # 检查当前是否在交易时间
            is_trading = self._is_trading_time(instrument.trading_time)
            
            return TradingTimeInfo(
                symbol=symbol,
                trading_time=instrument.trading_time,
                is_trading=is_trading,
                next_trading_time=self._get_next_trading_time(instrument.trading_time),
            )
            
        except Exception as e:
            logger.error(f"获取交易时间信息失败 {symbol}: {e}")
            return None
    
    def _is_trading_time(self, trading_time: Dict[str, Any]) -> bool:
        """检查当前是否在交易时间"""
        try:
            current_time = datetime.now().time()
            
            # 检查日盘交易时间
            if "day" in trading_time:
                for time_range in trading_time["day"]:
                    start_time = time.fromisoformat(time_range[0])
                    end_time = time.fromisoformat(time_range[1])
                    
                    if start_time <= current_time <= end_time:
                        return True
            
            # 检查夜盘交易时间
            if "night" in trading_time:
                for time_range in trading_time["night"]:
                    start_time = time.fromisoformat(time_range[0])
                    end_time = time.fromisoformat(time_range[1])
                    
                    # 夜盘可能跨天
                    if start_time > end_time:
                        if current_time >= start_time or current_time <= end_time:
                            return True
                    else:
                        if start_time <= current_time <= end_time:
                            return True
            
            return False
            
        except Exception:
            return False
    
    def _get_next_trading_time(self, trading_time: Dict[str, Any]) -> Optional[str]:
        """获取下一个交易时间"""
        # 简化实现，返回下一个日盘开始时间
        if "day" in trading_time and trading_time["day"]:
            return trading_time["day"][0][0]
        return None
    
    async def get_market_status(self) -> MarketStatus:
        """获取市场状态"""
        try:
            current_time = datetime.now()
            
            # 简化的市场状态判断
            is_trading_time = self._is_general_trading_time(current_time.time())
            
            return MarketStatus(
                is_trading_time=is_trading_time,
                current_session="day" if is_trading_time else None,
                market_date=current_time.strftime("%Y-%m-%d"),
            )
            
        except Exception as e:
            logger.error(f"获取市场状态失败: {e}")
            raise ExternalServiceError(f"获取市场状态失败: {str(e)}")
    
    def _is_general_trading_time(self, current_time: time) -> bool:
        """检查是否在一般交易时间内"""
        # 简化的交易时间判断（9:00-15:00）
        return time(9, 0) <= current_time <= time(15, 0)
    
    async def get_market_stats(self) -> MarketDataStats:
        """获取市场数据统计"""
        try:
            # 从Redis获取统计信息
            quote_count = len(self.redis_client.keys("quote:*"))
            kline_count = len(self.redis_client.keys("klines:*"))
            subscription_count = len(self._subscribed_symbols)
            
            # 简化的缓存命中率计算
            cache_hit_rate = 0.85  # 模拟值
            
            return MarketDataStats(
                quote_count=quote_count,
                kline_count=kline_count,
                subscription_count=subscription_count,
                cache_hit_rate=cache_hit_rate,
                last_update=datetime.now().isoformat(),
            )
            
        except Exception as e:
            logger.error(f"获取市场数据统计失败: {e}")
            raise ExternalServiceError(f"获取市场数据统计失败: {str(e)}")
    
    async def _store_quote_to_influx(self, quote_data: Dict[str, Any]):
        """存储行情数据到InfluxDB"""
        try:
            from ..core.data_validator import MarketDataValidator
            
            # 验证和格式化数据
            validated_data = MarketDataValidator.validate_quote_data(quote_data)
            
            # 存储到InfluxDB
            influx_manager.write_quote(validated_data["symbol"], validated_data)
            
        except Exception as e:
            logger.warning(f"存储行情数据到InfluxDB失败: {e}")
    
    async def _store_kline_to_influx(
        self,
        symbol: str,
        kline_data: Dict[str, Any],
        duration: int
    ):
        """存储K线数据到InfluxDB"""
        try:
            from ..core.data_validator import MarketDataValidator
            
            # 验证和格式化数据
            validated_data = MarketDataValidator.validate_kline_data(kline_data)
            validated_data["symbol"] = symbol
            validated_data["period"] = f"{duration}s"
            
            # 存储到InfluxDB
            influx_manager.write_kline(symbol, validated_data)
            
        except Exception as e:
            logger.warning(f"存储K线数据到InfluxDB失败: {e}")
    
    async def _data_update_task(self):
        """数据更新任务"""
        while True:
            try:
                await asyncio.sleep(1)  # 每秒更新一次
                
                # 更新订阅的行情数据
                if self._subscribed_symbols:
                    symbols = list(self._subscribed_symbols)
                    await self.get_quotes(symbols)
                
            except Exception as e:
                logger.error(f"数据更新任务异常: {e}")
                await asyncio.sleep(5)  # 出错时等待5秒


# 创建全局市场数据服务实例
market_service = MarketService()