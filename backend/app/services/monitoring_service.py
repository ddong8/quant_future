"""
系统监控服务
负责收集系统性能指标、健康检查和监控数据管理
"""

import asyncio
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database_manager import DatabaseManager
from app.core.influxdb import InfluxDBManager
from app.core.logging import get_logger
from app.models.system import SystemMetrics, HealthCheck, AlertRule
from app.services.notification_service import NotificationService

logger = get_logger(__name__)


class SystemMonitoringService:
    """系统监控服务"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.influx_manager = InfluxDBManager()
        self.notification_service = NotificationService()
        self.is_running = False
        self.collection_interval = 30  # 30秒收集一次
        
    async def start_monitoring(self):
        """启动监控"""
        if self.is_running:
            logger.warning("监控服务已在运行")
            return
            
        self.is_running = True
        logger.info("启动系统监控服务")
        
        # 启动监控任务
        await asyncio.gather(
            self._collect_system_metrics(),
            self._perform_health_checks(),
            self._check_alert_rules()
        )
    
    async def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        logger.info("停止系统监控服务")
    
    async def _collect_system_metrics(self):
        """收集系统性能指标"""
        while self.is_running:
            try:
                metrics = await self._get_system_metrics()
                
                # 保存到时序数据库
                await self._save_metrics_to_influx(metrics)
                
                # 保存关键指标到关系数据库
                await self._save_metrics_to_db(metrics)
                
                logger.debug(f"收集系统指标: CPU={metrics['cpu_percent']}%, Memory={metrics['memory_percent']}%")
                
            except Exception as e:
                logger.error(f"收集系统指标失败: {e}")
            
            await asyncio.sleep(self.collection_interval)
    
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """获取系统性能指标"""
        # CPU指标
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # 内存指标
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # 磁盘指标
        disk_usage = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        # 网络指标
        network_io = psutil.net_io_counters()
        
        # 进程指标
        process_count = len(psutil.pids())
        
        # 数据库连接指标
        db_metrics = await self._get_database_metrics()
        
        # 应用指标
        app_metrics = await self._get_application_metrics()
        
        return {
            'timestamp': datetime.utcnow(),
            
            # CPU指标
            'cpu_percent': cpu_percent,
            'cpu_count': cpu_count,
            'cpu_freq_current': cpu_freq.current if cpu_freq else 0,
            'cpu_freq_max': cpu_freq.max if cpu_freq else 0,
            
            # 内存指标
            'memory_total': memory.total,
            'memory_available': memory.available,
            'memory_percent': memory.percent,
            'memory_used': memory.used,
            'memory_free': memory.free,
            'swap_total': swap.total,
            'swap_used': swap.used,
            'swap_percent': swap.percent,
            
            # 磁盘指标
            'disk_total': disk_usage.total,
            'disk_used': disk_usage.used,
            'disk_free': disk_usage.free,
            'disk_percent': disk_usage.percent,
            'disk_read_bytes': disk_io.read_bytes if disk_io else 0,
            'disk_write_bytes': disk_io.write_bytes if disk_io else 0,
            'disk_read_count': disk_io.read_count if disk_io else 0,
            'disk_write_count': disk_io.write_count if disk_io else 0,
            
            # 网络指标
            'network_bytes_sent': network_io.bytes_sent,
            'network_bytes_recv': network_io.bytes_recv,
            'network_packets_sent': network_io.packets_sent,
            'network_packets_recv': network_io.packets_recv,
            
            # 进程指标
            'process_count': process_count,
            
            # 数据库指标
            **db_metrics,
            
            # 应用指标
            **app_metrics
        }
    
    async def _get_database_metrics(self) -> Dict[str, Any]:
        """获取数据库性能指标"""
        try:
            with self.db_manager.get_session() as db:
                # PostgreSQL特定指标
                result = db.execute(text("""
                    SELECT 
                        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                        (SELECT count(*) FROM pg_stat_activity) as total_connections,
                        (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections,
                        (SELECT sum(numbackends) FROM pg_stat_database) as backends,
                        (SELECT sum(xact_commit) FROM pg_stat_database) as transactions_committed,
                        (SELECT sum(xact_rollback) FROM pg_stat_database) as transactions_rolled_back,
                        (SELECT sum(blks_read) FROM pg_stat_database) as blocks_read,
                        (SELECT sum(blks_hit) FROM pg_stat_database) as blocks_hit,
                        (SELECT sum(tup_returned) FROM pg_stat_database) as tuples_returned,
                        (SELECT sum(tup_fetched) FROM pg_stat_database) as tuples_fetched,
                        (SELECT sum(tup_inserted) FROM pg_stat_database) as tuples_inserted,
                        (SELECT sum(tup_updated) FROM pg_stat_database) as tuples_updated,
                        (SELECT sum(tup_deleted) FROM pg_stat_database) as tuples_deleted
                """)).fetchone()
                
                if result:
                    return {
                        'db_active_connections': result.active_connections or 0,
                        'db_total_connections': result.total_connections or 0,
                        'db_max_connections': result.max_connections or 0,
                        'db_backends': result.backends or 0,
                        'db_transactions_committed': result.transactions_committed or 0,
                        'db_transactions_rolled_back': result.transactions_rolled_back or 0,
                        'db_blocks_read': result.blocks_read or 0,
                        'db_blocks_hit': result.blocks_hit or 0,
                        'db_cache_hit_ratio': (result.blocks_hit / (result.blocks_hit + result.blocks_read)) * 100 if (result.blocks_hit + result.blocks_read) > 0 else 0,
                        'db_tuples_returned': result.tuples_returned or 0,
                        'db_tuples_fetched': result.tuples_fetched or 0,
                        'db_tuples_inserted': result.tuples_inserted or 0,
                        'db_tuples_updated': result.tuples_updated or 0,
                        'db_tuples_deleted': result.tuples_deleted or 0
                    }
        except Exception as e:
            logger.error(f"获取数据库指标失败: {e}")
        
        return {
            'db_active_connections': 0,
            'db_total_connections': 0,
            'db_max_connections': 0,
            'db_backends': 0,
            'db_transactions_committed': 0,
            'db_transactions_rolled_back': 0,
            'db_blocks_read': 0,
            'db_blocks_hit': 0,
            'db_cache_hit_ratio': 0,
            'db_tuples_returned': 0,
            'db_tuples_fetched': 0,
            'db_tuples_inserted': 0,
            'db_tuples_updated': 0,
            'db_tuples_deleted': 0
        }
    
    async def _get_application_metrics(self) -> Dict[str, Any]:
        """获取应用程序指标"""
        try:
            with self.db_manager.get_session() as db:
                # 获取用户数量
                user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
                
                # 获取活跃用户数量（最近24小时）
                active_users = db.execute(text("""
                    SELECT COUNT(DISTINCT user_id) 
                    FROM user_activities 
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                """)).scalar()
                
                # 获取策略数量
                strategy_count = db.execute(text("SELECT COUNT(*) FROM strategies")).scalar()
                
                # 获取运行中的策略数量
                running_strategies = db.execute(text("""
                    SELECT COUNT(*) FROM strategies WHERE status = 'running'
                """)).scalar()
                
                # 获取今日订单数量
                today_orders = db.execute(text("""
                    SELECT COUNT(*) FROM orders 
                    WHERE DATE(created_at) = CURRENT_DATE
                """)).scalar()
                
                # 获取今日成交数量
                today_trades = db.execute(text("""
                    SELECT COUNT(*) FROM orders 
                    WHERE DATE(created_at) = CURRENT_DATE AND status = 'filled'
                """)).scalar()
                
                return {
                    'app_user_count': user_count or 0,
                    'app_active_users': active_users or 0,
                    'app_strategy_count': strategy_count or 0,
                    'app_running_strategies': running_strategies or 0,
                    'app_today_orders': today_orders or 0,
                    'app_today_trades': today_trades or 0,
                    'app_trade_success_rate': (today_trades / today_orders * 100) if today_orders > 0 else 0
                }
        except Exception as e:
            logger.error(f"获取应用指标失败: {e}")
        
        return {
            'app_user_count': 0,
            'app_active_users': 0,
            'app_strategy_count': 0,
            'app_running_strategies': 0,
            'app_today_orders': 0,
            'app_today_trades': 0,
            'app_trade_success_rate': 0
        }
    
    async def _save_metrics_to_influx(self, metrics: Dict[str, Any]):
        """保存指标到InfluxDB"""
        try:
            # 准备数据点
            points = []
            
            # 系统指标
            system_point = {
                'measurement': 'system_metrics',
                'time': metrics['timestamp'],
                'fields': {
                    'cpu_percent': metrics['cpu_percent'],
                    'memory_percent': metrics['memory_percent'],
                    'disk_percent': metrics['disk_percent'],
                    'network_bytes_sent': metrics['network_bytes_sent'],
                    'network_bytes_recv': metrics['network_bytes_recv'],
                    'process_count': metrics['process_count']
                }
            }
            points.append(system_point)
            
            # 数据库指标
            db_point = {
                'measurement': 'database_metrics',
                'time': metrics['timestamp'],
                'fields': {
                    'active_connections': metrics['db_active_connections'],
                    'total_connections': metrics['db_total_connections'],
                    'cache_hit_ratio': metrics['db_cache_hit_ratio'],
                    'transactions_committed': metrics['db_transactions_committed'],
                    'transactions_rolled_back': metrics['db_transactions_rolled_back']
                }
            }
            points.append(db_point)
            
            # 应用指标
            app_point = {
                'measurement': 'application_metrics',
                'time': metrics['timestamp'],
                'fields': {
                    'user_count': metrics['app_user_count'],
                    'active_users': metrics['app_active_users'],
                    'strategy_count': metrics['app_strategy_count'],
                    'running_strategies': metrics['app_running_strategies'],
                    'today_orders': metrics['app_today_orders'],
                    'today_trades': metrics['app_today_trades'],
                    'trade_success_rate': metrics['app_trade_success_rate']
                }
            }
            points.append(app_point)
            
            # 写入InfluxDB
            await self.influx_manager.write_points(points)
            
        except Exception as e:
            logger.error(f"保存指标到InfluxDB失败: {e}")
    
    async def _save_metrics_to_db(self, metrics: Dict[str, Any]):
        """保存关键指标到关系数据库"""
        try:
            with self.db_manager.get_session() as db:
                system_metrics = SystemMetrics(
                    timestamp=metrics['timestamp'],
                    cpu_percent=metrics['cpu_percent'],
                    memory_percent=metrics['memory_percent'],
                    disk_percent=metrics['disk_percent'],
                    network_bytes_sent=metrics['network_bytes_sent'],
                    network_bytes_recv=metrics['network_bytes_recv'],
                    db_active_connections=metrics['db_active_connections'],
                    db_cache_hit_ratio=metrics['db_cache_hit_ratio'],
                    app_user_count=metrics['app_user_count'],
                    app_active_users=metrics['app_active_users'],
                    app_running_strategies=metrics['app_running_strategies']
                )
                
                db.add(system_metrics)
                db.commit()
                
        except Exception as e:
            logger.error(f"保存指标到数据库失败: {e}")
    
    async def _perform_health_checks(self):
        """执行健康检查"""
        while self.is_running:
            try:
                health_results = await self._check_system_health()
                
                # 保存健康检查结果
                await self._save_health_check_results(health_results)
                
                logger.debug(f"健康检查完成: {len(health_results)} 项检查")
                
            except Exception as e:
                logger.error(f"健康检查失败: {e}")
            
            await asyncio.sleep(60)  # 每分钟检查一次
    
    async def _check_system_health(self) -> List[Dict[str, Any]]:
        """检查系统健康状态"""
        health_checks = []
        
        # 数据库连接检查
        db_health = await self._check_database_health()
        health_checks.append(db_health)
        
        # InfluxDB连接检查
        influx_health = await self._check_influxdb_health()
        health_checks.append(influx_health)
        
        # 磁盘空间检查
        disk_health = await self._check_disk_space()
        health_checks.append(disk_health)
        
        # 内存使用检查
        memory_health = await self._check_memory_usage()
        health_checks.append(memory_health)
        
        # CPU使用检查
        cpu_health = await self._check_cpu_usage()
        health_checks.append(cpu_health)
        
        # 服务端口检查
        port_health = await self._check_service_ports()
        health_checks.extend(port_health)
        
        return health_checks
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """检查数据库健康状态"""
        try:
            start_time = time.time()
            
            with self.db_manager.get_session() as db:
                db.execute(text("SELECT 1")).fetchone()
            
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            status = 'healthy' if response_time < 1000 else 'warning'
            if response_time > 5000:
                status = 'critical'
            
            return {
                'check_name': 'database_connection',
                'status': status,
                'response_time': response_time,
                'message': f'数据库响应时间: {response_time:.2f}ms',
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            return {
                'check_name': 'database_connection',
                'status': 'critical',
                'response_time': None,
                'message': f'数据库连接失败: {str(e)}',
                'timestamp': datetime.utcnow()
            }
    
    async def _check_influxdb_health(self) -> Dict[str, Any]:
        """检查InfluxDB健康状态"""
        try:
            start_time = time.time()
            
            # 尝试ping InfluxDB
            await self.influx_manager.ping()
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                'check_name': 'influxdb_connection',
                'status': 'healthy',
                'response_time': response_time,
                'message': f'InfluxDB响应时间: {response_time:.2f}ms',
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            return {
                'check_name': 'influxdb_connection',
                'status': 'critical',
                'response_time': None,
                'message': f'InfluxDB连接失败: {str(e)}',
                'timestamp': datetime.utcnow()
            }
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """检查磁盘空间"""
        try:
            disk_usage = psutil.disk_usage('/')
            usage_percent = disk_usage.percent
            
            status = 'healthy'
            if usage_percent > 80:
                status = 'warning'
            if usage_percent > 90:
                status = 'critical'
            
            return {
                'check_name': 'disk_space',
                'status': status,
                'value': usage_percent,
                'message': f'磁盘使用率: {usage_percent:.1f}%',
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            return {
                'check_name': 'disk_space',
                'status': 'critical',
                'value': None,
                'message': f'磁盘检查失败: {str(e)}',
                'timestamp': datetime.utcnow()
            }
    
    async def _check_memory_usage(self) -> Dict[str, Any]:
        """检查内存使用"""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            
            status = 'healthy'
            if usage_percent > 80:
                status = 'warning'
            if usage_percent > 90:
                status = 'critical'
            
            return {
                'check_name': 'memory_usage',
                'status': status,
                'value': usage_percent,
                'message': f'内存使用率: {usage_percent:.1f}%',
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            return {
                'check_name': 'memory_usage',
                'status': 'critical',
                'value': None,
                'message': f'内存检查失败: {str(e)}',
                'timestamp': datetime.utcnow()
            }
    
    async def _check_cpu_usage(self) -> Dict[str, Any]:
        """检查CPU使用"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            status = 'healthy'
            if cpu_percent > 80:
                status = 'warning'
            if cpu_percent > 90:
                status = 'critical'
            
            return {
                'check_name': 'cpu_usage',
                'status': status,
                'value': cpu_percent,
                'message': f'CPU使用率: {cpu_percent:.1f}%',
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            return {
                'check_name': 'cpu_usage',
                'status': 'critical',
                'value': None,
                'message': f'CPU检查失败: {str(e)}',
                'timestamp': datetime.utcnow()
            }
    
    async def _check_service_ports(self) -> List[Dict[str, Any]]:
        """检查服务端口"""
        import socket
        
        ports_to_check = [
            {'port': 8000, 'name': 'api_server'},
            {'port': 5432, 'name': 'postgresql'},
            {'port': 8086, 'name': 'influxdb'},
            {'port': 6379, 'name': 'redis'}
        ]
        
        results = []
        
        for port_info in ports_to_check:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex(('localhost', port_info['port']))
                sock.close()
                
                if result == 0:
                    status = 'healthy'
                    message = f"端口 {port_info['port']} 可访问"
                else:
                    status = 'critical'
                    message = f"端口 {port_info['port']} 不可访问"
                
                results.append({
                    'check_name': f"port_{port_info['name']}",
                    'status': status,
                    'value': port_info['port'],
                    'message': message,
                    'timestamp': datetime.utcnow()
                })
                
            except Exception as e:
                results.append({
                    'check_name': f"port_{port_info['name']}",
                    'status': 'critical',
                    'value': port_info['port'],
                    'message': f"端口检查失败: {str(e)}",
                    'timestamp': datetime.utcnow()
                })
        
        return results
    
    async def _save_health_check_results(self, health_results: List[Dict[str, Any]]):
        """保存健康检查结果"""
        try:
            with self.db_manager.get_session() as db:
                for result in health_results:
                    health_check = HealthCheck(
                        check_name=result['check_name'],
                        status=result['status'],
                        response_time=result.get('response_time'),
                        value=result.get('value'),
                        message=result['message'],
                        timestamp=result['timestamp']
                    )
                    
                    db.add(health_check)
                
                db.commit()
                
        except Exception as e:
            logger.error(f"保存健康检查结果失败: {e}")
    
    async def _check_alert_rules(self):
        """检查告警规则"""
        while self.is_running:
            try:
                # 获取所有启用的告警规则
                alert_rules = await self._get_active_alert_rules()
                
                for rule in alert_rules:
                    await self._evaluate_alert_rule(rule)
                
                logger.debug(f"检查了 {len(alert_rules)} 个告警规则")
                
            except Exception as e:
                logger.error(f"检查告警规则失败: {e}")
            
            await asyncio.sleep(60)  # 每分钟检查一次
    
    async def _get_active_alert_rules(self) -> List[AlertRule]:
        """获取活跃的告警规则"""
        try:
            with self.db_manager.get_session() as db:
                return db.query(AlertRule).filter(
                    AlertRule.enabled == True
                ).all()
        except Exception as e:
            logger.error(f"获取告警规则失败: {e}")
            return []
    
    async def _evaluate_alert_rule(self, rule: AlertRule):
        """评估告警规则"""
        try:
            # 根据规则类型获取当前值
            current_value = await self._get_metric_value(rule.metric_name)
            
            if current_value is None:
                return
            
            # 检查是否触发告警
            should_alert = False
            
            if rule.operator == 'gt' and current_value > rule.threshold:
                should_alert = True
            elif rule.operator == 'lt' and current_value < rule.threshold:
                should_alert = True
            elif rule.operator == 'eq' and current_value == rule.threshold:
                should_alert = True
            elif rule.operator == 'gte' and current_value >= rule.threshold:
                should_alert = True
            elif rule.operator == 'lte' and current_value <= rule.threshold:
                should_alert = True
            
            if should_alert:
                await self._trigger_alert(rule, current_value)
            
        except Exception as e:
            logger.error(f"评估告警规则失败: {e}")
    
    async def _get_metric_value(self, metric_name: str) -> Optional[float]:
        """获取指标值"""
        try:
            # 从最新的系统指标中获取值
            with self.db_manager.get_session() as db:
                latest_metrics = db.query(SystemMetrics).order_by(
                    SystemMetrics.timestamp.desc()
                ).first()
                
                if latest_metrics:
                    return getattr(latest_metrics, metric_name, None)
                    
        except Exception as e:
            logger.error(f"获取指标值失败: {e}")
        
        return None
    
    async def _trigger_alert(self, rule: AlertRule, current_value: float):
        """触发告警"""
        try:
            # 检查是否在静默期内
            if await self._is_in_silence_period(rule):
                return
            
            # 发送告警通知
            message = f"告警: {rule.name}\n"
            message += f"指标: {rule.metric_name}\n"
            message += f"当前值: {current_value}\n"
            message += f"阈值: {rule.threshold}\n"
            message += f"条件: {rule.operator}\n"
            message += f"时间: {datetime.utcnow()}"
            
            await self.notification_service.send_alert(
                title=f"系统告警: {rule.name}",
                message=message,
                level=rule.severity,
                channels=rule.notification_channels
            )
            
            # 记录告警历史
            await self._record_alert_history(rule, current_value)
            
            logger.warning(f"触发告警: {rule.name}, 当前值: {current_value}")
            
        except Exception as e:
            logger.error(f"触发告警失败: {e}")
    
    async def _is_in_silence_period(self, rule: AlertRule) -> bool:
        """检查是否在静默期内"""
        try:
            with self.db_manager.get_session() as db:
                # 查找最近的告警记录
                from app.models.system import AlertHistory
                
                recent_alert = db.query(AlertHistory).filter(
                    AlertHistory.rule_id == rule.id,
                    AlertHistory.created_at > datetime.utcnow() - timedelta(minutes=rule.silence_duration)
                ).first()
                
                return recent_alert is not None
                
        except Exception as e:
            logger.error(f"检查静默期失败: {e}")
            return False
    
    async def _record_alert_history(self, rule: AlertRule, current_value: float):
        """记录告警历史"""
        try:
            with self.db_manager.get_session() as db:
                from app.models.system import AlertHistory
                
                alert_history = AlertHistory(
                    rule_id=rule.id,
                    metric_name=rule.metric_name,
                    current_value=current_value,
                    threshold=rule.threshold,
                    operator=rule.operator,
                    severity=rule.severity,
                    message=f"{rule.metric_name} {rule.operator} {rule.threshold}, 当前值: {current_value}",
                    created_at=datetime.utcnow()
                )
                
                db.add(alert_history)
                db.commit()
                
        except Exception as e:
            logger.error(f"记录告警历史失败: {e}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态概览"""
        try:
            with self.db_manager.get_session() as db:
                # 获取最新的系统指标
                latest_metrics = db.query(SystemMetrics).order_by(
                    SystemMetrics.timestamp.desc()
                ).first()
                
                # 获取最近的健康检查结果
                health_checks = db.query(HealthCheck).filter(
                    HealthCheck.timestamp > datetime.utcnow() - timedelta(minutes=5)
                ).all()
                
                # 统计健康检查状态
                health_status = {
                    'healthy': 0,
                    'warning': 0,
                    'critical': 0
                }
                
                for check in health_checks:
                    health_status[check.status] = health_status.get(check.status, 0) + 1
                
                # 计算总体健康状态
                overall_status = 'healthy'
                if health_status['critical'] > 0:
                    overall_status = 'critical'
                elif health_status['warning'] > 0:
                    overall_status = 'warning'
                
                return {
                    'overall_status': overall_status,
                    'last_update': latest_metrics.timestamp if latest_metrics else None,
                    'system_metrics': {
                        'cpu_percent': latest_metrics.cpu_percent if latest_metrics else 0,
                        'memory_percent': latest_metrics.memory_percent if latest_metrics else 0,
                        'disk_percent': latest_metrics.disk_percent if latest_metrics else 0,
                        'db_active_connections': latest_metrics.db_active_connections if latest_metrics else 0,
                        'app_running_strategies': latest_metrics.app_running_strategies if latest_metrics else 0
                    },
                    'health_checks': health_status,
                    'monitoring_status': 'running' if self.is_running else 'stopped'
                }
                
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {
                'overall_status': 'unknown',
                'last_update': None,
                'system_metrics': {},
                'health_checks': {},
                'monitoring_status': 'error'
            }


# 全局监控服务实例
monitoring_service = SystemMonitoringService()