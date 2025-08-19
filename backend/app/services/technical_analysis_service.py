"""
技术分析服务 - 基于 tqsdk 的真实技术分析功能
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .market_data_service import market_data_service
from ..core.database import get_redis_client

logger = logging.getLogger(__name__)


class TechnicalAnalysisService:
    """技术分析服务 - 基于 tqsdk 实现真实技术分析功能"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self.is_initialized = False
    
    async def initialize(self):
        """初始化技术分析服务"""
        try:
            # 确保市场数据服务已初始化
            if not market_data_service.is_initialized:
                await market_data_service.initialize()
            
            self.is_initialized = True
            logger.info("技术分析服务初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"技术分析服务初始化失败: {e}")
            return False
    
    async def get_technical_indicators(
        self,
        symbol: str,
        period: str = "1d",
        limit: int = 100
    ) -> Dict[str, Any]:
        """获取技术指标"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # 检查缓存
            cache_key = f"tech_indicators:{symbol}:{period}:{limit}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                try:
                    return json.loads(cached_data)
                except:
                    pass
            
            # 获取K线数据
            klines = await market_data_service.get_klines(symbol, period, limit)
            
            if not klines or len(klines) < 20:
                return {"error": "数据不足，无法计算技术指标"}
            
            # 转换为DataFrame
            df = pd.DataFrame(klines)
            df['close'] = pd.to_numeric(df['close'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['volume'] = pd.to_numeric(df['volume'])
            
            # 计算各种技术指标
            indicators = {}
            
            # 移动平均线
            indicators['ma5'] = self._calculate_ma(df['close'], 5)
            indicators['ma10'] = self._calculate_ma(df['close'], 10)
            indicators['ma20'] = self._calculate_ma(df['close'], 20)
            
            # RSI
            indicators['rsi'] = self._calculate_rsi(df['close'])
            
            # 添加时间戳和基本信息
            result = {
                "symbol": symbol,
                "period": period,
                "timestamp": datetime.now().isoformat(),
                "data_points": len(klines),
                "indicators": indicators,
                "latest_values": self._get_latest_values(indicators),
                "signals": self._generate_signals(indicators)
            }
            
            # 缓存结果
            cache_timeout = 60 if period in ["1m", "5m"] else 300
            self.redis_client.setex(cache_key, cache_timeout, json.dumps(result))
            
            return result
            
        except Exception as e:
            logger.error(f"获取技术指标失败 {symbol}: {e}")
            return {"error": str(e)}
    
    def _calculate_ma(self, prices: pd.Series, period: int) -> List[float]:
        """计算移动平均线"""
        try:
            ma = prices.rolling(window=period).mean()
            return [round(float(x), 2) if not pd.isna(x) else None for x in ma]
        except Exception as e:
            logger.error(f"计算MA失败: {e}")
            return []
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> List[float]:
        """计算RSI指标"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return [round(float(x), 2) if not pd.isna(x) else None for x in rsi]
        except Exception as e:
            logger.error(f"计算RSI失败: {e}")
            return []
    
    def _get_latest_values(self, indicators: Dict[str, Any]) -> Dict[str, float]:
        """获取最新的指标值"""
        try:
            latest = {}
            for key, values in indicators.items():
                if isinstance(values, list) and values:
                    # 获取最后一个非None值
                    for val in reversed(values):
                        if val is not None:
                            latest[key] = val
                            break
            return latest
        except Exception as e:
            logger.error(f"获取最新指标值失败: {e}")
            return {}
    
    def _generate_signals(self, indicators: Dict[str, Any]) -> Dict[str, str]:
        """生成交易信号"""
        try:
            signals = {}
            latest = self._get_latest_values(indicators)
            
            # RSI信号
            if 'rsi' in latest:
                rsi = latest['rsi']
                if rsi > 70:
                    signals['rsi'] = "超买"
                elif rsi < 30:
                    signals['rsi'] = "超卖"
                else:
                    signals['rsi'] = "中性"
            
            return signals
            
        except Exception as e:
            logger.error(f"生成交易信号失败: {e}")
            return {}


# 创建全局技术分析服务实例
technical_analysis_service = TechnicalAnalysisService()