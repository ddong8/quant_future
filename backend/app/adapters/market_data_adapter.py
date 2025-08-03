"""
市场数据适配器
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

class MarketDataAdapter(ABC):
    """市场数据适配器抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get('name', 'unknown')
        self.is_connected = False
        self.last_error = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接到数据源"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接"""
        pass
    
    @abstractmethod
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取实时报价"""
        pass
    
    @abstractmethod
    async def get_klines(self, symbol: str, interval: str, 
                        start_time: datetime = None, end_time: datetime = None,
                        limit: int = 1000) -> List[Dict[str, Any]]:
        """获取K线数据"""
        pass
    
    @abstractmethod
    async def get_trades(self, symbol: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """获取成交数据"""
        pass
    
    @abstractmethod
    async def get_depth(self, symbol: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """获取深度数据"""
        pass
    
    @abstractmethod
    async def subscribe_quotes(self, symbols: List[str]) -> AsyncGenerator[Dict[str, Any], None]:
        """订阅实时报价"""
        pass
    
    @abstractmethod
    async def subscribe_trades(self, symbols: List[str]) -> AsyncGenerator[Dict[str, Any], None]:
        """订阅成交数据"""
        pass
    
    @abstractmethod
    async def subscribe_depth(self, symbols: List[str]) -> AsyncGenerator[Dict[str, Any], None]:
        """订阅深度数据"""
        pass
    
    @abstractmethod
    def get_supported_symbols(self) -> List[str]:
        """获取支持的标的列表"""
        pass
    
    @abstractmethod
    def get_supported_intervals(self) -> List[str]:
        """获取支持的时间间隔"""
        pass
    
    def is_realtime(self) -> bool:
        """是否实时数据"""
        return self.config.get('is_realtime', False)
    
    def get_delay_seconds(self) -> int:
        """获取延迟秒数"""
        return self.config.get('delay_seconds', 0)

class YahooFinanceAdapter(MarketDataAdapter):
    """Yahoo Finance数据适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = "https://query1.finance.yahoo.com"
    
    async def connect(self) -> bool:
        """连接到Yahoo Finance"""
        try:
            # Yahoo Finance不需要特殊连接
            self.is_connected = True
            logger.info("Yahoo Finance连接成功")
            return True
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Yahoo Finance连接失败: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """断开连接"""
        self.is_connected = False
        return True
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取实时报价"""
        try:
            import aiohttp
            
            url = f"{self.base_url}/v8/finance/chart/{symbol}"
            params = {
                'interval': '1m',
                'range': '1d'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get('chart', {}).get('result', [])
                        
                        if result:
                            chart_data = result[0]
                            meta = chart_data.get('meta', {})
                            
                            return {
                                'symbol': symbol,
                                'price': Decimal(str(meta.get('regularMarketPrice', 0))),
                                'change': Decimal(str(meta.get('regularMarketPrice', 0) - meta.get('previousClose', 0))),
                                'change_percent': Decimal(str(((meta.get('regularMarketPrice', 0) - meta.get('previousClose', 0)) / meta.get('previousClose', 1)) * 100)),
                                'volume': Decimal(str(meta.get('regularMarketVolume', 0))),
                                'open_price': Decimal(str(meta.get('regularMarketOpen', 0))),
                                'high_price': Decimal(str(meta.get('regularMarketDayHigh', 0))),
                                'low_price': Decimal(str(meta.get('regularMarketDayLow', 0))),
                                'prev_close': Decimal(str(meta.get('previousClose', 0))),
                                'quote_time': datetime.fromtimestamp(meta.get('regularMarketTime', 0)),
                                'data_provider': self.name
                            }
            
            return None
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取Yahoo Finance报价失败: {e}")
            return None
    
    async def get_klines(self, symbol: str, interval: str, 
                        start_time: datetime = None, end_time: datetime = None,
                        limit: int = 1000) -> List[Dict[str, Any]]:
        """获取K线数据"""
        try:
            import aiohttp
            
            # 映射时间间隔
            interval_map = {
                '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1h', '1d': '1d', '1w': '1wk', '1M': '1mo'
            }
            
            yahoo_interval = interval_map.get(interval, '1d')
            
            url = f"{self.base_url}/v8/finance/chart/{symbol}"
            params = {
                'interval': yahoo_interval,
                'range': '1y'  # 默认1年数据
            }
            
            if start_time and end_time:
                params['period1'] = int(start_time.timestamp())
                params['period2'] = int(end_time.timestamp())
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get('chart', {}).get('result', [])
                        
                        if result:
                            chart_data = result[0]
                            timestamps = chart_data.get('timestamp', [])
                            indicators = chart_data.get('indicators', {})
                            quote = indicators.get('quote', [{}])[0]
                            
                            klines = []
                            for i, timestamp in enumerate(timestamps):
                                if i >= limit:
                                    break
                                
                                open_price = quote.get('open', [])[i] if i < len(quote.get('open', [])) else None
                                high_price = quote.get('high', [])[i] if i < len(quote.get('high', [])) else None
                                low_price = quote.get('low', [])[i] if i < len(quote.get('low', [])) else None
                                close_price = quote.get('close', [])[i] if i < len(quote.get('close', [])) else None
                                volume = quote.get('volume', [])[i] if i < len(quote.get('volume', [])) else None
                                
                                if all(v is not None for v in [open_price, high_price, low_price, close_price]):
                                    open_time = datetime.fromtimestamp(timestamp)
                                    
                                    klines.append({
                                        'symbol': symbol,
                                        'interval': interval,
                                        'open_time': open_time,
                                        'close_time': open_time,  # Yahoo不提供close_time
                                        'open_price': Decimal(str(open_price)),
                                        'high_price': Decimal(str(high_price)),
                                        'low_price': Decimal(str(low_price)),
                                        'close_price': Decimal(str(close_price)),
                                        'volume': Decimal(str(volume or 0)),
                                        'data_provider': self.name,
                                        'is_final': True
                                    })
                            
                            return klines
            
            return []
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取Yahoo Finance K线数据失败: {e}")
            return []
    
    async def get_trades(self, symbol: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """获取成交数据"""
        # Yahoo Finance不提供详细的成交数据
        return []
    
    async def get_depth(self, symbol: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """获取深度数据"""
        # Yahoo Finance不提供深度数据
        return None
    
    async def subscribe_quotes(self, symbols: List[str]) -> AsyncGenerator[Dict[str, Any], None]:
        """订阅实时报价"""
        # Yahoo Finance不支持WebSocket订阅，使用轮询模拟
        while True:
            for symbol in symbols:
                quote = await self.get_quote(symbol)
                if quote:
                    yield quote
            await asyncio.sleep(1)  # 1秒轮询一次
    
    async def subscribe_trades(self, symbols: List[str]) -> AsyncGenerator[Dict[str, Any], None]:
        """订阅成交数据"""
        # Yahoo Finance不支持成交数据订阅
        return
        yield  # 使函数成为生成器
    
    async def subscribe_depth(self, symbols: List[str]) -> AsyncGenerator[Dict[str, Any], None]:
        """订阅深度数据"""
        # Yahoo Finance不支持深度数据订阅
        return
        yield  # 使函数成为生成器
    
    def get_supported_symbols(self) -> List[str]:
        """获取支持的标的列表"""
        # Yahoo Finance支持大部分美股、港股等
        return ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']  # 示例
    
    def get_supported_intervals(self) -> List[str]:
        """获取支持的时间间隔"""
        return ['1m', '5m', '15m', '30m', '1h', '1d', '1w', '1M']

class SimulatedAdapter(MarketDataAdapter):
    """模拟数据适配器（用于测试）"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
        self.base_prices = {
            'AAPL': 150.0, 'GOOGL': 2500.0, 'MSFT': 300.0,
            'TSLA': 800.0, 'AMZN': 3200.0
        }
    
    async def connect(self) -> bool:
        """连接到模拟数据源"""
        self.is_connected = True
        logger.info("模拟数据源连接成功")
        return True
    
    async def disconnect(self) -> bool:
        """断开连接"""
        self.is_connected = False
        return True
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取模拟报价"""
        try:
            import random
            
            if symbol not in self.base_prices:
                return None
            
            base_price = self.base_prices[symbol]
            # 生成随机价格变动
            change_percent = random.uniform(-0.05, 0.05)  # ±5%
            current_price = base_price * (1 + change_percent)
            
            return {
                'symbol': symbol,
                'price': Decimal(str(round(current_price, 2))),
                'change': Decimal(str(round(current_price - base_price, 2))),
                'change_percent': Decimal(str(round(change_percent * 100, 2))),
                'volume': Decimal(str(random.randint(1000000, 10000000))),
                'bid_price': Decimal(str(round(current_price - 0.01, 2))),
                'ask_price': Decimal(str(round(current_price + 0.01, 2))),
                'bid_size': Decimal(str(random.randint(100, 1000))),
                'ask_size': Decimal(str(random.randint(100, 1000))),
                'open_price': Decimal(str(round(base_price * random.uniform(0.98, 1.02), 2))),
                'high_price': Decimal(str(round(current_price * random.uniform(1.0, 1.03), 2))),
                'low_price': Decimal(str(round(current_price * random.uniform(0.97, 1.0), 2))),
                'prev_close': Decimal(str(base_price)),
                'quote_time': datetime.now(),
                'data_provider': self.name
            }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取模拟报价失败: {e}")
            return None
    
    async def get_klines(self, symbol: str, interval: str, 
                        start_time: datetime = None, end_time: datetime = None,
                        limit: int = 1000) -> List[Dict[str, Any]]:
        """获取模拟K线数据"""
        try:
            import random
            from datetime import timedelta
            
            if symbol not in self.base_prices:
                return []
            
            base_price = self.base_prices[symbol]
            klines = []
            
            # 生成模拟K线数据
            current_time = end_time or datetime.now()
            interval_minutes = self._get_interval_minutes(interval)
            
            for i in range(min(limit, 100)):  # 限制生成数量
                open_time = current_time - timedelta(minutes=interval_minutes * (limit - i))
                close_time = open_time + timedelta(minutes=interval_minutes)
                
                # 生成OHLC数据
                open_price = base_price * random.uniform(0.95, 1.05)
                close_price = open_price * random.uniform(0.98, 1.02)
                high_price = max(open_price, close_price) * random.uniform(1.0, 1.02)
                low_price = min(open_price, close_price) * random.uniform(0.98, 1.0)
                volume = random.randint(100000, 1000000)
                
                klines.append({
                    'symbol': symbol,
                    'interval': interval,
                    'open_time': open_time,
                    'close_time': close_time,
                    'open_price': Decimal(str(round(open_price, 2))),
                    'high_price': Decimal(str(round(high_price, 2))),
                    'low_price': Decimal(str(round(low_price, 2))),
                    'close_price': Decimal(str(round(close_price, 2))),
                    'volume': Decimal(str(volume)),
                    'turnover': Decimal(str(round(volume * close_price, 2))),
                    'trade_count': random.randint(100, 1000),
                    'data_provider': self.name,
                    'is_final': True
                })
            
            return klines
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取模拟K线数据失败: {e}")
            return []
    
    async def get_trades(self, symbol: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """获取模拟成交数据"""
        try:
            import random
            
            if symbol not in self.base_prices:
                return []
            
            base_price = self.base_prices[symbol]
            trades = []
            
            for i in range(min(limit, 50)):  # 限制生成数量
                price = base_price * random.uniform(0.99, 1.01)
                quantity = random.randint(100, 10000)
                
                trades.append({
                    'symbol': symbol,
                    'trade_id': f"T{i:06d}",
                    'price': Decimal(str(round(price, 2))),
                    'quantity': Decimal(str(quantity)),
                    'amount': Decimal(str(round(price * quantity, 2))),
                    'side': random.choice(['BUY', 'SELL']),
                    'is_buyer_maker': random.choice([True, False]),
                    'trade_time': datetime.now() - timedelta(seconds=i),
                    'data_provider': self.name
                })
            
            return trades
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取模拟成交数据失败: {e}")
            return []
    
    async def get_depth(self, symbol: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """获取模拟深度数据"""
        try:
            import random
            
            if symbol not in self.base_prices:
                return None
            
            base_price = self.base_prices[symbol]
            
            # 生成买盘数据
            bids = []
            for i in range(limit):
                price = base_price * (1 - (i + 1) * 0.001)  # 递减价格
                quantity = random.randint(100, 10000)
                bids.append([Decimal(str(round(price, 2))), Decimal(str(quantity))])
            
            # 生成卖盘数据
            asks = []
            for i in range(limit):
                price = base_price * (1 + (i + 1) * 0.001)  # 递增价格
                quantity = random.randint(100, 10000)
                asks.append([Decimal(str(round(price, 2))), Decimal(str(quantity))])
            
            return {
                'symbol': symbol,
                'bids': bids,
                'asks': asks,
                'snapshot_time': datetime.now(),
                'data_provider': self.name,
                'depth_level': limit
            }
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"获取模拟深度数据失败: {e}")
            return None
    
    async def subscribe_quotes(self, symbols: List[str]) -> AsyncGenerator[Dict[str, Any], None]:
        """订阅模拟报价"""
        while True:
            for symbol in symbols:
                if symbol in self.symbols:
                    quote = await self.get_quote(symbol)
                    if quote:
                        yield quote
            await asyncio.sleep(1)  # 1秒推送一次
    
    async def subscribe_trades(self, symbols: List[str]) -> AsyncGenerator[Dict[str, Any], None]:
        """订阅模拟成交数据"""
        while True:
            for symbol in symbols:
                if symbol in self.symbols:
                    trades = await self.get_trades(symbol, 1)
                    for trade in trades:
                        yield trade
            await asyncio.sleep(0.5)  # 0.5秒推送一次
    
    async def subscribe_depth(self, symbols: List[str]) -> AsyncGenerator[Dict[str, Any], None]:
        """订阅模拟深度数据"""
        while True:
            for symbol in symbols:
                if symbol in self.symbols:
                    depth = await self.get_depth(symbol)
                    if depth:
                        yield depth
            await asyncio.sleep(2)  # 2秒推送一次
    
    def get_supported_symbols(self) -> List[str]:
        """获取支持的标的列表"""
        return self.symbols
    
    def get_supported_intervals(self) -> List[str]:
        """获取支持的时间间隔"""
        return ['1m', '5m', '15m', '30m', '1h', '1d', '1w', '1M']
    
    def _get_interval_minutes(self, interval: str) -> int:
        """获取时间间隔对应的分钟数"""
        interval_map = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '1d': 1440, '1w': 10080, '1M': 43200
        }
        return interval_map.get(interval, 1)

class MarketDataAdapterFactory:
    """市场数据适配器工厂"""
    
    _adapters = {
        'yahoo_finance': YahooFinanceAdapter,
        'simulated': SimulatedAdapter,
    }
    
    @classmethod
    def create_adapter(cls, provider_name: str, config: Dict[str, Any]) -> MarketDataAdapter:
        """创建数据适配器"""
        adapter_class = cls._adapters.get(provider_name.lower())
        if not adapter_class:
            raise ValueError(f"不支持的数据提供商: {provider_name}")
        
        config['name'] = provider_name
        return adapter_class(config)
    
    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """获取支持的提供商列表"""
        return list(cls._adapters.keys())