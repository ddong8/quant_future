"""
持仓图表服务 - 增强版
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from decimal import Decimal
import pandas as pd
import numpy as np

from ..models.position import Position, PositionStatus, PositionHistory
from ..models.user import User
from ..utils.position_calculator import PositionCalculator

logger = logging.getLogger(__name__)


class PositionChartService:
    """持仓图表服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.calculator = PositionCalculator()
    
    def get_position_pnl_chart(self, position_id: int, period: str = '1d') -> Dict[str, Any]:
        """获取持仓盈亏图表数据"""
        try:
            position = self.db.query(Position).filter(Position.id == position_id).first()
            if not position:
                return {'error': '持仓不存在'}
            
            # 根据周期确定时间范围
            end_time = datetime.now()
            if period == '1d':
                start_time = end_time - timedelta(days=1)
                interval = timedelta(hours=1)
            elif period == '1w':
                start_time = end_time - timedelta(weeks=1)
                interval = timedelta(days=1)
            elif period == '1m':
                start_time = end_time - timedelta(days=30)
                interval = timedelta(days=1)
            elif period == '3m':
                start_time = end_time - timedelta(days=90)
                interval = timedelta(days=3)
            elif period == '1y':
                start_time = end_time - timedelta(days=365)
                interval = timedelta(weeks=1)
            else:
                start_time = end_time - timedelta(days=1)
                interval = timedelta(hours=1)
            
            # 首先尝试从历史记录获取真实数据
            historical_data = self._get_historical_pnl_data(position_id, start_time, end_time)
            
            if historical_data:
                chart_data = historical_data
            else:
                # 如果没有历史数据，生成模拟数据
                chart_data = self._generate_pnl_chart_data(position, start_time, end_time, interval)
            
            # 计算技术指标
            technical_indicators = self._calculate_technical_indicators(chart_data)
            
            return {
                'position_id': position_id,
                'symbol': position.symbol,
                'period': period,
                'data': chart_data,
                'technical_indicators': technical_indicators,
                'summary': self._calculate_chart_summary(chart_data),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取持仓盈亏图表失败: {e}")
            return {'error': str(e)}
    
    def get_portfolio_performance_chart(self, user_id: int, period: str = '1m') -> Dict[str, Any]:
        """获取投资组合绩效图表"""
        try:
            # 获取用户所有持仓
            positions = self.db.query(Position).filter(
                and_(
                    Position.user_id == user_id,
                    Position.status == PositionStatus.OPEN
                )
            ).all()
            
            if not positions:
                return {'error': '没有持仓数据'}
            
            # 根据周期确定时间范围
            end_time = datetime.now()
            if period == '1w':
                start_time = end_time - timedelta(weeks=1)
                interval = timedelta(days=1)
            elif period == '1m':
                start_time = end_time - timedelta(days=30)
                interval = timedelta(days=1)
            elif period == '3m':
                start_time = end_time - timedelta(days=90)
                interval = timedelta(days=3)
            elif period == '6m':
                start_time = end_time - timedelta(days=180)
                interval = timedelta(weeks=1)
            elif period == '1y':
                start_time = end_time - timedelta(days=365)
                interval = timedelta(weeks=1)
            else:
                start_time = end_time - timedelta(days=30)
                interval = timedelta(days=1)
            
            # 获取组合历史数据
            portfolio_history = self._get_portfolio_historical_data(user_id, start_time, end_time)
            
            if portfolio_history:
                chart_data = portfolio_history
            else:
                # 生成组合绩效数据
                chart_data = self._generate_portfolio_chart_data(positions, start_time, end_time, interval)
            
            # 计算绩效指标
            performance_metrics = self._calculate_performance_metrics(chart_data)
            
            # 计算风险指标
            risk_metrics = self._calculate_portfolio_risk_metrics(chart_data)
            
            return {
                'user_id': user_id,
                'period': period,
                'data': chart_data,
                'performance_metrics': performance_metrics,
                'risk_metrics': risk_metrics,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取投资组合绩效图表失败: {e}")
            return {'error': str(e)}
    
    def get_realtime_pnl_summary(self, user_id: int) -> Dict[str, Any]:
        """获取实时盈亏摘要"""
        try:
            positions = self.db.query(Position).filter(
                and_(
                    Position.user_id == user_id,
                    Position.status == PositionStatus.OPEN
                )
            ).all()
            
            if not positions:
                return {'error': '没有持仓数据'}
            
            # 计算实时指标
            total_market_value = sum(float(pos.market_value or 0) for pos in positions)
            total_cost = sum(float(pos.quantity * pos.average_cost) for pos in positions)
            total_unrealized_pnl = sum(float(pos.unrealized_pnl or 0) for pos in positions)
            total_daily_pnl = sum(float(pos.daily_pnl or 0) for pos in positions)
            
            # 计算百分比
            total_return_percent = (total_unrealized_pnl / total_cost * 100) if total_cost > 0 else 0
            daily_return_percent = (total_daily_pnl / total_market_value * 100) if total_market_value > 0 else 0
            
            # 统计盈亏分布
            profit_positions = [pos for pos in positions if float(pos.unrealized_pnl or 0) > 0]
            loss_positions = [pos for pos in positions if float(pos.unrealized_pnl or 0) < 0]
            
            # 最佳和最差表现
            best_performer = max(positions, key=lambda x: float(x.unrealized_pnl_percent or 0)) if positions else None
            worst_performer = min(positions, key=lambda x: float(x.unrealized_pnl_percent or 0)) if positions else None
            
            return {
                'user_id': user_id,
                'summary': {
                    'total_market_value': total_market_value,
                    'total_cost': total_cost,
                    'total_unrealized_pnl': total_unrealized_pnl,
                    'total_return_percent': total_return_percent,
                    'total_daily_pnl': total_daily_pnl,
                    'daily_return_percent': daily_return_percent,
                    'position_count': len(positions)
                },
                'distribution': {
                    'profit_positions': len(profit_positions),
                    'loss_positions': len(loss_positions),
                    'profit_ratio': len(profit_positions) / len(positions) * 100 if positions else 0
                },
                'performers': {
                    'best': {
                        'symbol': best_performer.symbol if best_performer else None,
                        'pnl_percent': float(best_performer.unrealized_pnl_percent or 0) if best_performer else 0
                    },
                    'worst': {
                        'symbol': worst_performer.symbol if worst_performer else None,
                        'pnl_percent': float(worst_performer.unrealized_pnl_percent or 0) if worst_performer else 0
                    }
                },
                'updated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取实时盈亏摘要失败: {e}")
            return {'error': str(e)}
    
    def _get_historical_pnl_data(self, position_id: int, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """获取历史盈亏数据"""
        try:
            history_records = self.db.query(PositionHistory).filter(
                and_(
                    PositionHistory.position_id == position_id,
                    PositionHistory.recorded_at >= start_time,
                    PositionHistory.recorded_at <= end_time
                )
            ).order_by(PositionHistory.recorded_at).all()
            
            return [
                {
                    'timestamp': record.recorded_at.isoformat(),
                    'price': float(record.current_price) if record.current_price else 0,
                    'pnl': float(record.total_pnl),
                    'pnl_percent': float(record.return_rate) * 100,
                    'daily_pnl': float(record.daily_pnl),
                    'daily_pnl_percent': float(record.daily_pnl_percent),
                    'market_value': float(record.market_value) if record.market_value else 0
                }
                for record in history_records
            ]
            
        except Exception as e:
            logger.error(f"获取历史盈亏数据失败: {e}")
            return []
    
    def _get_portfolio_historical_data(self, user_id: int, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """获取组合历史数据"""
        try:
            # 按日期聚合用户的所有持仓历史
            history_records = self.db.query(PositionHistory).filter(
                and_(
                    PositionHistory.user_id == user_id,
                    PositionHistory.recorded_at >= start_time,
                    PositionHistory.recorded_at <= end_time
                )
            ).order_by(PositionHistory.recorded_at).all()
            
            # 按时间戳分组
            grouped_data = {}
            for record in history_records:
                timestamp = record.recorded_at.isoformat()
                if timestamp not in grouped_data:
                    grouped_data[timestamp] = {
                        'portfolio_value': 0,
                        'total_cost': 0,
                        'total_pnl': 0,
                        'daily_pnl': 0
                    }
                
                grouped_data[timestamp]['portfolio_value'] += float(record.market_value or 0)
                grouped_data[timestamp]['total_cost'] += float(record.quantity * record.avg_cost)
                grouped_data[timestamp]['total_pnl'] += float(record.total_pnl)
                grouped_data[timestamp]['daily_pnl'] += float(record.daily_pnl)
            
            # 转换为列表格式
            portfolio_data = []
            for timestamp, data in sorted(grouped_data.items()):
                total_return_percent = (data['total_pnl'] / data['total_cost'] * 100) if data['total_cost'] > 0 else 0
                daily_return_percent = (data['daily_pnl'] / data['portfolio_value'] * 100) if data['portfolio_value'] > 0 else 0
                
                portfolio_data.append({
                    'timestamp': timestamp,
                    'portfolio_value': data['portfolio_value'],
                    'total_cost': data['total_cost'],
                    'total_return': data['total_pnl'],
                    'total_return_percent': total_return_percent,
                    'daily_return': data['daily_pnl'],
                    'daily_return_percent': daily_return_percent
                })
            
            return portfolio_data
            
        except Exception as e:
            logger.error(f"获取组合历史数据失败: {e}")
            return []
    
    def _calculate_technical_indicators(self, chart_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算技术指标"""
        try:
            if len(chart_data) < 20:
                return {}
            
            prices = [point['price'] for point in chart_data]
            pnls = [point['pnl'] for point in chart_data]
            
            # 移动平均线
            ma_5 = np.convolve(prices, np.ones(5)/5, mode='valid')
            ma_20 = np.convolve(prices, np.ones(20)/20, mode='valid')
            
            # 波动率
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns) * np.sqrt(252)  # 年化波动率
            
            # 最大回撤
            cumulative_pnl = np.cumsum(pnls)
            running_max = np.maximum.accumulate(cumulative_pnl)
            drawdown = (cumulative_pnl - running_max) / np.abs(running_max)
            max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
            
            return {
                'ma_5': ma_5.tolist() if len(ma_5) > 0 else [],
                'ma_20': ma_20.tolist() if len(ma_20) > 0 else [],
                'volatility': float(volatility),
                'max_drawdown': float(max_drawdown),
                'current_drawdown': float(drawdown[-1]) if len(drawdown) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            return {}
    
    def _calculate_chart_summary(self, chart_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算图表摘要"""
        try:
            if not chart_data:
                return {}
            
            pnls = [point['pnl'] for point in chart_data]
            pnl_percents = [point['pnl_percent'] for point in chart_data]
            
            return {
                'max_pnl': max(pnls),
                'min_pnl': min(pnls),
                'final_pnl': pnls[-1],
                'max_pnl_percent': max(pnl_percents),
                'min_pnl_percent': min(pnl_percents),
                'final_pnl_percent': pnl_percents[-1],
                'data_points': len(chart_data)
            }
            
        except Exception as e:
            logger.error(f"计算图表摘要失败: {e}")
            return {}
    
    def _calculate_performance_metrics(self, chart_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算绩效指标"""
        try:
            if len(chart_data) < 2:
                return {}
            
            returns = [point['daily_return_percent'] for point in chart_data[1:]]
            
            # 基础指标
            total_return = chart_data[-1]['total_return_percent']
            avg_daily_return = np.mean(returns)
            volatility = np.std(returns) * np.sqrt(252)  # 年化波动率
            
            # 夏普比率（假设无风险利率为3%）
            risk_free_rate = 3.0
            sharpe_ratio = (total_return - risk_free_rate) / volatility if volatility > 0 else 0
            
            # 最大回撤
            cumulative_returns = np.cumprod([1 + r/100 for r in returns])
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = (cumulative_returns - running_max) / running_max
            max_drawdown = np.min(drawdowns) * 100 if len(drawdowns) > 0 else 0
            
            # 胜率
            positive_days = len([r for r in returns if r > 0])
            win_rate = (positive_days / len(returns)) * 100 if returns else 0
            
            return {
                'total_return': total_return,
                'avg_daily_return': avg_daily_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'best_day': max(returns) if returns else 0,
                'worst_day': min(returns) if returns else 0
            }
            
        except Exception as e:
            logger.error(f"计算绩效指标失败: {e}")
            return {}
    
    def _calculate_portfolio_risk_metrics(self, chart_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算组合风险指标"""
        try:
            if len(chart_data) < 20:
                return {}
            
            returns = [point['daily_return_percent'] for point in chart_data[1:]]
            
            # VaR计算
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)
            
            # CVaR计算
            cvar_95 = np.mean([r for r in returns if r <= var_95])
            
            # 下行波动率
            negative_returns = [r for r in returns if r < 0]
            downside_volatility = np.std(negative_returns) * np.sqrt(252) if negative_returns else 0
            
            # 索提诺比率
            avg_return = np.mean(returns) * 252  # 年化
            sortino_ratio = (avg_return - 3.0) / downside_volatility if downside_volatility > 0 else 0
            
            return {
                'var_95': var_95,
                'var_99': var_99,
                'cvar_95': cvar_95,
                'downside_volatility': downside_volatility,
                'sortino_ratio': sortino_ratio,
                'skewness': float(pd.Series(returns).skew()) if len(returns) > 3 else 0,
                'kurtosis': float(pd.Series(returns).kurtosis()) if len(returns) > 3 else 0
            }
            
        except Exception as e:
            logger.error(f"计算组合风险指标失败: {e}")
            return {}
    
    def _generate_pnl_chart_data(self, position: Position, start_time: datetime, 
                                end_time: datetime, interval: timedelta) -> List[Dict[str, Any]]:
        """生成盈亏图表数据（模拟）"""
        try:
            chart_data = []
            current_time = start_time
            
            # 基础参数
            base_price = float(position.average_cost)
            current_price = float(position.current_price or position.average_cost)
            quantity = float(position.quantity)
            
            # 生成价格走势（模拟）
            import random
            price_trend = np.linspace(base_price, current_price, int((end_time - start_time) / interval))
            
            for i, price in enumerate(price_trend):
                # 添加随机波动
                price_with_noise = price * (1 + random.uniform(-0.02, 0.02))
                
                # 计算盈亏
                if position.position_type.value == 'LONG':
                    pnl = quantity * (price_with_noise - base_price)
                else:
                    pnl = quantity * (base_price - price_with_noise)
                
                pnl_percent = (pnl / (quantity * base_price)) * 100 if base_price > 0 else 0
                
                # 计算今日盈亏（简化）
                if i > 0:
                    prev_price = price_trend[i-1] * (1 + random.uniform(-0.02, 0.02))
                    if position.position_type.value == 'LONG':
                        daily_pnl = quantity * (price_with_noise - prev_price)
                    else:
                        daily_pnl = quantity * (prev_price - price_with_noise)
                    daily_pnl_percent = (daily_pnl / (quantity * prev_price)) * 100 if prev_price > 0 else 0
                else:
                    daily_pnl = 0
                    daily_pnl_percent = 0
                
                chart_data.append({
                    'timestamp': current_time.isoformat(),
                    'price': round(price_with_noise, 2),
                    'pnl': round(pnl, 2),
                    'pnl_percent': round(pnl_percent, 2),
                    'daily_pnl': round(daily_pnl, 2),
                    'daily_pnl_percent': round(daily_pnl_percent, 2),
                    'market_value': round(quantity * price_with_noise, 2)
                })
                
                current_time += interval
            
            return chart_data
            
        except Exception as e:
            logger.error(f"生成盈亏图表数据失败: {e}")
            return []
    
    def _generate_portfolio_chart_data(self, positions: List[Position], start_time: datetime,
                                     end_time: datetime, interval: timedelta) -> List[Dict[str, Any]]:
        """生成投资组合图表数据（模拟）"""
        try:
            chart_data = []
            current_time = start_time
            
            # 计算初始总成本
            total_cost = sum(float(pos.quantity * pos.average_cost) for pos in positions)
            current_total_value = sum(float(pos.market_value or 0) for pos in positions)
            
            # 生成时间序列数据
            time_points = int((end_time - start_time) / interval)
            value_trend = np.linspace(total_cost, current_total_value, time_points)
            
            import random
            for i, portfolio_value in enumerate(value_trend):
                # 添加随机波动
                portfolio_value_with_noise = portfolio_value * (1 + random.uniform(-0.03, 0.03))
                
                # 计算收益指标
                total_return = portfolio_value_with_noise - total_cost
                total_return_percent = (total_return / total_cost) * 100 if total_cost > 0 else 0
                
                # 计算日收益（简化）
                if i > 0:
                    prev_value = chart_data[i-1]['portfolio_value']
                    daily_return = portfolio_value_with_noise - prev_value
                    daily_return_percent = (daily_return / prev_value) * 100 if prev_value > 0 else 0
                else:
                    daily_return = 0
                    daily_return_percent = 0
                
                chart_data.append({
                    'timestamp': current_time.isoformat(),
                    'portfolio_value': round(portfolio_value_with_noise, 2),
                    'total_cost': round(total_cost, 2),
                    'total_return': round(total_return, 2),
                    'total_return_percent': round(total_return_percent, 2),
                    'daily_return': round(daily_return, 2),
                    'daily_return_percent': round(daily_return_percent, 2)
                })
                
                current_time += interval
            
            return chart_data
            
        except Exception as e:
            logger.error(f"生成投资组合图表数据失败: {e}")
            return []