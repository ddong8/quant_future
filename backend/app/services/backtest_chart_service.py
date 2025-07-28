"""
回测图表数据格式化服务
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class BacktestChartService:
    """回测图表数据格式化服务"""
    
    def __init__(self):
        pass
    
    def format_equity_curve_data(self, equity_curve: List[Dict[str, Any]]) -> Dict[str, Any]:
        """格式化资金曲线数据"""
        try:
            if not equity_curve:
                return {"timestamps": [], "values": [], "cash": [], "market_value": []}
            
            df = pd.DataFrame(equity_curve)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.sort_values('timestamp', inplace=True)
            
            return {
                "timestamps": df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                "values": df['total_value'].tolist(),
                "cash": df['available_cash'].tolist(),
                "market_value": df['market_value'].tolist(),
                "unrealized_pnl": df['unrealized_pnl'].tolist(),
                "realized_pnl": df['realized_pnl'].tolist(),
            }
            
        except Exception as e:
            logger.error(f"格式化资金曲线数据失败: {e}")
            return {"timestamps": [], "values": [], "cash": [], "market_value": []}
    
    def format_drawdown_data(self, equity_curve: List[Dict[str, Any]]) -> Dict[str, Any]:
        """格式化回撤数据"""
        try:
            if not equity_curve:
                return {"timestamps": [], "drawdown": [], "underwater": []}
            
            df = pd.DataFrame(equity_curve)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.sort_values('timestamp', inplace=True)
            
            # 计算回撤
            peak = df['total_value'].expanding().max()
            drawdown = (df['total_value'] - peak) / peak
            
            # 水下时间（连续回撤期间）
            underwater = (drawdown < 0).astype(int)
            
            return {
                "timestamps": df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                "drawdown": drawdown.tolist(),
                "underwater": underwater.tolist(),
                "peak_values": peak.tolist(),
            }
            
        except Exception as e:
            logger.error(f"格式化回撤数据失败: {e}")
            return {"timestamps": [], "drawdown": [], "underwater": []}
    
    def format_returns_distribution_data(self, daily_returns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """格式化收益率分布数据"""
        try:
            if not daily_returns:
                return {"returns": [], "histogram": {"bins": [], "counts": []}}
            
            df = pd.DataFrame(daily_returns)
            returns = df['return'].dropna()
            
            if len(returns) == 0:
                return {"returns": [], "histogram": {"bins": [], "counts": []}}
            
            # 直方图数据
            counts, bins = np.histogram(returns, bins=50)
            bin_centers = (bins[:-1] + bins[1:]) / 2
            
            # 统计信息
            stats = {
                "mean": returns.mean(),
                "std": returns.std(),
                "skewness": returns.skew(),
                "kurtosis": returns.kurtosis(),
                "min": returns.min(),
                "max": returns.max(),
                "percentiles": {
                    "5%": returns.quantile(0.05),
                    "25%": returns.quantile(0.25),
                    "50%": returns.quantile(0.50),
                    "75%": returns.quantile(0.75),
                    "95%": returns.quantile(0.95),
                }
            }
            
            return {
                "returns": returns.tolist(),
                "histogram": {
                    "bins": bin_centers.tolist(),
                    "counts": counts.tolist(),
                },
                "statistics": stats,
            }
            
        except Exception as e:
            logger.error(f"格式化收益率分布数据失败: {e}")
            return {"returns": [], "histogram": {"bins": [], "counts": []}}
    
    def format_monthly_returns_data(self, daily_returns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """格式化月度收益率数据"""
        try:
            if not daily_returns:
                return {"years": [], "months": [], "returns": []}
            
            df = pd.DataFrame(daily_returns)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # 计算月度收益
            monthly_returns = df['return'].resample('M').apply(lambda x: (1 + x).prod() - 1)
            
            # 创建热力图数据
            heatmap_data = []
            years = []
            months = list(range(1, 13))
            
            for year in sorted(monthly_returns.index.year.unique()):
                year_data = []
                years.append(year)
                
                for month in months:
                    try:
                        value = monthly_returns[
                            (monthly_returns.index.year == year) & 
                            (monthly_returns.index.month == month)
                        ].iloc[0]
                        year_data.append(value)
                    except (IndexError, KeyError):
                        year_data.append(None)
                
                heatmap_data.append(year_data)
            
            return {
                "years": years,
                "months": months,
                "returns": heatmap_data,
                "month_names": ["1月", "2月", "3月", "4月", "5月", "6月", 
                              "7月", "8月", "9月", "10月", "11月", "12月"],
            }
            
        except Exception as e:
            logger.error(f"格式化月度收益率数据失败: {e}")
            return {"years": [], "months": [], "returns": []}
    
    def format_rolling_metrics_data(self, daily_returns: List[Dict[str, Any]], window: int = 252) -> Dict[str, Any]:
        """格式化滚动指标数据"""
        try:
            if not daily_returns:
                return {"timestamps": [], "metrics": {}}
            
            df = pd.DataFrame(daily_returns)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            returns = df['return'].dropna()
            
            if len(returns) < window:
                return {"timestamps": [], "metrics": {}}
            
            # 计算滚动指标
            rolling_return = returns.rolling(window).mean() * 252
            rolling_volatility = returns.rolling(window).std() * np.sqrt(252)
            rolling_sharpe = (rolling_return - 0.03) / rolling_volatility  # 假设无风险利率3%
            
            # 滚动最大回撤
            rolling_cumret = (1 + returns).rolling(window).apply(lambda x: x.prod() - 1)
            rolling_peak = rolling_cumret.rolling(window, min_periods=1).max()
            rolling_drawdown = (rolling_cumret - rolling_peak) / rolling_peak
            rolling_max_dd = rolling_drawdown.rolling(window).min().abs()
            
            # 过滤有效数据
            valid_data = rolling_return.dropna()
            
            return {
                "timestamps": valid_data.index.strftime('%Y-%m-%d').tolist(),
                "metrics": {
                    "rolling_return": rolling_return.dropna().tolist(),
                    "rolling_volatility": rolling_volatility.dropna().tolist(),
                    "rolling_sharpe": rolling_sharpe.dropna().tolist(),
                    "rolling_max_drawdown": rolling_max_dd.dropna().tolist(),
                },
                "window": window,
            }
            
        except Exception as e:
            logger.error(f"格式化滚动指标数据失败: {e}")
            return {"timestamps": [], "metrics": {}}
    
    def format_trade_analysis_data(self, trade_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """格式化交易分析数据"""
        try:
            if not trade_records:
                return {"symbols": {}, "hourly": {}, "daily": {}, "summary": {}}
            
            df = pd.DataFrame(trade_records)
            
            # 按品种分析
            symbol_analysis = {}
            for symbol in df['symbol'].unique():
                symbol_df = df[df['symbol'] == symbol]
                symbol_analysis[symbol] = {
                    "total_trades": len(symbol_df),
                    "buy_trades": len(symbol_df[symbol_df['side'] == 'buy']),
                    "sell_trades": len(symbol_df[symbol_df['side'] == 'sell']),
                    "avg_quantity": symbol_df['quantity'].mean(),
                    "total_commission": symbol_df['commission'].sum() if 'commission' in symbol_df.columns else 0,
                }
            
            # 时间分布分析
            hourly_distribution = {}
            daily_distribution = {}
            
            if 'filled_time' in df.columns:
                df['filled_time'] = pd.to_datetime(df['filled_time'])
                
                # 小时分布
                df['hour'] = df['filled_time'].dt.hour
                hourly_counts = df['hour'].value_counts().sort_index()
                hourly_distribution = {
                    "hours": hourly_counts.index.tolist(),
                    "counts": hourly_counts.values.tolist(),
                }
                
                # 日期分布
                df['date'] = df['filled_time'].dt.date
                daily_counts = df['date'].value_counts().sort_index()
                daily_distribution = {
                    "dates": [str(date) for date in daily_counts.index],
                    "counts": daily_counts.values.tolist(),
                }
            
            # 交易摘要
            summary = {
                "total_trades": len(df),
                "unique_symbols": df['symbol'].nunique(),
                "total_quantity": df['quantity'].sum(),
                "total_commission": df['commission'].sum() if 'commission' in df.columns else 0,
                "avg_commission_per_trade": df['commission'].mean() if 'commission' in df.columns else 0,
            }
            
            return {
                "symbols": symbol_analysis,
                "hourly": hourly_distribution,
                "daily": daily_distribution,
                "summary": summary,
            }
            
        except Exception as e:
            logger.error(f"格式化交易分析数据失败: {e}")
            return {"symbols": {}, "hourly": {}, "daily": {}, "summary": {}}
    
    def format_comparison_data(self, backtests_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """格式化比较数据"""
        try:
            if not backtests_data:
                return {"metrics": [], "radar_chart": {}, "correlation": {}}
            
            # 提取指标数据
            metrics_data = []
            for data in backtests_data:
                metrics_data.append({
                    "name": data.get("name", "未知"),
                    "total_return": data.get("total_return", 0),
                    "annual_return": data.get("annual_return", 0),
                    "max_drawdown": data.get("max_drawdown", 0),
                    "sharpe_ratio": data.get("sharpe_ratio", 0),
                    "sortino_ratio": data.get("sortino_ratio", 0),
                    "win_rate": data.get("win_rate", 0),
                    "profit_factor": data.get("profit_factor", 0),
                    "volatility": data.get("volatility", 0),
                })
            
            # 雷达图数据
            radar_metrics = ["total_return", "sharpe_ratio", "win_rate", "profit_factor"]
            radar_data = {
                "metrics": radar_metrics,
                "strategies": []
            }
            
            for data in metrics_data:
                strategy_values = []
                for metric in radar_metrics:
                    value = data.get(metric, 0)
                    # 标准化处理（简单的0-1标准化）
                    if metric == "total_return":
                        normalized_value = max(0, min(1, (value + 1) / 2))  # -100%到100%映射到0-1
                    elif metric == "sharpe_ratio":
                        normalized_value = max(0, min(1, (value + 2) / 4))  # -2到2映射到0-1
                    elif metric in ["win_rate"]:
                        normalized_value = max(0, min(1, value))  # 0-1
                    elif metric == "profit_factor":
                        normalized_value = max(0, min(1, value / 3))  # 0-3映射到0-1
                    else:
                        normalized_value = value
                    
                    strategy_values.append(normalized_value)
                
                radar_data["strategies"].append({
                    "name": data["name"],
                    "values": strategy_values
                })
            
            # 相关性分析（如果有收益率数据）
            correlation_data = {}
            
            return {
                "metrics": metrics_data,
                "radar_chart": radar_data,
                "correlation": correlation_data,
            }
            
        except Exception as e:
            logger.error(f"格式化比较数据失败: {e}")
            return {"metrics": [], "radar_chart": {}, "correlation": {}}
    
    def format_risk_metrics_data(self, daily_returns: List[Dict[str, Any]], 
                                equity_curve: List[Dict[str, Any]]) -> Dict[str, Any]:
        """格式化风险指标数据"""
        try:
            risk_data = {
                "var_analysis": {},
                "drawdown_analysis": {},
                "volatility_analysis": {},
                "tail_risk": {},
            }
            
            if daily_returns:
                df_returns = pd.DataFrame(daily_returns)
                returns = df_returns['return'].dropna()
                
                if len(returns) > 0:
                    # VaR分析
                    var_levels = [0.01, 0.05, 0.10]
                    var_values = [returns.quantile(level) for level in var_levels]
                    
                    risk_data["var_analysis"] = {
                        "levels": [f"{level*100:.0f}%" for level in var_levels],
                        "values": var_values,
                        "cvar_values": [returns[returns <= var].mean() for var in var_values],
                    }
                    
                    # 波动率分析
                    rolling_vol = returns.rolling(30).std() * np.sqrt(252)
                    risk_data["volatility_analysis"] = {
                        "current_volatility": returns.std() * np.sqrt(252),
                        "rolling_volatility": {
                            "timestamps": df_returns['date'].iloc[29:].dt.strftime('%Y-%m-%d').tolist(),
                            "values": rolling_vol.dropna().tolist(),
                        }
                    }
                    
                    # 尾部风险
                    risk_data["tail_risk"] = {
                        "skewness": returns.skew(),
                        "kurtosis": returns.kurtosis(),
                        "worst_5_days": returns.nsmallest(5).tolist(),
                        "best_5_days": returns.nlargest(5).tolist(),
                    }
            
            if equity_curve:
                df_equity = pd.DataFrame(equity_curve)
                df_equity['timestamp'] = pd.to_datetime(df_equity['timestamp'])
                
                # 回撤分析
                peak = df_equity['total_value'].expanding().max()
                drawdown = (df_equity['total_value'] - peak) / peak
                
                # 找到回撤期间
                drawdown_periods = self._find_drawdown_periods(df_equity, drawdown)
                
                risk_data["drawdown_analysis"] = {
                    "max_drawdown": abs(drawdown.min()),
                    "current_drawdown": abs(drawdown.iloc[-1]) if len(drawdown) > 0 else 0,
                    "drawdown_periods": len(drawdown_periods),
                    "avg_drawdown_duration": np.mean([p["duration"] for p in drawdown_periods]) if drawdown_periods else 0,
                    "longest_drawdown": max([p["duration"] for p in drawdown_periods]) if drawdown_periods else 0,
                }
            
            return risk_data
            
        except Exception as e:
            logger.error(f"格式化风险指标数据失败: {e}")
            return {"var_analysis": {}, "drawdown_analysis": {}, "volatility_analysis": {}, "tail_risk": {}}
    
    def _find_drawdown_periods(self, df_equity: pd.DataFrame, drawdown: pd.Series) -> List[Dict[str, Any]]:
        """找到回撤期间"""
        periods = []
        in_drawdown = False
        start_idx = None
        
        for i, dd in enumerate(drawdown):
            if dd < 0 and not in_drawdown:
                in_drawdown = True
                start_idx = i
            elif dd >= 0 and in_drawdown:
                in_drawdown = False
                if start_idx is not None:
                    duration = (df_equity.iloc[i]['timestamp'] - df_equity.iloc[start_idx]['timestamp']).days
                    periods.append({
                        "start": df_equity.iloc[start_idx]['timestamp'].strftime('%Y-%m-%d'),
                        "end": df_equity.iloc[i-1]['timestamp'].strftime('%Y-%m-%d'),
                        "duration": duration,
                        "max_drawdown": abs(drawdown.iloc[start_idx:i].min()),
                    })
        
        return periods
    
    def format_performance_attribution_data(self, trade_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """格式化业绩归因数据"""
        try:
            if not trade_records:
                return {"symbol_contribution": {}, "time_contribution": {}, "factor_analysis": {}}
            
            df = pd.DataFrame(trade_records)
            
            # 按品种归因（简化版本）
            symbol_contribution = {}
            for symbol in df['symbol'].unique():
                symbol_df = df[df['symbol'] == symbol]
                # 这里需要更复杂的逻辑来计算每个品种的贡献
                symbol_contribution[symbol] = {
                    "trade_count": len(symbol_df),
                    "total_quantity": symbol_df['quantity'].sum(),
                    "commission_cost": symbol_df['commission'].sum() if 'commission' in symbol_df.columns else 0,
                }
            
            # 时间归因
            time_contribution = {}
            if 'filled_time' in df.columns:
                df['filled_time'] = pd.to_datetime(df['filled_time'])
                df['month'] = df['filled_time'].dt.to_period('M')
                
                monthly_trades = df.groupby('month').size()
                time_contribution = {
                    "monthly_trades": {
                        "periods": [str(period) for period in monthly_trades.index],
                        "counts": monthly_trades.values.tolist(),
                    }
                }
            
            return {
                "symbol_contribution": symbol_contribution,
                "time_contribution": time_contribution,
                "factor_analysis": {},  # 可以扩展因子分析
            }
            
        except Exception as e:
            logger.error(f"格式化业绩归因数据失败: {e}")
            return {"symbol_contribution": {}, "time_contribution": {}, "factor_analysis": {}}