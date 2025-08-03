"""
持仓计算工具类
"""
import math
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

class PositionCalculator:
    """持仓计算工具类"""
    
    @staticmethod
    def calculate_average_cost(trades: List[Dict[str, Any]]) -> Tuple[Decimal, Decimal]:
        """
        计算平均成本和总成本
        
        Args:
            trades: 交易记录列表，每个记录包含 quantity, price, commission
            
        Returns:
            (average_cost, total_cost)
        """
        if not trades:
            return Decimal('0'), Decimal('0')
        
        total_quantity = Decimal('0')
        total_cost = Decimal('0')
        
        for trade in trades:
            quantity = Decimal(str(trade['quantity']))
            price = Decimal(str(trade['price']))
            commission = Decimal(str(trade.get('commission', 0)))
            
            if quantity > 0:  # 买入
                total_quantity += quantity
                total_cost += quantity * price + commission
            else:  # 卖出
                sell_quantity = abs(quantity)
                if total_quantity > 0:
                    # 计算卖出成本
                    avg_cost = total_cost / total_quantity if total_quantity > 0 else Decimal('0')
                    sell_cost = sell_quantity * avg_cost
                    
                    # 更新总数量和总成本
                    total_quantity -= sell_quantity
                    total_cost -= sell_cost
                    
                    # 扣除手续费
                    total_cost -= commission
        
        if total_quantity > 0:
            average_cost = total_cost / total_quantity
        else:
            average_cost = Decimal('0')
            total_cost = Decimal('0')
        
        return average_cost, total_cost
    
    @staticmethod
    def calculate_pnl(quantity: Decimal, average_cost: Decimal, current_price: Decimal,
                     position_type: str = 'LONG') -> Tuple[Decimal, Decimal]:
        """
        计算盈亏
        
        Args:
            quantity: 持仓数量
            average_cost: 平均成本
            current_price: 当前价格
            position_type: 持仓类型 ('LONG' 或 'SHORT')
            
        Returns:
            (unrealized_pnl, market_value)
        """
        if quantity == 0 or not current_price:
            return Decimal('0'), Decimal('0')
        
        market_value = quantity * current_price
        
        if position_type == 'LONG':
            unrealized_pnl = quantity * (current_price - average_cost)
        else:  # SHORT
            unrealized_pnl = quantity * (average_cost - current_price)
        
        return unrealized_pnl, market_value
    
    @staticmethod
    def calculate_return_rate(pnl: Decimal, cost: Decimal) -> float:
        """
        计算收益率
        
        Args:
            pnl: 盈亏金额
            cost: 成本金额
            
        Returns:
            收益率（小数形式）
        """
        if cost == 0:
            return 0.0
        
        return float(pnl / cost)
    
    @staticmethod
    def calculate_risk_metrics(price_history: List[float], position_quantity: float,
                              position_cost: float) -> Dict[str, float]:
        """
        计算风险指标
        
        Args:
            price_history: 价格历史数据
            position_quantity: 持仓数量
            position_cost: 持仓成本
            
        Returns:
            风险指标字典
        """
        if not price_history or len(price_history) < 2:
            return {
                'volatility': 0.0,
                'var_95': 0.0,
                'var_99': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0
            }
        
        # 转换为numpy数组
        prices = np.array(price_history)
        
        # 计算收益率
        returns = np.diff(prices) / prices[:-1]
        
        # 波动率（年化）
        volatility = np.std(returns) * np.sqrt(252)
        
        # VaR计算
        var_95 = np.percentile(returns, 5) * position_quantity * prices[-1]
        var_99 = np.percentile(returns, 1) * position_quantity * prices[-1]
        
        # 最大回撤
        cumulative_returns = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        # 夏普比率（假设无风险利率为0）
        mean_return = np.mean(returns)
        sharpe_ratio = mean_return / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        return {
            'volatility': float(volatility),
            'var_95': float(var_95),
            'var_99': float(var_99),
            'max_drawdown': float(max_drawdown),
            'sharpe_ratio': float(sharpe_ratio)
        }
    
    @staticmethod
    def calculate_portfolio_correlation(positions_data: List[Dict[str, Any]],
                                      price_data: Dict[str, List[float]]) -> np.ndarray:
        """
        计算投资组合相关性矩阵
        
        Args:
            positions_data: 持仓数据列表
            price_data: 价格数据字典 {symbol: [prices]}
            
        Returns:
            相关性矩阵
        """
        symbols = [pos['symbol'] for pos in positions_data]
        
        # 构建价格矩阵
        price_matrix = []
        for symbol in symbols:
            if symbol in price_data and len(price_data[symbol]) > 1:
                prices = np.array(price_data[symbol])
                returns = np.diff(prices) / prices[:-1]
                price_matrix.append(returns)
        
        if not price_matrix:
            return np.array([])
        
        # 计算相关性矩阵
        price_matrix = np.array(price_matrix)
        correlation_matrix = np.corrcoef(price_matrix)
        
        return correlation_matrix
    
    @staticmethod
    def calculate_position_concentration(positions: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        计算持仓集中度
        
        Args:
            positions: 持仓列表
            
        Returns:
            集中度指标
        """
        if not positions:
            return {
                'herfindahl_index': 0.0,
                'top_5_concentration': 0.0,
                'max_position_weight': 0.0
            }
        
        # 计算总市值
        total_market_value = sum(pos.get('market_value', 0) for pos in positions)
        
        if total_market_value == 0:
            return {
                'herfindahl_index': 0.0,
                'top_5_concentration': 0.0,
                'max_position_weight': 0.0
            }
        
        # 计算权重
        weights = [pos.get('market_value', 0) / total_market_value for pos in positions]
        weights.sort(reverse=True)
        
        # Herfindahl指数
        herfindahl_index = sum(w ** 2 for w in weights)
        
        # 前5大持仓集中度
        top_5_concentration = sum(weights[:5])
        
        # 最大持仓权重
        max_position_weight = weights[0] if weights else 0.0
        
        return {
            'herfindahl_index': herfindahl_index,
            'top_5_concentration': top_5_concentration,
            'max_position_weight': max_position_weight
        }
    
    @staticmethod
    def calculate_optimal_position_size(account_balance: float, risk_per_trade: float,
                                      entry_price: float, stop_loss_price: float) -> float:
        """
        计算最优持仓规模（基于风险管理）
        
        Args:
            account_balance: 账户余额
            risk_per_trade: 每笔交易风险比例（如0.02表示2%）
            entry_price: 入场价格
            stop_loss_price: 止损价格
            
        Returns:
            建议持仓数量
        """
        if entry_price <= 0 or stop_loss_price <= 0 or entry_price == stop_loss_price:
            return 0.0
        
        # 计算每股风险
        risk_per_share = abs(entry_price - stop_loss_price)
        
        # 计算总风险金额
        total_risk_amount = account_balance * risk_per_trade
        
        # 计算持仓数量
        position_size = total_risk_amount / risk_per_share
        
        return position_size
    
    @staticmethod
    def calculate_kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        计算凯利公式建议的仓位比例
        
        Args:
            win_rate: 胜率
            avg_win: 平均盈利
            avg_loss: 平均亏损
            
        Returns:
            建议仓位比例
        """
        if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
            return 0.0
        
        # 凯利公式: f = (bp - q) / b
        # 其中 b = avg_win / avg_loss, p = win_rate, q = 1 - win_rate
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - win_rate
        
        kelly_fraction = (b * p - q) / b
        
        # 限制最大仓位比例
        return max(0.0, min(kelly_fraction, 0.25))  # 最大25%
    
    @staticmethod
    def calculate_position_beta(position_returns: List[float], 
                               market_returns: List[float]) -> float:
        """
        计算持仓相对于市场的贝塔系数
        
        Args:
            position_returns: 持仓收益率序列
            market_returns: 市场收益率序列
            
        Returns:
            贝塔系数
        """
        if len(position_returns) != len(market_returns) or len(position_returns) < 2:
            return 0.0
        
        pos_returns = np.array(position_returns)
        mkt_returns = np.array(market_returns)
        
        # 计算协方差和方差
        covariance = np.cov(pos_returns, mkt_returns)[0, 1]
        market_variance = np.var(mkt_returns)
        
        if market_variance == 0:
            return 0.0
        
        beta = covariance / market_variance
        return float(beta)
    
    @staticmethod
    def calculate_tracking_error(position_returns: List[float],
                                benchmark_returns: List[float]) -> float:
        """
        计算跟踪误差
        
        Args:
            position_returns: 持仓收益率序列
            benchmark_returns: 基准收益率序列
            
        Returns:
            跟踪误差（年化）
        """
        if len(position_returns) != len(benchmark_returns) or len(position_returns) < 2:
            return 0.0
        
        pos_returns = np.array(position_returns)
        bench_returns = np.array(benchmark_returns)
        
        # 计算超额收益
        excess_returns = pos_returns - bench_returns
        
        # 计算跟踪误差（年化）
        tracking_error = np.std(excess_returns) * np.sqrt(252)
        
        return float(tracking_error)
    
    @staticmethod
    def calculate_information_ratio(position_returns: List[float],
                                   benchmark_returns: List[float]) -> float:
        """
        计算信息比率
        
        Args:
            position_returns: 持仓收益率序列
            benchmark_returns: 基准收益率序列
            
        Returns:
            信息比率
        """
        if len(position_returns) != len(benchmark_returns) or len(position_returns) < 2:
            return 0.0
        
        pos_returns = np.array(position_returns)
        bench_returns = np.array(benchmark_returns)
        
        # 计算超额收益
        excess_returns = pos_returns - bench_returns
        
        # 计算平均超额收益和跟踪误差
        avg_excess_return = np.mean(excess_returns)
        tracking_error = np.std(excess_returns)
        
        if tracking_error == 0:
            return 0.0
        
        # 信息比率 = 平均超额收益 / 跟踪误差
        information_ratio = avg_excess_return / tracking_error
        
        return float(information_ratio)

class PositionRiskAnalyzer:
    """持仓风险分析器"""
    
    def __init__(self):
        self.calculator = PositionCalculator()
    
    def analyze_position_risk(self, position_data: Dict[str, Any],
                             price_history: List[float],
                             market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        综合分析持仓风险
        
        Args:
            position_data: 持仓数据
            price_history: 价格历史
            market_data: 市场数据（可选）
            
        Returns:
            风险分析结果
        """
        result = {
            'position_id': position_data.get('id'),
            'symbol': position_data.get('symbol'),
            'risk_level': 'LOW',
            'risk_score': 0.0,
            'risk_factors': [],
            'recommendations': []
        }
        
        # 基础风险指标
        risk_metrics = self.calculator.calculate_risk_metrics(
            price_history,
            float(position_data.get('quantity', 0)),
            float(position_data.get('total_cost', 0))
        )
        
        result['risk_metrics'] = risk_metrics
        
        # 风险评分计算
        risk_score = 0.0
        
        # 波动率风险
        volatility = risk_metrics.get('volatility', 0)
        if volatility > 0.3:  # 30%以上波动率
            risk_score += 30
            result['risk_factors'].append('高波动率')
        elif volatility > 0.2:  # 20-30%波动率
            risk_score += 20
            result['risk_factors'].append('中等波动率')
        
        # 最大回撤风险
        max_drawdown = abs(risk_metrics.get('max_drawdown', 0))
        if max_drawdown > 0.2:  # 20%以上回撤
            risk_score += 25
            result['risk_factors'].append('高回撤风险')
        elif max_drawdown > 0.1:  # 10-20%回撤
            risk_score += 15
            result['risk_factors'].append('中等回撤风险')
        
        # 持仓集中度风险
        position_value = float(position_data.get('market_value', 0))
        if market_data and 'total_portfolio_value' in market_data:
            concentration = position_value / market_data['total_portfolio_value']
            if concentration > 0.2:  # 单一持仓超过20%
                risk_score += 20
                result['risk_factors'].append('持仓过度集中')
            elif concentration > 0.1:  # 单一持仓超过10%
                risk_score += 10
                result['risk_factors'].append('持仓集中度偏高')
        
        # 止损设置风险
        if not position_data.get('stop_loss_price'):
            risk_score += 15
            result['risk_factors'].append('未设置止损')
            result['recommendations'].append('建议设置止损价格')
        
        # 持仓时间风险
        opened_at = position_data.get('opened_at')
        if opened_at:
            from datetime import datetime
            if isinstance(opened_at, str):
                opened_at = datetime.fromisoformat(opened_at.replace('Z', '+00:00'))
            
            holding_days = (datetime.now() - opened_at.replace(tzinfo=None)).days
            if holding_days > 365:  # 持仓超过1年
                risk_score += 10
                result['risk_factors'].append('长期持仓')
        
        # 确定风险等级
        if risk_score >= 70:
            result['risk_level'] = 'HIGH'
        elif risk_score >= 40:
            result['risk_level'] = 'MEDIUM'
        else:
            result['risk_level'] = 'LOW'
        
        result['risk_score'] = risk_score
        
        # 生成建议
        if volatility > 0.25:
            result['recommendations'].append('考虑降低持仓规模以控制风险')
        
        if max_drawdown > 0.15:
            result['recommendations'].append('建议设置更严格的止损策略')
        
        if not result['recommendations']:
            result['recommendations'].append('当前风险水平可接受，继续监控')
        
        return result
    
    def generate_risk_report(self, positions: List[Dict[str, Any]],
                           market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成投资组合风险报告
        
        Args:
            positions: 持仓列表
            market_data: 市场数据
            
        Returns:
            风险报告
        """
        report = {
            'report_date': datetime.now().isoformat(),
            'portfolio_summary': {},
            'risk_analysis': {},
            'position_risks': [],
            'recommendations': []
        }
        
        if not positions:
            return report
        
        # 投资组合摘要
        total_value = sum(float(pos.get('market_value', 0)) for pos in positions)
        total_pnl = sum(float(pos.get('total_pnl', 0)) for pos in positions)
        
        report['portfolio_summary'] = {
            'total_positions': len(positions),
            'total_value': total_value,
            'total_pnl': total_pnl,
            'return_rate': total_pnl / total_value if total_value > 0 else 0
        }
        
        # 集中度分析
        concentration_metrics = self.calculator.calculate_position_concentration(positions)
        report['risk_analysis']['concentration'] = concentration_metrics
        
        # 个别持仓风险分析
        high_risk_count = 0
        for position in positions:
            # 这里需要价格历史数据，实际使用时需要从数据源获取
            price_history = market_data.get('price_history', {}).get(position.get('symbol'), [])
            
            if price_history:
                risk_analysis = self.analyze_position_risk(
                    position, price_history, {'total_portfolio_value': total_value}
                )
                report['position_risks'].append(risk_analysis)
                
                if risk_analysis['risk_level'] == 'HIGH':
                    high_risk_count += 1
        
        # 整体风险评估
        if high_risk_count > len(positions) * 0.3:  # 超过30%的持仓为高风险
            report['risk_analysis']['overall_risk'] = 'HIGH'
            report['recommendations'].append('投资组合整体风险偏高，建议调整持仓结构')
        elif high_risk_count > 0:
            report['risk_analysis']['overall_risk'] = 'MEDIUM'
            report['recommendations'].append('部分持仓存在较高风险，建议重点关注')
        else:
            report['risk_analysis']['overall_risk'] = 'LOW'
            report['recommendations'].append('投资组合风险水平可控')
        
        # 集中度建议
        if concentration_metrics['max_position_weight'] > 0.25:
            report['recommendations'].append('单一持仓占比过高，建议分散投资')
        
        if concentration_metrics['herfindahl_index'] > 0.2:
            report['recommendations'].append('投资组合集中度较高，建议增加持仓多样性')
        
        return report