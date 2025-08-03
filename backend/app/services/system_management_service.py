"""
系统管理服务
"""
import logging
import os
import csv
import json
import hashlib
import psutil
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, text
import pandas as pd
from io import StringIO, BytesIO

from ..models.system_management import (
    DataExportTask, SystemBackup, SystemLog, SystemMetric,
    SystemAlert, SystemConfiguration, SystemMaintenanceWindow,
    ExportStatus, ExportFormat, BackupStatus, LogLevel
)
from ..models.user import User
from ..schemas.system_management import (
    DataExportRequest, SystemBackupRequest, SystemLogQuery,
    SystemMetricQuery, SystemHealthCheck, SystemPerformanceReport,
    SystemOptimizationReport, DataCleanupRequest
)

logger = logging.getLogger(__name__)

class SystemManagementService:
    """系统管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.export_base_path = "/tmp/exports"  # 可配置
        self.backup_base_path = "/tmp/backups"  # 可配置
    
    # ==================== 数据导出功能 ====================
    
    def create_export_task(self, user_id: int, request: DataExportRequest) -> Dict[str, Any]:
        """创建数据导出任务"""
        try:
            import uuid
            
            task_id = f"export_{uuid.uuid4().hex[:8]}"
            
            # 创建导出任务
            task = DataExportTask(
                task_name=request.task_name,
                task_id=task_id,
                user_id=user_id,
                export_type=request.export_type,
                export_format=request.export_format,
                export_config=request.export_config,
                filters=request.filters,
                date_range=request.date_range,
                status=ExportStatus.PENDING,
                expires_at=datetime.now() + timedelta(days=7)  # 7天后过期
            )
            
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            
            # 异步执行导出任务
            asyncio.create_task(self._execute_export_task(task.id))
            
            logger.info(f"数据导出任务创建成功: {task_id}")
            return self._format_export_task(task)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建数据导出任务失败: {e}")
            raise
    
    async def _execute_export_task(self, task_id: int):
        """执行数据导出任务"""
        try:
            task = self.db.query(DataExportTask).filter(
                DataExportTask.id == task_id
            ).first()
            
            if not task:
                return
            
            # 更新状态为处理中
            task.status = ExportStatus.PROCESSING
            task.started_at = datetime.now()
            self.db.commit()
            
            # 根据导出类型执行不同的导出逻辑
            if task.export_type == "users":
                await self._export_users_data(task)
            elif task.export_type == "orders":
                await self._export_orders_data(task)
            elif task.export_type == "positions":
                await self._export_positions_data(task)
            elif task.export_type == "transactions":
                await self._export_transactions_data(task)
            elif task.export_type == "notifications":
                await self._export_notifications_data(task)
            elif task.export_type == "logs":
                await self._export_logs_data(task)
            else:
                raise ValueError(f"不支持的导出类型: {task.export_type}")
            
            # 更新状态为完成
            task.status = ExportStatus.COMPLETED
            task.completed_at = datetime.now()
            task.progress = 100
            
            self.db.commit()
            
            logger.info(f"数据导出任务完成: {task.task_id}")
            
        except Exception as e:
            # 更新状态为失败
            task.status = ExportStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            
            self.db.commit()
            
            logger.error(f"数据导出任务失败: {e}")
    
    async def _export_users_data(self, task: DataExportTask):
        """导出用户数据"""
        try:
            # 构建查询
            query = self.db.query(User)
            
            # 应用过滤条件
            if task.filters:
                if 'is_active' in task.filters:
                    query = query.filter(User.is_active == task.filters['is_active'])
                if 'created_after' in task.filters:
                    query = query.filter(User.created_at >= task.filters['created_after'])
            
            # 应用日期范围
            if task.date_range:
                if 'start_date' in task.date_range:
                    query = query.filter(User.created_at >= task.date_range['start_date'])
                if 'end_date' in task.date_range:
                    query = query.filter(User.created_at <= task.date_range['end_date'])
            
            # 获取总数
            total_count = query.count()
            task.total_records = total_count
            
            # 分批导出
            batch_size = 1000
            exported_count = 0
            
            # 创建导出文件
            file_name = f"{task.task_id}_users.{task.export_format.value}"
            file_path = os.path.join(self.export_base_path, file_name)
            
            os.makedirs(self.export_base_path, exist_ok=True)
            
            if task.export_format == ExportFormat.CSV:
                await self._export_to_csv(query, file_path, self._format_user_for_export)
            elif task.export_format == ExportFormat.JSON:
                await self._export_to_json(query, file_path, self._format_user_for_export)
            elif task.export_format == ExportFormat.EXCEL:
                await self._export_to_excel(query, file_path, self._format_user_for_export)
            
            # 更新任务信息
            task.file_path = file_path
            task.file_name = file_name
            task.file_size = os.path.getsize(file_path)
            task.exported_records = total_count
            task.download_url = f"/api/v1/system/exports/download/{task.task_id}"
            
        except Exception as e:
            logger.error(f"导出用户数据失败: {e}")
            raise
    
    async def _export_to_csv(self, query, file_path: str, formatter):
        """导出为CSV格式"""
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = None
            
            for item in query.yield_per(1000):
                formatted_item = formatter(item)
                
                if writer is None:
                    # 创建CSV写入器
                    fieldnames = formatted_item.keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                
                writer.writerow(formatted_item)
    
    async def _export_to_json(self, query, file_path: str, formatter):
        """导出为JSON格式"""
        data = []
        for item in query.yield_per(1000):
            data.append(formatter(item))
        
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2, default=str)
    
    async def _export_to_excel(self, query, file_path: str, formatter):
        """导出为Excel格式"""
        data = []
        for item in query.yield_per(1000):
            data.append(formatter(item))
        
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False, engine='openpyxl')
    
    def _format_user_for_export(self, user: User) -> Dict[str, Any]:
        """格式化用户数据用于导出"""
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'phone': user.phone,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
            'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None
        }
    
    def get_export_tasks(self, user_id: int, limit: int = 50, skip: int = 0) -> Dict[str, Any]:
        """获取用户的导出任务列表"""
        try:
            query = self.db.query(DataExportTask).filter(
                DataExportTask.user_id == user_id
            )
            
            total_count = query.count()
            tasks = query.order_by(desc(DataExportTask.created_at)).offset(skip).limit(limit).all()
            
            return {
                'tasks': [self._format_export_task(task) for task in tasks],
                'total_count': total_count,
                'page': skip // limit + 1,
                'page_size': limit,
                'total_pages': (total_count + limit - 1) // limit
            }
            
        except Exception as e:
            logger.error(f"获取导出任务列表失败: {e}")
            raise
    
    def get_export_task(self, task_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """获取导出任务详情"""
        try:
            task = self.db.query(DataExportTask).filter(
                DataExportTask.task_id == task_id,
                DataExportTask.user_id == user_id
            ).first()
            
            if not task:
                return None
            
            return self._format_export_task(task)
            
        except Exception as e:
            logger.error(f"获取导出任务详情失败: {e}")
            raise
    
    def cancel_export_task(self, task_id: str, user_id: int) -> bool:
        """取消导出任务"""
        try:
            task = self.db.query(DataExportTask).filter(
                DataExportTask.task_id == task_id,
                DataExportTask.user_id == user_id,
                DataExportTask.status.in_([ExportStatus.PENDING, ExportStatus.PROCESSING])
            ).first()
            
            if not task:
                return False
            
            task.status = ExportStatus.CANCELLED
            task.completed_at = datetime.now()
            
            self.db.commit()
            
            logger.info(f"导出任务已取消: {task_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"取消导出任务失败: {e}")
            raise
    
    # ==================== 系统备份功能 ====================
    
    def create_backup(self, request: SystemBackupRequest, user_id: int) -> Dict[str, Any]:
        """创建系统备份"""
        try:
            import uuid
            
            backup_id = f"backup_{uuid.uuid4().hex[:8]}"
            
            backup = SystemBackup(
                backup_name=request.backup_name,
                backup_id=backup_id,
                backup_type=request.backup_type,
                backup_scope=request.backup_scope,
                status=BackupStatus.PENDING,
                created_by=user_id
            )
            
            self.db.add(backup)
            self.db.commit()
            self.db.refresh(backup)
            
            # 异步执行备份任务
            asyncio.create_task(self._execute_backup_task(backup.id))
            
            logger.info(f"系统备份任务创建成功: {backup_id}")
            return self._format_backup(backup)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建系统备份失败: {e}")
            raise
    
    async def _execute_backup_task(self, backup_id: int):
        """执行备份任务"""
        try:
            backup = self.db.query(SystemBackup).filter(
                SystemBackup.id == backup_id
            ).first()
            
            if not backup:
                return
            
            # 更新状态为运行中
            backup.status = BackupStatus.RUNNING
            backup.started_at = datetime.now()
            self.db.commit()
            
            # 创建备份文件
            file_name = f"{backup.backup_id}.sql"
            file_path = os.path.join(self.backup_base_path, file_name)
            
            os.makedirs(self.backup_base_path, exist_ok=True)
            
            # 执行数据库备份
            await self._perform_database_backup(backup, file_path)
            
            # 计算校验和
            checksum = self._calculate_file_checksum(file_path)
            
            # 更新备份信息
            backup.status = BackupStatus.COMPLETED
            backup.completed_at = datetime.now()
            backup.file_path = file_path
            backup.file_size = os.path.getsize(file_path)
            backup.checksum = checksum
            backup.progress = 100
            
            self.db.commit()
            
            logger.info(f"系统备份完成: {backup.backup_id}")
            
        except Exception as e:
            # 更新状态为失败
            backup.status = BackupStatus.FAILED
            backup.error_message = str(e)
            backup.completed_at = datetime.now()
            
            self.db.commit()
            
            logger.error(f"系统备份失败: {e}")
    
    async def _perform_database_backup(self, backup: SystemBackup, file_path: str):
        """执行数据库备份"""
        # 这里应该根据实际的数据库类型执行备份
        # 示例使用PostgreSQL的pg_dump
        import subprocess
        
        try:
            # 构建备份命令
            cmd = [
                'pg_dump',
                '--host=localhost',
                '--port=5432',
                '--username=postgres',
                '--dbname=trading_platform',
                '--file=' + file_path,
                '--verbose'
            ]
            
            # 如果是增量备份，添加相应参数
            if backup.backup_type.value == 'incremental':
                # 增量备份逻辑
                pass
            
            # 执行备份命令
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                raise Exception(f"备份命令执行失败: {process.stderr}")
            
            logger.info(f"数据库备份完成: {file_path}")
            
        except Exception as e:
            logger.error(f"执行数据库备份失败: {e}")
            raise
    
    def _calculate_file_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    # ==================== 系统日志管理 ====================
    
    def get_system_logs(self, query: SystemLogQuery) -> Dict[str, Any]:
        """获取系统日志"""
        try:
            db_query = self.db.query(SystemLog)
            
            # 应用过滤条件
            if query.log_level:
                db_query = db_query.filter(SystemLog.log_level == query.log_level)
            
            if query.logger_name:
                db_query = db_query.filter(SystemLog.logger_name.ilike(f"%{query.logger_name}%"))
            
            if query.module:
                db_query = db_query.filter(SystemLog.module.ilike(f"%{query.module}%"))
            
            if query.user_id:
                db_query = db_query.filter(SystemLog.user_id == query.user_id)
            
            if query.keyword:
                db_query = db_query.filter(SystemLog.message.ilike(f"%{query.keyword}%"))
            
            if query.start_time:
                db_query = db_query.filter(SystemLog.created_at >= query.start_time)
            
            if query.end_time:
                db_query = db_query.filter(SystemLog.created_at <= query.end_time)
            
            # 获取总数
            total_count = db_query.count()
            
            # 分页查询
            logs = db_query.order_by(desc(SystemLog.created_at)).offset(
                (query.page - 1) * query.page_size
            ).limit(query.page_size).all()
            
            return {
                'logs': [self._format_system_log(log) for log in logs],
                'total_count': total_count,
                'page': query.page,
                'page_size': query.page_size,
                'total_pages': (total_count + query.page_size - 1) // query.page_size
            }
            
        except Exception as e:
            logger.error(f"获取系统日志失败: {e}")
            raise
    
    def get_system_log_stats(self, days: int = 7) -> Dict[str, Any]:
        """获取系统日志统计"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # 总日志数
            total_logs = self.db.query(SystemLog).filter(
                SystemLog.created_at >= start_date
            ).count()
            
            # 按级别统计
            level_stats = self.db.query(
                SystemLog.log_level,
                func.count(SystemLog.id).label('count')
            ).filter(
                SystemLog.created_at >= start_date
            ).group_by(SystemLog.log_level).all()
            
            logs_by_level = {stat.log_level.value: stat.count for stat in level_stats}
            
            # 按模块统计
            module_stats = self.db.query(
                SystemLog.module,
                func.count(SystemLog.id).label('count')
            ).filter(
                SystemLog.created_at >= start_date,
                SystemLog.module.isnot(None)
            ).group_by(SystemLog.module).limit(10).all()
            
            logs_by_module = {stat.module: stat.count for stat in module_stats}
            
            # 错误率
            error_count = logs_by_level.get('error', 0) + logs_by_level.get('critical', 0)
            error_rate = (error_count / total_logs * 100) if total_logs > 0 else 0
            
            # 最近错误
            recent_errors = self.db.query(SystemLog).filter(
                SystemLog.log_level.in_([LogLevel.ERROR, LogLevel.CRITICAL]),
                SystemLog.created_at >= start_date
            ).order_by(desc(SystemLog.created_at)).limit(10).all()
            
            return {
                'total_logs': total_logs,
                'logs_by_level': logs_by_level,
                'logs_by_module': logs_by_module,
                'error_rate': round(error_rate, 2),
                'recent_errors': [self._format_system_log(log) for log in recent_errors]
            }
            
        except Exception as e:
            logger.error(f"获取系统日志统计失败: {e}")
            raise
    
    # ==================== 系统性能监控 ====================
    
    def get_system_health(self) -> SystemHealthCheck:
        """获取系统健康状态"""
        try:
            components = {}
            overall_status = "healthy"
            
            # 检查数据库连接
            try:
                self.db.execute(text("SELECT 1"))
                components['database'] = {
                    'status': 'healthy',
                    'response_time': 0.1,
                    'message': '数据库连接正常'
                }
            except Exception as e:
                components['database'] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'message': '数据库连接异常'
                }
                overall_status = "unhealthy"
            
            # 检查系统资源
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                overall_status = "degraded"
            
            components['system_resources'] = {
                'status': 'healthy' if cpu_percent < 80 and memory.percent < 80 else 'degraded',
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'disk_usage': disk.percent
            }
            
            # 检查活跃连接数
            active_users = self.db.query(User).filter(
                User.is_active == True,
                User.last_login_at >= datetime.now() - timedelta(hours=1)
            ).count()
            
            components['active_users'] = {
                'status': 'healthy',
                'count': active_users
            }
            
            return SystemHealthCheck(
                overall_status=overall_status,
                components=components,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"获取系统健康状态失败: {e}")
            raise
    
    def get_performance_report(self) -> SystemPerformanceReport:
        """获取系统性能报告"""
        try:
            # 系统资源使用情况
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # 数据库性能
            db_stats = self._get_database_performance()
            
            # 响应时间统计
            response_times = self._get_response_times()
            
            # 错误率统计
            error_rates = self._get_error_rates()
            
            # 活跃用户数
            active_users = self.db.query(User).filter(
                User.is_active == True,
                User.last_login_at >= datetime.now() - timedelta(hours=1)
            ).count()
            
            return SystemPerformanceReport(
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_io={
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv
                },
                database_performance=db_stats,
                response_times=response_times,
                error_rates=error_rates,
                active_users=active_users,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"获取系统性能报告失败: {e}")
            raise
    
    def _get_database_performance(self) -> Dict[str, Any]:
        """获取数据库性能指标"""
        try:
            # 查询数据库统计信息
            result = self.db.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC
                LIMIT 10
            """)).fetchall()
            
            return {
                'active_connections': 10,  # 示例值
                'slow_queries': 2,
                'table_stats': [dict(row) for row in result]
            }
            
        except Exception as e:
            logger.warning(f"获取数据库性能指标失败: {e}")
            return {}
    
    def _get_response_times(self) -> Dict[str, float]:
        """获取响应时间统计"""
        # 这里应该从日志或监控系统获取实际的响应时间数据
        return {
            'api_avg': 150.5,
            'api_p95': 300.2,
            'api_p99': 500.8,
            'database_avg': 25.3
        }
    
    def _get_error_rates(self) -> Dict[str, float]:
        """获取错误率统计"""
        try:
            # 从系统日志获取错误率
            total_logs = self.db.query(SystemLog).filter(
                SystemLog.created_at >= datetime.now() - timedelta(hours=1)
            ).count()
            
            error_logs = self.db.query(SystemLog).filter(
                SystemLog.created_at >= datetime.now() - timedelta(hours=1),
                SystemLog.log_level.in_([LogLevel.ERROR, LogLevel.CRITICAL])
            ).count()
            
            error_rate = (error_logs / total_logs * 100) if total_logs > 0 else 0
            
            return {
                'overall': round(error_rate, 2),
                'api': 1.2,
                'database': 0.5
            }
            
        except Exception as e:
            logger.warning(f"获取错误率统计失败: {e}")
            return {'overall': 0.0, 'api': 0.0, 'database': 0.0}
    
    # ==================== 私有辅助方法 ====================
    
    def _format_export_task(self, task: DataExportTask) -> Dict[str, Any]:
        """格式化导出任务数据"""
        return {
            'id': task.id,
            'task_name': task.task_name,
            'task_id': task.task_id,
            'user_id': task.user_id,
            'export_type': task.export_type,
            'export_format': task.export_format.value,
            'status': task.status.value,
            'progress': task.progress,
            'file_name': task.file_name,
            'file_size': task.file_size,
            'download_url': task.download_url,
            'total_records': task.total_records,
            'exported_records': task.exported_records,
            'started_at': task.started_at,
            'completed_at': task.completed_at,
            'expires_at': task.expires_at,
            'error_message': task.error_message,
            'created_at': task.created_at,
            'updated_at': task.updated_at
        }
    
    def _format_backup(self, backup: SystemBackup) -> Dict[str, Any]:
        """格式化备份数据"""
        return {
            'id': backup.id,
            'backup_name': backup.backup_name,
            'backup_id': backup.backup_id,
            'backup_type': backup.backup_type.value,
            'status': backup.status.value,
            'progress': backup.progress,
            'file_size': backup.file_size,
            'compressed_size': backup.compressed_size,
            'total_tables': backup.total_tables,
            'backed_up_tables': backup.backed_up_tables,
            'total_records': backup.total_records,
            'started_at': backup.started_at,
            'completed_at': backup.completed_at,
            'checksum': backup.checksum,
            'is_verified': backup.is_verified,
            'error_message': backup.error_message,
            'created_at': backup.created_at,
            'updated_at': backup.updated_at,
            'created_by': backup.created_by
        }
    
    def _format_system_log(self, log: SystemLog) -> Dict[str, Any]:
        """格式化系统日志数据"""
        return {
            'id': log.id,
            'log_level': log.log_level.value,
            'logger_name': log.logger_name,
            'module': log.module,
            'message': log.message,
            'exception': log.exception,
            'user_id': log.user_id,
            'session_id': log.session_id,
            'request_id': log.request_id,
            'method': log.method,
            'url': log.url,
            'ip_address': log.ip_address,
            'duration_ms': log.duration_ms,
            'memory_usage': log.memory_usage,
            'extra_data': log.extra_data,
            'created_at': log.created_at
        }