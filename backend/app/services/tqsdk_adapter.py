"""
tqsdk适配器服务
"""
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import logging
import json
from contextlib import asynccontextmanager

try:
    from tqsdk import TqApi, TqAuth, TqSim, TqAccount
    from tqsdk.objs import Quote, Kline, Position, Order, Account
    TQSDK_AVAILABLE = True
except ImportError:
    TQSDK_AVAILABLE = False
    # 创建模拟类用于开发环境
    class TqApi:
        def __init__(self, *args, **kwargs):
            pass
    class TqAuth:
        def __init__(self, *args, **kwargs):
            pass
    class TqSim:
        def __init__(self, *args, **kwargs):
            pass
    class TqAccount:
        def __init__(self, *args, **kwargs):
            pass
    class Quote:
        pass
    class Kline:
        pass
    class Position:
        pass
    class Order:
        pass
    class Account:
        pass

from ..core.config import settings
from ..core.exceptions import ExternalServiceError, SystemError
from ..core.database import get_redis_client

logger = logging.getLogger(__name__)


class TQSDKAdapter:
    """tqsdk适配器类"""
    
    def __init__(self):
        self.api: Optional[TqApi] = None
        self.auth: Optional[TqAuth] = None
        self.account: Optional[TqAccount] = None
        self.is_connected = False
        self.is_sim_trading = True  # 默认使用模拟交易
        self.redis_client = get_redis_client()
        self.quote_callbacks: List[Callable] = []
        self.order_callbacks: List[Callable] = []
        self.position_callbacks: List[Callable] = []
        self._instruments_cache: Dict[str, Any] = {}
        self._quotes_cache: Dict[str, Quote] = {}
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_delay = 5  # 秒
        
        if not TQSDK_AVAILABLE:
            logger.warning("tqsdk未安装，使用模拟模式")
    
    async def initialize(
        self,
        auth_token: Optional[str] = None,
        account_id: Optional[str] = None,
        use_sim: bool = True
    ) -> bool:
        """初始化tqsdk连接"""
        try:
            if not TQSDK_AVAILABLE:
                logger.info("tqsdk不可用，初始化模拟适配器")
                self.is_connected = True
                return True
            
            # 设置认证
            if auth_token or settings.TQSDK_AUTH:
                self.auth = TqAuth(auth_token or settings.TQSDK_AUTH)
            
            # 设置账户
            if use_sim:
                self.account = TqSim()
                self.is_sim_trading = True
                logger.info("使用模拟交易账户")
            else:
                if account_id or settings.TQSDK_ACCOUNT:
                    self.account = TqAccount(account_id or settings.TQSDK_ACCOUNT)
                    self.is_sim_trading = False
                    logger.info(f"使用实盘交易账户: {account_id or settings.TQSDK_ACCOUNT}")
                else:
                    raise SystemError("实盘交易需要提供账户ID")
            
            # 创建API实例
            self.api = TqApi(
                account=self.account,
                auth=self.auth,
                web_gui=False,  # 不启用web界面
                debug=settings.DEBUG,
            )
            
            # 等待连接建立
            await asyncio.sleep(1)
            
            self.is_connected = True
            self._reconnect_attempts = 0
            
            logger.info("tqsdk连接初始化成功")
            
            # 启动监控任务
            asyncio.create_task(self._connection_monitor())
            
            return True
            
        except Exception as e:
            logger.error(f"tqsdk初始化失败: {e}")
            self.is_connected = False
            raise ExternalServiceError(f"tqsdk初始化失败: {str(e)}")
    
    async def close(self):
        """关闭连接"""
        try:
            if self.api and TQSDK_AVAILABLE:
                self.api.close()
            
            self.is_connected = False
            self.api = None
            
            logger.info("tqsdk连接已关闭")
            
        except Exception as e:
            logger.error(f"关闭tqsdk连接失败: {e}")
    
    async def _connection_monitor(self):
        """连接监控和自动重连"""
        while True:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次
                
                if not self.is_connected:
                    continue
                
                # 检查连接状态
                if not await self._check_connection():
                    logger.warning("tqsdk连接断开，尝试重连")
                    await self._reconnect()
                
            except Exception as e:
                logger.error(f"连接监控异常: {e}")
    
    async def _check_connection(self) -> bool:
        """检查连接状态"""
        try:
            if not self.api or not TQSDK_AVAILABLE:
                return self.is_connected
            
            # 尝试获取一个简单的数据来测试连接
            quote = self.api.get_quote("SHFE.cu2401")
            return quote is not None
            
        except Exception:
            return False
    
    async def _reconnect(self):
        """自动重连"""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.error("达到最大重连次数，停止重连")
            self.is_connected = False
            return
        
        try:
            self._reconnect_attempts += 1
            logger.info(f"尝试重连 ({self._reconnect_attempts}/{self._max_reconnect_attempts})")
            
            # 关闭现有连接
            if self.api:
                self.api.close()
            
            # 等待一段时间后重连
            await asyncio.sleep(self._reconnect_delay)
            
            # 重新初始化
            await self.initialize(
                auth_token=settings.TQSDK_AUTH,
                account_id=settings.TQSDK_ACCOUNT,
                use_sim=self.is_sim_trading
            )
            
            logger.info("重连成功")
            
        except Exception as e:
            logger.error(f"重连失败: {e}")
            # 指数退避
            self._reconnect_delay = min(self._reconnect_delay * 2, 300)
    
    def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            "is_connected": self.is_connected,
            "is_sim_trading": self.is_sim_trading,
            "reconnect_attempts": self._reconnect_attempts,
            "tqsdk_available": TQSDK_AVAILABLE,
        }
    
    async def get_instruments(self, exchange: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取合约信息"""
        try:
            # 检查缓存
            cache_key = f"instruments:{exchange or 'all'}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            
            if not self.is_connected or not TQSDK_AVAILABLE:
                # 返回模拟数据
                mock_instruments = self._get_mock_instruments(exchange)
                # 缓存5分钟
                self.redis_client.setex(cache_key, 300, json.dumps(mock_instruments))
                return mock_instruments
            
            # 从tqsdk获取合约信息
            instruments = []
            
            # 主要交易所列表
            exchanges = [exchange] if exchange else [
                "SHFE", "DCE", "CZCE", "INE", "CFFEX"
            ]
            
            for exch in exchanges:
                try:
                    # 获取交易所的所有合约
                    exch_instruments = self.api.query_quotes(
                        ins_class="FUTURE",
                        exchange_id=exch
                    )
                    
                    for symbol in exch_instruments:
                        quote = self.api.get_quote(symbol)
                        if quote:
                            instrument_info = {
                                "symbol": symbol,
                                "exchange": exch,
                                "name": getattr(quote, 'instrument_name', symbol),
                                "product_id": getattr(quote, 'product_id', ''),
                                "volume_multiple": getattr(quote, 'volume_multiple', 1),
                                "price_tick": getattr(quote, 'price_tick', 0.01),
                                "margin_rate": getattr(quote, 'margin_rate', 0.1),
                                "commission_rate": getattr(quote, 'commission_rate', 0.0001),
                                "expired": getattr(quote, 'expired', False),
                                "trading_time": getattr(quote, 'trading_time', {}),
                            }
                            instruments.append(instrument_info)
                
                except Exception as e:
                    logger.warning(f"获取{exch}合约信息失败: {e}")
                    continue
            
            # 缓存5分钟
            self.redis_client.setex(cache_key, 300, json.dumps(instruments))
            
            logger.info(f"获取到{len(instruments)}个合约信息")
            return instruments
            
        except Exception as e:
            logger.error(f"获取合约信息失败: {e}")
            raise ExternalServiceError(f"获取合约信息失败: {str(e)}")
    
    def _get_mock_instruments(self, exchange: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取模拟合约信息"""
        mock_data = [
            {
                "symbol": "SHFE.cu2601",
                "exchange": "SHFE",
                "name": "沪铜2601",
                "product_id": "cu",
                "volume_multiple": 5,
                "price_tick": 10,
                "margin_rate": 0.08,
                "commission_rate": 0.0001,
                "expired": False,
                "trading_time": {"day": [["09:00:00", "10:15:00"], ["10:30:00", "11:30:00"]]},
            },
            {
                "symbol": "DCE.i2601",
                "exchange": "DCE",
                "name": "铁矿石2601",
                "product_id": "i",
                "volume_multiple": 100,
                "price_tick": 0.5,
                "margin_rate": 0.1,
                "commission_rate": 0.0001,
                "expired": False,
                "trading_time": {"day": [["09:00:00", "10:15:00"], ["10:30:00", "11:30:00"]]},
            },
            {
                "symbol": "CZCE.MA601",
                "exchange": "CZCE",
                "name": "甲醇601",
                "product_id": "MA",
                "volume_multiple": 10,
                "price_tick": 1,
                "margin_rate": 0.07,
                "commission_rate": 0.0001,
                "expired": False,
                "trading_time": {"day": [["09:00:00", "10:15:00"], ["10:30:00", "11:30:00"]]},
            },
        ]
        
        if exchange:
            return [item for item in mock_data if item["exchange"] == exchange]
        
        return mock_data
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取实时行情"""
        try:
            if not self.is_connected or not TQSDK_AVAILABLE:
                # 返回模拟行情数据
                return self._get_mock_quote(symbol)
            
            quote = self.api.get_quote(symbol)
            if not quote:
                return None
            
            quote_data = {
                "symbol": symbol,
                "last_price": getattr(quote, 'last_price', 0),
                "bid_price": getattr(quote, 'bid_price1', 0),
                "ask_price": getattr(quote, 'ask_price1', 0),
                "bid_volume": getattr(quote, 'bid_volume1', 0),
                "ask_volume": getattr(quote, 'ask_volume1', 0),
                "volume": getattr(quote, 'volume', 0),
                "open_interest": getattr(quote, 'open_interest', 0),
                "open": getattr(quote, 'open', 0),
                "high": getattr(quote, 'highest', 0),
                "low": getattr(quote, 'lowest', 0),
                "pre_close": getattr(quote, 'pre_close', 0),
                "upper_limit": getattr(quote, 'upper_limit', 0),
                "lower_limit": getattr(quote, 'lower_limit', 0),
                "datetime": getattr(quote, 'datetime', datetime.now().isoformat()),
            }
            
            # 缓存行情数据
            self._quotes_cache[symbol] = quote
            
            return quote_data
            
        except Exception as e:
            logger.error(f"获取行情失败 {symbol}: {e}")
            return None
    
    def _get_mock_quote(self, symbol: str) -> Dict[str, Any]:
        """获取模拟行情数据"""
        import random
        
        # 根据2025年8月的价格水平调整基础价格
        if "cu" in symbol:
            base_price = 75000  # 沪铜当前价格水平
        elif "i" in symbol:
            base_price = 800    # 铁矿石当前价格水平
        elif "MA" in symbol:
            base_price = 2500   # 甲醇当前价格水平
        elif "rb" in symbol:
            base_price = 3500   # 螺纹钢当前价格水平
        elif "c" in symbol:
            base_price = 2800   # 玉米当前价格水平
        else:
            base_price = 3000   # 默认价格
            
        price = base_price + random.uniform(-base_price * 0.05, base_price * 0.05)
        
        return {
            "symbol": symbol,
            "last_price": round(price, 2),
            "bid_price": round(price - 1, 2),
            "ask_price": round(price + 1, 2),
            "bid_volume": random.randint(1, 100),
            "ask_volume": random.randint(1, 100),
            "volume": random.randint(1000, 10000),
            "open_interest": random.randint(10000, 100000),
            "open": round(price * 0.99, 2),
            "high": round(price * 1.02, 2),
            "low": round(price * 0.98, 2),
            "pre_close": round(price * 0.995, 2),
            "upper_limit": round(price * 1.1, 2),
            "lower_limit": round(price * 0.9, 2),
            "datetime": datetime.now().isoformat(),
        }
    
    async def get_klines(
        self,
        symbol: str,
        duration: int = 60,
        data_length: int = 200
    ) -> List[Dict[str, Any]]:
        """获取K线数据"""
        try:
            if not self.is_connected or not TQSDK_AVAILABLE:
                # 返回模拟K线数据
                return self._get_mock_klines(symbol, duration, data_length)
            
            klines = self.api.get_kline_serial(
                symbol,
                duration_seconds=duration,
                data_length=data_length
            )
            
            if klines is None:
                return []
            
            kline_data = []
            for i in range(len(klines)):
                kline_data.append({
                    "datetime": klines.iloc[i]['datetime'],
                    "open": klines.iloc[i]['open'],
                    "high": klines.iloc[i]['high'],
                    "low": klines.iloc[i]['low'],
                    "close": klines.iloc[i]['close'],
                    "volume": klines.iloc[i]['volume'],
                    "open_interest": klines.iloc[i].get('open_oi', 0),
                })
            
            return kline_data
            
        except Exception as e:
            logger.error(f"获取K线数据失败 {symbol}: {e}")
            return []
    
    def _get_mock_klines(
        self,
        symbol: str,
        duration: int,
        data_length: int
    ) -> List[Dict[str, Any]]:
        """获取模拟K线数据"""
        import random
        
        # 根据2025年8月的价格水平调整基础价格
        if "cu" in symbol:
            base_price = 75000  # 沪铜当前价格水平
        elif "i" in symbol:
            base_price = 800    # 铁矿石当前价格水平
        elif "MA" in symbol:
            base_price = 2500   # 甲醇当前价格水平
        elif "rb" in symbol:
            base_price = 3500   # 螺纹钢当前价格水平
        elif "c" in symbol:
            base_price = 2800   # 玉米当前价格水平
        else:
            base_price = 3000   # 默认价格
            
        klines = []
        
        current_time = datetime.now()
        price = base_price
        
        for i in range(data_length):
            # 生成随机价格变动
            change = random.uniform(-price * 0.02, price * 0.02)
            new_price = max(price + change, price * 0.9)
            
            open_price = price
            close_price = new_price
            high_price = max(open_price, close_price) * random.uniform(1.0, 1.01)
            low_price = min(open_price, close_price) * random.uniform(0.99, 1.0)
            
            klines.append({
                "datetime": (current_time - timedelta(seconds=duration * (data_length - i - 1))).isoformat(),
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": random.randint(100, 1000),
                "open_interest": random.randint(1000, 10000),
            })
            
            price = new_price
        
        return klines
    
    def add_quote_callback(self, callback: Callable):
        """添加行情回调函数"""
        self.quote_callbacks.append(callback)
    
    def remove_quote_callback(self, callback: Callable):
        """移除行情回调函数"""
        if callback in self.quote_callbacks:
            self.quote_callbacks.remove(callback)
    
    async def subscribe_quotes(self, symbols: List[str]):
        """订阅行情"""
        try:
            if not self.is_connected or not TQSDK_AVAILABLE:
                logger.info(f"模拟订阅行情: {symbols}")
                return
            
            for symbol in symbols:
                quote = self.api.get_quote(symbol)
                if quote:
                    self._quotes_cache[symbol] = quote
            
            logger.info(f"订阅行情成功: {symbols}")
            
        except Exception as e:
            logger.error(f"订阅行情失败: {e}")
            raise ExternalServiceError(f"订阅行情失败: {str(e)}")
    
    async def unsubscribe_quotes(self, symbols: List[str]):
        """取消订阅行情"""
        try:
            for symbol in symbols:
                if symbol in self._quotes_cache:
                    del self._quotes_cache[symbol]
            
            logger.info(f"取消订阅行情: {symbols}")
            
        except Exception as e:
            logger.error(f"取消订阅行情失败: {e}")


# 创建全局tqsdk适配器实例
tqsdk_adapter = TQSDKAdapter()