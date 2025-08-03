"""
实时风险监控服务
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func
from decimal import Decimal

from ..models.risk import RiskRule, RiskEvent
from ..models.position import Position
from ..models.trading import TradingAccount
from ..models.user import User
from ..models.order import Order
from ..utils.risk_calculator import RiskCalculator

logger = logging.getLogger(__name__)

class RiskMonitoringService:
    """实时风险监控服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.risk_calculator = RiskCalculator()
    
    # ==================== 实时风险指标计算 ====================
    
    def calculate_real_time_risk_metrics(self, user_id: int) -> Dict[str, Any]:
        """计算实时风险指标"""
        try:
            # 获取用户账户信息
            account = self.db.query(TradingAccount).filter(
                TradingAccount.user_id == user_id
            ).first()
            
            if not account:
                return {}
            
            # 获取用户持仓
            positions = self.db.query(Position).filter(
                Position.user_id == user_id,
                Position.status == 'OPEN'
            ).all()
            
            # 获取用户活跃订单
            active_orders = self.db.query(Order).filter(
                Order.user_id == user_id,
                Order.status.in_(['PENDING', 'PARTIALLY_FILLED'])
            ).all()
            
            # 计算基础风险指标
            total_equity = float(account.total_equity or 0)
            available_balance = float(account.available_balance or 0)
            used_margin = float(account.used_margin or 0)
            
            # 计算持仓风险
            total_position_value = sum(float(pos.market_value or 0) for pos in positions)
            total_unrealized_pnl = sum(float(pos.unrealized_pnl or 0) for pos in positions)
            
            # 计算风险指标
            risk_metrics = {
                'account_metrics': {
                    'total_equity': total_equity,
                    'available_balance': available_balance,
                    'used_margin': used_margin,
                    'margin_ratio': (used_margin / total_equity * 100) if total_equity > 0 else 0,
                    'free_margin_ratio': (available_balance / total_equity * 100) if total_equity > 0 else 0
                },
                'position_metrics': {
                    'total_positions': len(positions),
                    'total_position_value': total_position_value,
                    'total_unrealized_pnl': total_unrealized_pnl,
                    'position_concentration': self._calculate_position_concentration(positions),
                    'largest_position_ratio': self._calculate_largest_position_ratio(positions, total_equity)
                },
                'risk_indicators': {
                    'leverage_ratio': (total_position_value / total_equity) if total_equity > 0 else 0,
                    'drawdown_ratio': self._calculate_drawdown_ratio(user_id),
                    'var_1d': self._calculate_var(positions, 0.95, 1),  # 1日95%VaR
                    'var_5d': self._calculate_var(positions, 0.95, 5),  # 5日95%VaR
                    'beta': self._calculate_portfolio_beta(positions),
                    'sharpe_ratio': self._calculate_sharpe_ratio(user_id)
                },
                'order_metrics': {
                    'active_orders': len(active_orders),
                    'pending_buy_value': sum(float(order.quantity * order.price) for order in active_orders if order.side == 'BUY'),
                    'pending_sell_value': sum(float(order.quantity * order.price) for order in active_orders if order.side == 'SELL')
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return risk_metrics
            
        except Exception as e:
            logger.error(f"计算实时风险指标失败: {e}")
            return {}
    
    def _calculate_position_concentration(self, positions: List[Position]) -> Dict[str, float]:
        """计算持仓集中度"""
        if not positions:
            return {'herfindahl_index': 0, 'top3_concentration': 0, 'top5_concentration': 0}
        
        # 按市值排序
        position_values = [float(pos.market_value or 0) for pos in positions]
        total_value = sum(position_values)
        
        if total_value == 0:
            return {'herfindahl_index': 0, 'top3_concentration': 0, 'top5_concentration': 0}
        
        # 计算权重
        weights = [value / total_value for value in position_values]
        weights.sort(reverse=True)
        
        # 赫芬达尔指数
        herfindahl_index = sum(w * w for w in weights)
        
        # 前3大持仓集中度
        top3_concentration = sum(weights[:3]) * 100
        
        # 前5大持仓集中度
        top5_concentration = sum(weights[:5]) * 100
        
        return {
            'herfindahl_index': herfindahl_index,
            'top3_concentration': top3_concentration,
            'top5_concentration': top5_concentration
        }
    
    def _calculate_largest_position_ratio(self, positions: List[Position], total_equity: float) -> float:
        """计算最大持仓占比"""
        if not positions or total_equity == 0:
            return 0
        
        largest_position = max(float(pos.market_value or 0) for pos in positions)
        return (largest_position / total_equity) * 100
    
    def _calculate_drawdown_ratio(self, user_id: int) -> float:
        """计算回撤比率"""
        try:
            # 获取最近30天的账户净值历史
            # 这里简化处理，实际应该从账户净值历史表获取
            account = self.db.query(TradingAccount).filter(
                TradingAccount.user_id == user_id
            ).first()
            
            if not account:
                return 0
            
            current_equity = float(account.total_equity or 0)
            initial_balance = float(account.initial_balance or current_equity)
            
            if initial_balance == 0:
                return 0
            
            # 简化计算：当前净值相对于初始资金的回撤
            if current_equity < initial_balance:
                return ((initial_balance - current_equity) / initial_balance) * 100
            
            return 0
            
        except Exception as e:
            logger.error(f"计算回撤比率失败: {e}")
            return 0
    
    def _calculate_var(self, positions: List[Position], confidence_level: float, days: int) -> float:
        """计算风险价值(VaR)"""
        try:
            if not positions:
                return 0
            
            # 简化VaR计算，实际应该基于历史价格波动率
            total_value = sum(float(pos.market_value or 0) for pos in positions)
            
            # 假设日波动率为2%
            daily_volatility = 0.02
            period_volatility = daily_volatility * (days ** 0.5)
            
            # 根据置信水平计算VaR
            if confidence_level == 0.95:
                z_score = 1.645
            elif confidence_level == 0.99:
                z_score = 2.326
            else:
                z_score = 1.645
            
            var = total_value * period_volatility * z_score
            return var
            
        except Exception as e:
            logger.error(f"计算VaR失败: {e}")
            return 0
    
    def _calculate_portfolio_beta(self, positions: List[Position]) -> float:
        """计算组合贝塔值"""
        try:
            # 简化处理，实际应该基于历史价格数据计算
            if not positions:
                return 0
            
            # 假设平均贝塔值为1.0
            return 1.0
            
        except Exception as e:
            logger.error(f"计算组合贝塔失败: {e}")
            return 1.0
    
    def _calculate_sharpe_ratio(self, user_id: int) -> float:
        """计算夏普比率"""
        try:
            # 简化处理，实际应该基于历史收益率数据计算
            # 这里返回一个示例值
            return 1.2
            
        except Exception as e:
            logger.error(f"计算夏普比率失败: {e}")
            return 0
    
    # ==================== 风险预警检查 ====================
    
    def check_risk_alerts(self, user_id: int) -> List[Dict[str, Any]]:
        """检查风险预警"""
        try:
            alerts = []
            
            # 获取风险指标
            risk_metrics = self.calculate_real_time_risk_metrics(user_id)
            if not risk_metrics:
                return alerts
            
            account_metrics = risk_metrics.get('account_metrics', {})
            position_metrics = risk_metrics.get('position_metrics', {})
            risk_indicators = risk_metrics.get('risk_indicators', {})
            
            # 检查保证金比率
            margin_ratio = account_metrics.get('margin_ratio', 0)
            if margin_ratio > 80:
                alerts.append({
                    'type': 'MARGIN_WARNING',
                    'severity': 'HIGH' if margin_ratio > 90 else 'MEDIUM',
                    'title': '保证金比率过高',
                    'message': f'当前保证金比率为 {margin_ratio:.1f}%，存在强制平仓风险',
                    'value': margin_ratio,
                    'threshold': 80,
                    'timestamp': datetime.now().isoformat()
                })
            
            # 检查杠杆比率
            leverage_ratio = risk_indicators.get('leverage_ratio', 0)
            if leverage_ratio > 5:
                alerts.append({
                    'type': 'LEVERAGE_WARNING',
                    'severity': 'HIGH' if leverage_ratio > 10 else 'MEDIUM',
                    'title': '杠杆比率过高',
                    'message': f'当前杠杆比率为 {leverage_ratio:.1f}倍，风险较高',
                    'value': leverage_ratio,
                    'threshold': 5,
                    'timestamp': datetime.now().isoformat()
                })
            
            # 检查持仓集中度
            concentration = position_metrics.get('position_concentration', {})
            top3_concentration = concentration.get('top3_concentration', 0)
            if top3_concentration > 60:
                alerts.append({
                    'type': 'CONCENTRATION_WARNING',
                    'severity': 'MEDIUM',
                    'title': '持仓集中度过高',
                    'message': f'前3大持仓占比 {top3_concentration:.1f}%，建议分散投资',
                    'value': top3_concentration,
                    'threshold': 60,
                    'timestamp': datetime.now().isoformat()
                })
            
            # 检查回撤比率
            drawdown_ratio = risk_indicators.get('drawdown_ratio', 0)
            if drawdown_ratio > 20:
                alerts.append({
                    'type': 'DRAWDOWN_WARNING',
                    'severity': 'HIGH' if drawdown_ratio > 30 else 'MEDIUM',
                    'title': '回撤比率过高',
                    'message': f'当前回撤比率为 {drawdown_ratio:.1f}%，建议控制风险',
                    'value': drawdown_ratio,
                    'threshold': 20,
                    'timestamp': datetime.now().isoformat()
                })
            
            # 检查VaR
            var_1d = risk_indicators.get('var_1d', 0)
            total_equity = account_metrics.get('total_equity', 0)
            if var_1d > 0 and total_equity > 0:
                var_ratio = (var_1d / total_equity) * 100
                if var_ratio > 5:
                    alerts.append({
                        'type': 'VAR_WARNING',
                        'severity': 'MEDIUM',
                        'title': 'VaR风险过高',
                        'message': f'1日VaR占净值比例为 {var_ratio:.1f}%，存在较大损失风险',
                        'value': var_ratio,
                        'threshold': 5,
                        'timestamp': datetime.now().isoformat()
                    })
            
            return alerts
            
        except Exception as e:
            logger.error(f"检查风险预警失败: {e}")
            return []
    
    # ==================== 风险事件记录 ====================
    
    def record_risk_event(self, user_id: int, event_data: Dict[str, Any]) -> Optional[RiskEvent]:
        """记录风险事件"""
        try:
            risk_event = RiskEvent(
                user_id=user_id,
                event_type=event_data['event_type'],
                severity=event_data['severity'],
                title=event_data['title'],
                description=event_data.get('description', ''),
                risk_value=Decimal(str(event_data.get('risk_value', 0))),
                threshold_value=Decimal(str(event_data.get('threshold_value', 0))),
                triggered_rule_id=event_data.get('triggered_rule_id'),
                metadata=event_data.get('metadata', {}),
                is_resolved=False
            )
            
            self.db.add(risk_event)
            self.db.commit()
            self.db.refresh(risk_event)
            
            logger.info(f"记录风险事件成功: {user_id}, {event_data['event_type']}")
            return risk_event
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"记录风险事件失败: {e}")
            return None
    
    def get_risk_events(self, user_id: int, days: int = 30, 
                       event_type: str = None, severity: str = None) -> List[Dict[str, Any]]:
        """获取风险事件"""
        try:
            start_time = datetime.now() - timedelta(days=days)
            
            query = self.db.query(RiskEvent).filter(
                RiskEvent.user_id == user_id,
                RiskEvent.created_at >= start_time
            )
            
            if event_type:
                query = query.filter(RiskEvent.event_type == event_type)
            
            if severity:
                query = query.filter(RiskEvent.severity == severity)
            
            events = query.order_by(desc(RiskEvent.created_at)).all()
            
            result = []
            for event in events:
                result.append({
                    'id': event.id,
                    'event_type': event.event_type,
                    'severity': event.severity,
                    'title': event.title,
                    'description': event.description,
                    'risk_value': float(event.risk_value or 0),
                    'threshold_value': float(event.threshold_value or 0),
                    'triggered_rule_id': event.triggered_rule_id,
                    'metadata': event.metadata,
                    'is_resolved': event.is_resolved,
                    'resolved_at': event.resolved_at.isoformat() if event.resolved_at else None,
                    'created_at': event.created_at.isoformat()
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取风险事件失败: {e}")
            return []
    
    def resolve_risk_event(self, user_id: int, event_id: int, resolution_note: str = None) -> bool:
        """解决风险事件"""
        try:
            event = self.db.query(RiskEvent).filter(
                and_(
                    RiskEvent.id == event_id,
                    RiskEvent.user_id == user_id
                )
            ).first()
            
            if not event:
                return False
            
            event.is_resolved = True
            event.resolved_at = datetime.now()
            if resolution_note:
                event.resolution_note = resolution_note
            
            self.db.commit()
            
            logger.info(f"解决风险事件成功: {event_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"解决风险事件失败: {e}")
            return False
    
    # ==================== 风险监控统计 ====================
    
    def get_risk_statistics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """获取风险统计"""
        try:
            start_time = datetime.now() - timedelta(days=days)
            
            # 获取风险事件统计
            events = self.db.query(RiskEvent).filter(
                RiskEvent.user_id == user_id,
                RiskEvent.created_at >= start_time
            ).all()
            
            # 按严重程度分类
            severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
            event_type_counts = {}
            resolved_count = 0
            
            for event in events:
                severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1
                event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1
                if event.is_resolved:
                    resolved_count += 1
            
            # 获取当前风险指标
            current_metrics = self.calculate_real_time_risk_metrics(user_id)
            
            return {
                'period_days': days,
                'event_statistics': {
                    'total_events': len(events),
                    'resolved_events': resolved_count,
                    'unresolved_events': len(events) - resolved_count,
                    'resolution_rate': (resolved_count / len(events) * 100) if events else 0,
                    'severity_distribution': severity_counts,
                    'event_type_distribution': event_type_counts
                },
                'current_risk_level': self._assess_overall_risk_level(current_metrics),
                'risk_trend': self._calculate_risk_trend(user_id, days),
                'recommendations': self._generate_risk_recommendations(current_metrics, events)
            }
            
        except Exception as e:
            logger.error(f"获取风险统计失败: {e}")
            return {}
    
    def _assess_overall_risk_level(self, risk_metrics: Dict[str, Any]) -> str:
        """评估整体风险水平"""
        if not risk_metrics:
            return 'UNKNOWN'
        
        risk_score = 0
        
        # 保证金比率评分
        margin_ratio = risk_metrics.get('account_metrics', {}).get('margin_ratio', 0)
        if margin_ratio > 90:
            risk_score += 3
        elif margin_ratio > 80:
            risk_score += 2
        elif margin_ratio > 70:
            risk_score += 1
        
        # 杠杆比率评分
        leverage_ratio = risk_metrics.get('risk_indicators', {}).get('leverage_ratio', 0)
        if leverage_ratio > 10:
            risk_score += 3
        elif leverage_ratio > 5:
            risk_score += 2
        elif leverage_ratio > 3:
            risk_score += 1
        
        # 回撤比率评分
        drawdown_ratio = risk_metrics.get('risk_indicators', {}).get('drawdown_ratio', 0)
        if drawdown_ratio > 30:
            risk_score += 3
        elif drawdown_ratio > 20:
            risk_score += 2
        elif drawdown_ratio > 10:
            risk_score += 1
        
        # 持仓集中度评分
        concentration = risk_metrics.get('position_metrics', {}).get('position_concentration', {})
        top3_concentration = concentration.get('top3_concentration', 0)
        if top3_concentration > 80:
            risk_score += 2
        elif top3_concentration > 60:
            risk_score += 1
        
        # 根据总分评估风险等级
        if risk_score >= 7:
            return 'HIGH'
        elif risk_score >= 4:
            return 'MEDIUM'
        elif risk_score >= 2:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _calculate_risk_trend(self, user_id: int, days: int) -> str:
        """计算风险趋势"""
        try:
            # 简化处理，实际应该基于历史风险指标计算趋势
            recent_events = self.db.query(RiskEvent).filter(
                RiskEvent.user_id == user_id,
                RiskEvent.created_at >= datetime.now() - timedelta(days=7)
            ).count()
            
            older_events = self.db.query(RiskEvent).filter(
                RiskEvent.user_id == user_id,
                RiskEvent.created_at >= datetime.now() - timedelta(days=14),
                RiskEvent.created_at < datetime.now() - timedelta(days=7)
            ).count()
            
            if recent_events > older_events:
                return 'INCREASING'
            elif recent_events < older_events:
                return 'DECREASING'
            else:
                return 'STABLE'
                
        except Exception as e:
            logger.error(f"计算风险趋势失败: {e}")
            return 'UNKNOWN'
    
    def _generate_risk_recommendations(self, risk_metrics: Dict[str, Any], 
                                     events: List[RiskEvent]) -> List[str]:
        """生成风险建议"""
        recommendations = []
        
        if not risk_metrics:
            return recommendations
        
        # 基于风险指标生成建议
        margin_ratio = risk_metrics.get('account_metrics', {}).get('margin_ratio', 0)
        if margin_ratio > 80:
            recommendations.append("保证金比率过高，建议减少持仓或增加资金")
        
        leverage_ratio = risk_metrics.get('risk_indicators', {}).get('leverage_ratio', 0)
        if leverage_ratio > 5:
            recommendations.append("杠杆比率过高，建议降低杠杆水平")
        
        concentration = risk_metrics.get('position_metrics', {}).get('position_concentration', {})
        top3_concentration = concentration.get('top3_concentration', 0)
        if top3_concentration > 60:
            recommendations.append("持仓过于集中，建议分散投资降低风险")
        
        drawdown_ratio = risk_metrics.get('risk_indicators', {}).get('drawdown_ratio', 0)
        if drawdown_ratio > 20:
            recommendations.append("回撤较大，建议重新评估投资策略")
        
        # 基于风险事件生成建议
        high_severity_events = [e for e in events if e.severity == 'HIGH']
        if len(high_severity_events) > 3:
            recommendations.append("高风险事件频发，建议暂停交易并重新评估风险管理策略")
        
        return recommendations