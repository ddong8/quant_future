"""
历史数据查询服务
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import logging
import json
import pandas as pd
from sqlalchemy.orm import Session

from ..core.database import get_redis_client
from ..core.influxdb import influx_manager
from ..core.exceptions import ValidationError, ExternalServiceError
from ..core.dependencies import PaginationParams
from ..services.tqsdk_adapter import tqsdk_adapter
from ..schemas.market import KlineData, QuoteData

logger = logging.getLogger(__name__)


class HistoryService:
    """历史数据查询服务"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        
        # 缓存配置
        self.kline_cache_ttl = {
            60: 300,      # 1分钟K线缓存5分钟
            300: 900,     # 5分钟K线缓存15分钟
            900: 1800,    # 15分钟K线缓存30分钟
            1800: 3600,   # 30分钟K线缓存1小时
            3600: 7200,   # 1小时K线缓存2小时
            86400: 14400, # 日K线缓存4小时
        }
        
        # 支持的时间周期（秒）
        self.supported_periods = [60, 300, 900, 1800, 3600, 86400]
        
        # 时间周期转换映射
        self.period_names = {
            60: "1m",
            300: "5m", 
            900: "15m",
            1800: "30m",
            3600: "1h",
            86400: "1d",
        }
    
    async def get_klines(
        self,
        symbol: str,
        period: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[KlineData]:
        """获取K线数据"""
        try:
            # 验证参数
            if period not in self.supported_periods:
                raise ValidationError(f"不支持的时间周期: {period}秒")
            
            if limit > 8000:
                raise ValidationError("数据长度不能超过8000")
            
            # 设置默认时间范围
            if not end_time:
                end_time = datetime.now()
            
            if not start_time:
                start_time = end_time - timedelta(seconds=period * limit)
            
            # 检查缓存
            cache_key = self._get_kline_cache_key(symbol, period, start_time, end_time, limit)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                logger.info(f"从缓存获取K线数据: {symbol} {self.period_names[period]}")
                klines_data = json.loads(cached_data)
                return [KlineData(**kline) for kline in klines_data]
            
            # 从InfluxDB查询历史数据
            klines = await self._query_klines_from_influx(
                symbol, period, start_time, end_time, limit
            )
            
            # 如果InfluxDB没有数据，从tqsdk获取
            if not klines:
                klines = await self._query_klines_from_tqsdk(
                    symbol, period, start_time, end_time, limit
                )
            
            # 缓存数据
            if klines:
                cache_ttl = self.kline_cache_ttl.get(period, 300)
                klines_data = [kline.dict() for kline in klines]
                self.redis_client.setex(cache_key, cache_ttl, json.dumps(klines_data, default=str))
            
            logger.info(f"获取K线数据成功: {symbol} {self.period_names[period]} {len(klines)}条")
            return klines
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            raise ExternalServiceError(f"获取K线数据失败: {str(e)}")
    
    async def get_quotes_history(
        self,
        symbol: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[QuoteData]:
        """获取历史行情数据"""
        try:
            if not end_time:
                end_time = datetime.now()
            
            # 检查缓存
            cache_key = f"quotes_history:{symbol}:{start_time.isoformat()}:{end_time.isoformat()}:{limit}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                logger.info(f"从缓存获取历史行情: {symbol}")
                quotes_data = json.loads(cached_data)
                return [QuoteData(**quote) for quote in quotes_data]
            
            # 从InfluxDB查询
            quotes = await self._query_quotes_from_influx(symbol, start_time, end_time, limit)
            
            # 缓存数据（缓存10分钟）
            if quotes:
                quotes_data = [quote.dict() for quote in quotes]
                self.redis_client.setex(cache_key, 600, json.dumps(quotes_data, default=str))
            
            logger.info(f"获取历史行情成功: {symbol} {len(quotes)}条")
            return quotes
            
        except Exception as e:
            logger.error(f"获取历史行情失败: {e}")
            raise ExternalServiceError(f"获取历史行情失败: {str(e)}")
    
    async def get_klines_paginated(
        self,
        symbol: str,
        period: int,
        pagination: PaginationParams,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Tuple[List[KlineData], int]:
        """分页获取K线数据"""
        try:
            # 先获取总数
            total_count = await self._count_klines(symbol, period, start_time, end_time)
            
            # 计算偏移量对应的时间
            if not end_time:
                end_time = datetime.now()
            
            # 根据分页参数调整查询范围
            skip_seconds = pagination.offset * period
            query_end_time = end_time - timedelta(seconds=skip_seconds)
            query_start_time = query_end_time - timedelta(seconds=pagination.page_size * period)
            
            if start_time and query_start_time < start_time:
                query_start_time = start_time
            
            # 获取数据
            klines = await self.get_klines(
                symbol, period, query_start_time, query_end_time, pagination.page_size
            )
            
            # 按时间倒序排列（最新的在前面）
            klines.sort(key=lambda x: x.datetime, reverse=True)
            
            return klines, total_count
            
        except Exception as e:
            logger.error(f"分页获取K线数据失败: {e}")
            raise ExternalServiceError(f"分页获取K线数据失败: {str(e)}")
    
    async def convert_kline_period(
        self,
        symbol: str,
        source_period: int,
        target_period: int,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[KlineData]:
        """转换K线时间周期"""
        try:
            if target_period <= source_period:
                raise ValidationError("目标周期必须大于源周期")
            
            if target_period % source_period != 0:
                raise ValidationError("目标周期必须是源周期的整数倍")
            
            # 获取源数据
            source_klines = await self.get_klines(
                symbol, source_period, start_time, end_time, limit * (target_period // source_period)
            )
            
            if not source_klines:
                return []
            
            # 转换数据
            converted_klines = self._aggregate_klines(source_klines, target_period)
            
            logger.info(f"K线周期转换成功: {symbol} {source_period}s -> {target_period}s")
            return converted_klines[:limit]
            
        except Exception as e:
            logger.error(f"K线周期转换失败: {e}")
            raise ExternalServiceError(f"K线周期转换失败: {str(e)}")
    
    async def get_market_summary(
        self,
        symbols: List[str],
        period: int = 86400
    ) -> Dict[str, Dict[str, Any]]:
        """获取市场概况"""
        try:
            summary = {}
            
            # 并发获取各合约的最新K线数据
            tasks = []
            for symbol in symbols:
                task = self.get_klines(symbol, period, limit=2)  # 获取最近2根K线
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for symbol, result in zip(symbols, results):
                if isinstance(result, Exception):
                    logger.warning(f"获取{symbol}数据失败: {result}")
                    continue
                
                if not result or len(result) < 1:
                    continue
                
                latest_kline = result[0]
                prev_kline = result[1] if len(result) > 1 else None
                
                # 计算涨跌幅
                change = 0
                change_rate = 0
                if prev_kline:
                    change = latest_kline.close - prev_kline.close
                    change_rate = (change / prev_kline.close) * 100 if prev_kline.close > 0 else 0
                
                summary[symbol] = {
                    "symbol": symbol,
                    "close": latest_kline.close,
                    "open": latest_kline.open,
                    "high": latest_kline.high,
                    "low": latest_kline.low,
                    "volume": latest_kline.volume,
                    "change": change,
                    "change_rate": change_rate,
                    "datetime": latest_kline.datetime,
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"获取市场概况失败: {e}")
            raise ExternalServiceError(f"获取市场概况失败: {str(e)}")
    
    async def _query_klines_from_influx(
        self,
        symbol: str,
        period: int,
        start_time: datetime,
        end_time: datetime,
        limit: int
    ) -> List[KlineData]:
        """从InfluxDB查询K线数据"""
        try:
            period_str = f"{period}s"
            klines_data = influx_manager.query_klines(
                symbol, period_str, start_time, end_time, limit
            )
            
            klines = []
            for data in klines_data:
                if all(key in data for key in ['datetime', 'open', 'high', 'low', 'close', 'volume']):
                    kline = KlineData(
                        datetime=data['datetime'],
                        open=data['open'],
                        high=data['high'],
                        low=data['low'],
                        close=data['close'],
                        volume=data['volume'],
                        open_interest=data.get('open_interest', 0)
                    )
                    klines.append(kline)
            
            return klines
            
        except Exception as e:
            logger.warning(f"从InfluxDB查询K线数据失败: {e}")
            return []
    
    async def _query_klines_from_tqsdk(
        self,
        symbol: str,
        period: int,
        start_time: datetime,
        end_time: datetime,
        limit: int
    ) -> List[KlineData]:
        """从tqsdk查询K线数据"""
        try:
            # 计算需要的数据长度
            duration_seconds = int((end_time - start_time).total_seconds())
            data_length = min(duration_seconds // period, limit)
            
            klines_data = await tqsdk_adapter.get_klines(symbol, period, data_length)
            
            klines = []
            for data in klines_data:
                kline_time = datetime.fromisoformat(data['datetime'].replace('Z', '+00:00'))
                
                # 过滤时间范围
                if start_time <= kline_time <= end_time:
                    kline = KlineData(**data)
                    klines.append(kline)
            
            return klines
            
        except Exception as e:
            logger.warning(f"从tqsdk查询K线数据失败: {e}")
            return []
    
    async def _query_quotes_from_influx(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        limit: int
    ) -> List[QuoteData]:
        """从InfluxDB查询行情数据"""
        try:
            quotes_data = influx_manager.query_quotes(symbol, start_time, end_time, limit)
            
            quotes = []
            for data in quotes_data:
                if 'symbol' in data and 'last_price' in data:
                    quote = QuoteData(
                        symbol=data['symbol'],
                        last_price=data.get('last_price', 0),
                        bid_price=data.get('bid_price', 0),
                        ask_price=data.get('ask_price', 0),
                        bid_volume=data.get('bid_volume', 0),
                        ask_volume=data.get('ask_volume', 0),
                        volume=data.get('volume', 0),
                        open_interest=data.get('open_interest', 0),
                        open=data.get('open', 0),
                        high=data.get('high', 0),
                        low=data.get('low', 0),
                        pre_close=data.get('pre_close', 0),
                        upper_limit=data.get('upper_limit', 0),
                        lower_limit=data.get('lower_limit', 0),
                        datetime=data.get('datetime', datetime.now().isoformat())
                    )
                    quotes.append(quote)
            
            return quotes
            
        except Exception as e:
            logger.warning(f"从InfluxDB查询行情数据失败: {e}")
            return []
    
    async def _count_klines(
        self,
        symbol: str,
        period: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """统计K线数据数量"""
        try:
            if not end_time:
                end_time = datetime.now()
            
            if not start_time:
                # 默认查询最近30天
                start_time = end_time - timedelta(days=30)
            
            # 简化计算：根据时间范围估算数量
            duration_seconds = int((end_time - start_time).total_seconds())
            estimated_count = duration_seconds // period
            
            return min(estimated_count, 8000)  # 限制最大数量
            
        except Exception as e:
            logger.warning(f"统计K线数据数量失败: {e}")
            return 0
    
    def _aggregate_klines(self, source_klines: List[KlineData], target_period: int) -> List[KlineData]:
        """聚合K线数据到更大的时间周期"""
        if not source_klines:
            return []
        
        # 转换为DataFrame便于处理
        data = []
        for kline in source_klines:
            data.append({
                'datetime': datetime.fromisoformat(kline.datetime.replace('Z', '+00:00')),
                'open': kline.open,
                'high': kline.high,
                'low': kline.low,
                'close': kline.close,
                'volume': kline.volume,
                'open_interest': kline.open_interest,
            })
        
        df = pd.DataFrame(data)
        df.set_index('datetime', inplace=True)
        
        # 按目标周期重采样
        period_str = f"{target_period}S"
        
        aggregated = df.resample(period_str).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'open_interest': 'last',
        }).dropna()
        
        # 转换回KlineData对象
        result = []
        for timestamp, row in aggregated.iterrows():
            kline = KlineData(
                datetime=timestamp.isoformat(),
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=int(row['volume']),
                open_interest=int(row['open_interest']),
            )
            result.append(kline)
        
        return result
    
    def _get_kline_cache_key(
        self,
        symbol: str,
        period: int,
        start_time: datetime,
        end_time: datetime,
        limit: int
    ) -> str:
        """生成K线缓存键"""
        return f"klines:{symbol}:{period}:{start_time.isoformat()}:{end_time.isoformat()}:{limit}"
    
    def clear_cache(self, symbol: Optional[str] = None):
        """清理缓存"""
        try:
            if symbol:
                # 清理指定合约的缓存
                pattern = f"klines:{symbol}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"清理{symbol}的K线缓存: {len(keys)}个键")
            else:
                # 清理所有K线缓存
                pattern = "klines:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"清理所有K线缓存: {len(keys)}个键")
        
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")


# 创建全局历史数据服务实例
history_service = HistoryService()