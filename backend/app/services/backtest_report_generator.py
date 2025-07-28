"""
回测报告生成器
"""
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from jinja2 import Template, Environment, FileSystemLoader
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
import seaborn as sns
import base64
from io import BytesIO
import logging

from ..models import Backtest, BacktestReport
from ..core.config import settings
from .backtest_analyzer import BacktestAnalyzer, PerformanceMetrics

logger = logging.getLogger(__name__)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 设置样式
sns.set_style("whitegrid")
plt.style.use('seaborn-v0_8')


class BacktestReportGenerator:
    """回测报告生成器"""
    
    def __init__(self):
        self.analyzer = BacktestAnalyzer()
        self.template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'reports')
        self.output_dir = os.path.join(settings.BASE_DIR, 'reports')
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.template_dir, exist_ok=True)
        
        # 初始化Jinja2环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True
        )
    
    def generate_html_report(self, 
                           backtest: Backtest, 
                           metrics: PerformanceMetrics,
                           include_charts: bool = True) -> str:
        """生成HTML报告"""
        try:
            # 准备报告数据
            report_data = self._prepare_report_data(backtest, metrics)
            
            # 生成图表
            charts = {}
            if include_charts:
                charts = self._generate_charts(backtest, metrics)
            
            # 渲染HTML模板
            template = self._get_or_create_html_template()
            html_content = template.render(
                backtest=backtest,
                metrics=metrics,
                report_data=report_data,
                charts=charts,
                generated_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            # 保存报告文件
            filename = f"backtest_report_{backtest.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML报告生成成功: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"生成HTML报告失败: {e}")
            raise
    
    def generate_summary_report(self, backtest: Backtest, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """生成摘要报告"""
        try:
            summary = {
                "基本信息": {
                    "回测名称": backtest.name,
                    "策略ID": backtest.strategy_id,
                    "回测期间": f"{backtest.start_date.strftime('%Y-%m-%d')} 至 {backtest.end_date.strftime('%Y-%m-%d')}",
                    "初始资金": f"¥{backtest.initial_capital:,.2f}",
                    "最终资金": f"¥{backtest.final_capital:,.2f}",
                    "交易品种": ", ".join(backtest.symbols),
                },
                "核心指标": {
                    "总收益率": f"{metrics.total_return:.2%}",
                    "年化收益率": f"{metrics.annual_return:.2%}",
                    "最大回撤": f"{metrics.max_drawdown:.2%}",
                    "夏普比率": f"{metrics.sharpe_ratio:.3f}",
                    "胜率": f"{metrics.win_rate:.2%}",
                    "盈亏比": f"{metrics.profit_factor:.2f}",
                },
                "风险评估": self.analyzer.generate_risk_report(metrics),
                "性能摘要": self.analyzer.generate_performance_summary(metrics),
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"生成摘要报告失败: {e}")
            return {}
    
    def generate_detailed_report(self, backtest: Backtest, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """生成详细报告"""
        try:
            # 基础摘要
            summary = self.generate_summary_report(backtest, metrics)
            
            # 详细数据
            detailed_data = {
                "资金曲线数据": backtest.equity_curve or [],
                "交易记录": backtest.trade_records or [],
                "日收益率": backtest.daily_returns or [],
                "月度统计": self._calculate_monthly_stats(backtest.daily_returns or []),
                "年度统计": self._calculate_yearly_stats(backtest.daily_returns or []),
                "回撤分析": self._analyze_drawdowns(backtest.equity_curve or []),
                "交易分析": self._analyze_trades(backtest.trade_records or []),
            }
            
            # 合并数据
            detailed_report = {**summary, **detailed_data}
            
            return detailed_report
            
        except Exception as e:
            logger.error(f"生成详细报告失败: {e}")
            return {}
    
    def generate_comparison_report(self, backtests: List[Backtest], metrics_list: List[PerformanceMetrics]) -> Dict[str, Any]:
        """生成比较报告"""
        try:
            if len(backtests) != len(metrics_list):
                raise ValueError("回测数量与指标数量不匹配")
            
            comparison_data = {
                "回测对比": [],
                "指标对比": {},
                "排名分析": {},
                "相关性分析": {},
            }
            
            # 基础对比数据
            for backtest, metrics in zip(backtests, metrics_list):
                comparison_data["回测对比"].append({
                    "名称": backtest.name,
                    "ID": backtest.id,
                    "总收益率": metrics.total_return,
                    "年化收益率": metrics.annual_return,
                    "最大回撤": metrics.max_drawdown,
                    "夏普比率": metrics.sharpe_ratio,
                    "索提诺比率": metrics.sortino_ratio,
                    "胜率": metrics.win_rate,
                    "盈亏比": metrics.profit_factor,
                    "波动率": metrics.volatility,
                })
            
            # 指标对比
            metrics_names = ['total_return', 'annual_return', 'max_drawdown', 'sharpe_ratio', 
                           'sortino_ratio', 'win_rate', 'profit_factor', 'volatility']
            
            for metric_name in metrics_names:
                values = [getattr(metrics, metric_name) for metrics in metrics_list]
                comparison_data["指标对比"][metric_name] = {
                    "最大值": max(values),
                    "最小值": min(values),
                    "平均值": sum(values) / len(values),
                    "标准差": pd.Series(values).std(),
                }
            
            # 排名分析
            for metric_name in metrics_names:
                values = [(i, getattr(metrics_list[i], metric_name)) for i in range(len(metrics_list))]
                # 对于回撤，值越小排名越高
                reverse = metric_name == 'max_drawdown'
                sorted_values = sorted(values, key=lambda x: x[1], reverse=not reverse)
                comparison_data["排名分析"][metric_name] = [
                    {"回测ID": backtests[idx].id, "回测名称": backtests[idx].name, "值": value, "排名": rank + 1}
                    for rank, (idx, value) in enumerate(sorted_values)
                ]
            
            return comparison_data
            
        except Exception as e:
            logger.error(f"生成比较报告失败: {e}")
            return {}
    
    def _prepare_report_data(self, backtest: Backtest, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """准备报告数据"""
        return {
            "backtest_info": {
                "name": backtest.name,
                "description": backtest.description,
                "strategy_id": backtest.strategy_id,
                "start_date": backtest.start_date.strftime('%Y-%m-%d'),
                "end_date": backtest.end_date.strftime('%Y-%m-%d'),
                "duration_days": (backtest.end_date - backtest.start_date).days,
                "initial_capital": backtest.initial_capital,
                "final_capital": backtest.final_capital,
                "symbols": backtest.symbols,
                "parameters": backtest.parameters,
            },
            "performance_summary": self.analyzer.generate_performance_summary(metrics),
            "risk_report": self.analyzer.generate_risk_report(metrics),
        }
    
    def _generate_charts(self, backtest: Backtest, metrics: PerformanceMetrics) -> Dict[str, str]:
        """生成图表"""
        charts = {}
        
        try:
            # 资金曲线图
            if backtest.equity_curve:
                charts['equity_curve'] = self._create_equity_curve_chart(backtest.equity_curve)
            
            # 回撤图
            if backtest.equity_curve:
                charts['drawdown'] = self._create_drawdown_chart(backtest.equity_curve)
            
            # 日收益率分布图
            if backtest.daily_returns:
                charts['returns_distribution'] = self._create_returns_distribution_chart(backtest.daily_returns)
            
            # 月度收益热力图
            if backtest.daily_returns:
                charts['monthly_returns'] = self._create_monthly_returns_heatmap(backtest.daily_returns)
            
            # 滚动指标图
            if backtest.daily_returns:
                charts['rolling_metrics'] = self._create_rolling_metrics_chart(backtest.daily_returns)
            
        except Exception as e:
            logger.error(f"生成图表失败: {e}")
        
        return charts
    
    def _create_equity_curve_chart(self, equity_curve: List[Dict[str, Any]]) -> str:
        """创建资金曲线图"""
        df = pd.DataFrame(equity_curve)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(df['timestamp'], df['total_value'], linewidth=2, label='总资产')
        ax.plot(df['timestamp'], df['available_cash'], linewidth=1, alpha=0.7, label='可用资金')
        
        ax.set_title('资金曲线', fontsize=16, fontweight='bold')
        ax.set_xlabel('时间')
        ax.set_ylabel('资金 (元)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 格式化x轴
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def _create_drawdown_chart(self, equity_curve: List[Dict[str, Any]]) -> str:
        """创建回撤图"""
        df = pd.DataFrame(equity_curve)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 计算回撤
        peak = df['total_value'].expanding().max()
        drawdown = (df['total_value'] - peak) / peak
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.fill_between(df['timestamp'], drawdown, 0, alpha=0.3, color='red', label='回撤')
        ax.plot(df['timestamp'], drawdown, color='red', linewidth=1)
        
        ax.set_title('回撤分析', fontsize=16, fontweight='bold')
        ax.set_xlabel('时间')
        ax.set_ylabel('回撤比例')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 格式化y轴为百分比
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.1%}'.format(y)))
        
        # 格式化x轴
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def _create_returns_distribution_chart(self, daily_returns: List[Dict[str, Any]]) -> str:
        """创建收益率分布图"""
        df = pd.DataFrame(daily_returns)
        returns = df['return'].dropna()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 直方图
        ax1.hist(returns, bins=50, alpha=0.7, density=True, color='skyblue', edgecolor='black')
        ax1.set_title('日收益率分布', fontsize=14, fontweight='bold')
        ax1.set_xlabel('日收益率')
        ax1.set_ylabel('密度')
        ax1.grid(True, alpha=0.3)
        
        # Q-Q图
        from scipy import stats
        stats.probplot(returns, dist="norm", plot=ax2)
        ax2.set_title('Q-Q图 (正态性检验)', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def _create_monthly_returns_heatmap(self, daily_returns: List[Dict[str, Any]]) -> str:
        """创建月度收益热力图"""
        df = pd.DataFrame(daily_returns)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 计算月度收益
        monthly_returns = df['return'].resample('M').apply(lambda x: (1 + x).prod() - 1)
        
        # 创建年月矩阵
        monthly_returns.index = pd.to_datetime(monthly_returns.index)
        monthly_data = monthly_returns.groupby([monthly_returns.index.year, monthly_returns.index.month]).first().unstack()
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        sns.heatmap(monthly_data, annot=True, fmt='.2%', cmap='RdYlGn', center=0, 
                   cbar_kws={'label': '月收益率'}, ax=ax)
        
        ax.set_title('月度收益率热力图', fontsize=16, fontweight='bold')
        ax.set_xlabel('月份')
        ax.set_ylabel('年份')
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def _create_rolling_metrics_chart(self, daily_returns: List[Dict[str, Any]]) -> str:
        """创建滚动指标图"""
        df = pd.DataFrame(daily_returns)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 计算滚动指标
        rolling_metrics = self.analyzer.calculate_rolling_metrics(df, window=252)
        
        if not rolling_metrics:
            return ""
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 滚动收益率
        if 'rolling_return' in rolling_metrics:
            axes[0, 0].plot(rolling_metrics['rolling_return'].index, rolling_metrics['rolling_return'])
            axes[0, 0].set_title('滚动年化收益率')
            axes[0, 0].set_ylabel('收益率')
            axes[0, 0].grid(True, alpha=0.3)
        
        # 滚动波动率
        if 'rolling_volatility' in rolling_metrics:
            axes[0, 1].plot(rolling_metrics['rolling_volatility'].index, rolling_metrics['rolling_volatility'])
            axes[0, 1].set_title('滚动年化波动率')
            axes[0, 1].set_ylabel('波动率')
            axes[0, 1].grid(True, alpha=0.3)
        
        # 滚动夏普比率
        if 'rolling_sharpe' in rolling_metrics:
            axes[1, 0].plot(rolling_metrics['rolling_sharpe'].index, rolling_metrics['rolling_sharpe'])
            axes[1, 0].set_title('滚动夏普比率')
            axes[1, 0].set_ylabel('夏普比率')
            axes[1, 0].grid(True, alpha=0.3)
        
        # 滚动最大回撤
        if 'rolling_max_drawdown' in rolling_metrics:
            axes[1, 1].plot(rolling_metrics['rolling_max_drawdown'].index, rolling_metrics['rolling_max_drawdown'])
            axes[1, 1].set_title('滚动最大回撤')
            axes[1, 1].set_ylabel('最大回撤')
            axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def _fig_to_base64(self, fig) -> str:
        """将matplotlib图形转换为base64字符串"""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        return f"data:image/png;base64,{image_base64}"
    
    def _calculate_monthly_stats(self, daily_returns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """计算月度统计"""
        if not daily_returns:
            return []
        
        df = pd.DataFrame(daily_returns)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 按月分组计算
        monthly_stats = []
        for year_month, group in df.groupby(pd.Grouper(freq='M')):
            if not group.empty:
                monthly_return = (1 + group['return']).prod() - 1
                monthly_stats.append({
                    'year_month': year_month.strftime('%Y-%m'),
                    'return': monthly_return,
                    'volatility': group['return'].std() * np.sqrt(21),  # 月化波动率
                    'max_daily_return': group['return'].max(),
                    'min_daily_return': group['return'].min(),
                    'trading_days': len(group)
                })
        
        return monthly_stats
    
    def _calculate_yearly_stats(self, daily_returns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """计算年度统计"""
        if not daily_returns:
            return []
        
        df = pd.DataFrame(daily_returns)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 按年分组计算
        yearly_stats = []
        for year, group in df.groupby(pd.Grouper(freq='Y')):
            if not group.empty:
                yearly_return = (1 + group['return']).prod() - 1
                yearly_stats.append({
                    'year': year.year,
                    'return': yearly_return,
                    'volatility': group['return'].std() * np.sqrt(252),  # 年化波动率
                    'sharpe_ratio': (yearly_return - 0.03) / (group['return'].std() * np.sqrt(252)),
                    'max_daily_return': group['return'].max(),
                    'min_daily_return': group['return'].min(),
                    'positive_days': (group['return'] > 0).sum(),
                    'negative_days': (group['return'] < 0).sum(),
                    'trading_days': len(group)
                })
        
        return yearly_stats
    
    def _analyze_drawdowns(self, equity_curve: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析回撤"""
        if not equity_curve:
            return {}
        
        df = pd.DataFrame(equity_curve)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 计算回撤
        peak = df['total_value'].expanding().max()
        drawdown = (df['total_value'] - peak) / peak
        
        # 找到所有回撤期间
        drawdown_periods = []
        in_drawdown = False
        start_idx = None
        
        for i, dd in enumerate(drawdown):
            if dd < 0 and not in_drawdown:
                # 开始回撤
                in_drawdown = True
                start_idx = i
            elif dd >= 0 and in_drawdown:
                # 结束回撤
                in_drawdown = False
                if start_idx is not None:
                    period_dd = drawdown.iloc[start_idx:i]
                    drawdown_periods.append({
                        'start_date': df.iloc[start_idx]['timestamp'],
                        'end_date': df.iloc[i-1]['timestamp'],
                        'duration_days': (df.iloc[i-1]['timestamp'] - df.iloc[start_idx]['timestamp']).days,
                        'max_drawdown': abs(period_dd.min()),
                        'recovery_date': df.iloc[i]['timestamp'] if i < len(df) else None
                    })
        
        # 如果最后还在回撤中
        if in_drawdown and start_idx is not None:
            period_dd = drawdown.iloc[start_idx:]
            drawdown_periods.append({
                'start_date': df.iloc[start_idx]['timestamp'],
                'end_date': df.iloc[-1]['timestamp'],
                'duration_days': (df.iloc[-1]['timestamp'] - df.iloc[start_idx]['timestamp']).days,
                'max_drawdown': abs(period_dd.min()),
                'recovery_date': None  # 尚未恢复
            })
        
        # 统计信息
        if drawdown_periods:
            avg_duration = sum(p['duration_days'] for p in drawdown_periods) / len(drawdown_periods)
            avg_drawdown = sum(p['max_drawdown'] for p in drawdown_periods) / len(drawdown_periods)
            max_duration = max(p['duration_days'] for p in drawdown_periods)
        else:
            avg_duration = avg_drawdown = max_duration = 0
        
        return {
            'drawdown_periods': drawdown_periods,
            'total_drawdown_periods': len(drawdown_periods),
            'avg_drawdown_duration': avg_duration,
            'max_drawdown_duration': max_duration,
            'avg_drawdown_magnitude': avg_drawdown,
        }
    
    def _analyze_trades(self, trade_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析交易"""
        if not trade_records:
            return {}
        
        df = pd.DataFrame(trade_records)
        
        # 基础统计
        total_trades = len(df)
        buy_trades = len(df[df['side'] == 'buy'])
        sell_trades = len(df[df['side'] == 'sell'])
        
        # 按品种分组
        symbol_stats = {}
        for symbol in df['symbol'].unique():
            symbol_df = df[df['symbol'] == symbol]
            symbol_stats[symbol] = {
                'total_trades': len(symbol_df),
                'buy_trades': len(symbol_df[symbol_df['side'] == 'buy']),
                'sell_trades': len(symbol_df[symbol_df['side'] == 'sell']),
                'avg_quantity': symbol_df['quantity'].mean(),
                'total_commission': symbol_df['commission'].sum(),
            }
        
        # 时间分布
        if 'filled_time' in df.columns:
            df['filled_time'] = pd.to_datetime(df['filled_time'])
            df['hour'] = df['filled_time'].dt.hour
            hourly_distribution = df['hour'].value_counts().sort_index().to_dict()
        else:
            hourly_distribution = {}
        
        return {
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'symbol_stats': symbol_stats,
            'hourly_distribution': hourly_distribution,
            'total_commission': df['commission'].sum() if 'commission' in df.columns else 0,
            'avg_commission_per_trade': df['commission'].mean() if 'commission' in df.columns else 0,
        }
    
    def _get_or_create_html_template(self) -> Template:
        """获取或创建HTML模板"""
        template_path = os.path.join(self.template_dir, 'backtest_report.html')
        
        if not os.path.exists(template_path):
            # 创建默认模板
            self._create_default_html_template(template_path)
        
        return self.jinja_env.get_template('backtest_report.html')
    
    def _create_default_html_template(self, template_path: str):
        """创建默认HTML模板"""
        template_content = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>回测报告 - {{ backtest.name }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .header { text-align: center; margin-bottom: 30px; }
        .section { margin-bottom: 30px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .metric-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
        .metric-value { font-size: 1.5em; font-weight: bold; color: #2c3e50; }
        .chart { text-align: center; margin: 20px 0; }
        .chart img { max-width: 100%; height: auto; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .positive { color: #27ae60; }
        .negative { color: #e74c3c; }
    </style>
</head>
<body>
    <div class="header">
        <h1>回测报告</h1>
        <h2>{{ backtest.name }}</h2>
        <p>生成时间: {{ generated_at }}</p>
    </div>

    <div class="section">
        <h3>基本信息</h3>
        <div class="metrics-grid">
            <div class="metric-card">
                <div>回测期间</div>
                <div class="metric-value">{{ report_data.backtest_info.start_date }} 至 {{ report_data.backtest_info.end_date }}</div>
            </div>
            <div class="metric-card">
                <div>初始资金</div>
                <div class="metric-value">¥{{ "{:,.2f}".format(report_data.backtest_info.initial_capital) }}</div>
            </div>
            <div class="metric-card">
                <div>最终资金</div>
                <div class="metric-value">¥{{ "{:,.2f}".format(report_data.backtest_info.final_capital) }}</div>
            </div>
            <div class="metric-card">
                <div>交易品种</div>
                <div class="metric-value">{{ report_data.backtest_info.symbols | join(", ") }}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h3>核心指标</h3>
        <div class="metrics-grid">
            <div class="metric-card">
                <div>总收益率</div>
                <div class="metric-value {{ 'positive' if metrics.total_return > 0 else 'negative' }}">{{ "{:.2%}".format(metrics.total_return) }}</div>
            </div>
            <div class="metric-card">
                <div>年化收益率</div>
                <div class="metric-value {{ 'positive' if metrics.annual_return > 0 else 'negative' }}">{{ "{:.2%}".format(metrics.annual_return) }}</div>
            </div>
            <div class="metric-card">
                <div>最大回撤</div>
                <div class="metric-value negative">{{ "{:.2%}".format(metrics.max_drawdown) }}</div>
            </div>
            <div class="metric-card">
                <div>夏普比率</div>
                <div class="metric-value">{{ "{:.3f}".format(metrics.sharpe_ratio) }}</div>
            </div>
            <div class="metric-card">
                <div>胜率</div>
                <div class="metric-value">{{ "{:.2%}".format(metrics.win_rate) }}</div>
            </div>
            <div class="metric-card">
                <div>盈亏比</div>
                <div class="metric-value">{{ "{:.2f}".format(metrics.profit_factor) }}</div>
            </div>
        </div>
    </div>

    {% if charts %}
    <div class="section">
        <h3>图表分析</h3>
        
        {% if charts.equity_curve %}
        <div class="chart">
            <h4>资金曲线</h4>
            <img src="{{ charts.equity_curve }}" alt="资金曲线">
        </div>
        {% endif %}
        
        {% if charts.drawdown %}
        <div class="chart">
            <h4>回撤分析</h4>
            <img src="{{ charts.drawdown }}" alt="回撤分析">
        </div>
        {% endif %}
        
        {% if charts.returns_distribution %}
        <div class="chart">
            <h4>收益率分布</h4>
            <img src="{{ charts.returns_distribution }}" alt="收益率分布">
        </div>
        {% endif %}
    </div>
    {% endif %}

    <div class="section">
        <h3>风险分析</h3>
        <div class="metrics-grid">
            <div class="metric-card">
                <div>年化波动率</div>
                <div class="metric-value">{{ "{:.2%}".format(metrics.volatility) }}</div>
            </div>
            <div class="metric-card">
                <div>索提诺比率</div>
                <div class="metric-value">{{ "{:.3f}".format(metrics.sortino_ratio) }}</div>
            </div>
            <div class="metric-card">
                <div>卡玛比率</div>
                <div class="metric-value">{{ "{:.3f}".format(metrics.calmar_ratio) }}</div>
            </div>
            <div class="metric-card">
                <div>95% VaR</div>
                <div class="metric-value negative">{{ "{:.2%}".format(metrics.var_95) }}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h3>交易统计</h3>
        <div class="metrics-grid">
            <div class="metric-card">
                <div>总交易次数</div>
                <div class="metric-value">{{ metrics.total_trades }}</div>
            </div>
            <div class="metric-card">
                <div>盈利交易</div>
                <div class="metric-value positive">{{ metrics.winning_trades }}</div>
            </div>
            <div class="metric-card">
                <div>亏损交易</div>
                <div class="metric-value negative">{{ metrics.losing_trades }}</div>
            </div>
            <div class="metric-card">
                <div>平均盈利</div>
                <div class="metric-value positive">{{ "{:.2f}".format(metrics.avg_win) }}</div>
            </div>
            <div class="metric-card">
                <div>平均亏损</div>
                <div class="metric-value negative">{{ "{:.2f}".format(metrics.avg_loss) }}</div>
            </div>
        </div>
    </div>
</body>
</html>
        '''
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content.strip())