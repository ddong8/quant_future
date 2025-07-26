"""
InfluxDB时序数据库操作工具
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import logging

from .config import settings

logger = logging.getLogger(__name__)


class InfluxDBManager:
    """InfluxDB管理器"""
    
    def __init__(self):
        self.client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG,
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        self.bucket = settings.INFLUXDB_BUCKET
    
    def write_quote(self, symbol: str, quote_data: Dict[str, Any]) -> bool:
        """写入行情数据"""
        try:
            point = (
                Point("quotes")
                .tag("symbol", symbol)
                .field("last_price", float(quote_data.get("last_price", 0)))
                .field("bid_price", float(quote_data.get("bid_price", 0)))
                .field("ask_price", float(quote_data.get("ask_price", 0)))
                .field("volume", int(quote_data.get("volume", 0)))
                .field("open_interest", int(quote_data.get("open_interest", 0)))
                .time(quote_data.get("timestamp", datetime.utcnow()), WritePrecision.MS)
            )
            
            self.write_api.write(bucket=self.bucket, record=point)
            return True
        except Exception as e:
            logger.error(f"写入行情数据失败: {e}")
            return False
    
    def write_kline(self, symbol: str, kline_data: Dict[str, Any]) -> bool:
        """写入K线数据"""
        try:
            point = (
                Point("klines")
                .tag("symbol", symbol)
                .tag("period", kline_data.get("period", "1m"))
                .field("open", float(kline_data.get("open", 0)))
                .field("high", float(kline_data.get("high", 0)))
                .field("low", float(kline_data.get("low", 0)))
                .field("close", float(kline_data.get("close", 0)))
                .field("volume", int(kline_data.get("volume", 0)))
                .time(kline_data.get("datetime", datetime.utcnow()), WritePrecision.MS)
            )
            
            self.write_api.write(bucket=self.bucket, record=point)
            return True
        except Exception as e:
            logger.error(f"写入K线数据失败: {e}")
            return False
    
    def write_trade_record(self, trade_data: Dict[str, Any]) -> bool:
        """写入交易记录"""
        try:
            point = (
                Point("trades")
                .tag("symbol", trade_data.get("symbol"))
                .tag("strategy_id", str(trade_data.get("strategy_id")))
                .tag("direction", trade_data.get("direction"))
                .field("price", float(trade_data.get("price", 0)))
                .field("volume", int(trade_data.get("volume", 0)))
                .field("amount", float(trade_data.get("amount", 0)))
                .field("commission", float(trade_data.get("commission", 0)))
                .time(trade_data.get("timestamp", datetime.utcnow()), WritePrecision.MS)
            )
            
            self.write_api.write(bucket=self.bucket, record=point)
            return True
        except Exception as e:
            logger.error(f"写入交易记录失败: {e}")
            return False
    
    def query_quotes(
        self,
        symbol: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """查询行情数据"""
        try:
            time_filter = f'time >= {int(start_time.timestamp())}s'
            if end_time:
                time_filter += f' and time <= {int(end_time.timestamp())}s'
            
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: {int(start_time.timestamp())}s{f', stop: {int(end_time.timestamp())}s' if end_time else ''})
                |> filter(fn: (r) => r._measurement == "quotes")
                |> filter(fn: (r) => r.symbol == "{symbol}")
                |> limit(n: {limit})
                |> sort(columns: ["_time"])
            '''
            
            result = self.query_api.query(query)
            
            quotes = []
            for table in result:
                for record in table.records:
                    quote = {
                        "symbol": record.values.get("symbol"),
                        "timestamp": record.get_time(),
                        record.get_field(): record.get_value()
                    }
                    quotes.append(quote)
            
            return quotes
        except Exception as e:
            logger.error(f"查询行情数据失败: {e}")
            return []
    
    def query_klines(
        self,
        symbol: str,
        period: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """查询K线数据"""
        try:
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: {int(start_time.timestamp())}s{f', stop: {int(end_time.timestamp())}s' if end_time else ''})
                |> filter(fn: (r) => r._measurement == "klines")
                |> filter(fn: (r) => r.symbol == "{symbol}")
                |> filter(fn: (r) => r.period == "{period}")
                |> limit(n: {limit})
                |> sort(columns: ["_time"])
            '''
            
            result = self.query_api.query(query)
            
            klines = []
            for table in result:
                for record in table.records:
                    kline = {
                        "symbol": record.values.get("symbol"),
                        "period": record.values.get("period"),
                        "datetime": record.get_time(),
                        record.get_field(): record.get_value()
                    }
                    klines.append(kline)
            
            return klines
        except Exception as e:
            logger.error(f"查询K线数据失败: {e}")
            return []
    
    def close(self):
        """关闭连接"""
        if self.client:
            self.client.close()


# 创建全局InfluxDB管理器实例
influx_manager = InfluxDBManager()