"""
报告生成服务
负责交易报告的生成、模板管理和数据聚合
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func

from app.core.database_manager import DatabaseManager
from app.core.logging import get_logger
from app.models.user import User
from app.models.trading import Order, Position
from app.models.backtest import Backtest
from app.models.system import SystemLog
from app.schemas.report import (
    ReportTemplate, ReportRequest, ReportData, 
    TradingReport, PerformanceReport, RiskReport
)

logger = get_logger(__name__)


class ReportService:
    """报告生成服务"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.template_dir = Path("templates/reports")
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化Jinja2环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # 注册自定义过滤器
        self._register_filters()
    
    def _register_filters(self):
        """注册自定义过滤器"""
        
        @self.jinja_env.filter('currency')
        def currency_filter(value):
            """货币格式化"""
            if value is None:
                return '¥0.00'
            return f'¥{value:,.2f}'
        
        @self.jinja_env.filter('percent')
        def percent_filter(value):
            """百分比格式化"""
            if value is None:
                return '0.00%'
            return f'{value * 100:.2f}%'
        
        @self.jinja_env.filter('datetime')
        def datetime_filter(value, format='%Y-%m-%d %H:%M:%S'):
            """日期时间格式化"""
            if isinstance(value, str):
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return value.strftime(format)
    
    async def generate_trading_report(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        template_name: str = 'trading_report.html'
    ) -> str:
        """生成交易报告"""
        try:
            # 收集交易数据
            report_data = await self._collect_trading_data(user_id, start_date, end_date)
            
            # 加载模板
            template = self.jinja_env.get_template(template_name)
            
            # 渲染报告
            html_content = template.render(
                report_data=report_data,
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                generated_at=datetime.utcnow()
            )
            
            return html_content
            
        except Exception as e:
            logger.error(f"生成交易报告失败: {e}")
            raise
    
    async def _collect_trading_data(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """收集交易数据"""
        try:
            with self.db_manager.get_session() as db:
                # 获取用户信息
                user = db.query(User).filter(User.id == user_id).first()
                
                # 获取订单数据
                orders = db.query(Order).filter(
                    and_(
                        Order.user_id == user_id,
                        Order.created_at >= start_date,
                        Order.created_at <= end_date
                    )
                ).order_by(desc(Order.created_at)).all()
                
                # 获取持仓数据
                positions = db.query(Position).filter(
                    and_(
                        Position.user_id == user_id,
                        Position.created_at >= start_date,
                        Position.created_at <= end_date
                    )
                ).all()
                
                # 计算统计数据
                stats = self._calculate_trading_stats(orders, positions)
                
                return {
                    'user': user,
                    'orders': orders,
                    'positions': positions,
                    'statistics': stats,
                    'period': {
                        'start': start_date,
                        'end': end_date,
                        'days': (end_date - start_date).days
                    }
                }
                
        except Exception as e:
            logger.error(f"收集交易数据失败: {e}")
            raise
    
    def _calculate_trading_stats(
        self,
        orders: List[Order],
        positions: List[Position]
    ) -> Dict[str, Any]:
        """计算交易统计数据"""
        try:
            # 订单统计
            total_orders = len(orders)
            filled_orders = [o for o in orders if o.status == 'filled']
            buy_orders = [o for o in orders if o.side == 'buy']
            sell_orders = [o for o in orders if o.side == 'sell']
            
            # 交易金额统计
            total_volume = sum(o.filled_quantity * o.avg_fill_price for o in filled_orders)
            total_commission = sum(o.commission for o in filled_orders)
            
            # 盈亏统计
            total_pnl = sum(p.total_pnl for p in positions)
            realized_pnl = sum(p.realized_pnl for p in positions)
            unrealized_pnl = sum(p.unrealized_pnl for p in positions)
            
            # 成功率计算
            profitable_positions = [p for p in positions if p.total_pnl > 0]
            win_rate = len(profitable_positions) / len(positions) if positions else 0
            
            return {
                'total_orders': total_orders,
                'filled_orders': len(filled_orders),
                'buy_orders': len(buy_orders),
                'sell_orders': len(sell_orders),
                'fill_rate': len(filled_orders) / total_orders if total_orders > 0 else 0,
                'total_volume': total_volume,
                'total_commission': total_commission,
                'total_pnl': total_pnl,
                'realized_pnl': realized_pnl,
                'unrealized_pnl': unrealized_pnl,
                'win_rate': win_rate,
                'total_positions': len(positions),
                'profitable_positions': len(profitable_positions),
                'avg_position_size': sum(p.quantity for p in positions) / len(positions) if positions else 0
            }
            
        except Exception as e:
            logger.error(f"计算交易统计失败: {e}")
            return {}
    
    async def generate_performance_report(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        template_name: str = 'performance_report.html'
    ) -> str:
        """生成绩效报告"""
        try:
            # 收集绩效数据
            report_data = await self._collect_performance_data(user_id, start_date, end_date)
            
            # 加载模板
            template = self.jinja_env.get_template(template_name)
            
            # 渲染报告
            html_content = template.render(
                report_data=report_data,
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                generated_at=datetime.utcnow()
            )
            
            return html_content
            
        except Exception as e:
            logger.error(f"生成绩效报告失败: {e}")
            raise    
    a
sync def _collect_performance_data(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """收集绩效数据"""
        try:
            with self.db_manager.get_session() as db:
                # 获取回测数据
                backtests = db.query(Backtest).filter(
                    and_(
                        Backtest.user_id == user_id,
                        Backtest.created_at >= start_date,
                        Backtest.created_at <= end_date,
                        Backtest.status == 'completed'
                    )
                ).all()
                
                # 获取交易数据
                trading_data = await self._collect_trading_data(user_id, start_date, end_date)
                
                # 计算绩效指标
                performance_metrics = self._calculate_performance_metrics(
                    backtests, trading_data
                )
                
                return {
                    'backtests': backtests,
                    'trading_data': trading_data,
                    'performance_metrics': performance_metrics,
                    'period': {
                        'start': start_date,
                        'end': end_date,
                        'days': (end_date - start_date).days
                    }
                }
                
        except Exception as e:
            logger.error(f"收集绩效数据失败: {e}")
            raise
    
    def _calculate_performance_metrics(
        self,
        backtests: List[Backtest],
        trading_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算绩效指标"""
        try:
            # 回测绩效
            if backtests:
                backtest_returns = [bt.total_return for bt in backtests if bt.total_return]
                avg_backtest_return = sum(backtest_returns) / len(backtest_returns) if backtest_returns else 0
                best_backtest = max(backtests, key=lambda x: x.total_return or 0)
                worst_backtest = min(backtests, key=lambda x: x.total_return or 0)
            else:
                avg_backtest_return = 0
                best_backtest = None
                worst_backtest = None
            
            # 实盘绩效
            positions = trading_data.get('positions', [])
            if positions:
                returns = [p.total_pnl / p.cost_basis for p in positions if p.cost_basis > 0]
                avg_return = sum(returns) / len(returns) if returns else 0
                max_return = max(returns) if returns else 0
                min_return = min(returns) if returns else 0
                
                # 计算夏普比率（简化版）
                if returns:
                    import statistics
                    return_std = statistics.stdev(returns) if len(returns) > 1 else 0
                    sharpe_ratio = avg_return / return_std if return_std > 0 else 0
                else:
                    sharpe_ratio = 0
            else:
                avg_return = 0
                max_return = 0
                min_return = 0
                sharpe_ratio = 0
            
            return {
                'backtest_metrics': {
                    'total_backtests': len(backtests),
                    'avg_return': avg_backtest_return,
                    'best_backtest': best_backtest,
                    'worst_backtest': worst_backtest
                },
                'trading_metrics': {
                    'avg_return': avg_return,
                    'max_return': max_return,
                    'min_return': min_return,
                    'sharpe_ratio': sharpe_ratio,
                    'total_pnl': trading_data.get('statistics', {}).get('total_pnl', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"计算绩效指标失败: {e}")
            return {}
    
    async def generate_risk_report(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        template_name: str = 'risk_report.html'
    ) -> str:
        """生成风险报告"""
        try:
            # 收集风险数据
            report_data = await self._collect_risk_data(user_id, start_date, end_date)
            
            # 加载模板
            template = self.jinja_env.get_template(template_name)
            
            # 渲染报告
            html_content = template.render(
                report_data=report_data,
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                generated_at=datetime.utcnow()
            )
            
            return html_content
            
        except Exception as e:
            logger.error(f"生成风险报告失败: {e}")
            raise
    
    async def _collect_risk_data(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """收集风险数据"""
        try:
            with self.db_manager.get_session() as db:
                # 获取风险事件日志
                risk_logs = db.query(SystemLog).filter(
                    and_(
                        SystemLog.user_id == user_id,
                        SystemLog.created_at >= start_date,
                        SystemLog.created_at <= end_date,
                        SystemLog.level.in_(['WARNING', 'ERROR', 'CRITICAL'])
                    )
                ).all()
                
                # 获取交易数据用于风险分析
                trading_data = await self._collect_trading_data(user_id, start_date, end_date)
                
                # 计算风险指标
                risk_metrics = self._calculate_risk_metrics(trading_data, risk_logs)
                
                return {
                    'risk_logs': risk_logs,
                    'trading_data': trading_data,
                    'risk_metrics': risk_metrics,
                    'period': {
                        'start': start_date,
                        'end': end_date,
                        'days': (end_date - start_date).days
                    }
                }
                
        except Exception as e:
            logger.error(f"收集风险数据失败: {e}")
            raise
    
    def _calculate_risk_metrics(
        self,
        trading_data: Dict[str, Any],
        risk_logs: List[SystemLog]
    ) -> Dict[str, Any]:
        """计算风险指标"""
        try:
            positions = trading_data.get('positions', [])
            orders = trading_data.get('orders', [])
            
            # 持仓风险
            if positions:
                position_values = [abs(p.market_value) for p in positions]
                total_exposure = sum(position_values)
                max_position = max(position_values) if position_values else 0
                concentration_risk = max_position / total_exposure if total_exposure > 0 else 0
                
                # 计算VaR（简化版）
                pnl_values = [p.unrealized_pnl for p in positions]
                if pnl_values:
                    pnl_values.sort()
                    var_95 = pnl_values[int(len(pnl_values) * 0.05)] if len(pnl_values) > 20 else min(pnl_values)
                else:
                    var_95 = 0
            else:
                total_exposure = 0
                concentration_risk = 0
                var_95 = 0
            
            # 交易风险
            failed_orders = [o for o in orders if o.status in ['rejected', 'cancelled']]
            order_failure_rate = len(failed_orders) / len(orders) if orders else 0
            
            # 风险事件统计
            critical_events = [log for log in risk_logs if log.level == 'CRITICAL']
            error_events = [log for log in risk_logs if log.level == 'ERROR']
            warning_events = [log for log in risk_logs if log.level == 'WARNING']
            
            return {
                'position_risk': {
                    'total_exposure': total_exposure,
                    'concentration_risk': concentration_risk,
                    'var_95': var_95,
                    'position_count': len(positions)
                },
                'trading_risk': {
                    'order_failure_rate': order_failure_rate,
                    'total_orders': len(orders),
                    'failed_orders': len(failed_orders)
                },
                'risk_events': {
                    'critical_count': len(critical_events),
                    'error_count': len(error_events),
                    'warning_count': len(warning_events),
                    'total_events': len(risk_logs)
                }
            }
            
        except Exception as e:
            logger.error(f"计算风险指标失败: {e}")
            return {}
    
    async def create_report_template(
        self,
        template_name: str,
        template_content: str,
        template_type: str = 'html'
    ) -> bool:
        """创建报告模板"""
        try:
            template_path = self.template_dir / f"{template_name}.{template_type}"
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            logger.info(f"创建报告模板成功: {template_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建报告模板失败: {e}")
            return False
    
    async def get_template_list(self) -> List[Dict[str, Any]]:
        """获取模板列表"""
        try:
            templates = []
            
            for template_file in self.template_dir.glob("*.html"):
                templates.append({
                    'name': template_file.stem,
                    'type': 'html',
                    'path': str(template_file),
                    'size': template_file.stat().st_size,
                    'modified': datetime.fromtimestamp(template_file.stat().st_mtime)
                })
            
            return templates
            
        except Exception as e:
            logger.error(f"获取模板列表失败: {e}")
            return []
    
    async def export_report_to_pdf(
        self,
        html_content: str,
        output_path: str = None
    ) -> str:
        """导出报告为PDF"""
        try:
            import weasyprint
            
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"reports/report_{timestamp}.pdf"
            
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 生成PDF
            weasyprint.HTML(string=html_content).write_pdf(output_path)
            
            logger.info(f"PDF报告生成成功: {output_path}")
            return output_path
            
        except ImportError:
            logger.warning("weasyprint未安装，无法生成PDF")
            raise ValueError("PDF生成功能需要安装weasyprint")
        except Exception as e:
            logger.error(f"生成PDF失败: {e}")
            raise
    
    async def schedule_report_generation(
        self,
        user_id: int,
        report_type: str,
        schedule_config: Dict[str, Any]
    ) -> bool:
        """调度报告生成"""
        try:
            # 这里应该集成到任务调度系统
            # 暂时记录调度配置
            logger.info(f"调度报告生成: 用户{user_id}, 类型{report_type}, 配置{schedule_config}")
            
            # TODO: 实现实际的调度逻辑
            return True
            
        except Exception as e:
            logger.error(f"调度报告生成失败: {e}")
            return False
    
    async def generate_custom_report(
        self,
        user_id: int,
        template_name: str,
        data_sources: List[str],
        parameters: Dict[str, Any]
    ) -> str:
        """生成自定义报告"""
        try:
            # 根据数据源收集数据
            report_data = {}
            
            for source in data_sources:
                if source == 'trading':
                    report_data['trading'] = await self._collect_trading_data(
                        user_id,
                        parameters.get('start_date'),
                        parameters.get('end_date')
                    )
                elif source == 'performance':
                    report_data['performance'] = await self._collect_performance_data(
                        user_id,
                        parameters.get('start_date'),
                        parameters.get('end_date')
                    )
                elif source == 'risk':
                    report_data['risk'] = await self._collect_risk_data(
                        user_id,
                        parameters.get('start_date'),
                        parameters.get('end_date')
                    )
            
            # 加载自定义模板
            template = self.jinja_env.get_template(template_name)
            
            # 渲染报告
            html_content = template.render(
                report_data=report_data,
                parameters=parameters,
                user_id=user_id,
                generated_at=datetime.utcnow()
            )
            
            return html_content
            
        except Exception as e:
            logger.error(f"生成自定义报告失败: {e}")
            raise


# 全局报告服务实例
report_service = ReportService()