"""
回测结果分析服务
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json
import io
import base64
from decimal import Decimal

from ..models.backtest import Backtest, BacktestStatus
from ..core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class BacktestAnalysisService:
    """回测结果分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_performance_metrics(self, backtest_id: int) -> Dict[str, Any]:
        """计算回测性能指标"""
        try:
            backtest = self.db.query(Backtest).filter(
                Backtest.id == backtest_id,
                Backtest.status == BacktestStatus.COMPLETED
            ).first()
            
            if not backtest:
                raise NotFoundError("回测不存在或未完成")
            
            # 获取回测数据
            equity_curve = backtest.equity_curve or []
            daily_returns = backtest.daily_returns or []
            trades_detail = backtest.trades_detail or []
            
            if not equity_curve or not daily_returns:
                raise ValidationError("回测数据不完整")
            
            # 基础指标
            metrics = self._calculate_basic_metrics(backtest, equity_curve, daily_returns)
            
            # 风险指标
            risk_metrics = self._calculate_risk_metrics(daily_returns, equity_curve)
            metrics.update(risk_metrics)
            
            # 交易指标
            trade_metrics = self._calculate_trade_metrics(trades_detail)
            metrics.update(trade_metrics)
            
            # 基准比较指标
            if backtest.benchmark:
                benchmark_metrics = self._calculate_benchmark_metrics(
                    backtest, daily_returns, equity_curve
                )
                metrics.update(benchmark_metrics)
            
            # 时间序列指标
            time_metrics = self._calculate_time_metrics(backtest, equity_curve)
            metrics.update(time_metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"计算性能指标失败: {str(e)}")
            raise
    
    def _calculate_basic_metrics(self, backtest: Backtest, equity_curve: List[Dict], 
                                daily_returns: List[Dict]) -> Dict[str, Any]:
        """计算基础指标"""
        initial_capital = float(backtest.initial_capital)
        final_capital = equity_curve[-1]['equity'] if equity_curve else initial_capital
        
        # 总收益率
        total_return = (final_capital - initial_capital) / initial_capital
        
        # 年化收益率
        start_date = datetime.fromisoformat(backtest.start_date)
        end_date = datetime.fromisoformat(backtest.end_date)
        days = (end_date - start_date).days
        years = days / 365.25
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # 累计收益
        cumulative_returns = [point['return'] for point in equity_curve]
        
        return {
            'total_return': round(total_return, 4),
            'annual_return': round(annual_return, 4),
            'cumulative_return': round(cumulative_returns[-1] if cumulative_returns else 0, 4),
            'initial_capital': initial_capital,
            'final_capital': round(final_capital, 2),
            'total_pnl': round(final_capital - initial_capital, 2),
            'trading_days': len(daily_returns),
            'calendar_days': days
        }
    
    def _calculate_risk_metrics(self, daily_returns: List[Dict], 
                               equity_curve: List[Dict]) -> Dict[str, Any]:
        """计算风险指标"""
        if not daily_returns:
            return {}
        
        returns = [point['return'] for point in daily_returns]
        returns_array = np.array(returns)
        
        # 波动率
        volatility = np.std(returns_array) * np.sqrt(252)  # 年化波动率
        
        # 夏普比率
        risk_free_rate = 0.03  # 假设无风险利率3%
        excess_returns = returns_array - risk_free_rate / 252
        sharpe_ratio = np.mean(excess_returns) / np.std(returns_array) * np.sqrt(252) if np.std(returns_array) > 0 else 0
        
        # 索提诺比率
        downside_returns = returns_array[returns_array < 0]
        downside_deviation = np.std(downside_returns) if len(downside_returns) > 0 else 0
        sortino_ratio = np.mean(excess_returns) / downside_deviation * np.sqrt(252) if downside_deviation > 0 else 0
        
        # 最大回撤
        equity_values = [point['equity'] for point in equity_curve]
        peak = np.maximum.accumulate(equity_values)
        drawdown = (np.array(equity_values) - peak) / peak
        max_drawdown = np.min(drawdown)
        
        # 卡玛比率
        calmar_ratio = np.mean(returns_array) * 252 / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # VaR (Value at Risk)
        var_95 = np.percentile(returns_array, 5)
        var_99 = np.percentile(returns_array, 1)
        
        # CVaR (Conditional Value at Risk)
        cvar_95 = np.mean(returns_array[returns_array <= var_95])
        cvar_99 = np.mean(returns_array[returns_array <= var_99])
        
        # 最大回撤持续时间
        drawdown_duration = self._calculate_drawdown_duration(equity_values)
        
        return {
            'volatility': round(volatility, 4),
            'sharpe_ratio': round(sharpe_ratio, 4),
            'sortino_ratio': round(sortino_ratio, 4),
            'max_drawdown': round(abs(max_drawdown), 4),
            'calmar_ratio': round(calmar_ratio, 4),
            'var_95': round(var_95, 4),
            'var_99': round(var_99, 4),
            'cvar_95': round(cvar_95, 4),
            'cvar_99': round(cvar_99, 4),
            'max_drawdown_duration': drawdown_duration,
            'downside_deviation': round(downside_deviation, 4)
        }
    
    def _calculate_trade_metrics(self, trades_detail: List[Dict]) -> Dict[str, Any]:
        """计算交易指标"""
        if not trades_detail:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'avg_trade_duration': 0,
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0
            }
        
        # 分离买卖交易
        buy_trades = [t for t in trades_detail if t['side'] == 'buy']
        sell_trades = [t for t in trades_detail if t['side'] == 'sell']
        
        # 计算每笔交易的盈亏
        trade_pnls = [t['pnl'] for t in trades_detail if 'pnl' in t]
        
        if not trade_pnls:
            return {
                'total_trades': len(trades_detail),
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0
            }
        
        # 盈利和亏损交易
        winning_trades = [pnl for pnl in trade_pnls if pnl > 0]
        losing_trades = [pnl for pnl in trade_pnls if pnl < 0]
        
        # 基础统计
        total_trades = len(trade_pnls)
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        win_rate = win_count / total_trades if total_trades > 0 else 0
        
        # 平均盈亏
        avg_win = np.mean(winning_trades) if winning_trades else 0
        avg_loss = np.mean(losing_trades) if losing_trades else 0
        
        # 盈亏比
        profit_factor = sum(winning_trades) / abs(sum(losing_trades)) if losing_trades else float('inf')
        
        # 最大连续盈亏
        max_consecutive_wins = self._calculate_max_consecutive(trade_pnls, lambda x: x > 0)
        max_consecutive_losses = self._calculate_max_consecutive(trade_pnls, lambda x: x < 0)
        
        # 交易频率
        trade_frequency = self._calculate_trade_frequency(trades_detail)
        
        return {
            'total_trades': total_trades,
            'winning_trades': win_count,
            'losing_trades': loss_count,
            'win_rate': round(win_rate, 4),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 4) if profit_factor != float('inf') else 999.99,
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses,
            'trade_frequency': trade_frequency,
            'avg_trade_pnl': round(np.mean(trade_pnls), 2),
            'best_trade': round(max(trade_pnls), 2),
            'worst_trade': round(min(trade_pnls), 2)
        }
    
    def _calculate_benchmark_metrics(self, backtest: Backtest, daily_returns: List[Dict],
                                   equity_curve: List[Dict]) -> Dict[str, Any]:
        """计算基准比较指标"""
        # 这里需要获取基准数据，简化处理
        # 实际应用中需要从数据源获取基准指数的历史数据
        
        # 模拟基准收益率（实际应该从数据库或API获取）
        benchmark_returns = self._get_benchmark_returns(backtest.benchmark, 
                                                       backtest.start_date, 
                                                       backtest.end_date)
        
        if not benchmark_returns:
            return {}
        
        strategy_returns = [point['return'] for point in daily_returns]
        
        # 确保长度一致
        min_length = min(len(strategy_returns), len(benchmark_returns))
        strategy_returns = strategy_returns[:min_length]
        benchmark_returns = benchmark_returns[:min_length]
        
        strategy_array = np.array(strategy_returns)
        benchmark_array = np.array(benchmark_returns)
        
        # 阿尔法和贝塔
        covariance = np.cov(strategy_array, benchmark_array)[0, 1]
        benchmark_variance = np.var(benchmark_array)
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
        
        risk_free_rate = 0.03 / 252  # 日无风险利率
        alpha = np.mean(strategy_array) - risk_free_rate - beta * (np.mean(benchmark_array) - risk_free_rate)
        alpha_annualized = alpha * 252
        
        # 信息比率
        excess_returns = strategy_array - benchmark_array
        tracking_error = np.std(excess_returns) * np.sqrt(252)
        information_ratio = np.mean(excess_returns) * 252 / tracking_error if tracking_error > 0 else 0
        
        # 基准总收益率
        benchmark_total_return = (1 + benchmark_array).prod() - 1
        
        return {
            'benchmark': backtest.benchmark,
            'benchmark_return': round(benchmark_total_return, 4),
            'alpha': round(alpha_annualized, 4),
            'beta': round(beta, 4),
            'information_ratio': round(information_ratio, 4),
            'tracking_error': round(tracking_error, 4),
            'correlation': round(np.corrcoef(strategy_array, benchmark_array)[0, 1], 4)
        }
    
    def _calculate_time_metrics(self, backtest: Backtest, equity_curve: List[Dict]) -> Dict[str, Any]:
        """计算时间相关指标"""
        if not equity_curve:
            return {}
        
        # 按月统计收益
        monthly_returns = self._calculate_monthly_returns(equity_curve)
        
        # 最佳和最差月份
        best_month = max(monthly_returns) if monthly_returns else 0
        worst_month = min(monthly_returns) if monthly_returns else 0
        
        # 正收益月份比例
        positive_months = len([r for r in monthly_returns if r > 0])
        positive_month_ratio = positive_months / len(monthly_returns) if monthly_returns else 0
        
        return {
            'monthly_returns': monthly_returns,
            'best_month': round(best_month, 4),
            'worst_month': round(worst_month, 4),
            'positive_months': positive_months,
            'total_months': len(monthly_returns),
            'positive_month_ratio': round(positive_month_ratio, 4)
        }
    
    def generate_analysis_report(self, backtest_id: int) -> Dict[str, Any]:
        """生成分析报告"""
        try:
            backtest = self.db.query(Backtest).filter(Backtest.id == backtest_id).first()
            if not backtest:
                raise NotFoundError("回测不存在")
            
            # 计算性能指标
            metrics = self.calculate_performance_metrics(backtest_id)
            
            # 生成图表数据
            charts = self.generate_chart_data(backtest_id)
            
            # 生成交易分析
            trade_analysis = self.analyze_trades(backtest_id)
            
            # 生成风险分析
            risk_analysis = self.analyze_risk(backtest_id)
            
            # 生成总结和建议
            summary = self._generate_summary(backtest, metrics)
            recommendations = self._generate_recommendations(metrics, trade_analysis)
            
            report = {
                'backtest_info': {
                    'id': backtest.id,
                    'name': backtest.name,
                    'description': backtest.description,
                    'strategy_id': backtest.strategy_id,
                    'start_date': backtest.start_date,
                    'end_date': backtest.end_date,
                    'initial_capital': float(backtest.initial_capital),
                    'status': backtest.status,
                    'created_at': backtest.created_at.isoformat()
                },
                'performance_metrics': metrics,
                'charts': charts,
                'trade_analysis': trade_analysis,
                'risk_analysis': risk_analysis,
                'summary': summary,
                'recommendations': recommendations,
                'generated_at': datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成分析报告失败: {str(e)}")
            raise
    
    def generate_chart_data(self, backtest_id: int) -> Dict[str, Any]:
        """生成图表数据"""
        try:
            backtest = self.db.query(Backtest).filter(Backtest.id == backtest_id).first()
            if not backtest:
                raise NotFoundError("回测不存在")
            
            charts = {}
            
            # 净值曲线
            if backtest.equity_curve:
                charts['equity_curve'] = self._format_equity_curve(backtest.equity_curve)
            
            # 回撤曲线
            if backtest.drawdown_curve:
                charts['drawdown_curve'] = self._format_drawdown_curve(backtest.drawdown_curve)
            
            # 日收益率分布
            if backtest.daily_returns:
                charts['returns_distribution'] = self._format_returns_distribution(backtest.daily_returns)
            
            # 月度收益热力图
            if backtest.daily_returns:
                charts['monthly_returns_heatmap'] = self._format_monthly_heatmap(backtest.daily_returns)
            
            # 交易分析图表
            if backtest.trades_detail:
                charts['trade_analysis'] = self._format_trade_charts(backtest.trades_detail)
            
            # 持仓分析
            if backtest.positions:
                charts['position_analysis'] = self._format_position_charts(backtest.positions)
            
            return charts
            
        except Exception as e:
            logger.error(f"生成图表数据失败: {str(e)}")
            raise
    
    def analyze_trades(self, backtest_id: int) -> Dict[str, Any]:
        """分析交易记录"""
        try:
            backtest = self.db.query(Backtest).filter(Backtest.id == backtest_id).first()
            if not backtest or not backtest.trades_detail:
                return {}
            
            trades = backtest.trades_detail
            
            # 交易时间分析
            time_analysis = self._analyze_trade_timing(trades)
            
            # 持仓时间分析
            holding_analysis = self._analyze_holding_periods(trades)
            
            # 盈亏分析
            pnl_analysis = self._analyze_trade_pnl(trades)
            
            # 交易规模分析
            size_analysis = self._analyze_trade_sizes(trades)
            
            return {
                'time_analysis': time_analysis,
                'holding_analysis': holding_analysis,
                'pnl_analysis': pnl_analysis,
                'size_analysis': size_analysis,
                'trade_summary': {
                    'total_trades': len(trades),
                    'buy_trades': len([t for t in trades if t['side'] == 'buy']),
                    'sell_trades': len([t for t in trades if t['side'] == 'sell']),
                    'avg_trade_size': np.mean([t['quantity'] for t in trades]),
                    'total_volume': sum([t['quantity'] * t['price'] for t in trades])
                }
            }
            
        except Exception as e:
            logger.error(f"分析交易记录失败: {str(e)}")
            raise
    
    def analyze_risk(self, backtest_id: int) -> Dict[str, Any]:
        """分析风险指标"""
        try:
            backtest = self.db.query(Backtest).filter(Backtest.id == backtest_id).first()
            if not backtest:
                raise NotFoundError("回测不存在")
            
            # 获取收益率数据
            daily_returns = backtest.daily_returns or []
            if not daily_returns:
                return {}
            
            returns = [point['return'] for point in daily_returns]
            returns_array = np.array(returns)
            
            # 风险度量
            risk_measures = {
                'volatility': np.std(returns_array) * np.sqrt(252),
                'skewness': self._calculate_skewness(returns_array),
                'kurtosis': self._calculate_kurtosis(returns_array),
                'var_95': np.percentile(returns_array, 5),
                'var_99': np.percentile(returns_array, 1),
                'max_daily_loss': np.min(returns_array),
                'max_daily_gain': np.max(returns_array)
            }
            
            # 回撤分析
            drawdown_analysis = self._analyze_drawdowns(backtest.equity_curve or [])
            
            # 风险调整收益
            risk_adjusted_returns = self._calculate_risk_adjusted_returns(returns_array)
            
            return {
                'risk_measures': risk_measures,
                'drawdown_analysis': drawdown_analysis,
                'risk_adjusted_returns': risk_adjusted_returns,
                'risk_level': self._assess_risk_level(risk_measures)
            }
            
        except Exception as e:
            logger.error(f"分析风险指标失败: {str(e)}")
            raise
    
    def export_report(self, backtest_id: int, format: str = 'json') -> bytes:
        """导出分析报告"""
        try:
            report = self.generate_analysis_report(backtest_id)
            
            if format.lower() == 'json':
                return json.dumps(report, indent=2, ensure_ascii=False).encode('utf-8')
            elif format.lower() == 'csv':
                return self._export_to_csv(report)
            elif format.lower() == 'excel':
                return self._export_to_excel(report)
            else:
                raise ValidationError(f"不支持的导出格式: {format}")
                
        except Exception as e:
            logger.error(f"导出报告失败: {str(e)}")
            raise
    
    # 辅助方法
    def _calculate_drawdown_duration(self, equity_values: List[float]) -> int:
        """计算最大回撤持续时间"""
        peak = equity_values[0]
        max_duration = 0
        current_duration = 0
        
        for value in equity_values:
            if value >= peak:
                peak = value
                current_duration = 0
            else:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
        
        return max_duration
    
    def _calculate_max_consecutive(self, values: List[float], condition) -> int:
        """计算最大连续次数"""
        max_count = 0
        current_count = 0
        
        for value in values:
            if condition(value):
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0
        
        return max_count
    
    def _calculate_trade_frequency(self, trades: List[Dict]) -> Dict[str, float]:
        """计算交易频率"""
        if not trades:
            return {'daily': 0, 'weekly': 0, 'monthly': 0}
        
        # 简化计算，实际需要根据交易时间计算
        total_days = 252  # 假设一年交易日
        total_trades = len(trades)
        
        return {
            'daily': round(total_trades / total_days, 2),
            'weekly': round(total_trades / (total_days / 5), 2),
            'monthly': round(total_trades / (total_days / 21), 2)
        }
    
    def _get_benchmark_returns(self, benchmark: str, start_date: str, end_date: str) -> List[float]:
        """获取基准收益率（模拟数据）"""
        # 实际应用中需要从数据源获取真实的基准数据
        # 这里生成模拟数据
        np.random.seed(42)
        days = (datetime.fromisoformat(end_date) - datetime.fromisoformat(start_date)).days
        return np.random.normal(0.0005, 0.015, days).tolist()
    
    def _calculate_monthly_returns(self, equity_curve: List[Dict]) -> List[float]:
        """计算月度收益率"""
        if not equity_curve:
            return []
        
        # 简化处理，实际需要按月分组计算
        monthly_returns = []
        for i in range(0, len(equity_curve), 21):  # 假设每月21个交易日
            if i + 21 < len(equity_curve):
                start_equity = equity_curve[i]['equity']
                end_equity = equity_curve[i + 21]['equity']
                monthly_return = (end_equity - start_equity) / start_equity
                monthly_returns.append(monthly_return)
        
        return monthly_returns
    
    def _generate_summary(self, backtest: Backtest, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """生成总结"""
        return {
            'overall_performance': 'excellent' if metrics.get('sharpe_ratio', 0) > 2 else 
                                 'good' if metrics.get('sharpe_ratio', 0) > 1 else 
                                 'average' if metrics.get('sharpe_ratio', 0) > 0 else 'poor',
            'key_strengths': self._identify_strengths(metrics),
            'key_weaknesses': self._identify_weaknesses(metrics),
            'risk_assessment': 'low' if metrics.get('max_drawdown', 1) < 0.1 else 
                             'medium' if metrics.get('max_drawdown', 1) < 0.2 else 'high'
        }
    
    def _generate_recommendations(self, metrics: Dict[str, Any], trade_analysis: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if metrics.get('max_drawdown', 0) > 0.2:
            recommendations.append("考虑加强风险控制，降低最大回撤")
        
        if metrics.get('win_rate', 0) < 0.4:
            recommendations.append("优化策略逻辑，提高胜率")
        
        if metrics.get('sharpe_ratio', 0) < 1:
            recommendations.append("改善风险调整收益，提高夏普比率")
        
        return recommendations
    
    def _identify_strengths(self, metrics: Dict[str, Any]) -> List[str]:
        """识别优势"""
        strengths = []
        
        if metrics.get('sharpe_ratio', 0) > 1.5:
            strengths.append("优秀的风险调整收益")
        
        if metrics.get('win_rate', 0) > 0.6:
            strengths.append("较高的胜率")
        
        if metrics.get('max_drawdown', 1) < 0.1:
            strengths.append("良好的风险控制")
        
        return strengths
    
    def _identify_weaknesses(self, metrics: Dict[str, Any]) -> List[str]:
        """识别劣势"""
        weaknesses = []
        
        if metrics.get('max_drawdown', 0) > 0.3:
            weaknesses.append("回撤过大")
        
        if metrics.get('win_rate', 1) < 0.3:
            weaknesses.append("胜率偏低")
        
        if metrics.get('volatility', 0) > 0.3:
            weaknesses.append("波动率较高")
        
        return weaknesses
    
    # 格式化图表数据的方法
    def _format_equity_curve(self, equity_curve: List[Dict]) -> Dict[str, Any]:
        """格式化净值曲线数据"""
        return {
            'type': 'line',
            'title': '净值曲线',
            'data': [
                {
                    'date': point['date'],
                    'equity': point['equity'],
                    'return': point.get('return', 0)
                }
                for point in equity_curve
            ]
        }
    
    def _format_drawdown_curve(self, drawdown_curve: List[Dict]) -> Dict[str, Any]:
        """格式化回撤曲线数据"""
        return {
            'type': 'area',
            'title': '回撤曲线',
            'data': [
                {
                    'date': point['date'],
                    'drawdown': point['drawdown']
                }
                for point in drawdown_curve
            ]
        }
    
    def _format_returns_distribution(self, daily_returns: List[Dict]) -> Dict[str, Any]:
        """格式化收益率分布数据"""
        returns = [point['return'] for point in daily_returns]
        
        # 计算直方图数据
        hist, bins = np.histogram(returns, bins=50)
        
        return {
            'type': 'histogram',
            'title': '日收益率分布',
            'data': {
                'bins': bins.tolist(),
                'counts': hist.tolist(),
                'statistics': {
                    'mean': np.mean(returns),
                    'std': np.std(returns),
                    'skewness': self._calculate_skewness(np.array(returns)),
                    'kurtosis': self._calculate_kurtosis(np.array(returns))
                }
            }
        }
    
    def _calculate_skewness(self, data: np.ndarray) -> float:
        """计算偏度"""
        mean = np.mean(data)
        std = np.std(data)
        return np.mean(((data - mean) / std) ** 3) if std > 0 else 0
    
    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """计算峰度"""
        mean = np.mean(data)
        std = np.std(data)
        return np.mean(((data - mean) / std) ** 4) - 3 if std > 0 else 0
    
    def _format_monthly_heatmap(self, daily_returns: List[Dict]) -> Dict[str, Any]:
        """格式化月度收益热力图数据"""
        # 简化处理，实际需要按年月分组
        return {
            'type': 'heatmap',
            'title': '月度收益热力图',
            'data': []  # 需要实现具体的月度分组逻辑
        }
    
    def _format_trade_charts(self, trades_detail: List[Dict]) -> Dict[str, Any]:
        """格式化交易分析图表"""
        return {
            'trade_pnl': {
                'type': 'bar',
                'title': '交易盈亏分布',
                'data': [
                    {
                        'trade_id': trade.get('id', i),
                        'pnl': trade.get('pnl', 0),
                        'side': trade.get('side', 'unknown')
                    }
                    for i, trade in enumerate(trades_detail)
                ]
            }
        }
    
    def _format_position_charts(self, positions: List[Dict]) -> Dict[str, Any]:
        """格式化持仓分析图表"""
        return {
            'position_value': {
                'type': 'area',
                'title': '持仓价值变化',
                'data': positions
            }
        }
    
    def _analyze_trade_timing(self, trades: List[Dict]) -> Dict[str, Any]:
        """分析交易时机"""
        return {
            'hour_distribution': {},  # 按小时分布
            'day_distribution': {},   # 按星期分布
            'month_distribution': {}  # 按月份分布
        }
    
    def _analyze_holding_periods(self, trades: List[Dict]) -> Dict[str, Any]:
        """分析持仓时间"""
        return {
            'avg_holding_period': 0,
            'max_holding_period': 0,
            'min_holding_period': 0
        }
    
    def _analyze_trade_pnl(self, trades: List[Dict]) -> Dict[str, Any]:
        """分析交易盈亏"""
        pnls = [trade.get('pnl', 0) for trade in trades]
        
        return {
            'total_pnl': sum(pnls),
            'avg_pnl': np.mean(pnls) if pnls else 0,
            'best_trade': max(pnls) if pnls else 0,
            'worst_trade': min(pnls) if pnls else 0,
            'pnl_std': np.std(pnls) if pnls else 0
        }
    
    def _analyze_trade_sizes(self, trades: List[Dict]) -> Dict[str, Any]:
        """分析交易规模"""
        sizes = [trade.get('quantity', 0) for trade in trades]
        
        return {
            'avg_size': np.mean(sizes) if sizes else 0,
            'max_size': max(sizes) if sizes else 0,
            'min_size': min(sizes) if sizes else 0,
            'size_std': np.std(sizes) if sizes else 0
        }
    
    def _analyze_drawdowns(self, equity_curve: List[Dict]) -> Dict[str, Any]:
        """分析回撤"""
        if not equity_curve:
            return {}
        
        equity_values = [point['equity'] for point in equity_curve]
        peak = np.maximum.accumulate(equity_values)
        drawdown = (np.array(equity_values) - peak) / peak
        
        return {
            'max_drawdown': np.min(drawdown),
            'avg_drawdown': np.mean(drawdown[drawdown < 0]) if any(drawdown < 0) else 0,
            'drawdown_periods': len([d for d in drawdown if d < 0]),
            'recovery_time': self._calculate_drawdown_duration(equity_values)
        }
    
    def _calculate_risk_adjusted_returns(self, returns: np.ndarray) -> Dict[str, float]:
        """计算风险调整收益"""
        if len(returns) == 0:
            return {}
        
        return {
            'sharpe_ratio': np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0,
            'calmar_ratio': np.mean(returns) * 252 / abs(np.min(returns)) if np.min(returns) < 0 else 0,
            'omega_ratio': self._calculate_omega_ratio(returns)
        }
    
    def _calculate_omega_ratio(self, returns: np.ndarray, threshold: float = 0) -> float:
        """计算Omega比率"""
        gains = returns[returns > threshold]
        losses = returns[returns <= threshold]
        
        if len(losses) == 0:
            return float('inf')
        
        return np.sum(gains - threshold) / np.sum(threshold - losses) if np.sum(threshold - losses) > 0 else 0
    
    def _assess_risk_level(self, risk_measures: Dict[str, float]) -> str:
        """评估风险水平"""
        volatility = risk_measures.get('volatility', 0)
        
        if volatility < 0.1:
            return 'low'
        elif volatility < 0.2:
            return 'medium'
        else:
            return 'high'
    
    def _export_to_csv(self, report: Dict[str, Any]) -> bytes:
        """导出为CSV格式"""
        # 简化实现，实际需要更复杂的CSV格式化
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入性能指标
        writer.writerow(['指标', '数值'])
        for key, value in report.get('performance_metrics', {}).items():
            writer.writerow([key, value])
        
        return output.getvalue().encode('utf-8')
    
    def _export_to_excel(self, report: Dict[str, Any]) -> bytes:
        """导出为Excel格式"""
        # 需要安装openpyxl库
        try:
            import openpyxl
            from openpyxl import Workbook
            
            wb = Workbook()
            ws = wb.active
            ws.title = "回测报告"
            
            # 写入基本信息
            ws.append(['回测报告'])
            ws.append(['生成时间', report.get('generated_at', '')])
            ws.append([])
            
            # 写入性能指标
            ws.append(['性能指标'])
            for key, value in report.get('performance_metrics', {}).items():
                ws.append([key, value])
            
            # 保存到字节流
            output = io.BytesIO()
            wb.save(output)
            return output.getvalue()
            
        except ImportError:
            raise ValidationError("需要安装openpyxl库才能导出Excel格式")
        except Exception as e:
            raise ValidationError(f"导出Excel失败: {str(e)}")