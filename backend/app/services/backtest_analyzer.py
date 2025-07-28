"""
回测结果分析服务
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import math

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    # 收益指标
    total_return: float = 0.0
    annual_return: float = 0.0
    monthly_return: float = 0.0
    daily_return: float = 0.0
    cumulative_return: float = 0.0
    
    # 风险指标
    volatility: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    var_95: float = 0.0  # 95% VaR
    cvar_95: float = 0.0  # 95% CVaR
    
    # 风险调整收益指标
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    information_ratio: float = 0.0
    
    # 交易指标
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    avg_trade_duration: float = 0.0
    
    # 其他指标
    beta: Optional[float] = None
    alpha: Optional[float] = None
    correlation: Optional[float] = None
    tracking_error: Optional[float] = None
    
    # 极值统计
    best_day: float = 0.0
    worst_day: float = 0.0
    best_month: float = 0.0
    worst_month: float = 0.0
    
    # 分布统计
    skewness: float = 0.0
    kurtosis: float = 0.0
    
    # 回撤统计
    avg_drawdown: float = 0.0
    max_drawdown_start: Optional[datetime] = None
    max_drawdown_end: Optional[datetime] = None


class BacktestAnalyzer:
    """回测结果分析器"""
    
    def __init__(self, risk_free_rate: float = 0.03):
        self.risk_free_rate = risk_free_rate  # 无风险利率
        
    def analyze_backtest_results(self, 
                                equity_curve: List[Dict[str, Any]],
                                trade_records: List[Dict[str, Any]],
                                daily_returns: List[Dict[str, Any]],
                                initial_capital: float,
                                start_date: datetime,
                                end_date: datetime) -> PerformanceMetrics:
        """分析回测结果"""
        try:
            metrics = PerformanceMetrics()
            
            if not equity_curve or not daily_returns:
                logger.warning("缺少必要的回测数据")
                return metrics
            
            # 转换数据格式
            equity_df = self._convert_equity_curve(equity_curve)
            returns_df = self._convert_daily_returns(daily_returns)
            trades_df = self._convert_trade_records(trade_records) if trade_records else pd.DataFrame()
            
            # 计算收益指标
            self._calculate_return_metrics(metrics, equity_df, returns_df, initial_capital, start_date, end_date)
            
            # 计算风险指标
            self._calculate_risk_metrics(metrics, equity_df, returns_df)
            
            # 计算风险调整收益指标
            self._calculate_risk_adjusted_metrics(metrics, returns_df)
            
            # 计算交易指标
            if not trades_df.empty:
                self._calculate_trade_metrics(metrics, trades_df)
            
            # 计算回撤指标
            self._calculate_drawdown_metrics(metrics, equity_df)
            
            # 计算分布统计
            self._calculate_distribution_metrics(metrics, returns_df)
            
            return metrics
            
        except Exception as e:
            logger.error(f"回测结果分析失败: {e}")
            return PerformanceMetrics()
    
    def _convert_equity_curve(self, equity_curve: List[Dict[str, Any]]) -> pd.DataFrame:
        """转换资金曲线数据"""
        df = pd.DataFrame(equity_curve)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        return df
    
    def _convert_daily_returns(self, daily_returns: List[Dict[str, Any]]) -> pd.DataFrame:
        """转换日收益率数据"""
        df = pd.DataFrame(daily_returns)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        return df
    
    def _convert_trade_records(self, trade_records: List[Dict[str, Any]]) -> pd.DataFrame:
        """转换交易记录数据"""
        df = pd.DataFrame(trade_records)
        if not df.empty:
            df['created_time'] = pd.to_datetime(df['created_time'])
            df['filled_time'] = pd.to_datetime(df['filled_time'])
            df.sort_values('filled_time', inplace=True)
        return df
    
    def _calculate_return_metrics(self, metrics: PerformanceMetrics, 
                                 equity_df: pd.DataFrame, 
                                 returns_df: pd.DataFrame,
                                 initial_capital: float,
                                 start_date: datetime,
                                 end_date: datetime):
        """计算收益指标"""
        if equity_df.empty:
            return
        
        final_value = equity_df['total_value'].iloc[-1]
        
        # 总收益率
        metrics.total_return = (final_value - initial_capital) / initial_capital
        
        # 累积收益率
        metrics.cumulative_return = metrics.total_return
        
        # 计算年化收益率
        days = (end_date - start_date).days
        if days > 0:
            years = days / 365.25
            metrics.annual_return = (1 + metrics.total_return) ** (1 / years) - 1
        
        # 计算月收益率和日收益率
        if not returns_df.empty and 'return' in returns_df.columns:
            returns = returns_df['return'].dropna()
            if len(returns) > 0:
                metrics.daily_return = returns.mean()
                metrics.monthly_return = (1 + metrics.daily_return) ** 21 - 1  # 假设21个交易日/月
    
    def _calculate_risk_metrics(self, metrics: PerformanceMetrics, 
                               equity_df: pd.DataFrame, 
                               returns_df: pd.DataFrame):
        """计算风险指标"""
        if returns_df.empty or 'return' in returns_df.columns:
            return
        
        returns = returns_df['return'].dropna()
        if len(returns) == 0:
            return
        
        # 波动率（年化）
        metrics.volatility = returns.std() * np.sqrt(252)
        
        # VaR和CVaR (95%)
        if len(returns) >= 20:  # 至少需要20个观测值
            sorted_returns = returns.sort_values()
            var_index = int(len(sorted_returns) * 0.05)
            metrics.var_95 = abs(sorted_returns.iloc[var_index])
            metrics.cvar_95 = abs(sorted_returns.iloc[:var_index].mean())
        
        # 极值统计
        metrics.best_day = returns.max()
        metrics.worst_day = returns.min()
        
        # 月度收益率极值（如果有足够数据）
        if len(returns) >= 21:
            monthly_returns = returns.rolling(21).sum()
            metrics.best_month = monthly_returns.max()
            metrics.worst_month = monthly_returns.min()
    
    def _calculate_risk_adjusted_metrics(self, metrics: PerformanceMetrics, 
                                       returns_df: pd.DataFrame):
        """计算风险调整收益指标"""
        if returns_df.empty or 'return' not in returns_df.columns:
            return
        
        returns = returns_df['return'].dropna()
        if len(returns) == 0:
            return
        
        daily_risk_free = self.risk_free_rate / 252
        excess_returns = returns - daily_risk_free
        
        # 夏普比率
        if metrics.volatility > 0:
            metrics.sharpe_ratio = (metrics.annual_return - self.risk_free_rate) / metrics.volatility
        
        # 索提诺比率
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 0:
            downside_std = negative_returns.std() * np.sqrt(252)
            if downside_std > 0:
                metrics.sortino_ratio = (metrics.annual_return - self.risk_free_rate) / downside_std
        
        # 卡玛比率
        if metrics.max_drawdown > 0:
            metrics.calmar_ratio = metrics.annual_return / metrics.max_drawdown
        
        # 信息比率（相对于基准的超额收益/跟踪误差）
        # 这里简化为相对于无风险利率
        if len(excess_returns) > 0:
            tracking_error = excess_returns.std() * np.sqrt(252)
            if tracking_error > 0:
                metrics.information_ratio = excess_returns.mean() * 252 / tracking_error
    
    def _calculate_trade_metrics(self, metrics: PerformanceMetrics, trades_df: pd.DataFrame):
        """计算交易指标"""
        if trades_df.empty:
            return
        
        # 基础交易统计
        metrics.total_trades = len(trades_df)
        
        # 计算每笔交易的盈亏（简化计算）
        # 实际应该根据买卖配对计算
        buy_trades = trades_df[trades_df['side'] == 'buy']
        sell_trades = trades_df[trades_df['side'] == 'sell']
        
        # 简化的盈亏计算
        trade_pnls = []
        for _, trade in trades_df.iterrows():
            # 这里需要更复杂的逻辑来计算每笔交易的实际盈亏
            # 暂时使用简化计算
            pnl = 0  # 实际需要根据买卖配对计算
            trade_pnls.append(pnl)
        
        if trade_pnls:
            winning_trades = [pnl for pnl in trade_pnls if pnl > 0]
            losing_trades = [pnl for pnl in trade_pnls if pnl < 0]
            
            metrics.winning_trades = len(winning_trades)
            metrics.losing_trades = len(losing_trades)
            
            if metrics.total_trades > 0:
                metrics.win_rate = metrics.winning_trades / metrics.total_trades
            
            if winning_trades:
                metrics.avg_win = np.mean(winning_trades)
            
            if losing_trades:
                metrics.avg_loss = abs(np.mean(losing_trades))
            
            # 盈亏比
            total_profit = sum(winning_trades)
            total_loss = abs(sum(losing_trades))
            if total_loss > 0:
                metrics.profit_factor = total_profit / total_loss
        
        # 平均交易持续时间
        if 'created_time' in trades_df.columns and 'filled_time' in trades_df.columns:
            durations = (trades_df['filled_time'] - trades_df['created_time']).dt.total_seconds()
            metrics.avg_trade_duration = durations.mean() / 3600  # 转换为小时
    
    def _calculate_drawdown_metrics(self, metrics: PerformanceMetrics, equity_df: pd.DataFrame):
        """计算回撤指标"""
        if equity_df.empty or 'total_value' not in equity_df.columns:
            return
        
        values = equity_df['total_value']
        
        # 计算回撤序列
        peak = values.expanding().max()
        drawdown = (values - peak) / peak
        
        # 最大回撤
        metrics.max_drawdown = abs(drawdown.min())
        
        # 平均回撤
        negative_drawdowns = drawdown[drawdown < 0]
        if len(negative_drawdowns) > 0:
            metrics.avg_drawdown = abs(negative_drawdowns.mean())
        
        # 最大回撤持续时间
        max_dd_idx = drawdown.idxmin()
        if max_dd_idx is not None:
            metrics.max_drawdown_end = max_dd_idx
            
            # 找到回撤开始时间
            before_max_dd = drawdown.loc[:max_dd_idx]
            peak_before = before_max_dd[before_max_dd == 0]
            if not peak_before.empty:
                metrics.max_drawdown_start = peak_before.index[-1]
                
                # 计算持续时间
                duration = (metrics.max_drawdown_end - metrics.max_drawdown_start).days
                metrics.max_drawdown_duration = duration
    
    def _calculate_distribution_metrics(self, metrics: PerformanceMetrics, returns_df: pd.DataFrame):
        """计算分布统计指标"""
        if returns_df.empty or 'return' not in returns_df.columns:
            return
        
        returns = returns_df['return'].dropna()
        if len(returns) < 4:  # 至少需要4个观测值计算偏度和峰度
            return
        
        # 偏度
        metrics.skewness = returns.skew()
        
        # 峰度
        metrics.kurtosis = returns.kurtosis()
    
    def generate_performance_summary(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """生成性能摘要"""
        return {
            "收益指标": {
                "总收益率": f"{metrics.total_return:.2%}",
                "年化收益率": f"{metrics.annual_return:.2%}",
                "月收益率": f"{metrics.monthly_return:.2%}",
                "日收益率": f"{metrics.daily_return:.4%}",
            },
            "风险指标": {
                "年化波动率": f"{metrics.volatility:.2%}",
                "最大回撤": f"{metrics.max_drawdown:.2%}",
                "95% VaR": f"{metrics.var_95:.2%}",
                "95% CVaR": f"{metrics.cvar_95:.2%}",
            },
            "风险调整收益": {
                "夏普比率": f"{metrics.sharpe_ratio:.3f}",
                "索提诺比率": f"{metrics.sortino_ratio:.3f}",
                "卡玛比率": f"{metrics.calmar_ratio:.3f}",
                "信息比率": f"{metrics.information_ratio:.3f}",
            },
            "交易统计": {
                "总交易次数": metrics.total_trades,
                "胜率": f"{metrics.win_rate:.2%}",
                "盈亏比": f"{metrics.profit_factor:.2f}",
                "平均盈利": f"{metrics.avg_win:.2f}",
                "平均亏损": f"{metrics.avg_loss:.2f}",
            },
            "极值统计": {
                "最佳单日": f"{metrics.best_day:.2%}",
                "最差单日": f"{metrics.worst_day:.2%}",
                "最佳月度": f"{metrics.best_month:.2%}",
                "最差月度": f"{metrics.worst_month:.2%}",
            },
            "分布特征": {
                "偏度": f"{metrics.skewness:.3f}",
                "峰度": f"{metrics.kurtosis:.3f}",
            }
        }
    
    def calculate_benchmark_comparison(self, 
                                     strategy_returns: List[float],
                                     benchmark_returns: List[float]) -> Dict[str, float]:
        """计算与基准的比较指标"""
        if not strategy_returns or not benchmark_returns:
            return {}
        
        strategy_series = pd.Series(strategy_returns)
        benchmark_series = pd.Series(benchmark_returns)
        
        # 确保长度一致
        min_length = min(len(strategy_series), len(benchmark_series))
        strategy_series = strategy_series[:min_length]
        benchmark_series = benchmark_series[:min_length]
        
        if len(strategy_series) < 2:
            return {}
        
        # 计算相关性
        correlation = strategy_series.corr(benchmark_series)
        
        # 计算Beta
        covariance = strategy_series.cov(benchmark_series)
        benchmark_variance = benchmark_series.var()
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
        
        # 计算Alpha
        strategy_mean = strategy_series.mean() * 252  # 年化
        benchmark_mean = benchmark_series.mean() * 252  # 年化
        risk_free_daily = self.risk_free_rate / 252
        alpha = strategy_mean - (risk_free_daily * 252 + beta * (benchmark_mean - risk_free_daily * 252))
        
        # 计算跟踪误差
        excess_returns = strategy_series - benchmark_series
        tracking_error = excess_returns.std() * np.sqrt(252)
        
        return {
            "correlation": correlation,
            "beta": beta,
            "alpha": alpha,
            "tracking_error": tracking_error,
            "information_ratio": excess_returns.mean() * 252 / tracking_error if tracking_error > 0 else 0
        }
    
    def calculate_rolling_metrics(self, 
                                 returns_df: pd.DataFrame, 
                                 window: int = 252) -> Dict[str, pd.Series]:
        """计算滚动指标"""
        if returns_df.empty or 'return' not in returns_df.columns:
            return {}
        
        returns = returns_df['return'].dropna()
        
        if len(returns) < window:
            return {}
        
        # 滚动年化收益率
        rolling_return = returns.rolling(window).mean() * 252
        
        # 滚动波动率
        rolling_volatility = returns.rolling(window).std() * np.sqrt(252)
        
        # 滚动夏普比率
        daily_risk_free = self.risk_free_rate / 252
        rolling_sharpe = (rolling_return - self.risk_free_rate) / rolling_volatility
        
        # 滚动最大回撤
        rolling_cumret = (1 + returns).rolling(window).apply(lambda x: x.prod() - 1)
        rolling_peak = rolling_cumret.rolling(window, min_periods=1).max()
        rolling_drawdown = (rolling_cumret - rolling_peak) / rolling_peak
        rolling_max_dd = rolling_drawdown.rolling(window).min().abs()
        
        return {
            "rolling_return": rolling_return,
            "rolling_volatility": rolling_volatility,
            "rolling_sharpe": rolling_sharpe,
            "rolling_max_drawdown": rolling_max_dd
        }
    
    def generate_risk_report(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """生成风险报告"""
        # 风险等级评估
        risk_level = "低"
        if metrics.volatility > 0.20:
            risk_level = "高"
        elif metrics.volatility > 0.15:
            risk_level = "中"
        
        # 回撤风险评估
        drawdown_risk = "低"
        if metrics.max_drawdown > 0.20:
            drawdown_risk = "高"
        elif metrics.max_drawdown > 0.10:
            drawdown_risk = "中"
        
        # 风险建议
        recommendations = []
        
        if metrics.max_drawdown > 0.15:
            recommendations.append("最大回撤较大，建议优化止损策略")
        
        if metrics.volatility > 0.25:
            recommendations.append("波动率较高，建议降低仓位或分散投资")
        
        if metrics.sharpe_ratio < 1.0:
            recommendations.append("夏普比率偏低，建议优化策略以提高风险调整收益")
        
        if metrics.win_rate < 0.4:
            recommendations.append("胜率较低，建议改进选股或择时逻辑")
        
        return {
            "风险等级": risk_level,
            "回撤风险": drawdown_risk,
            "风险指标": {
                "波动率": f"{metrics.volatility:.2%}",
                "最大回撤": f"{metrics.max_drawdown:.2%}",
                "VaR(95%)": f"{metrics.var_95:.2%}",
                "CVaR(95%)": f"{metrics.cvar_95:.2%}",
                "回撤持续时间": f"{metrics.max_drawdown_duration}天",
            },
            "风险建议": recommendations,
            "风险分布": {
                "偏度": metrics.skewness,
                "峰度": metrics.kurtosis,
                "正态性": "正态" if abs(metrics.skewness) < 0.5 and abs(metrics.kurtosis) < 3 else "非正态"
            }
        }