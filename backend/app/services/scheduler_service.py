"""
定时任务调度服务
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from ..core.database import get_db
from .anomaly_detection_service import AnomalyDetectionService
from .risk_engine import get_risk_engine
from .account_service import AccountService

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务调度服务"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def start(self):
        """启动调度器"""
        if self.is_running:
            return
        
        try:
            # 注册定时任务
            await self._register_jobs()
            
            # 启动调度器
            self.scheduler.start()
            self.is_running = True
            
            logger.info("定时任务调度器启动成功")
            
        except Exception as e:
            logger.error(f"启动定时任务调度器失败: {e}")
            raise
    
    async def stop(self):
        """停止调度器"""
        if not self.is_running:
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            
            logger.info("定时任务调度器已停止")
            
        except Exception as e:
            logger.error(f"停止定时任务调度器失败: {e}")
    
    async def _register_jobs(self):
        """注册定时任务"""
        try:
            # 异常检测任务 - 每5分钟执行一次
            self.scheduler.add_job(
                func=self._run_anomaly_detection,
                trigger=IntervalTrigger(minutes=5),
                id="anomaly_detection",
                name="异常检测任务",
                max_instances=1,
                coalesce=True
            )
            
            # 风险监控任务 - 每分钟执行一次
            self.scheduler.add_job(
                func=self._run_risk_monitoring,
                trigger=IntervalTrigger(minutes=1),
                id="risk_monitoring",
                name="风险监控任务",
                max_instances=1,
                coalesce=True
            )
            
            # 账户余额更新任务 - 每30秒执行一次
            self.scheduler.add_job(
                func=self._update_account_balances,
                trigger=IntervalTrigger(seconds=30),
                id="balance_update",
                name="账户余额更新任务",
                max_instances=1,
                coalesce=True
            )
            
            # 持仓市值更新任务 - 每10秒执行一次
            self.scheduler.add_job(
                func=self._update_position_values,
                trigger=IntervalTrigger(seconds=10),
                id="position_update",
                name="持仓市值更新任务",
                max_instances=1,
                coalesce=True
            )
            
            # 日终清算任务 - 每天凌晨2点执行
            self.scheduler.add_job(
                func=self._daily_settlement,
                trigger=CronTrigger(hour=2, minute=0),
                id="daily_settlement",
                name="日终清算任务",
                max_instances=1,
                coalesce=True
            )
            
            # 系统健康检查任务 - 每10分钟执行一次
            self.scheduler.add_job(
                func=self._system_health_check,
                trigger=IntervalTrigger(minutes=10),
                id="health_check",
                name="系统健康检查任务",
                max_instances=1,
                coalesce=True
            )
            
            logger.info("定时任务注册完成")
            
        except Exception as e:
            logger.error(f"注册定时任务失败: {e}")
            raise
    
    async def _run_anomaly_detection(self):
        """运行异常检测任务"""
        try:
            logger.debug("开始执行异常检测任务")
            
            db = next(get_db())
            try:
                anomaly_service = AnomalyDetectionService(db)
                alerts = await anomaly_service.run_anomaly_detection()
                
                if alerts:
                    logger.info(f"异常检测完成，发现 {len(alerts)} 个异常")
                    
                    # 统计异常类型
                    anomaly_stats = {}
                    for alert in alerts:
                        anomaly_type = alert.anomaly_type.value
                        anomaly_stats[anomaly_type] = anomaly_stats.get(anomaly_type, 0) + 1
                    
                    logger.info(f"异常统计: {anomaly_stats}")
                else:
                    logger.debug("异常检测完成，未发现异常")
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"异常检测任务执行失败: {e}")
    
    async def _run_risk_monitoring(self):
        """运行风险监控任务"""
        try:
            logger.debug("开始执行风险监控任务")
            
            db = next(get_db())
            try:
                risk_engine = get_risk_engine(db)
                
                # 获取所有活跃用户
                from ..models import User
                active_users = db.query(User).filter(User.is_active == True).all()
                
                high_risk_users = []
                
                for user in active_users:
                    try:
                        risk_result = await risk_engine.monitor_real_time_risk(user.id)
                        
                        if risk_result.get('risk_level') == 'HIGH':
                            high_risk_users.append({
                                'user_id': user.id,
                                'username': user.username,
                                'risk_alerts': risk_result.get('risk_alerts', [])
                            })
                            
                    except Exception as e:\n                        logger.error(f"用户 {user.id} 风险监控失败: {e}")\n                \n                if high_risk_users:\n                    logger.warning(f"发现 {len(high_risk_users)} 个高风险用户")\n                    for user_info in high_risk_users:\n                        logger.warning(f"高风险用户: {user_info['username']} (ID: {user_info['user_id']})")\n                \n            finally:\n                db.close()\n                \n        except Exception as e:\n            logger.error(f"风险监控任务执行失败: {e}")\n    \n    async def _update_account_balances(self):\n        """更新账户余额任务"""\n        try:\n            logger.debug("开始执行账户余额更新任务")\n            \n            db = next(get_db())\n            try:\n                account_service = AccountService(db)\n                \n                # 获取所有活跃账户\n                from ..models import TradingAccount\n                active_accounts = db.query(TradingAccount).filter(\n                    TradingAccount.is_active == True\n                ).all()\n                \n                updated_count = 0\n                \n                for account in active_accounts:\n                    try:\n                        # 重新计算账户指标\n                        metrics = account_service.calculate_account_metrics(account.user_id)\n                        \n                        # 更新未实现盈亏\n                        if 'unrealized_pnl' in metrics:\n                            account_service.update_unrealized_pnl(\n                                account.user_id, \n                                metrics['unrealized_pnl']\n                            )\n                            updated_count += 1\n                            \n                    except Exception as e:\n                        logger.error(f"更新账户 {account.account_id} 余额失败: {e}")\n                \n                logger.debug(f"账户余额更新完成，更新了 {updated_count} 个账户")\n                \n            finally:\n                db.close()\n                \n        except Exception as e:\n            logger.error(f"账户余额更新任务执行失败: {e}")\n    \n    async def _update_position_values(self):\n        """更新持仓市值任务"""\n        try:\n            logger.debug("开始执行持仓市值更新任务")\n            \n            db = next(get_db())\n            try:\n                from ..services.position_service import PositionService\n                position_service = PositionService(db)\n                \n                # 这里应该获取最新的市场价格数据\n                # 简化实现：使用模拟价格数据\n                market_data = {\n                    "SHFE.cu2401": 72000.0,\n                    "SHFE.al2401": 18500.0,\n                    "DCE.i2401": 650.0,\n                    # 添加更多品种的价格数据\n                }\n                \n                # 批量更新持仓市值\n                position_service.batch_update_market_values(market_data)\n                \n                logger.debug(f"持仓市值更新完成，更新了 {len(market_data)} 个品种")\n                \n            finally:\n                db.close()\n                \n        except Exception as e:\n            logger.error(f"持仓市值更新任务执行失败: {e}")\n    \n    async def _daily_settlement(self):\n        """日终清算任务"""\n        try:\n            logger.info("开始执行日终清算任务")\n            \n            db = next(get_db())\n            try:\n                # 执行日终清算逻辑\n                settlement_date = datetime.utcnow().date()\n                \n                # 1. 计算当日盈亏\n                await self._calculate_daily_pnl(db, settlement_date)\n                \n                # 2. 更新账户统计\n                await self._update_account_statistics(db, settlement_date)\n                \n                # 3. 生成日报\n                await self._generate_daily_report(db, settlement_date)\n                \n                # 4. 清理过期数据\n                await self._cleanup_expired_data(db)\n                \n                logger.info("日终清算任务执行完成")\n                \n            finally:\n                db.close()\n                \n        except Exception as e:\n            logger.error(f"日终清算任务执行失败: {e}")\n    \n    async def _system_health_check(self):\n        """系统健康检查任务"""\n        try:\n            logger.debug("开始执行系统健康检查任务")\n            \n            db = next(get_db())\n            try:\n                # 检查数据库连接\n                db.execute("SELECT 1")\n                \n                # 检查关键表的数据完整性\n                from ..models import User, TradingAccount, Order\n                \n                user_count = db.query(User).count()\n                account_count = db.query(TradingAccount).count()\n                order_count = db.query(Order).count()\n                \n                # 检查是否有异常数据\n                negative_balance_accounts = db.query(TradingAccount).filter(\n                    TradingAccount.available_balance < 0\n                ).count()\n                \n                if negative_balance_accounts > 0:\n                    logger.warning(f"发现 {negative_balance_accounts} 个负余额账户")\n                \n                # 检查系统资源使用情况\n                import psutil\n                cpu_percent = psutil.cpu_percent()\n                memory_percent = psutil.virtual_memory().percent\n                \n                if cpu_percent > 80:\n                    logger.warning(f"CPU使用率过高: {cpu_percent}%")\n                \n                if memory_percent > 80:\n                    logger.warning(f"内存使用率过高: {memory_percent}%")\n                \n                logger.debug(f"系统健康检查完成 - 用户: {user_count}, 账户: {account_count}, 订单: {order_count}")\n                \n            finally:\n                db.close()\n                \n        except Exception as e:\n            logger.error(f"系统健康检查任务执行失败: {e}")\n    \n    async def _calculate_daily_pnl(self, db: Session, settlement_date):\n        """计算当日盈亏"""\n        try:\n            # 实现当日盈亏计算逻辑\n            logger.debug(f"计算 {settlement_date} 的当日盈亏")\n            \n        except Exception as e:\n            logger.error(f"计算当日盈亏失败: {e}")\n    \n    async def _update_account_statistics(self, db: Session, settlement_date):\n        """更新账户统计"""\n        try:\n            # 实现账户统计更新逻辑\n            logger.debug(f"更新 {settlement_date} 的账户统计")\n            \n        except Exception as e:\n            logger.error(f"更新账户统计失败: {e}")\n    \n    async def _generate_daily_report(self, db: Session, settlement_date):\n        """生成日报"""\n        try:\n            # 实现日报生成逻辑\n            logger.debug(f"生成 {settlement_date} 的日报")\n            \n        except Exception as e:\n            logger.error(f"生成日报失败: {e}")\n    \n    async def _cleanup_expired_data(self, db: Session):\n        """清理过期数据"""\n        try:\n            # 清理30天前的日志数据\n            cutoff_date = datetime.utcnow() - timedelta(days=30)\n            \n            # 这里可以添加清理逻辑\n            logger.debug(f"清理 {cutoff_date} 之前的过期数据")\n            \n        except Exception as e:\n            logger.error(f"清理过期数据失败: {e}")\n    \n    def get_job_status(self) -> Dict[str, Any]:\n        """获取任务状态"""\n        if not self.is_running:\n            return {"status": "stopped", "jobs": []}\n        \n        jobs = []\n        for job in self.scheduler.get_jobs():\n            jobs.append({\n                "id": job.id,\n                "name": job.name,\n                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,\n                "trigger": str(job.trigger)\n            })\n        \n        return {\n            "status": "running",\n            "jobs": jobs,\n            "scheduler_state": str(self.scheduler.state)\n        }\n\n\n# 全局调度器实例\nscheduler_service = SchedulerService()