"""
风险计算工具类
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class RiskCalculator:
    """风险计算器"""
    
    def __init__(self):
        self.risk_free_rate = 0.03  # 无风险利率，默认3%
    
    # ==================== 基础计算 ====================
    
    def calculate_portfolio_value(self, positions: List[Any], price_data: Dict[str, float]) -> Decimal:
        """计算组合总价值"""
        total_value = Decimal('0')
        
        for position in positions:
            symbol = position.symbol
            quantity = Decimal(str(position.quantity))
            price = Decimal(str(price_data.get(symbol, 0)))
            
            position_value = quantity * price
            total_value += position_value
        
        return total_value
    
    def calculate_total_exposure(self, positions: List[Any], price_data: Dict[str, float]) -> Decimal:
        """计算总敞口（绝对值）"""
        total_exposure = Decimal('0')
        
        for position in positions:
            symbol = position.symbol
            quantity = abs(Decimal(str(position.quantity)))
            price = Decimal(str(price_data.get(symbol, 0)))
            
            exposure = quantity * price
            total_exposure += exposure
        
        return total_exposure
    
    def calculate_net_exposure(self, positions: List[Any], price_data: Dict[str, float]) -> Decimal:
        """计算净敞口"""
        net_exposure = Decimal('0')
        
        for position in positions:
            symbol = position.symbol
            quantity = Decimal(str(position.quantity))
            price = Decimal(str(price_data.get(symbol, 0)))
            
            exposure = quantity * price
            net_exposure += exposure
        
        return net_exposure
    
    def calculate_leverage_ratio(self, total_exposure: Decimal, portfolio_value: Decimal) -> Optional[Decimal]:
        """计算杠杆率"""
        if portfolio_value <= 0:
            return None
        
        return total_exposure / portfolio_value
    
    def calculate_concentration_ratio(self, positions: List[Any], price_data: Dict[str, float]) -> Optional[Decimal]:
        """计算集中度比率（最大持仓占比）"""
        if not positions:
            return None
        
        total_value = self.calculate_portfolio_value(positions, price_data)
        if total_value <= 0:
            return None
        
        max_position_value = Decimal('0')
        
        for position in positions:
            symbol = position.symbol
            quantity = abs(Decimal(str(position.quantity)))
            price = Decimal(str(price_data.get(symbol, 0)))
            
            position_value = quantity * price
            max_position_value = max(max_position_value, position_value)
        
        return max_position_value / total_value
    
    def calculate_liquidity_ratio(self, positions: List[Any]) -> Optional[Decimal]:
        """计算流动性比率"""
        if not positions:
            return None
        
        # 这里应该根据实际的流动性数据计算
        # 暂时返回一个模拟值
        return Decimal('0.8')
    
    # ==================== 收益计算 ====================
    
    def calculate_daily_return(self, user_id: int, date: datetime) -> Optional[Decimal]:
        """计算日收益率"""
        try:
            # 这里应该从数据库获取历史净值数据
            # 暂时返回模拟数据
            return Decimal('0.001')  # 0.1%
        except Exception as e:
            logger.error(f"Error calculating daily return: {e}")
            return None
    
    def calculate_cumulative_return(self, user_id: int, date: datetime) -> Optional[Decimal]:
        """计算累计收益率"""
        try:
            # 这里应该从数据库获取历史净值数据
            # 暂时返回模拟数据
            return Decimal('0.05')  # 5%
        except Exception as e:
            logger.error(f"Error calculating cumulative return: {e}")
            return None
    
    def calculate_annualized_return(self, returns: List[float], periods_per_year: int = 252) -> Optional[float]:
        """计算年化收益率"""
        if not returns:
            return None
        
        try:
            total_return = np.prod([1 + r for r in returns]) - 1
            periods = len(returns)
            
            if periods == 0:
                return None
            
            annualized = (1 + total_return) ** (periods_per_year / periods) - 1
            return annualized
        except Exception as e:
            logger.error(f"Error calculating annualized return: {e}")
            return None
    
    # ==================== 风险计算 ====================
    
    def calculate_volatility(self, user_id: int, date: datetime, window: int = 30) -> Optional[Decimal]:
        """计算波动率"""
        try:
            # 这里应该从数据库获取历史收益率数据
            # 暂时返回模拟数据
            returns = np.random.normal(0.001, 0.02, window)  # 模拟收益率数据
            
            volatility = np.std(returns) * np.sqrt(252)  # 年化波动率
            return Decimal(str(volatility))
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return None
    
    def calculate_max_drawdown(self, user_id: int, date: datetime, window: int = 252) -> Optional[Decimal]:
        """计算最大回撤"""
        try:
            # 这里应该从数据库获取历史净值数据
            # 暂时返回模拟数据
            nav_values = np.cumprod(1 + np.random.normal(0.001, 0.02, window))
            
            # 计算回撤
            peak = np.maximum.accumulate(nav_values)
            drawdown = (nav_values - peak) / peak
            
            max_drawdown = np.min(drawdown)
            return Decimal(str(max_drawdown))
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return None
    
    def calculate_current_drawdown(self, user_id: int, date: datetime) -> Optional[Decimal]:
        """计算当前回撤"""
        try:
            # 这里应该从数据库获取历史净值数据
            # 暂时返回模拟数据
            return Decimal('-0.02')  # -2%
        except Exception as e:
            logger.error(f"Error calculating current drawdown: {e}")
            return None
    
    def calculate_var(self, positions: List[Any], price_data: Dict[str, float], 
                     confidence: float = 0.95, holding_period: int = 1) -> Optional[Decimal]:
        """计算VaR (Value at Risk)"""
        try:
            if not positions:
                return None
            
            # 获取历史价格数据和计算收益率
            returns_data = self._get_returns_data(positions, price_data)
            
            if not returns_data:
                return None
            
            # 计算组合收益率
            portfolio_returns = self._calculate_portfolio_returns(positions, returns_data, price_data)
            
            if len(portfolio_returns) == 0:
                return None
            
            # 计算VaR
            var_percentile = (1 - confidence) * 100
            var_value = np.percentile(portfolio_returns, var_percentile)
            
            # 调整持有期
            if holding_period > 1:
                var_value *= np.sqrt(holding_period)
            
            # 转换为货币金额
            portfolio_value = self.calculate_portfolio_value(positions, price_data)
            var_amount = abs(var_value) * portfolio_value
            
            return Decimal(str(var_amount))
        except Exception as e:
            logger.error(f"Error calculating VaR: {e}")
            return None
    
    def calculate_cvar(self, positions: List[Any], price_data: Dict[str, float], 
                      confidence: float = 0.95) -> Optional[Decimal]:
        """计算CVaR (Conditional Value at Risk)"""
        try:
            if not positions:
                return None
            
            # 获取历史价格数据和计算收益率
            returns_data = self._get_returns_data(positions, price_data)
            
            if not returns_data:
                return None
            
            # 计算组合收益率
            portfolio_returns = self._calculate_portfolio_returns(positions, returns_data, price_data)
            
            if len(portfolio_returns) == 0:
                return None
            
            # 计算CVaR
            var_percentile = (1 - confidence) * 100
            var_threshold = np.percentile(portfolio_returns, var_percentile)
            
            # 计算超过VaR阈值的平均损失
            tail_losses = portfolio_returns[portfolio_returns <= var_threshold]
            
            if len(tail_losses) == 0:
                return None
            
            cvar_value = np.mean(tail_losses)
            
            # 转换为货币金额
            portfolio_value = self.calculate_portfolio_value(positions, price_data)
            cvar_amount = abs(cvar_value) * portfolio_value
            
            return Decimal(str(cvar_amount))
        except Exception as e:
            logger.error(f"Error calculating CVaR: {e}")
            return None
    
    # ==================== 风险调整收益指标 ====================
    
    def calculate_sharpe_ratio(self, user_id: int, date: datetime, window: int = 252) -> Optional[Decimal]:
        """计算夏普比率"""
        try:
            # 这里应该从数据库获取历史收益率数据
            # 暂时返回模拟数据
            returns = np.random.normal(0.001, 0.02, window)
            
            if len(returns) == 0:
                return None
            
            # 计算年化收益率和波动率
            annualized_return = np.mean(returns) * 252
            annualized_volatility = np.std(returns) * np.sqrt(252)
            
            if annualized_volatility == 0:
                return None
            
            # 计算夏普比率
            sharpe = (annualized_return - self.risk_free_rate) / annualized_volatility
            return Decimal(str(sharpe))
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
            return None
    
    def calculate_sortino_ratio(self, user_id: int, date: datetime, window: int = 252) -> Optional[Decimal]:
        """计算索提诺比率"""
        try:
            # 这里应该从数据库获取历史收益率数据
            # 暂时返回模拟数据
            returns = np.random.normal(0.001, 0.02, window)
            
            if len(returns) == 0:
                return None
            
            # 计算年化收益率
            annualized_return = np.mean(returns) * 252
            
            # 计算下行波动率
            negative_returns = returns[returns < 0]
            if len(negative_returns) == 0:
                return None
            
            downside_volatility = np.std(negative_returns) * np.sqrt(252)
            
            if downside_volatility == 0:
                return None
            
            # 计算索提诺比率
            sortino = (annualized_return - self.risk_free_rate) / downside_volatility
            return Decimal(str(sortino))
        except Exception as e:
            logger.error(f"Error calculating Sortino ratio: {e}")
            return None
    
    def calculate_calmar_ratio(self, user_id: int, date: datetime) -> Optional[Decimal]:
        """计算卡玛比率"""
        try:
            # 获取年化收益率和最大回撤
            annualized_return = self.calculate_annualized_return([0.001] * 252)  # 模拟数据
            max_drawdown = self.calculate_max_drawdown(user_id, date)
            
            if annualized_return is None or max_drawdown is None or max_drawdown == 0:
                return None
            
            # 计算卡玛比率
            calmar = annualized_return / abs(float(max_drawdown))
            return Decimal(str(calmar))
        except Exception as e:
            logger.error(f"Error calculating Calmar ratio: {e}")
            return None
    
    def calculate_information_ratio(self, portfolio_returns: List[float], 
                                  benchmark_returns: List[float]) -> Optional[float]:
        """计算信息比率"""
        try:
            if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) == 0:
                return None
            
            # 计算超额收益
            excess_returns = np.array(portfolio_returns) - np.array(benchmark_returns)
            
            # 计算平均超额收益和跟踪误差
            mean_excess_return = np.mean(excess_returns)
            tracking_error = np.std(excess_returns)
            
            if tracking_error == 0:
                return None
            
            # 计算信息比率
            information_ratio = mean_excess_return / tracking_error
            return information_ratio
        except Exception as e:
            logger.error(f"Error calculating information ratio: {e}")
            return None
    
    # ==================== 相关性分析 ====================
    
    def calculate_correlation_matrix(self, positions: List[Any], 
                                   price_data: Dict[str, float]) -> Optional[pd.DataFrame]:
        """计算相关性矩阵"""
        try:
            if not positions:
                return None
            
            # 获取所有标的的收益率数据
            symbols = [pos.symbol for pos in positions]
            returns_data = {}
            
            for symbol in symbols:
                # 这里应该从数据库获取历史价格数据
                # 暂时生成模拟数据
                returns_data[symbol] = np.random.normal(0.001, 0.02, 252)
            
            # 创建DataFrame并计算相关性
            df = pd.DataFrame(returns_data)
            correlation_matrix = df.corr()
            
            return correlation_matrix
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {e}")
            return None
    
    def calculate_beta(self, asset_returns: List[float], 
                      market_returns: List[float]) -> Optional[float]:
        """计算Beta系数"""
        try:
            if len(asset_returns) != len(market_returns) or len(asset_returns) < 2:
                return None
            
            # 计算协方差和方差
            covariance = np.cov(asset_returns, market_returns)[0, 1]
            market_variance = np.var(market_returns)
            
            if market_variance == 0:
                return None
            
            beta = covariance / market_variance
            return beta
        except Exception as e:
            logger.error(f"Error calculating beta: {e}")
            return None
    
    # ==================== 辅助方法 ====================
    
    def _get_returns_data(self, positions: List[Any], 
                         price_data: Dict[str, float]) -> Dict[str, List[float]]:
        """获取收益率数据"""
        returns_data = {}
        
        for position in positions:
            symbol = position.symbol
            # 这里应该从数据库获取历史价格数据并计算收益率
            # 暂时生成模拟数据
            returns_data[symbol] = np.random.normal(0.001, 0.02, 252).tolist()
        
        return returns_data
    
    def _calculate_portfolio_returns(self, positions: List[Any], 
                                   returns_data: Dict[str, List[float]], 
                                   price_data: Dict[str, float]) -> np.ndarray:
        """计算组合收益率"""
        try:
            # 计算权重
            total_value = self.calculate_portfolio_value(positions, price_data)
            weights = {}
            
            for position in positions:
                symbol = position.symbol
                quantity = Decimal(str(position.quantity))
                price = Decimal(str(price_data.get(symbol, 0)))
                position_value = quantity * price
                
                if total_value > 0:
                    weights[symbol] = float(position_value / total_value)
                else:
                    weights[symbol] = 0
            
            # 计算组合收益率
            portfolio_returns = []
            max_length = max(len(returns) for returns in returns_data.values()) if returns_data else 0
            
            for i in range(max_length):
                portfolio_return = 0
                for symbol, weight in weights.items():
                    if symbol in returns_data and i < len(returns_data[symbol]):
                        portfolio_return += weight * returns_data[symbol][i]
                portfolio_returns.append(portfolio_return)
            
            return np.array(portfolio_returns)
        except Exception as e:
            logger.error(f"Error calculating portfolio returns: {e}")
            return np.array([])
    
    def calculate_risk_contribution(self, positions: List[Any], 
                                  price_data: Dict[str, float]) -> Dict[str, float]:
        """计算风险贡献度"""
        try:
            # 获取相关性矩阵
            correlation_matrix = self.calculate_correlation_matrix(positions, price_data)
            
            if correlation_matrix is None:
                return {}
            
            # 计算权重向量
            total_value = self.calculate_portfolio_value(positions, price_data)
            weights = []
            symbols = []
            
            for position in positions:
                symbol = position.symbol
                quantity = Decimal(str(position.quantity))
                price = Decimal(str(price_data.get(symbol, 0)))
                position_value = quantity * price
                
                if total_value > 0:
                    weight = float(position_value / total_value)
                else:
                    weight = 0
                
                weights.append(weight)
                symbols.append(symbol)
            
            weights = np.array(weights)
            
            # 计算组合方差
            portfolio_variance = np.dot(weights, np.dot(correlation_matrix.values, weights))
            
            if portfolio_variance <= 0:
                return {}
            
            # 计算边际风险贡献
            marginal_contributions = np.dot(correlation_matrix.values, weights) / np.sqrt(portfolio_variance)
            
            # 计算风险贡献度
            risk_contributions = {}
            for i, symbol in enumerate(symbols):
                risk_contributions[symbol] = weights[i] * marginal_contributions[i]
            
            return risk_contributions
        except Exception as e:
            logger.error(f"Error calculating risk contribution: {e}")
            return {}
    
    def calculate_expected_shortfall(self, returns: List[float], 
                                   confidence: float = 0.95) -> Optional[float]:
        """计算期望损失（Expected Shortfall）"""
        try:
            if not returns:
                return None
            
            returns_array = np.array(returns)
            var_threshold = np.percentile(returns_array, (1 - confidence) * 100)
            
            # 计算超过VaR阈值的平均损失
            tail_losses = returns_array[returns_array <= var_threshold]
            
            if len(tail_losses) == 0:
                return None
            
            expected_shortfall = np.mean(tail_losses)
            return expected_shortfall
        except Exception as e:
            logger.error(f"Error calculating expected shortfall: {e}")
            return None