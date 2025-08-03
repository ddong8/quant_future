"""
技术分析服务
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func
from decimal import Decimal

from ..models.market_data import Symbol, Kline
from ..models.user import User

logger = logging.getLogger(__name__)

class TechnicalAnalysisService:
    """技术分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== K线数据获取 ====================
    
    def get_kline_data(self, symbol_code: str, interval: str = '1d', 
                      start_time: datetime = None, end_time: datetime = None,
                      limit: int = 1000) -> List[Dict[str, Any]]:
        """获取K线数据"""
        try:
            # 获取标的信息
            symbol = self.db.query(Symbol).filter(Symbol.symbol == symbol_code).first()
            if not symbol:
                return []
            
            # 构建查询
            query = self.db.query(Kline).filter(
                Kline.symbol_id == symbol.id,
                Kline.interval == interval
            )
            
            if start_time:
                query = query.filter(Kline.open_time >= start_time)
            
            if end_time:
                query = query.filter(Kline.open_time <= end_time)
            
            # 获取数据
            klines = query.order_by(Kline.open_time).limit(limit).all()
            
            # 转换为字典格式
            result = []
            for kline in klines:
                result.append({
                    'timestamp': kline.open_time.timestamp() * 1000,  # ECharts需要毫秒时间戳
                    'open': float(kline.open_price),
                    'high': float(kline.high_price),
                    'low': float(kline.low_price),
                    'close': float(kline.close_price),
                    'volume': float(kline.volume),
                    'turnover': float(kline.turnover or 0),
                    'trade_count': kline.trade_count or 0,
                    'vwap': float(kline.vwap or 0)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            return []
    
    # ==================== 技术指标计算 ====================
    
    def calculate_ma(self, data: List[Dict[str, Any]], period: int = 20, 
                    price_type: str = 'close') -> List[float]:
        """计算移动平均线"""
        try:
            if len(data) < period:
                return []
            
            prices = [item[price_type] for item in data]
            ma_values = []
            
            for i in range(len(prices)):
                if i < period - 1:
                    ma_values.append(None)
                else:
                    ma = sum(prices[i-period+1:i+1]) / period
                    ma_values.append(round(ma, 4))
            
            return ma_values
            
        except Exception as e:
            logger.error(f"计算移动平均线失败: {e}")
            return []
    
    def calculate_ema(self, data: List[Dict[str, Any]], period: int = 20,
                     price_type: str = 'close') -> List[float]:
        """计算指数移动平均线"""
        try:
            if len(data) < period:
                return []
            
            prices = [item[price_type] for item in data]
            ema_values = []
            multiplier = 2 / (period + 1)
            
            # 第一个EMA值使用SMA
            sma = sum(prices[:period]) / period
            ema_values.extend([None] * (period - 1))
            ema_values.append(sma)
            
            # 计算后续EMA值
            for i in range(period, len(prices)):
                ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
                ema_values.append(round(ema, 4))
            
            return ema_values
            
        except Exception as e:
            logger.error(f"计算指数移动平均线失败: {e}")
            return []
    
    def calculate_bollinger_bands(self, data: List[Dict[str, Any]], period: int = 20,
                                std_dev: float = 2.0, price_type: str = 'close') -> Dict[str, List[float]]:
        """计算布林带"""
        try:
            if len(data) < period:
                return {'upper': [], 'middle': [], 'lower': []}
            
            prices = [item[price_type] for item in data]
            upper_band = []
            middle_band = []
            lower_band = []
            
            for i in range(len(prices)):
                if i < period - 1:
                    upper_band.append(None)
                    middle_band.append(None)
                    lower_band.append(None)
                else:
                    # 计算移动平均和标准差
                    window_prices = prices[i-period+1:i+1]
                    ma = sum(window_prices) / period
                    std = np.std(window_prices, ddof=0)
                    
                    upper_band.append(round(ma + (std_dev * std), 4))
                    middle_band.append(round(ma, 4))
                    lower_band.append(round(ma - (std_dev * std), 4))
            
            return {
                'upper': upper_band,
                'middle': middle_band,
                'lower': lower_band
            }
            
        except Exception as e:
            logger.error(f"计算布林带失败: {e}")
            return {'upper': [], 'middle': [], 'lower': []}
    
    def calculate_rsi(self, data: List[Dict[str, Any]], period: int = 14,
                     price_type: str = 'close') -> List[float]:
        """计算相对强弱指数"""
        try:
            if len(data) < period + 1:
                return []
            
            prices = [item[price_type] for item in data]
            rsi_values = []
            
            # 计算价格变化
            price_changes = []
            for i in range(1, len(prices)):
                price_changes.append(prices[i] - prices[i-1])
            
            # 分离上涨和下跌
            gains = [max(change, 0) for change in price_changes]
            losses = [abs(min(change, 0)) for change in price_changes]
            
            # 计算RSI
            for i in range(len(price_changes)):
                if i < period - 1:
                    rsi_values.append(None)
                elif i == period - 1:
                    # 第一个RSI值使用简单平均
                    avg_gain = sum(gains[i-period+1:i+1]) / period
                    avg_loss = sum(losses[i-period+1:i+1]) / period
                    
                    if avg_loss == 0:
                        rsi = 100
                    else:
                        rs = avg_gain / avg_loss
                        rsi = 100 - (100 / (1 + rs))
                    
                    rsi_values.append(round(rsi, 2))
                else:
                    # 使用指数移动平均
                    prev_avg_gain = (rsi_values[-1] if rsi_values[-1] is not None else 50) / 100 * 2 - 1
                    prev_avg_loss = 1 - prev_avg_gain
                    
                    avg_gain = (prev_avg_gain * (period - 1) + gains[i]) / period
                    avg_loss = (prev_avg_loss * (period - 1) + losses[i]) / period
                    
                    if avg_loss == 0:
                        rsi = 100
                    else:
                        rs = avg_gain / avg_loss
                        rsi = 100 - (100 / (1 + rs))
                    
                    rsi_values.append(round(rsi, 2))
            
            # 在开头添加None以匹配原始数据长度
            return [None] + rsi_values
            
        except Exception as e:
            logger.error(f"计算RSI失败: {e}")
            return []
    
    def calculate_macd(self, data: List[Dict[str, Any]], fast_period: int = 12,
                      slow_period: int = 26, signal_period: int = 9,
                      price_type: str = 'close') -> Dict[str, List[float]]:
        """计算MACD"""
        try:
            if len(data) < slow_period:
                return {'macd': [], 'signal': [], 'histogram': []}
            
            # 计算快线和慢线EMA
            fast_ema = self.calculate_ema(data, fast_period, price_type)
            slow_ema = self.calculate_ema(data, slow_period, price_type)
            
            # 计算MACD线
            macd_line = []
            for i in range(len(data)):
                if fast_ema[i] is None or slow_ema[i] is None:
                    macd_line.append(None)
                else:
                    macd_line.append(round(fast_ema[i] - slow_ema[i], 4))
            
            # 计算信号线（MACD的EMA）
            macd_data = [{'close': val} for val in macd_line if val is not None]
            if len(macd_data) >= signal_period:
                signal_ema = self.calculate_ema(macd_data, signal_period)
                # 调整信号线长度
                signal_line = [None] * (len(macd_line) - len(signal_ema)) + signal_ema
            else:
                signal_line = [None] * len(macd_line)
            
            # 计算柱状图
            histogram = []
            for i in range(len(macd_line)):
                if macd_line[i] is None or signal_line[i] is None:
                    histogram.append(None)
                else:
                    histogram.append(round(macd_line[i] - signal_line[i], 4))
            
            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            }
            
        except Exception as e:
            logger.error(f"计算MACD失败: {e}")
            return {'macd': [], 'signal': [], 'histogram': []}
    
    def calculate_kdj(self, data: List[Dict[str, Any]], k_period: int = 9,
                     d_period: int = 3, j_period: int = 3) -> Dict[str, List[float]]:
        """计算KDJ指标"""
        try:
            if len(data) < k_period:
                return {'k': [], 'd': [], 'j': []}
            
            k_values = []
            d_values = []
            j_values = []
            
            # 初始化K和D值
            prev_k = 50
            prev_d = 50
            
            for i in range(len(data)):
                if i < k_period - 1:
                    k_values.append(None)
                    d_values.append(None)
                    j_values.append(None)
                else:
                    # 计算最近k_period天的最高价和最低价
                    window_data = data[i-k_period+1:i+1]
                    highest_high = max(item['high'] for item in window_data)
                    lowest_low = min(item['low'] for item in window_data)
                    current_close = data[i]['close']
                    
                    # 计算RSV
                    if highest_high == lowest_low:
                        rsv = 50
                    else:
                        rsv = (current_close - lowest_low) / (highest_high - lowest_low) * 100
                    
                    # 计算K值
                    k = (2 * prev_k + rsv) / 3
                    k_values.append(round(k, 2))
                    
                    # 计算D值
                    d = (2 * prev_d + k) / 3
                    d_values.append(round(d, 2))
                    
                    # 计算J值
                    j = 3 * k - 2 * d
                    j_values.append(round(j, 2))
                    
                    prev_k = k
                    prev_d = d
            
            return {
                'k': k_values,
                'd': d_values,
                'j': j_values
            }
            
        except Exception as e:
            logger.error(f"计算KDJ失败: {e}")
            return {'k': [], 'd': [], 'j': []}
    
    # ==================== 综合技术分析 ====================
    
    def get_technical_indicators(self, symbol_code: str, interval: str = '1d',
                               indicators: List[str] = None, limit: int = 500) -> Dict[str, Any]:
        """获取技术指标数据"""
        try:
            # 获取K线数据
            kline_data = self.get_kline_data(symbol_code, interval, limit=limit)
            if not kline_data:
                return {}
            
            # 默认指标
            if indicators is None:
                indicators = ['ma5', 'ma10', 'ma20', 'ma60', 'bollinger', 'rsi', 'macd', 'kdj']
            
            result = {
                'symbol': symbol_code,
                'interval': interval,
                'kline_data': kline_data,
                'indicators': {}
            }
            
            # 计算各种技术指标
            for indicator in indicators:
                if indicator == 'ma5':
                    result['indicators']['ma5'] = self.calculate_ma(kline_data, 5)
                elif indicator == 'ma10':
                    result['indicators']['ma10'] = self.calculate_ma(kline_data, 10)
                elif indicator == 'ma20':
                    result['indicators']['ma20'] = self.calculate_ma(kline_data, 20)
                elif indicator == 'ma60':
                    result['indicators']['ma60'] = self.calculate_ma(kline_data, 60)
                elif indicator == 'ema12':
                    result['indicators']['ema12'] = self.calculate_ema(kline_data, 12)
                elif indicator == 'ema26':
                    result['indicators']['ema26'] = self.calculate_ema(kline_data, 26)
                elif indicator == 'bollinger':
                    result['indicators']['bollinger'] = self.calculate_bollinger_bands(kline_data)
                elif indicator == 'rsi':
                    result['indicators']['rsi'] = self.calculate_rsi(kline_data)
                elif indicator == 'macd':
                    result['indicators']['macd'] = self.calculate_macd(kline_data)
                elif indicator == 'kdj':
                    result['indicators']['kdj'] = self.calculate_kdj(kline_data)
            
            return result
            
        except Exception as e:
            logger.error(f"获取技术指标失败: {e}")
            return {}
    
    # ==================== 图表配置管理 ====================
    
    def save_chart_config(self, user_id: int, config_name: str, 
                         config_data: Dict[str, Any]) -> bool:
        """保存图表配置"""
        try:
            # 这里可以实现图表配置的保存逻辑
            # 暂时返回True，实际应该保存到数据库
            logger.info(f"保存图表配置: {user_id}, {config_name}")
            return True
            
        except Exception as e:
            logger.error(f"保存图表配置失败: {e}")
            return False
    
    def get_chart_configs(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的图表配置"""
        try:
            # 这里可以实现从数据库获取图表配置的逻辑
            # 暂时返回默认配置
            default_configs = [
                {
                    'id': 1,
                    'name': '默认配置',
                    'config': {
                        'indicators': ['ma5', 'ma10', 'ma20', 'bollinger', 'rsi', 'macd'],
                        'chart_type': 'candlestick',
                        'theme': 'light'
                    }
                }
            ]
            return default_configs
            
        except Exception as e:
            logger.error(f"获取图表配置失败: {e}")
            return []