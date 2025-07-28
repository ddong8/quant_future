"""
异常检测和处理服务
"""
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
import logging
import numpy as np
from dataclasses import dataclass
from enum import Enum

from ..models import User, Order, Position, TradingAccount, RiskEvent
from ..models.enums import OrderStatus, RiskEventType
from ..core.exceptions import SystemError

logger = logging.getLogger(__name__)


class AnomalyType(str, Enum):
    """异常类型枚举"""
    ABNORMAL_TRADING_FREQUENCY = "abnormal_trading_frequency"
    ABNORMAL_ORDER_SIZE = "abnormal_order_size"
    ABNORMAL_PRICE_DEVIATION = "abnormal_price_deviation"
    ABNORMAL_LOSS_PATTERN = "abnormal_loss_pattern"
    SYSTEM_PERFORMANCE_ANOMALY = "system_performance_anomaly"
    MARKET_DATA_ANOMALY = "market_data_anomaly"
    ACCOUNT_BALANCE_ANOMALY = "account_balance_anomaly"


@dataclass
class AnomalyAlert:
    """异常告警"""
    anomaly_type: AnomalyType
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    title: str
    description: str
    detected_at: datetime
    user_id: Optional[int] = None
    symbol: Optional[str] = None
    anomaly_data: Optional[Dict[str, Any]] = None
    suggested_actions: Optional[List[str]] = None


class AnomalyDetectionService:
    """异常检测服务"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # 异常检测器注册表
        self.detectors = {
            AnomalyType.ABNORMAL_TRADING_FREQUENCY: self._detect_trading_frequency_anomaly,
            AnomalyType.ABNORMAL_ORDER_SIZE: self._detect_order_size_anomaly,
            AnomalyType.ABNORMAL_PRICE_DEVIATION: self._detect_price_deviation_anomaly,
            AnomalyType.ABNORMAL_LOSS_PATTERN: self._detect_loss_pattern_anomaly,
            AnomalyType.ACCOUNT_BALANCE_ANOMALY: self._detect_balance_anomaly,
        }
        
        # 异常处理器注册表
        self.handlers = {
            AnomalyType.ABNORMAL_TRADING_FREQUENCY: self._handle_trading_frequency_anomaly,
            AnomalyType.ABNORMAL_ORDER_SIZE: self._handle_order_size_anomaly,
            AnomalyType.ABNORMAL_PRICE_DEVIATION: self._handle_price_deviation_anomaly,
            AnomalyType.ABNORMAL_LOSS_PATTERN: self._handle_loss_pattern_anomaly,
            AnomalyType.ACCOUNT_BALANCE_ANOMALY: self._handle_balance_anomaly,
        }
    
    async def run_anomaly_detection(self, user_id: Optional[int] = None) -> List[AnomalyAlert]:
        """运行异常检测"""
        try:
            alerts = []
            
            # 如果指定了用户，只检测该用户
            if user_id:
                user_alerts = await self._detect_user_anomalies(user_id)
                alerts.extend(user_alerts)
            else:
                # 检测所有活跃用户的异常
                active_users = self.db.query(User).filter(User.is_active == True).all()
                
                for user in active_users:
                    user_alerts = await self._detect_user_anomalies(user.id)
                    alerts.extend(user_alerts)
            
            # 检测系统级异常
            system_alerts = await self._detect_system_anomalies()
            alerts.extend(system_alerts)
            
            # 处理检测到的异常
            for alert in alerts:
                await self._handle_anomaly(alert)
            
            logger.info(f"异常检测完成，发现 {len(alerts)} 个异常")
            return alerts
            
        except Exception as e:
            logger.error(f"异常检测失败: {e}")
            raise SystemError(f"异常检测系统故障: {str(e)}")
    
    async def _detect_user_anomalies(self, user_id: int) -> List[AnomalyAlert]:
        """检测用户异常"""
        alerts = []
        
        try:
            # 运行各种异常检测器
            for anomaly_type, detector in self.detectors.items():
                try:
                    alert = await detector(user_id)
                    if alert:
                        alerts.append(alert)
                except Exception as e:
                    logger.error(f"检测器 {anomaly_type} 执行失败: {e}")
            
            return alerts
            
        except Exception as e:
            logger.error(f"用户异常检测失败: {e}")
            return []
    
    async def _detect_system_anomalies(self) -> List[AnomalyAlert]:
        """检测系统级异常"""
        alerts = []
        
        try:
            # 检测系统性能异常
            performance_alert = await self._detect_system_performance_anomaly()
            if performance_alert:
                alerts.append(performance_alert)
            
            # 检测市场数据异常
            market_data_alert = await self._detect_market_data_anomaly()
            if market_data_alert:
                alerts.append(market_data_alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"系统异常检测失败: {e}")
            return []
    
    async def _detect_trading_frequency_anomaly(self, user_id: int) -> Optional[AnomalyAlert]:
        """检测交易频率异常"""
        try:
            # 获取最近1小时的订单数量
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            recent_orders_count = self.db.query(func.count(Order.id)).filter(
                and_(
                    Order.user_id == user_id,
                    Order.created_at >= one_hour_ago
                )
            ).scalar()
            
            # 获取用户历史平均交易频率
            avg_orders_per_hour = await self._get_average_trading_frequency(user_id)
            
            # 如果当前频率超过历史平均的5倍，认为异常
            if recent_orders_count > max(avg_orders_per_hour * 5, 50):
                return AnomalyAlert(
                    anomaly_type=AnomalyType.ABNORMAL_TRADING_FREQUENCY,
                    severity="HIGH",
                    title="交易频率异常",
                    description=f"用户在过去1小时内下单 {recent_orders_count} 次，远超历史平均 {avg_orders_per_hour:.1f} 次",
                    detected_at=datetime.utcnow(),
                    user_id=user_id,
                    anomaly_data={\n                        "recent_orders_count": recent_orders_count,\n                        "average_orders_per_hour": avg_orders_per_hour,\n                        "threshold_multiplier": 5\n                    },\n                    suggested_actions=["暂停交易", "人工审核", "联系用户确认"]\n                )\n            \n            return None\n            \n        except Exception as e:\n            logger.error(f"交易频率异常检测失败: {e}")\n            return None\n    \n    async def _detect_order_size_anomaly(self, user_id: int) -> Optional[AnomalyAlert]:\n        """检测订单大小异常"""\n        try:\n            # 获取最近的订单\n            recent_orders = self.db.query(Order).filter(\n                and_(\n                    Order.user_id == user_id,\n                    Order.created_at >= datetime.utcnow() - timedelta(days=1)\n                )\n            ).all()\n            \n            if not recent_orders:\n                return None\n            \n            # 计算订单大小统计\n            order_sizes = [float(order.quantity) for order in recent_orders]\n            mean_size = np.mean(order_sizes)\n            std_size = np.std(order_sizes)\n            \n            # 检查是否有异常大的订单（超过3个标准差）\n            for order in recent_orders:\n                order_size = float(order.quantity)\n                if std_size > 0 and abs(order_size - mean_size) > 3 * std_size:\n                    return AnomalyAlert(\n                        anomaly_type=AnomalyType.ABNORMAL_ORDER_SIZE,\n                        severity="MEDIUM",\n                        title="订单大小异常",\n                        description=f"订单 {order.order_id} 大小 {order_size} 异常，偏离平均值 {abs(order_size - mean_size):.2f}",\n                        detected_at=datetime.utcnow(),\n                        user_id=user_id,\n                        anomaly_data={\n                            "order_id": order.order_id,\n                            "order_size": order_size,\n                            "mean_size": mean_size,\n                            "std_size": std_size,\n                            "deviation": abs(order_size - mean_size)\n                        },\n                        suggested_actions=["审核订单", "确认用户意图"]\n                    )\n            \n            return None\n            \n        except Exception as e:\n            logger.error(f"订单大小异常检测失败: {e}")\n            return None\n    \n    async def _detect_price_deviation_anomaly(self, user_id: int) -> Optional[AnomalyAlert]:\n        """检测价格偏离异常"""\n        try:\n            # 获取最近的限价订单\n            recent_limit_orders = self.db.query(Order).filter(\n                and_(\n                    Order.user_id == user_id,\n                    Order.price.isnot(None),\n                    Order.created_at >= datetime.utcnow() - timedelta(hours=1)\n                )\n            ).all()\n            \n            for order in recent_limit_orders:\n                # 这里应该获取当时的市场价格进行比较\n                # 简化实现：假设市场价格为50000\n                market_price = 50000.0\n                order_price = float(order.price)\n                \n                deviation = abs(order_price - market_price) / market_price\n                \n                # 如果价格偏离超过10%，认为异常\n                if deviation > 0.1:\n                    return AnomalyAlert(\n                        anomaly_type=AnomalyType.ABNORMAL_PRICE_DEVIATION,\n                        severity="MEDIUM",\n                        title="订单价格偏离异常",\n                        description=f"订单 {order.order_id} 价格 {order_price} 偏离市价 {market_price} 达 {deviation:.2%}",\n                        detected_at=datetime.utcnow(),\n                        user_id=user_id,\n                        symbol=order.symbol,\n                        anomaly_data={\n                            "order_id": order.order_id,\n                            "order_price": order_price,\n                            "market_price": market_price,\n                            "deviation": deviation\n                        },\n                        suggested_actions=["检查价格输入", "确认用户意图"]\n                    )\n            \n            return None\n            \n        except Exception as e:\n            logger.error(f"价格偏离异常检测失败: {e}")\n            return None\n    \n    async def _detect_loss_pattern_anomaly(self, user_id: int) -> Optional[AnomalyAlert]:\n        """检测亏损模式异常"""\n        try:\n            # 获取最近的已完成订单\n            recent_filled_orders = self.db.query(Order).filter(\n                and_(\n                    Order.user_id == user_id,\n                    Order.status == OrderStatus.FILLED,\n                    Order.completed_at >= datetime.utcnow() - timedelta(days=7)\n                )\n            ).order_by(desc(Order.completed_at)).all()\n            \n            if len(recent_filled_orders) < 10:  # 样本太少\n                return None\n            \n            # 计算连续亏损次数\n            consecutive_losses = 0\n            total_pnl = 0\n            \n            for order in recent_filled_orders:\n                pnl = float(order.realized_pnl or 0)\n                total_pnl += pnl\n                \n                if pnl < 0:\n                    consecutive_losses += 1\n                else:\n                    break\n            \n            # 如果连续亏损超过8次或总亏损超过账户的20%\n            account = self.db.query(TradingAccount).filter(\n                TradingAccount.user_id == user_id\n            ).first()\n            \n            if account:\n                loss_ratio = abs(total_pnl) / float(account.total_balance) if float(account.total_balance) > 0 else 0\n                \n                if consecutive_losses >= 8 or loss_ratio > 0.2:\n                    return AnomalyAlert(\n                        anomaly_type=AnomalyType.ABNORMAL_LOSS_PATTERN,\n                        severity="HIGH",\n                        title="异常亏损模式",\n                        description=f"连续亏损 {consecutive_losses} 次，总亏损比例 {loss_ratio:.2%}",\n                        detected_at=datetime.utcnow(),\n                        user_id=user_id,\n                        anomaly_data={\n                            "consecutive_losses": consecutive_losses,\n                            "total_pnl": total_pnl,\n                            "loss_ratio": loss_ratio,\n                            "orders_analyzed": len(recent_filled_orders)\n                        },\n                        suggested_actions=["暂停交易", "风险评估", "策略审查"]\n                    )\n            \n            return None\n            \n        except Exception as e:\n            logger.error(f"亏损模式异常检测失败: {e}")\n            return None\n    \n    async def _detect_balance_anomaly(self, user_id: int) -> Optional[AnomalyAlert]:\n        """检测账户余额异常"""\n        try:\n            account = self.db.query(TradingAccount).filter(\n                TradingAccount.user_id == user_id\n            ).first()\n            \n            if not account:\n                return None\n            \n            # 检查余额是否为负数\n            if float(account.available_balance) < 0:\n                return AnomalyAlert(\n                    anomaly_type=AnomalyType.ACCOUNT_BALANCE_ANOMALY,\n                    severity="CRITICAL",\n                    title="账户余额异常",\n                    description=f"可用余额为负数: {account.available_balance}",\n                    detected_at=datetime.utcnow(),\n                    user_id=user_id,\n                    anomaly_data={\n                        "available_balance": float(account.available_balance),\n                        "total_balance": float(account.total_balance),\n                        "used_margin": float(account.used_margin)\n                    },\n                    suggested_actions=["冻结账户", "紧急审查", "联系用户"]\n                )\n            \n            # 检查保证金比例是否过高\n            margin_ratio = float(account.used_margin) / float(account.total_balance) if float(account.total_balance) > 0 else 0\n            \n            if margin_ratio > 0.95:  # 保证金比例超过95%\n                return AnomalyAlert(\n                    anomaly_type=AnomalyType.ACCOUNT_BALANCE_ANOMALY,\n                    severity="HIGH",\n                    title="保证金比例异常",\n                    description=f"保证金比例过高: {margin_ratio:.2%}",\n                    detected_at=datetime.utcnow(),\n                    user_id=user_id,\n                    anomaly_data={\n                        "margin_ratio": margin_ratio,\n                        "used_margin": float(account.used_margin),\n                        "total_balance": float(account.total_balance)\n                    },\n                    suggested_actions=["强制平仓", "追加保证金", "风险警告"]\n                )\n            \n            return None\n            \n        except Exception as e:\n            logger.error(f"余额异常检测失败: {e}")\n            return None\n    \n    async def _detect_system_performance_anomaly(self) -> Optional[AnomalyAlert]:\n        """检测系统性能异常"""\n        try:\n            # 检查最近的订单处理延迟\n            recent_orders = self.db.query(Order).filter(\n                Order.created_at >= datetime.utcnow() - timedelta(minutes=30)\n            ).all()\n            \n            if not recent_orders:\n                return None\n            \n            # 计算平均处理时间（简化实现）\n            processing_times = []\n            for order in recent_orders:\n                if order.updated_at and order.created_at:\n                    processing_time = (order.updated_at - order.created_at).total_seconds()\n                    processing_times.append(processing_time)\n            \n            if processing_times:\n                avg_processing_time = np.mean(processing_times)\n                \n                # 如果平均处理时间超过10秒，认为系统性能异常\n                if avg_processing_time > 10:\n                    return AnomalyAlert(\n                        anomaly_type=AnomalyType.SYSTEM_PERFORMANCE_ANOMALY,\n                        severity="MEDIUM",\n                        title="系统性能异常",\n                        description=f"订单平均处理时间 {avg_processing_time:.2f} 秒，超过正常范围",\n                        detected_at=datetime.utcnow(),\n                        anomaly_data={\n                            "avg_processing_time": avg_processing_time,\n                            "orders_analyzed": len(processing_times),\n                            "threshold": 10\n                        },\n                        suggested_actions=["系统性能检查", "资源扩容", "优化处理流程"]\n                    )\n            \n            return None\n            \n        except Exception as e:\n            logger.error(f"系统性能异常检测失败: {e}")\n            return None\n    \n    async def _detect_market_data_anomaly(self) -> Optional[AnomalyAlert]:\n        """检测市场数据异常"""\n        try:\n            # 这里应该检查市场数据的连续性和合理性\n            # 简化实现：检查是否有市场数据更新\n            \n            # 假设检查最近是否有价格更新\n            # 实际实现需要连接到市场数据服务\n            \n            return None\n            \n        except Exception as e:\n            logger.error(f"市场数据异常检测失败: {e}")\n            return None\n    \n    async def _handle_anomaly(self, alert: AnomalyAlert):\n        """处理异常告警"""\n        try:\n            # 记录异常事件\n            await self._record_anomaly_event(alert)\n            \n            # 执行自动处理\n            if alert.anomaly_type in self.handlers:\n                handler = self.handlers[alert.anomaly_type]\n                await handler(alert)\n            \n            # 发送通知\n            await self._send_anomaly_notification(alert)\n            \n        except Exception as e:\n            logger.error(f"异常处理失败: {e}")\n    \n    async def _record_anomaly_event(self, alert: AnomalyAlert):\n        """记录异常事件"""\n        try:\n            risk_event = RiskEvent(\n                user_id=alert.user_id,\n                event_type=RiskEventType.ABNORMAL_TRADING,\n                severity=alert.severity,\n                title=alert.title,\n                description=alert.description,\n                event_data=alert.anomaly_data,\n                created_at=alert.detected_at,\n                updated_at=datetime.utcnow()\n            )\n            \n            self.db.add(risk_event)\n            self.db.commit()\n            \n            logger.info(f"异常事件已记录: {alert.title}")\n            \n        except Exception as e:\n            logger.error(f"记录异常事件失败: {e}")\n    \n    async def _send_anomaly_notification(self, alert: AnomalyAlert):\n        """发送异常通知"""\n        try:\n            # 这里应该调用通知服务发送告警\n            logger.warning(f"异常告警: {alert.title} - {alert.description}")\n            \n        except Exception as e:\n            logger.error(f"发送异常通知失败: {e}")\n    \n    async def _get_average_trading_frequency(self, user_id: int) -> float:\n        """获取用户历史平均交易频率"""\n        try:\n            # 获取过去30天的订单数据\n            thirty_days_ago = datetime.utcnow() - timedelta(days=30)\n            \n            total_orders = self.db.query(func.count(Order.id)).filter(\n                and_(\n                    Order.user_id == user_id,\n                    Order.created_at >= thirty_days_ago\n                )\n            ).scalar()\n            \n            # 计算每小时平均订单数\n            hours_in_30_days = 30 * 24\n            return total_orders / hours_in_30_days if hours_in_30_days > 0 else 0\n            \n        except Exception as e:\n            logger.error(f"获取平均交易频率失败: {e}")\n            return 0\n    \n    # 异常处理器实现\n    async def _handle_trading_frequency_anomaly(self, alert: AnomalyAlert):\n        """处理交易频率异常"""\n        if alert.severity == "HIGH" and alert.user_id:\n            # 可以实现暂停用户交易等逻辑\n            logger.warning(f"用户 {alert.user_id} 交易频率异常，建议暂停交易")\n    \n    async def _handle_order_size_anomaly(self, alert: AnomalyAlert):\n        """处理订单大小异常"""\n        if alert.user_id:\n            logger.warning(f"用户 {alert.user_id} 订单大小异常，建议人工审核")\n    \n    async def _handle_price_deviation_anomaly(self, alert: AnomalyAlert):\n        """处理价格偏离异常"""\n        if alert.user_id:\n            logger.warning(f"用户 {alert.user_id} 订单价格异常，建议确认")\n    \n    async def _handle_loss_pattern_anomaly(self, alert: AnomalyAlert):\n        """处理亏损模式异常"""\n        if alert.severity == "HIGH" and alert.user_id:\n            # 可以实现自动暂停交易等逻辑\n            logger.warning(f"用户 {alert.user_id} 亏损模式异常，建议暂停交易")\n    \n    async def _handle_balance_anomaly(self, alert: AnomalyAlert):\n        """处理余额异常"""\n        if alert.severity == "CRITICAL" and alert.user_id:\n            # 可以实现冻结账户等逻辑\n            logger.critical(f"用户 {alert.user_id} 账户余额异常，建议冻结账户")