"""
异常检测服务
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AnomalyAlert:
    """异常告警"""

    alert_id: str
    alert_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    user_id: Optional[int] = None
    strategy_id: Optional[int] = None
    timestamp: datetime = None
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.details is None:
            self.details = {}


class AnomalyDetectionService:
    """异常检测服务"""

    def __init__(self, db: Session):
        self.db = db

    async def detect_trading_anomalies(self, user_id: int) -> List[AnomalyAlert]:
        """检测交易异常"""
        alerts = []

        try:
            # 检测频繁交易
            frequent_trading_alert = await self._detect_frequent_trading(user_id)
            if frequent_trading_alert:
                alerts.append(frequent_trading_alert)

            # 检测大额交易
            large_trade_alert = await self._detect_large_trades(user_id)
            if large_trade_alert:
                alerts.append(large_trade_alert)

            # 检测异常盈亏
            pnl_alert = await self._detect_abnormal_pnl(user_id)
            if pnl_alert:
                alerts.append(pnl_alert)

            # 检测持仓异常
            position_alert = await self._detect_position_anomalies(user_id)
            if position_alert:
                alerts.append(position_alert)

        except Exception as e:
            logger.error(f"检测用户 {user_id} 交易异常失败: {e}")

        return alerts

    async def detect_system_anomalies(self) -> List[AnomalyAlert]:
        """检测系统异常"""
        alerts = []

        try:
            # 检测系统性能异常
            performance_alert = await self._detect_performance_anomalies()
            if performance_alert:
                alerts.append(performance_alert)

            # 检测数据异常
            data_alert = await self._detect_data_anomalies()
            if data_alert:
                alerts.append(data_alert)

            # 检测连接异常
            connection_alert = await self._detect_connection_anomalies()
            if connection_alert:
                alerts.append(connection_alert)

        except Exception as e:
            logger.error(f"检测系统异常失败: {e}")

        return alerts

    async def _detect_frequent_trading(self, user_id: int) -> Optional[AnomalyAlert]:
        """检测频繁交易"""
        try:
            # 查询最近1小时的交易次数
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)

            from ..models import Order

            trade_count = (
                self.db.query(Order)
                .filter(Order.user_id == user_id, Order.created_at >= one_hour_ago)
                .count()
            )

            # 如果1小时内交易超过100次，认为是频繁交易
            if trade_count > 100:
                return AnomalyAlert(
                    alert_id=f"frequent_trading_{user_id}_{datetime.utcnow().timestamp()}",
                    alert_type="FREQUENT_TRADING",
                    severity="HIGH",
                    message=f"用户在1小时内进行了{trade_count}次交易，疑似频繁交易",
                    user_id=user_id,
                    details={"trade_count": trade_count, "time_window": "1hour"},
                )

        except Exception as e:
            logger.error(f"检测频繁交易失败: {e}")

        return None

    async def _detect_large_trades(self, user_id: int) -> Optional[AnomalyAlert]:
        """检测大额交易"""
        try:
            # 查询最近的大额交易
            from ..models import Order

            recent_orders = (
                self.db.query(Order)
                .filter(
                    Order.user_id == user_id,
                    Order.created_at >= datetime.utcnow() - timedelta(hours=24),
                )
                .all()
            )

            large_trades = []
            for order in recent_orders:
                # 假设交易金额超过100万认为是大额交易
                if order.volume * order.price > 1000000:
                    large_trades.append(order)

            if large_trades:
                total_amount = sum(order.volume * order.price for order in large_trades)
                return AnomalyAlert(
                    alert_id=f"large_trade_{user_id}_{datetime.utcnow().timestamp()}",
                    alert_type="LARGE_TRADE",
                    severity="MEDIUM",
                    message=f"用户进行了{len(large_trades)}笔大额交易，总金额{total_amount:.2f}",
                    user_id=user_id,
                    details={
                        "trade_count": len(large_trades),
                        "total_amount": total_amount,
                    },
                )

        except Exception as e:
            logger.error(f"检测大额交易失败: {e}")

        return None

    async def _detect_abnormal_pnl(self, user_id: int) -> Optional[AnomalyAlert]:
        """检测异常盈亏"""
        try:
            # 这里应该实现盈亏异常检测逻辑
            # 简化实现：检查是否有异常的盈亏波动

            from ..models import Account

            account = self.db.query(Account).filter(Account.user_id == user_id).first()

            if account and account.total_pnl < -account.initial_balance * 0.5:
                return AnomalyAlert(
                    alert_id=f"abnormal_pnl_{user_id}_{datetime.utcnow().timestamp()}",
                    alert_type="ABNORMAL_PNL",
                    severity="CRITICAL",
                    message=f"用户总盈亏{account.total_pnl}，超过初始资金的50%",
                    user_id=user_id,
                    details={
                        "total_pnl": account.total_pnl,
                        "initial_balance": account.initial_balance,
                    },
                )

        except Exception as e:
            logger.error(f"检测异常盈亏失败: {e}")

        return None

    async def _detect_position_anomalies(self, user_id: int) -> Optional[AnomalyAlert]:
        """检测持仓异常"""
        try:
            # 检测持仓集中度等异常
            from ..models import Position

            positions = (
                self.db.query(Position)
                .filter(Position.user_id == user_id, Position.volume > 0)
                .all()
            )

            if len(positions) > 50:  # 持仓品种过多
                return AnomalyAlert(
                    alert_id=f"position_anomaly_{user_id}_{datetime.utcnow().timestamp()}",
                    alert_type="POSITION_ANOMALY",
                    severity="MEDIUM",
                    message=f"用户持仓品种过多，共{len(positions)}个品种",
                    user_id=user_id,
                    details={"position_count": len(positions)},
                )

        except Exception as e:
            logger.error(f"检测持仓异常失败: {e}")

        return None

    async def _detect_performance_anomalies(self) -> Optional[AnomalyAlert]:
        """检测系统性能异常"""
        try:
            # 检查系统资源使用情况
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent

            if cpu_percent > 90:
                return AnomalyAlert(
                    alert_id=f"performance_cpu_{datetime.utcnow().timestamp()}",
                    alert_type="PERFORMANCE_ANOMALY",
                    severity="HIGH",
                    message=f"CPU使用率过高: {cpu_percent}%",
                    details={"cpu_percent": cpu_percent},
                )

            if memory_percent > 90:
                return AnomalyAlert(
                    alert_id=f"performance_memory_{datetime.utcnow().timestamp()}",
                    alert_type="PERFORMANCE_ANOMALY",
                    severity="HIGH",
                    message=f"内存使用率过高: {memory_percent}%",
                    details={"memory_percent": memory_percent},
                )

        except Exception as e:
            logger.error(f"检测系统性能异常失败: {e}")

        return None

    async def _detect_data_anomalies(self) -> Optional[AnomalyAlert]:
        """检测数据异常"""
        try:
            # 检查数据完整性
            from ..models import User, Account, Order

            # 检查是否有用户没有对应的账户
            users_without_account = (
                self.db.query(User)
                .outerjoin(Account)
                .filter(Account.id.is_(None))
                .count()
            )

            if users_without_account > 0:
                return AnomalyAlert(
                    alert_id=f"data_integrity_{datetime.utcnow().timestamp()}",
                    alert_type="DATA_ANOMALY",
                    severity="MEDIUM",
                    message=f"发现{users_without_account}个用户没有对应的交易账户",
                    details={"users_without_account": users_without_account},
                )

        except Exception as e:
            logger.error(f"检测数据异常失败: {e}")

        return None

    async def _detect_connection_anomalies(self) -> Optional[AnomalyAlert]:
        """检测连接异常"""
        try:
            # 检查数据库连接
            from sqlalchemy import text

            self.db.execute(text("SELECT 1"))

            # 这里可以添加更多连接检查逻辑
            # 比如检查Redis连接、InfluxDB连接等

        except Exception as e:
            logger.error(f"检测连接异常失败: {e}")
            return AnomalyAlert(
                alert_id=f"connection_db_{datetime.utcnow().timestamp()}",
                alert_type="CONNECTION_ANOMALY",
                severity="CRITICAL",
                message=f"数据库连接异常: {str(e)}",
                details={"error": str(e)},
            )

        return None

    async def handle_alert(self, alert: AnomalyAlert):
        """处理异常告警"""
        try:
            logger.warning(f"处理异常告警: {alert.alert_type} - {alert.message}")

            # 根据告警类型和严重程度采取不同的处理措施
            if alert.severity == "CRITICAL":
                await self._handle_critical_alert(alert)
            elif alert.severity == "HIGH":
                await self._handle_high_alert(alert)
            elif alert.severity == "MEDIUM":
                await self._handle_medium_alert(alert)
            else:
                await self._handle_low_alert(alert)

        except Exception as e:
            logger.error(f"处理异常告警失败: {e}")

    async def _handle_critical_alert(self, alert: AnomalyAlert):
        """处理严重告警"""
        logger.critical(f"严重告警: {alert.message}")

        # 可以实现紧急处理逻辑，如暂停交易、发送紧急通知等
        if alert.alert_type == "ABNORMAL_PNL" and alert.user_id:
            logger.critical(f"用户 {alert.user_id} 盈亏异常，建议暂停交易")

    async def _handle_high_alert(self, alert: AnomalyAlert):
        """处理高级告警"""
        logger.error(f"高级告警: {alert.message}")

        # 可以实现高级处理逻辑
        if alert.alert_type == "FREQUENT_TRADING" and alert.user_id:
            logger.error(f"用户 {alert.user_id} 频繁交易，建议限制交易频率")

    async def _handle_medium_alert(self, alert: AnomalyAlert):
        """处理中级告警"""
        logger.warning(f"中级告警: {alert.message}")

        # 可以实现中级处理逻辑

    async def _handle_low_alert(self, alert: AnomalyAlert):
        """处理低级告警"""
        logger.info(f"低级告警: {alert.message}")

        # 可以实现低级处理逻辑
