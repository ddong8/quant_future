"""
日志管理服务
负责结构化日志记录、查询、轮转和分析
"""

import asyncio
import json
import os
import gzip
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func, text

from app.core.database_manager import DatabaseManager
from app.core.logging import get_logger
from app.models.system import SystemLog
from app.schemas.logging import LogEntry, LogQuery, LogStatistics

logger = get_logger(__name__)


class LogManagementService:
    """日志管理服务"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.log_retention_days = 30  # 日志保留天数
        self.log_rotation_size = 100 * 1024 * 1024  # 100MB
        self.log_directory = Path("logs")
        self.log_directory.mkdir(exist_ok=True)
        
    async def create_log_entry(
        self,
        level: str,
        message: str,
        logger_name: str = None,
        module: str = None,
        function: str = None,
        line_number: int = None,
        user_id: int = None,
        request_id: str = None,
        extra_data: Dict[str, Any] = None
    ) -> int:
        """创建日志条目"""
        try:
            with self.db_manager.get_session() as db:
                log_entry = SystemLog(
                    level=level.upper(),
                    logger=logger_name,
                    message=message,
                    module=module,
                    function=function,
                    line_number=line_number,
                    user_id=user_id,
                    request_id=request_id,
                    extra_data=extra_data or {}
                )
                
                db.add(log_entry)
                db.commit()
                db.refresh(log_entry)
                
                return log_entry.id
                
        except Exception as e:
            logger.error(f"创建日志条目失败: {e}")
            raise
    
    async def query_logs(
        self,
        query: LogQuery,
        page: int = 1,
        page_size: int = 100
    ) -> Tuple[List[SystemLog], int]:
        """查询日志"""
        try:
            with self.db_manager.get_session() as db:
                # 构建查询
                db_query = db.query(SystemLog)
                
                # 应用过滤条件
                if query.level:
                    db_query = db_query.filter(SystemLog.level == query.level.upper())
                
                if query.logger:
                    db_query = db_query.filter(SystemLog.logger.ilike(f"%{query.logger}%"))
                
                if query.module:
                    db_query = db_query.filter(SystemLog.module.ilike(f"%{query.module}%"))
                
                if query.message:
                    db_query = db_query.filter(SystemLog.message.ilike(f"%{query.message}%"))
                
                if query.user_id:
                    db_query = db_query.filter(SystemLog.user_id == query.user_id)
                
                if query.request_id:
                    db_query = db_query.filter(SystemLog.request_id == query.request_id)
                
                if query.start_time:
                    db_query = db_query.filter(SystemLog.created_at >= query.start_time)
                
                if query.end_time:
                    db_query = db_query.filter(SystemLog.created_at <= query.end_time)
                
                # 获取总数
                total = db_query.count()
                
                # 分页和排序
                logs = db_query.order_by(desc(SystemLog.created_at)).offset(
                    (page - 1) * page_size
                ).limit(page_size).all()
                
                return logs, total
                
        except Exception as e:
            logger.error(f"查询日志失败: {e}")
            raise
    
    async def get_log_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> LogStatistics:
        """获取日志统计信息"""
        try:
            with self.db_manager.get_session() as db:
                # 默认查询最近24小时
                if not end_time:
                    end_time = datetime.utcnow()
                if not start_time:
                    start_time = end_time - timedelta(hours=24)
                
                # 基础查询条件
                base_query = db.query(SystemLog).filter(
                    and_(
                        SystemLog.created_at >= start_time,
                        SystemLog.created_at <= end_time
                    )
                )
                
                # 总日志数
                total_logs = base_query.count()
                
                # 按级别统计
                level_stats = db.query(
                    SystemLog.level,
                    func.count(SystemLog.id).label('count')
                ).filter(
                    and_(
                        SystemLog.created_at >= start_time,
                        SystemLog.created_at <= end_time
                    )
                ).group_by(SystemLog.level).all()
                
                level_counts = {level: count for level, count in level_stats}
                
                # 按模块统计
                module_stats = db.query(
                    SystemLog.module,
                    func.count(SystemLog.id).label('count')
                ).filter(
                    and_(
                        SystemLog.created_at >= start_time,
                        SystemLog.created_at <= end_time
                    )
                ).group_by(SystemLog.module).order_by(
                    desc(func.count(SystemLog.id))
                ).limit(10).all()
                
                module_counts = {module or 'Unknown': count for module, count in module_stats}
                
                # 按用户统计
                user_stats = db.query(
                    SystemLog.user_id,
                    func.count(SystemLog.id).label('count')
                ).filter(
                    and_(
                        SystemLog.created_at >= start_time,
                        SystemLog.created_at <= end_time,
                        SystemLog.user_id.isnot(None)
                    )
                ).group_by(SystemLog.user_id).order_by(
                    desc(func.count(SystemLog.id))
                ).limit(10).all()
                
                user_counts = {str(user_id): count for user_id, count in user_stats}
                
                # 时间分布统计（按小时）
                hourly_stats = db.query(
                    func.date_trunc('hour', SystemLog.created_at).label('hour'),
                    func.count(SystemLog.id).label('count')
                ).filter(
                    and_(
                        SystemLog.created_at >= start_time,
                        SystemLog.created_at <= end_time
                    )
                ).group_by(
                    func.date_trunc('hour', SystemLog.created_at)
                ).order_by('hour').all()
                
                hourly_counts = {
                    hour.isoformat(): count for hour, count in hourly_stats
                }
                
                # 错误率统计
                error_count = base_query.filter(
                    SystemLog.level.in_(['ERROR', 'CRITICAL'])
                ).count()
                
                error_rate = (error_count / total_logs * 100) if total_logs > 0 else 0
                
                return LogStatistics(
                    total_logs=total_logs,
                    level_counts=level_counts,
                    module_counts=module_counts,
                    user_counts=user_counts,
                    hourly_counts=hourly_counts,
                    error_rate=error_rate,
                    start_time=start_time,
                    end_time=end_time
                )
                
        except Exception as e:
            logger.error(f"获取日志统计失败: {e}")
            raise
    
    async def analyze_error_patterns(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """分析错误模式"""
        try:
            with self.db_manager.get_session() as db:
                # 默认查询最近24小时
                if not end_time:
                    end_time = datetime.utcnow()
                if not start_time:
                    start_time = end_time - timedelta(hours=24)
                
                # 查询错误日志
                error_logs = db.query(SystemLog).filter(
                    and_(
                        SystemLog.level.in_(['ERROR', 'CRITICAL']),
                        SystemLog.created_at >= start_time,
                        SystemLog.created_at <= end_time
                    )
                ).all()
                
                # 分析错误模式
                error_patterns = {}
                
                for log in error_logs:
                    # 提取错误关键信息
                    key = f"{log.module}:{log.function}" if log.function else log.module or 'Unknown'
                    
                    if key not in error_patterns:
                        error_patterns[key] = {
                            'pattern': key,
                            'count': 0,
                            'first_occurrence': log.created_at,
                            'last_occurrence': log.created_at,
                            'sample_message': log.message,
                            'affected_users': set(),
                            'request_ids': set()
                        }
                    
                    pattern = error_patterns[key]
                    pattern['count'] += 1
                    
                    if log.created_at < pattern['first_occurrence']:
                        pattern['first_occurrence'] = log.created_at
                    if log.created_at > pattern['last_occurrence']:
                        pattern['last_occurrence'] = log.created_at
                    
                    if log.user_id:
                        pattern['affected_users'].add(log.user_id)
                    if log.request_id:
                        pattern['request_ids'].add(log.request_id)
                
                # 转换为列表并排序
                patterns_list = []
                for pattern in error_patterns.values():
                    patterns_list.append({
                        'pattern': pattern['pattern'],
                        'count': pattern['count'],
                        'first_occurrence': pattern['first_occurrence'].isoformat(),
                        'last_occurrence': pattern['last_occurrence'].isoformat(),
                        'sample_message': pattern['sample_message'],
                        'affected_users_count': len(pattern['affected_users']),
                        'unique_requests_count': len(pattern['request_ids']),
                        'frequency': pattern['count'] / ((end_time - start_time).total_seconds() / 3600)  # 每小时频率
                    })
                
                # 按出现次数排序
                patterns_list.sort(key=lambda x: x['count'], reverse=True)
                
                return patterns_list[:limit]
                
        except Exception as e:
            logger.error(f"分析错误模式失败: {e}")
            raise
    
    async def export_logs(
        self,
        query: LogQuery,
        format: str = 'json',
        max_records: int = 10000
    ) -> str:
        """导出日志"""
        try:
            logs, _ = await self.query_logs(query, page=1, page_size=max_records)
            
            if format.lower() == 'json':
                return await self._export_logs_json(logs)
            elif format.lower() == 'csv':
                return await self._export_logs_csv(logs)
            else:
                raise ValueError(f"不支持的导出格式: {format}")
                
        except Exception as e:
            logger.error(f"导出日志失败: {e}")
            raise
    
    async def _export_logs_json(self, logs: List[SystemLog]) -> str:
        """导出JSON格式日志"""
        log_data = []
        
        for log in logs:
            log_data.append({
                'id': log.id,
                'level': log.level,
                'logger': log.logger,
                'message': log.message,
                'module': log.module,
                'function': log.function,
                'line_number': log.line_number,
                'user_id': log.user_id,
                'request_id': log.request_id,
                'extra_data': log.extra_data,
                'created_at': log.created_at.isoformat()
            })
        
        return json.dumps(log_data, indent=2, ensure_ascii=False)
    
    async def _export_logs_csv(self, logs: List[SystemLog]) -> str:
        """导出CSV格式日志"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow([
            'ID', 'Level', 'Logger', 'Message', 'Module', 'Function',
            'Line Number', 'User ID', 'Request ID', 'Extra Data', 'Created At'
        ])
        
        # 写入数据
        for log in logs:
            writer.writerow([
                log.id,
                log.level,
                log.logger or '',
                log.message,
                log.module or '',
                log.function or '',
                log.line_number or '',
                log.user_id or '',
                log.request_id or '',
                json.dumps(log.extra_data) if log.extra_data else '',
                log.created_at.isoformat()
            ])
        
        return output.getvalue()
    
    async def rotate_logs(self):
        """日志轮转"""
        try:
            logger.info("开始日志轮转")
            
            # 数据库日志轮转
            await self._rotate_database_logs()
            
            # 文件日志轮转
            await self._rotate_file_logs()
            
            logger.info("日志轮转完成")
            
        except Exception as e:
            logger.error(f"日志轮转失败: {e}")
            raise
    
    async def _rotate_database_logs(self):
        """数据库日志轮转"""
        try:
            with self.db_manager.get_session() as db:
                # 删除过期日志
                cutoff_date = datetime.utcnow() - timedelta(days=self.log_retention_days)
                
                deleted_count = db.query(SystemLog).filter(
                    SystemLog.created_at < cutoff_date
                ).delete()
                
                db.commit()
                
                logger.info(f"删除了 {deleted_count} 条过期日志记录")
                
                # 优化表
                db.execute(text("VACUUM ANALYZE system_logs"))
                
        except Exception as e:
            logger.error(f"数据库日志轮转失败: {e}")
            raise
    
    async def _rotate_file_logs(self):
        """文件日志轮转"""
        try:
            log_files = list(self.log_directory.glob("*.log"))
            
            for log_file in log_files:
                if log_file.stat().st_size > self.log_rotation_size:
                    # 压缩并归档
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    archived_name = f"{log_file.stem}_{timestamp}.log.gz"
                    archived_path = self.log_directory / archived_name
                    
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(archived_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # 清空原文件
                    log_file.write_text("")
                    
                    logger.info(f"日志文件 {log_file.name} 已轮转到 {archived_name}")
            
            # 清理过期的归档文件
            await self._cleanup_archived_logs()
            
        except Exception as e:
            logger.error(f"文件日志轮转失败: {e}")
            raise
    
    async def _cleanup_archived_logs(self):
        """清理过期的归档日志"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.log_retention_days)
            archived_files = list(self.log_directory.glob("*.log.gz"))
            
            for archived_file in archived_files:
                file_time = datetime.fromtimestamp(archived_file.stat().st_mtime)
                if file_time < cutoff_time:
                    archived_file.unlink()
                    logger.info(f"删除过期归档文件: {archived_file.name}")
                    
        except Exception as e:
            logger.error(f"清理归档日志失败: {e}")
    
    async def get_log_health_status(self) -> Dict[str, Any]:
        """获取日志系统健康状态"""
        try:
            with self.db_manager.get_session() as db:
                # 最近1小时的日志统计
                recent_time = datetime.utcnow() - timedelta(hours=1)
                
                recent_logs = db.query(SystemLog).filter(
                    SystemLog.created_at >= recent_time
                ).count()
                
                # 错误日志统计
                error_logs = db.query(SystemLog).filter(
                    and_(
                        SystemLog.created_at >= recent_time,
                        SystemLog.level.in_(['ERROR', 'CRITICAL'])
                    )
                ).count()
                
                # 数据库大小估算
                db_size_result = db.execute(text("""
                    SELECT pg_size_pretty(pg_total_relation_size('system_logs')) as size
                """)).fetchone()
                
                db_size = db_size_result.size if db_size_result else 'Unknown'
                
                # 最老的日志
                oldest_log = db.query(SystemLog).order_by(SystemLog.created_at).first()
                oldest_date = oldest_log.created_at if oldest_log else None
                
                # 磁盘使用情况
                disk_usage = shutil.disk_usage(self.log_directory)
                disk_free_gb = disk_usage.free / (1024**3)
                
                return {
                    'status': 'healthy' if error_logs < recent_logs * 0.1 else 'warning',
                    'recent_logs_count': recent_logs,
                    'recent_error_count': error_logs,
                    'error_rate': (error_logs / recent_logs * 100) if recent_logs > 0 else 0,
                    'database_size': db_size,
                    'oldest_log_date': oldest_date.isoformat() if oldest_date else None,
                    'disk_free_gb': round(disk_free_gb, 2),
                    'log_retention_days': self.log_retention_days,
                    'last_rotation': None  # TODO: 记录最后轮转时间
                }
                
        except Exception as e:
            logger.error(f"获取日志健康状态失败: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def search_logs_full_text(
        self,
        search_text: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SystemLog]:
        """全文搜索日志"""
        try:
            with self.db_manager.get_session() as db:
                query = db.query(SystemLog)
                
                # 全文搜索条件
                search_condition = or_(
                    SystemLog.message.ilike(f"%{search_text}%"),
                    SystemLog.logger.ilike(f"%{search_text}%"),
                    SystemLog.module.ilike(f"%{search_text}%"),
                    SystemLog.function.ilike(f"%{search_text}%")
                )
                
                query = query.filter(search_condition)
                
                # 时间范围
                if start_time:
                    query = query.filter(SystemLog.created_at >= start_time)
                if end_time:
                    query = query.filter(SystemLog.created_at <= end_time)
                
                # 排序和限制
                logs = query.order_by(desc(SystemLog.created_at)).limit(limit).all()
                
                return logs
                
        except Exception as e:
            logger.error(f"全文搜索日志失败: {e}")
            raise
    
    async def get_log_trends(
        self,
        days: int = 7,
        interval: str = 'hour'
    ) -> Dict[str, Any]:
        """获取日志趋势数据"""
        try:
            with self.db_manager.get_session() as db:
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(days=days)
                
                # 根据间隔选择时间截断函数
                if interval == 'hour':
                    time_trunc = func.date_trunc('hour', SystemLog.created_at)
                elif interval == 'day':
                    time_trunc = func.date_trunc('day', SystemLog.created_at)
                else:
                    time_trunc = func.date_trunc('hour', SystemLog.created_at)
                
                # 总体趋势
                overall_trend = db.query(
                    time_trunc.label('time_period'),
                    func.count(SystemLog.id).label('count')
                ).filter(
                    and_(
                        SystemLog.created_at >= start_time,
                        SystemLog.created_at <= end_time
                    )
                ).group_by(time_trunc).order_by(time_trunc).all()
                
                # 按级别的趋势
                level_trend = db.query(
                    time_trunc.label('time_period'),
                    SystemLog.level,
                    func.count(SystemLog.id).label('count')
                ).filter(
                    and_(
                        SystemLog.created_at >= start_time,
                        SystemLog.created_at <= end_time
                    )
                ).group_by(time_trunc, SystemLog.level).order_by(time_trunc).all()
                
                # 格式化数据
                overall_data = [
                    {
                        'time': period.isoformat(),
                        'count': count
                    }
                    for period, count in overall_trend
                ]
                
                level_data = {}
                for period, level, count in level_trend:
                    if level not in level_data:
                        level_data[level] = []
                    level_data[level].append({
                        'time': period.isoformat(),
                        'count': count
                    })
                
                return {
                    'overall_trend': overall_data,
                    'level_trends': level_data,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'interval': interval
                }
                
        except Exception as e:
            logger.error(f"获取日志趋势失败: {e}")
            raise
    
    async def start_log_rotation_scheduler(self):
        """启动日志轮转调度器"""
        while True:
            try:
                # 每天凌晨2点执行日志轮转
                now = datetime.now()
                next_rotation = now.replace(hour=2, minute=0, second=0, microsecond=0)
                
                if next_rotation <= now:
                    next_rotation += timedelta(days=1)
                
                sleep_seconds = (next_rotation - now).total_seconds()
                await asyncio.sleep(sleep_seconds)
                
                await self.rotate_logs()
                
            except Exception as e:
                logger.error(f"日志轮转调度器错误: {e}")
                await asyncio.sleep(3600)  # 出错后等待1小时再试


# 全局日志管理服务实例
log_management_service = LogManagementService()