"""
数据验证和格式化工具
"""
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .exceptions import ValidationError

logger = logging.getLogger(__name__)


class MarketDataValidator:
    """市场数据验证器"""
    
    # 合约代码格式正则表达式
    SYMBOL_PATTERNS = {
        "SHFE": r"^SHFE\.[a-z]+\d{4}$",  # 上期所: SHFE.cu2401
        "DCE": r"^DCE\.[a-z]+\d{4}$",   # 大商所: DCE.i2401
        "CZCE": r"^CZCE\.[A-Z]+\d{3}$", # 郑商所: CZCE.MA401
        "INE": r"^INE\.[a-z]+\d{4}$",   # 上海国际能源: INE.sc2401
        "CFFEX": r"^CFFEX\.[A-Z]+\d{4}$", # 中金所: CFFEX.IF2401
    }
    
    @classmethod
    def validate_symbol(cls, symbol: str) -> bool:
        """验证合约代码格式"""
        if not symbol or not isinstance(symbol, str):
            return False
        
        # 检查是否匹配任一交易所格式
        for exchange, pattern in cls.SYMBOL_PATTERNS.items():
            if re.match(pattern, symbol):
                return True
        
        return False
    
    @classmethod
    def extract_exchange(cls, symbol: str) -> Optional[str]:
        """从合约代码提取交易所"""
        if not cls.validate_symbol(symbol):
            return None
        
        return symbol.split('.')[0]
    
    @classmethod
    def extract_product_id(cls, symbol: str) -> Optional[str]:
        """从合约代码提取品种代码"""
        if not cls.validate_symbol(symbol):
            return None
        
        exchange = cls.extract_exchange(symbol)
        instrument = symbol.split('.')[1]
        
        if exchange == "CZCE":
            # 郑商所格式: MA401 -> MA
            return re.match(r"([A-Z]+)\d+", instrument).group(1)
        else:
            # 其他交易所格式: cu2401 -> cu
            return re.match(r"([a-z]+)\d+", instrument).group(1)
    
    @classmethod
    def validate_quote_data(cls, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证和格式化行情数据"""
        try:
            # 必需字段检查
            required_fields = [
                "symbol", "last_price", "bid_price", "ask_price",
                "volume", "datetime"
            ]
            
            for field in required_fields:
                if field not in quote_data:
                    raise ValidationError(f"缺少必需字段: {field}")
            
            # 验证合约代码
            symbol = quote_data["symbol"]
            if not cls.validate_symbol(symbol):
                raise ValidationError(f"无效的合约代码: {symbol}")
            
            # 格式化数据
            formatted_data = {
                "symbol": symbol,
                "last_price": cls._validate_price(quote_data["last_price"]),
                "bid_price": cls._validate_price(quote_data["bid_price"]),
                "ask_price": cls._validate_price(quote_data["ask_price"]),
                "bid_volume": cls._validate_volume(quote_data.get("bid_volume", 0)),
                "ask_volume": cls._validate_volume(quote_data.get("ask_volume", 0)),
                "volume": cls._validate_volume(quote_data["volume"]),
                "open_interest": cls._validate_volume(quote_data.get("open_interest", 0)),
                "open": cls._validate_price(quote_data.get("open", 0)),
                "high": cls._validate_price(quote_data.get("high", 0)),
                "low": cls._validate_price(quote_data.get("low", 0)),
                "pre_close": cls._validate_price(quote_data.get("pre_close", 0)),
                "upper_limit": cls._validate_price(quote_data.get("upper_limit", 0)),
                "lower_limit": cls._validate_price(quote_data.get("lower_limit", 0)),
                "datetime": cls._validate_datetime(quote_data["datetime"]),
            }
            
            # 数据合理性检查
            cls._validate_quote_consistency(formatted_data)
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"行情数据验证失败: {e}")
            raise ValidationError(f"行情数据验证失败: {str(e)}")
    
    @classmethod
    def validate_kline_data(cls, kline_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证和格式化K线数据"""
        try:
            # 必需字段检查
            required_fields = ["datetime", "open", "high", "low", "close", "volume"]
            
            for field in required_fields:
                if field not in kline_data:
                    raise ValidationError(f"缺少必需字段: {field}")
            
            # 格式化数据
            formatted_data = {
                "datetime": cls._validate_datetime(kline_data["datetime"]),
                "open": cls._validate_price(kline_data["open"]),
                "high": cls._validate_price(kline_data["high"]),
                "low": cls._validate_price(kline_data["low"]),
                "close": cls._validate_price(kline_data["close"]),
                "volume": cls._validate_volume(kline_data["volume"]),
                "open_interest": cls._validate_volume(kline_data.get("open_interest", 0)),
            }
            
            # K线数据合理性检查
            cls._validate_kline_consistency(formatted_data)
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"K线数据验证失败: {e}")
            raise ValidationError(f"K线数据验证失败: {str(e)}")
    
    @classmethod
    def _validate_price(cls, price: Any) -> float:
        """验证价格数据"""
        try:
            price_float = float(price)
            if price_float < 0:
                raise ValueError("价格不能为负数")
            if price_float > 1000000:  # 100万的价格上限
                raise ValueError("价格超出合理范围")
            return round(price_float, 4)  # 保留4位小数
        except (ValueError, TypeError) as e:
            raise ValidationError(f"无效的价格数据: {price}")
    
    @classmethod
    def _validate_volume(cls, volume: Any) -> int:
        """验证成交量数据"""
        try:
            volume_int = int(volume)
            if volume_int < 0:
                raise ValueError("成交量不能为负数")
            return volume_int
        except (ValueError, TypeError) as e:
            raise ValidationError(f"无效的成交量数据: {volume}")
    
    @classmethod
    def _validate_datetime(cls, dt: Any) -> str:
        """验证时间数据"""
        try:
            if isinstance(dt, str):
                # 尝试解析ISO格式时间
                datetime.fromisoformat(dt.replace('Z', '+00:00'))
                return dt
            elif isinstance(dt, datetime):
                return dt.isoformat()
            else:
                raise ValueError("不支持的时间格式")
        except (ValueError, TypeError) as e:
            raise ValidationError(f"无效的时间数据: {dt}")
    
    @classmethod
    def _validate_quote_consistency(cls, quote_data: Dict[str, Any]):
        """验证行情数据一致性"""
        # 检查买卖价格关系
        if (quote_data["bid_price"] > 0 and quote_data["ask_price"] > 0 and
            quote_data["bid_price"] >= quote_data["ask_price"]):
            logger.warning(f"买价({quote_data['bid_price']})大于等于卖价({quote_data['ask_price']})")
        
        # 检查最新价是否在合理范围内
        if quote_data["last_price"] > 0:
            if quote_data["upper_limit"] > 0 and quote_data["last_price"] > quote_data["upper_limit"]:
                logger.warning(f"最新价({quote_data['last_price']})超过涨停价({quote_data['upper_limit']})")
            
            if quote_data["lower_limit"] > 0 and quote_data["last_price"] < quote_data["lower_limit"]:
                logger.warning(f"最新价({quote_data['last_price']})低于跌停价({quote_data['lower_limit']})")
        
        # 检查高低价关系
        if (quote_data["high"] > 0 and quote_data["low"] > 0 and
            quote_data["high"] < quote_data["low"]):
            raise ValidationError(f"最高价({quote_data['high']})不能低于最低价({quote_data['low']})")
    
    @classmethod
    def _validate_kline_consistency(cls, kline_data: Dict[str, Any]):
        """验证K线数据一致性"""
        open_price = kline_data["open"]
        high_price = kline_data["high"]
        low_price = kline_data["low"]
        close_price = kline_data["close"]
        
        # 检查高低价关系
        if high_price < low_price:
            raise ValidationError(f"最高价({high_price})不能低于最低价({low_price})")
        
        # 检查开盘价是否在高低价范围内
        if not (low_price <= open_price <= high_price):
            raise ValidationError(f"开盘价({open_price})不在高低价范围内")
        
        # 检查收盘价是否在高低价范围内
        if not (low_price <= close_price <= high_price):
            raise ValidationError(f"收盘价({close_price})不在高低价范围内")


class DataFormatter:
    """数据格式化工具"""
    
    @staticmethod
    def format_price(price: float, precision: int = 2) -> str:
        """格式化价格显示"""
        return f"{price:.{precision}f}"
    
    @staticmethod
    def format_volume(volume: int) -> str:
        """格式化成交量显示"""
        if volume >= 10000:
            return f"{volume/10000:.1f}万"
        else:
            return str(volume)
    
    @staticmethod
    def format_change_rate(current: float, previous: float) -> str:
        """计算和格式化涨跌幅"""
        if previous <= 0:
            return "0.00%"
        
        change_rate = (current - previous) / previous * 100
        return f"{change_rate:+.2f}%"
    
    @staticmethod
    def format_datetime(dt_str: str, format_type: str = "datetime") -> str:
        """格式化时间显示"""
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            
            if format_type == "time":
                return dt.strftime("%H:%M:%S")
            elif format_type == "date":
                return dt.strftime("%Y-%m-%d")
            else:
                return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return dt_str
    
    @staticmethod
    def calculate_technical_indicators(klines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算技术指标"""
        if not klines:
            return {}
        
        closes = [k["close"] for k in klines]
        volumes = [k["volume"] for k in klines]
        
        indicators = {}
        
        # 移动平均线
        if len(closes) >= 5:
            indicators["ma5"] = sum(closes[-5:]) / 5
        if len(closes) >= 10:
            indicators["ma10"] = sum(closes[-10:]) / 10
        if len(closes) >= 20:
            indicators["ma20"] = sum(closes[-20:]) / 20
        
        # 成交量移动平均
        if len(volumes) >= 5:
            indicators["vol_ma5"] = sum(volumes[-5:]) / 5
        
        # 当前价格相对位置
        if len(closes) >= 20:
            recent_high = max(closes[-20:])
            recent_low = min(closes[-20:])
            current_price = closes[-1]
            
            if recent_high > recent_low:
                indicators["price_position"] = (current_price - recent_low) / (recent_high - recent_low)
        
        return indicators