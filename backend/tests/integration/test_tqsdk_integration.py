"""
TQSDK集成测试（使用模拟数据）
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.services.tqsdk_adapter import TQSDKAdapter
from app.services.market_service import MarketService
from app.services.history_service import HistoryService


class TestTQSDKAdapter:
    """TQSDK适配器测试"""
    
    def test_adapter_initialization(self, mock_tqsdk):
        """测试适配器初始化"""
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            adapter = TQSDKAdapter()
            assert adapter is not None
            assert adapter.connected is True
    
    def test_get_quote(self, mock_tqsdk):
        """测试获取行情数据"""
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            adapter = TQSDKAdapter()
            
            quote = adapter.get_quote("SHFE.cu2401")
            
            assert quote is not None
            assert quote["symbol"] == "SHFE.cu2401"
            assert "last_price" in quote
            assert "bid_price1" in quote
            assert "ask_price1" in quote
            assert "volume" in quote
    
    def test_get_quote_invalid_symbol(self, mock_tqsdk):
        """测试获取无效合约行情"""
        mock_tqsdk.get_quote.side_effect = Exception("Invalid symbol")
        
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            adapter = TQSDKAdapter()
            
            with pytest.raises(Exception):
                adapter.get_quote("INVALID.symbol")
    
    def test_get_kline_data(self, mock_tqsdk):
        """测试获取K线数据"""
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            adapter = TQSDKAdapter()
            
            klines = adapter.get_kline_serial("SHFE.cu2401", 60)
            
            assert klines is not None
            assert len(klines) > 0
            
            kline = klines[0]
            assert "datetime" in kline
            assert "open" in kline
            assert "high" in kline
            assert "low" in kline
            assert "close" in kline
            assert "volume" in kline
    
    def test_insert_order(self, mock_tqsdk):
        """测试下单"""
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            adapter = TQSDKAdapter()
            
            order = adapter.insert_order(
                symbol="SHFE.cu2401",
                direction="BUY",
                offset="OPEN",
                volume=1,
                limit_price=70000.0
            )
            
            assert order is not None
            assert order["order_id"] == "test_order_123"
            assert order["status"] == "ALIVE"
            assert order["symbol"] == "SHFE.cu2401"
            assert order["direction"] == "BUY"
            assert order["volume_orign"] == 1
    
    def test_cancel_order(self, mock_tqsdk):
        """测试撤单"""
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            adapter = TQSDKAdapter()
            
            result = adapter.cancel_order("test_order_123")
            
            assert result is not None
            assert result["order_id"] == "test_order_123"
            assert result["status"] == "FINISHED"
    
    def test_connection_error_handling(self):
        """测试连接错误处理"""
        mock_api = MagicMock()
        mock_api.side_effect = ConnectionError("Connection failed")
        
        with patch('app.services.tqsdk_adapter.TqApi', side_effect=ConnectionError("Connection failed")):
            with pytest.raises(ConnectionError):
                TQSDKAdapter()
    
    def test_reconnection_mechanism(self, mock_tqsdk):
        """测试重连机制"""
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            adapter = TQSDKAdapter()
            
            # 模拟连接断开
            adapter.connected = False
            
            # 尝试重连
            adapter.reconnect()
            
            assert adapter.connected is True


class TestMarketServiceIntegration:
    """市场服务集成测试"""
    
    def test_get_realtime_quote(self, mock_tqsdk, mock_redis):
        """测试获取实时行情"""
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            with patch('app.core.redis.get_redis_client', return_value=mock_redis):
                market_service = MarketService()
                
                quote = market_service.get_realtime_quote("SHFE.cu2401")
                
                assert quote is not None
                assert quote["symbol"] == "SHFE.cu2401"
                assert quote["last_price"] == 70000.0
    
    def test_get_multiple_quotes(self, mock_tqsdk, mock_redis):
        """测试获取多个合约行情"""
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            with patch('app.core.redis.get_redis_client', return_value=mock_redis):
                market_service = MarketService()
                
                symbols = ["SHFE.cu2401", "DCE.i2401", "CZCE.MA401"]
                quotes = market_service.get_multiple_quotes(symbols)
                
                assert len(quotes) == len(symbols)
                for quote in quotes:
                    assert quote["symbol"] in symbols
                    assert "last_price" in quote
    
    def test_quote_caching(self, mock_tqsdk, mock_redis):
        """测试行情缓存"""
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            with patch('app.core.redis.get_redis_client', return_value=mock_redis):
                market_service = MarketService()
                
                # 第一次获取
                quote1 = market_service.get_realtime_quote("SHFE.cu2401")
                
                # 第二次获取应该从缓存读取
                quote2 = market_service.get_realtime_quote("SHFE.cu2401")
                
                assert quote1 == quote2
                # 验证Redis被调用
                assert mock_redis.get.called
    
    def test_subscribe_market_data(self, mock_tqsdk, mock_redis):
        """测试订阅市场数据"""
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            with patch('app.core.redis.get_redis_client', return_value=mock_redis):
                market_service = MarketService()
                
                # 订阅市场数据
                result = market_service.subscribe_market_data(["SHFE.cu2401"])
                
                assert result is True
                # 验证订阅状态被保存
                assert mock_redis.set.called
    
    def test_unsubscribe_market_data(self, mock_tqsdk, mock_redis):
        """测试取消订阅市场数据"""
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            with patch('app.core.redis.get_redis_client', return_value=mock_redis):
                market_service = MarketService()
                
                # 先订阅
                market_service.subscribe_market_data(["SHFE.cu2401"])
                
                # 取消订阅
                result = market_service.unsubscribe_market_data(["SHFE.cu2401"])
                
                assert result is True
                # 验证订阅状态被删除
                assert mock_redis.delete.called


class TestHistoryServiceIntegration:
    """历史数据服务集成测试"""
    
    def test_get_kline_data(self, mock_tqsdk, mock_influxdb):
        """测试获取K线数据"""
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            with patch('app.core.influxdb.get_influxdb_client', return_value=mock_influxdb):
                history_service = HistoryService()
                
                start_date = datetime.now() - timedelta(days=30)
                end_date = datetime.now()
                
                klines = history_service.get_kline_data(
                    symbol="SHFE.cu2401",
                    start_date=start_date,
                    end_date=end_date,
                    interval="1m"
                )
                
                assert klines is not None
                assert len(klines) > 0
                
                kline = klines[0]
                assert "datetime" in kline
                assert "open" in kline
                assert "high" in kline
                assert "low" in kline
                assert "close" in kline
                assert "volume" in kline
    
    def test_get_tick_data(self, mock_tqsdk, mock_influxdb):
        """测试获取Tick数据"""
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            with patch('app.core.influxdb.get_influxdb_client', return_value=mock_influxdb):
                history_service = HistoryService()
                
                start_date = datetime.now() - timedelta(hours=1)
                end_date = datetime.now()
                
                ticks = history_service.get_tick_data(
                    symbol="SHFE.cu2401",
                    start_date=start_date,
                    end_date=end_date
                )
                
                assert ticks is not None
                assert isinstance(ticks, list)
    
    def test_data_storage_to_influxdb(self, mock_tqsdk, mock_influxdb):
        """测试数据存储到InfluxDB"""
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            with patch('app.core.influxdb.get_influxdb_client', return_value=mock_influxdb):
                history_service = HistoryService()
                
                # 模拟存储K线数据
                kline_data = {
                    "symbol": "SHFE.cu2401",
                    "datetime": datetime.now(),
                    "open": 70000.0,
                    "high": 70100.0,
                    "low": 69900.0,
                    "close": 70050.0,
                    "volume": 100
                }
                
                result = history_service.store_kline_data(kline_data)
                
                assert result is True
                # 验证数据被写入InfluxDB
                assert len(mock_influxdb.data) > 0
    
    def test_data_aggregation(self, mock_tqsdk, mock_influxdb):
        """测试数据聚合"""
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            with patch('app.core.influxdb.get_influxdb_client', return_value=mock_influxdb):
                history_service = HistoryService()
                
                # 测试1分钟数据聚合为5分钟
                aggregated_data = history_service.aggregate_kline_data(
                    symbol="SHFE.cu2401",
                    from_interval="1m",
                    to_interval="5m",
                    start_date=datetime.now() - timedelta(hours=1),
                    end_date=datetime.now()
                )
                
                assert aggregated_data is not None
                assert isinstance(aggregated_data, list)


class TestTQSDKErrorHandling:
    """TQSDK错误处理测试"""
    
    def test_network_timeout_handling(self, mock_tqsdk):
        """测试网络超时处理"""
        mock_tqsdk.get_quote.side_effect = TimeoutError("Network timeout")
        
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            adapter = TQSDKAdapter()
            
            with pytest.raises(TimeoutError):
                adapter.get_quote("SHFE.cu2401")
    
    def test_api_rate_limit_handling(self, mock_tqsdk):
        """测试API限流处理"""
        mock_tqsdk.get_quote.side_effect = Exception("Rate limit exceeded")
        
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            adapter = TQSDKAdapter()
            
            with pytest.raises(Exception) as exc_info:
                adapter.get_quote("SHFE.cu2401")
            
            assert "rate limit" in str(exc_info.value).lower()
    
    def test_invalid_order_handling(self, mock_tqsdk):
        """测试无效订单处理"""
        mock_tqsdk.insert_order.side_effect = Exception("Invalid order parameters")
        
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            adapter = TQSDKAdapter()
            
            with pytest.raises(Exception) as exc_info:
                adapter.insert_order(
                    symbol="INVALID.symbol",
                    direction="INVALID",
                    offset="INVALID",
                    volume=-1
                )
            
            assert "invalid" in str(exc_info.value).lower()
    
    def test_market_closed_handling(self, mock_tqsdk):
        """测试市场关闭处理"""
        mock_tqsdk.get_quote.return_value = {
            "symbol": "SHFE.cu2401",
            "last_price": 0.0,  # 市场关闭时价格为0
            "trading_time": False
        }
        
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            adapter = TQSDKAdapter()
            
            quote = adapter.get_quote("SHFE.cu2401")
            
            assert quote["last_price"] == 0.0
            assert quote["trading_time"] is False


class TestTQSDKDataValidation:
    """TQSDK数据验证测试"""
    
    def test_quote_data_validation(self, mock_tqsdk):
        """测试行情数据验证"""
        # 模拟返回无效数据
        mock_tqsdk.get_quote.return_value = {
            "symbol": "SHFE.cu2401",
            "last_price": -1.0,  # 负价格
            "volume": -100  # 负成交量
        }
        
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            adapter = TQSDKAdapter()
            
            with pytest.raises(ValueError):
                adapter.validate_quote_data(mock_tqsdk.get_quote("SHFE.cu2401"))
    
    def test_kline_data_validation(self, mock_tqsdk):
        """测试K线数据验证"""
        # 模拟返回无效K线数据
        invalid_kline = {
            "datetime": "invalid_datetime",
            "open": 70000.0,
            "high": 69000.0,  # 最高价低于开盘价
            "low": 71000.0,   # 最低价高于开盘价
            "close": 70000.0,
            "volume": -100    # 负成交量
        }
        
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            adapter = TQSDKAdapter()
            
            with pytest.raises(ValueError):
                adapter.validate_kline_data(invalid_kline)
    
    def test_symbol_format_validation(self, mock_tqsdk):
        """测试合约代码格式验证"""
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            adapter = TQSDKAdapter()
            
            # 有效格式
            assert adapter.validate_symbol("SHFE.cu2401") is True
            assert adapter.validate_symbol("DCE.i2401") is True
            assert adapter.validate_symbol("CZCE.MA401") is True
            
            # 无效格式
            assert adapter.validate_symbol("invalid") is False
            assert adapter.validate_symbol("SHFE.") is False
            assert adapter.validate_symbol(".cu2401") is False


class TestTQSDKPerformance:
    """TQSDK性能测试"""
    
    def test_concurrent_quote_requests(self, mock_tqsdk):
        """测试并发行情请求"""
        import asyncio
        
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            adapter = TQSDKAdapter()
            
            async def get_quote_async(symbol):
                return adapter.get_quote(symbol)
            
            async def test_concurrent():
                symbols = ["SHFE.cu2401", "DCE.i2401", "CZCE.MA401"] * 10
                tasks = [get_quote_async(symbol) for symbol in symbols]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 验证所有请求都成功
                for result in results:
                    assert not isinstance(result, Exception)
                    assert "symbol" in result
            
            # 运行并发测试
            asyncio.run(test_concurrent())
    
    def test_memory_usage_with_large_dataset(self, mock_tqsdk, mock_influxdb):
        """测试大数据集的内存使用"""
        # 模拟大量K线数据
        large_kline_data = []
        for i in range(10000):
            large_kline_data.append({
                "datetime": f"2023-01-01 {i//60:02d}:{i%60:02d}:00",
                "open": 70000.0 + i,
                "high": 70100.0 + i,
                "low": 69900.0 + i,
                "close": 70050.0 + i,
                "volume": 100
            })
        
        mock_tqsdk.get_kline_serial.return_value = large_kline_data
        
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            with patch('app.core.influxdb.get_influxdb_client', return_value=mock_influxdb):
                history_service = HistoryService()
                
                # 获取大量数据
                klines = history_service.get_kline_data(
                    symbol="SHFE.cu2401",
                    start_date=datetime.now() - timedelta(days=1),
                    end_date=datetime.now(),
                    interval="1m"
                )
                
                assert len(klines) == 10000
                # 验证内存使用合理（这里只是简单检查不会崩溃）
    
    def test_data_processing_speed(self, mock_tqsdk):
        """测试数据处理速度"""
        import time
        
        with patch('app.services.tqsdk_adapter.TqApi', return_value=mock_tqsdk):
            adapter = TQSDKAdapter()
            
            # 测试处理1000个行情数据的时间
            start_time = time.time()
            
            for i in range(1000):
                quote = adapter.get_quote("SHFE.cu2401")
                # 简单的数据处理
                processed_quote = {
                    "symbol": quote["symbol"],
                    "price": quote["last_price"],
                    "timestamp": time.time()
                }
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 验证处理时间合理（应该在几秒内完成）
            assert processing_time < 10.0  # 10秒内完成
            
            # 计算处理速度
            speed = 1000 / processing_time
            assert speed > 100  # 每秒至少处理100个数据点