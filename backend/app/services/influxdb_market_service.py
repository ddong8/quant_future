"""
InfluxDB 市场数据服务
负责将实时市场数据存储到时序数据库
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import logging

from ..core.influxdb import influx_manager
from ..core.config import settings
from ..schemas.market import QuoteData, KlineData

logger = logging.getLogger(__name__)


class InfluxDBMarketService:
    """InfluxDB 市场数据服务"""
    
    def __init__(self):
        self.influx_manager = influx_manager
        self.batch_size = 100
        self.batch_timeout = 5  # 秒
        self._quote_batch = []
        self._kline_batch = []
        self._last_flush_time = datetime.utcnow()
    
    async def store_quote(self, symbol: str, quote_data: Dict[str, Any]) -> bool:
        """存储单个行情数据"""
        try:
            # 验证数据
            if not self._validate_quote_data(quote_data):
                logger.warning(f"行情数据验证失败: {symbol}")
                return False
            
            # 添加到批处理队列
            self._quote_batch.append({
                'symbol': symbol,
                'data': quote_data,
                'timestamp': datetime.utcnow()
            })
            
            # 检查是否需要刷新批处理
            await self._check_and_flush_quotes()
            
            return True
            
        except Exception as e:
            logger.error(f"存储行情数据失败 {symbol}: {e}")
            return False
    
    async def store_kline(self, symbol: str, kline_data: Dict[str, Any], period: str = "1m") -> bool:
        """存储单个K线数据"""
        try:
            # 验证数据
            if not self._validate_kline_data(kline_data):
                logger.warning(f"K线数据验证失败: {symbol}")
                return False
            
            # 添加到批处理队列
            self._kline_batch.append({
                'symbol': symbol,
                'period': period,
                'data': kline_data,
                'timestamp': datetime.utcnow()
            })
            
            # 检查是否需要刷新批处理
            await self._check_and_flush_klines()
            
            return True
            
        except Exception as e:
            logger.error(f"存储K线数据失败 {symbol}: {e}")
            return False
    
    async def store_quotes_batch(self, quotes: List[Dict[str, Any]]) -> int:
        """批量存储行情数据"""
        success_count = 0
        
        try:
            from influxdb_client import Point, WritePrecision
            
            points = []
            for quote in quotes:
                try:
                    symbol = quote.get('symbol')
                    data = quote.get('data', {})
                    
                    if not symbol or not self._validate_quote_data(data):
                        continue
                    
                    point = (
                        Point("quotes")
                        .tag("symbol", symbol)
                        .tag("exchange", data.get("exchange", "unknown"))
                        .field("last_price", float(data.get("last_price", 0)))
                        .field("bid_price", float(data.get("bid_price", 0)))
                        .field("ask_price", float(data.get("ask_price", 0)))
                        .field("bid_volume", int(data.get("bid_volume", 0)))
                        .field("ask_volume", int(data.get("ask_volume", 0)))
                        .field("volume", int(data.get("volume", 0)))
                        .field("open_interest", int(data.get("open_interest", 0)))
                        .field("open", float(data.get("open", 0)))
                        .field("high", float(data.get("high", 0)))
                        .field("low", float(data.get("low", 0)))
                        .field("pre_close", float(data.get("pre_close", 0)))
                        .field("change", float(data.get("change", 0)))
                        .field("change_percent", float(data.get("change_percent", 0)))
                        .time(data.get("datetime", datetime.utcnow()), WritePrecision.MS)
                    )
                    
                    points.append(point)
                    success_count += 1
                    
                except Exception as e:
                    logger.warning(f"处理行情数据失败 {quote.get('symbol')}: {e}")
                    continue
            
            if points:
                # 写入InfluxDB
                await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self.influx_manager.write_api.write(
                        bucket=settings.INFLUXDB_BUCKET, 
                        record=points
                    )
                )
                
                logger.info(f"批量存储行情数据成功: {len(points)}条")
            
        except Exception as e:
            logger.error(f"批量存储行情数据失败: {e}")
        
        return success_count
    
    async def store_klines_batch(self, klines: List[Dict[str, Any]]) -> int:
        """批量存储K线数据"""
        success_count = 0
        
        try:
            from influxdb_client import Point, WritePrecision
            
            points = []
            for kline in klines:
                try:
                    symbol = kline.get('symbol')
                    period = kline.get('period', '1m')
                    data = kline.get('data', {})
                    
                    if not symbol or not self._validate_kline_data(data):
                        continue
                    
                    point = (
                        Point("klines")
                        .tag("symbol", symbol)
                        .tag("period", period)
                        .tag("exchange", data.get("exchange", "unknown"))
                        .field("open", float(data.get("open", 0)))
                        .field("high", float(data.get("high", 0)))
                        .field("low", float(data.get("low", 0)))
                        .field("close", float(data.get("close", 0)))
                        .field("volume", int(data.get("volume", 0)))
                        .field("open_interest", int(data.get("open_interest", 0)))
                        .time(data.get("datetime", datetime.utcnow()), WritePrecision.MS)
                    )
                    
                    points.append(point)
                    success_count += 1
                    
                except Exception as e:
                    logger.warning(f"处理K线数据失败 {kline.get('symbol')}: {e}")
                    continue
            
            if points:
                # 写入InfluxDB
                await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self.influx_manager.write_api.write(
                        bucket=settings.INFLUXDB_BUCKET, 
                        record=points
                    )
                )
                
                logger.info(f"批量存储K线数据成功: {len(points)}条")
            
        except Exception as e:
            logger.error(f"批量存储K线数据失败: {e}")
        
        return success_count
    
    async def query_quotes(
        self,
        symbol: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """查询行情数据"""
        try:
            if not end_time:
                end_time = datetime.utcnow()
            
            # 构建查询
            query = f'''
                from(bucket: "{settings.INFLUXDB_BUCKET}")
                |> range(start: {int(start_time.timestamp())}s, stop: {int(end_time.timestamp())}s)
                |> filter(fn: (r) => r._measurement == "quotes")
                |> filter(fn: (r) => r.symbol == "{symbol}")
                |> limit(n: {limit})
                |> sort(columns: ["_time"])
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            # 执行查询
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.influx_manager.query_api.query(query)
            )
            
            quotes = []
            for table in result:
                for record in table.records:
                    quote = {
                        "symbol": record.values.get("symbol"),
                        "exchange": record.values.get("exchange"),
                        "datetime": record.get_time(),
                        "last_price": record.values.get("last_price"),
                        "bid_price": record.values.get("bid_price"),
                        "ask_price": record.values.get("ask_price"),
                        "volume": record.values.get("volume"),
                        "open_interest": record.values.get("open_interest"),
                        "open": record.values.get("open"),
                        "high": record.values.get("high"),
                        "low": record.values.get("low"),
                        "pre_close": record.values.get("pre_close"),
                        "change": record.values.get("change"),
                        "change_percent": record.values.get("change_percent"),
                    }
                    quotes.append(quote)
            
            logger.info(f"查询行情数据成功 {symbol}: {len(quotes)}条")
            return quotes
            
        except Exception as e:
            logger.error(f"查询行情数据失败 {symbol}: {e}")
            return []
    
    async def query_klines(
        self,
        symbol: str,
        period: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """查询K线数据"""
        try:
            if not end_time:
                end_time = datetime.utcnow()
            
            # 构建查询
            query = f'''
                from(bucket: "{settings.INFLUXDB_BUCKET}")
                |> range(start: {int(start_time.timestamp())}s, stop: {int(end_time.timestamp())}s)
                |> filter(fn: (r) => r._measurement == "klines")
                |> filter(fn: (r) => r.symbol == "{symbol}")
                |> filter(fn: (r) => r.period == "{period}")
                |> limit(n: {limit})
                |> sort(columns: ["_time"])
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            # 执行查询
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.influx_manager.query_api.query(query)
            )
            
            klines = []
            for table in result:
                for record in table.records:
                    kline = {
                        "symbol": record.values.get("symbol"),
                        "period": record.values.get("period"),
                        "exchange": record.values.get("exchange"),
                        "datetime": record.get_time(),
                        "open": record.values.get("open"),
                        "high": record.values.get("high"),
                        "low": record.values.get("low"),
                        "close": record.values.get("close"),
                        "volume": record.values.get("volume"),
                        "open_interest": record.values.get("open_interest"),
                    }
                    klines.append(kline)
            
            logger.info(f"查询K线数据成功 {symbol} {period}: {len(klines)}条")
            return klines
            
        except Exception as e:
            logger.error(f"查询K线数据失败 {symbol} {period}: {e}")
            return []
    
    async def get_latest_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取最新行情"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)  # 查询最近1小时
            
            quotes = await self.query_quotes(symbol, start_time, end_time, limit=1)
            return quotes[0] if quotes else None
            
        except Exception as e:
            logger.error(f"获取最新行情失败 {symbol}: {e}")
            return None
    
    async def _check_and_flush_quotes(self):
        """检查并刷新行情批处理"""
        now = datetime.utcnow()
        
        # 检查批处理大小或时间间隔
        if (len(self._quote_batch) >= self.batch_size or 
            (now - self._last_flush_time).seconds >= self.batch_timeout):
            
            if self._quote_batch:
                await self.store_quotes_batch(self._quote_batch)
                self._quote_batch.clear()
                self._last_flush_time = now
    
    async def _check_and_flush_klines(self):
        """检查并刷新K线批处理"""
        now = datetime.utcnow()
        
        # 检查批处理大小或时间间隔
        if (len(self._kline_batch) >= self.batch_size or 
            (now - self._last_flush_time).seconds >= self.batch_timeout):
            
            if self._kline_batch:
                await self.store_klines_batch(self._kline_batch)
                self._kline_batch.clear()
                self._last_flush_time = now
    
    def _validate_quote_data(self, data: Dict[str, Any]) -> bool:
        """验证行情数据"""
        required_fields = ['last_price']
        return all(field in data for field in required_fields)
    
    def _validate_kline_data(self, data: Dict[str, Any]) -> bool:
        """验证K线数据"""
        required_fields = ['open', 'high', 'low', 'close']
        return all(field in data for field in required_fields)
    
    async def flush_all_batches(self):
        """刷新所有批处理数据"""
        try:
            if self._quote_batch:
                await self.store_quotes_batch(self._quote_batch)
                self._quote_batch.clear()
            
            if self._kline_batch:
                await self.store_klines_batch(self._kline_batch)
                self._kline_batch.clear()
            
            self._last_flush_time = datetime.utcnow()
            logger.info("所有批处理数据已刷新")
            
        except Exception as e:
            logger.error(f"刷新批处理数据失败: {e}")


# 创建全局实例
influxdb_market_service = InfluxDBMarketService()