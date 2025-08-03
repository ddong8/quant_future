"""
数据导出服务
"""
import os
import csv
import json
import zipfile
import hashlib
import psutil
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from io import StringIO, BytesIO

from app.models.data_export import DataExportTask, SystemBackup, SystemLog, SystemMetrics, DataIntegrityCheck
from app.models.order import Order
from app.models.position import Position
from app.models.transaction import Transaction
from app.models.strategy import Strategy
from app.models.backtest import Backtest
from app.schemas.data_export import (
    DataExportTaskCreate, DataExportTaskUpdate, ExportFormat, ExportType, ExportStatus,
    SystemBackupRequest, SystemLogQuery, SystemMetrics as SystemMetricsSchema,
    PerformanceReport, DataIntegrityCheck as DataIntegrityCheckSchema
)
from app.core.config import settings


class DataExportService:
    """数据导出服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.export_dir = os.path.join(settings.UPLOAD_DIR, "exports")
        self.backup_dir = os.path.join(settings.UPLOAD_DIR, "backups")
        
        # 确保目录存在
        os.makedirs(self.export_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_export_task(self, user_id: int, request: DataExportTaskCreate) -> DataExportTask:
        """创建导出任务"""
        task = DataExportTask(
            user_id=user_id,
            export_type=request.export_type.value,
            format=request.format.value,
            filters=request.filters,
            include_fields=request.include_fields,
            exclude_fields=request.exclude_fields,
            compress=request.compress,
            password_protect=request.password_protect,
            expires_at=datetime.utcnow() + timedelta(days=7)  # 7天后过期
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        # 异步执行导出任务
        self._execute_export_task(task, request)
        
        return task
    
    def get_export_tasks(self, user_id: int, skip: int = 0, limit: int = 100) -> List[DataExportTask]:
        """获取用户的导出任务列表"""
        return self.db.query(DataExportTask).filter(
            DataExportTask.user_id == user_id
        ).order_by(DataExportTask.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_export_task(self, task_id: int, user_id: int) -> Optional[DataExportTask]:
        """获取导出任务详情"""
        return self.db.query(DataExportTask).filter(
            DataExportTask.id == task_id,
            DataExportTask.user_id == user_id
        ).first()
    
    def cancel_export_task(self, task_id: int, user_id: int) -> bool:
        """取消导出任务"""
        task = self.get_export_task(task_id, user_id)
        if not task or task.status in [ExportStatus.COMPLETED, ExportStatus.FAILED, ExportStatus.CANCELLED]:
            return False
        
        task.status = ExportStatus.CANCELLED.value
        task.completed_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def _execute_export_task(self, task: DataExportTask, request: DataExportTaskCreate):
        """执行导出任务"""
        try:
            # 更新任务状态
            task.status = ExportStatus.PROCESSING.value
            task.started_at = datetime.utcnow()
            self.db.commit()
            
            # 根据导出类型获取数据
            data = self._get_export_data(task.export_type, task.user_id, request)
            
            # 生成文件
            file_path = self._generate_export_file(task, data, request)
            
            # 更新任务信息
            task.file_path = file_path
            task.file_size = os.path.getsize(file_path)
            task.download_url = f"/api/v1/data-export/download/{task.id}"
            task.status = ExportStatus.COMPLETED.value
            task.progress = 100
            task.completed_at = datetime.utcnow()
            
        except Exception as e:
            task.status = ExportStatus.FAILED.value
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
        
        self.db.commit()
    
    def _get_export_data(self, export_type: str, user_id: int, request: DataExportTaskCreate) -> List[Dict]:
        """根据导出类型获取数据"""
        query_map = {
            ExportType.ORDERS: self._get_orders_data,
            ExportType.POSITIONS: self._get_positions_data,
            ExportType.TRANSACTIONS: self._get_transactions_data,
            ExportType.STRATEGIES: self._get_strategies_data,
            ExportType.BACKTESTS: self._get_backtests_data,
            ExportType.SYSTEM_LOGS: self._get_system_logs_data,
            ExportType.USER_DATA: self._get_user_data,
        }
        
        if export_type not in query_map:
            raise ValueError(f"Unsupported export type: {export_type}")
        
        return query_map[export_type](user_id, request)
    
    def _get_orders_data(self, user_id: int, request: DataExportTaskCreate) -> List[Dict]:
        """获取订单数据"""
        query = self.db.query(Order).filter(Order.user_id == user_id)
        
        if request.start_date:
            query = query.filter(Order.created_at >= request.start_date)
        if request.end_date:
            query = query.filter(Order.created_at <= request.end_date)
        
        orders = query.all()
        return [self._model_to_dict(order, request.include_fields, request.exclude_fields) for order in orders]
    
    def _get_positions_data(self, user_id: int, request: DataExportTaskCreate) -> List[Dict]:
        """获取持仓数据"""
        query = self.db.query(Position).filter(Position.user_id == user_id)
        
        if request.start_date:
            query = query.filter(Position.created_at >= request.start_date)
        if request.end_date:
            query = query.filter(Position.created_at <= request.end_date)
        
        positions = query.all()
        return [self._model_to_dict(position, request.include_fields, request.exclude_fields) for position in positions]
    
    def _get_transactions_data(self, user_id: int, request: DataExportTaskCreate) -> List[Dict]:
        """获取交易记录数据"""
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        
        if request.start_date:
            query = query.filter(Transaction.created_at >= request.start_date)
        if request.end_date:
            query = query.filter(Transaction.created_at <= request.end_date)
        
        transactions = query.all()
        return [self._model_to_dict(transaction, request.include_fields, request.exclude_fields) for transaction in transactions]
    
    def _get_strategies_data(self, user_id: int, request: DataExportTaskCreate) -> List[Dict]:
        """获取策略数据"""
        query = self.db.query(Strategy).filter(Strategy.user_id == user_id)
        
        if request.start_date:
            query = query.filter(Strategy.created_at >= request.start_date)
        if request.end_date:
            query = query.filter(Strategy.created_at <= request.end_date)
        
        strategies = query.all()
        return [self._model_to_dict(strategy, request.include_fields, request.exclude_fields) for strategy in strategies]
    
    def _get_backtests_data(self, user_id: int, request: DataExportTaskCreate) -> List[Dict]:
        """获取回测数据"""
        query = self.db.query(Backtest).filter(Backtest.user_id == user_id)
        
        if request.start_date:
            query = query.filter(Backtest.created_at >= request.start_date)
        if request.end_date:
            query = query.filter(Backtest.created_at <= request.end_date)
        
        backtests = query.all()
        return [self._model_to_dict(backtest, request.include_fields, request.exclude_fields) for backtest in backtests]
    
    def _get_system_logs_data(self, user_id: int, request: DataExportTaskCreate) -> List[Dict]:
        """获取系统日志数据（仅管理员）"""
        # 这里应该检查用户权限
        query = self.db.query(SystemLog)
        
        if request.start_date:
            query = query.filter(SystemLog.timestamp >= request.start_date)
        if request.end_date:
            query = query.filter(SystemLog.timestamp <= request.end_date)
        
        logs = query.limit(10000).all()  # 限制日志数量
        return [self._model_to_dict(log, request.include_fields, request.exclude_fields) for log in logs]
    
    def _get_user_data(self, user_id: int, request: DataExportTaskCreate) -> Dict[str, List[Dict]]:
        """获取用户所有数据"""
        return {
            "orders": self._get_orders_data(user_id, request),
            "positions": self._get_positions_data(user_id, request),
            "transactions": self._get_transactions_data(user_id, request),
            "strategies": self._get_strategies_data(user_id, request),
            "backtests": self._get_backtests_data(user_id, request),
        }
    
    def _model_to_dict(self, model, include_fields: Optional[List[str]] = None, exclude_fields: Optional[List[str]] = None) -> Dict:
        """将模型转换为字典"""
        result = {}
        
        # 获取模型的所有列
        mapper = inspect(model.__class__)
        for column in mapper.columns:
            value = getattr(model, column.name)
            
            # 处理日期时间
            if isinstance(value, datetime):
                value = value.isoformat()
            
            result[column.name] = value
        
        # 应用字段过滤
        if include_fields:
            result = {k: v for k, v in result.items() if k in include_fields}
        
        if exclude_fields:
            result = {k: v for k, v in result.items() if k not in exclude_fields}
        
        return result
    
    def _generate_export_file(self, task: DataExportTask, data: Union[List[Dict], Dict], request: DataExportTaskCreate) -> str:
        """生成导出文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{task.export_type}_{timestamp}.{task.format}"
        file_path = os.path.join(self.export_dir, filename)
        
        if task.format == ExportFormat.CSV.value:
            self._generate_csv_file(file_path, data)
        elif task.format == ExportFormat.EXCEL.value:
            self._generate_excel_file(file_path, data)
        elif task.format == ExportFormat.JSON.value:
            self._generate_json_file(file_path, data)
        else:
            raise ValueError(f"Unsupported format: {task.format}")
        
        # 压缩文件
        if request.compress:
            file_path = self._compress_file(file_path, request.password if request.password_protect else None)
        
        return file_path
    
    def _generate_csv_file(self, file_path: str, data: Union[List[Dict], Dict]):
        """生成CSV文件"""
        if isinstance(data, dict):
            # 多表数据，创建多个CSV文件并打包
            zip_path = file_path.replace('.csv', '.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for table_name, table_data in data.items():
                    if table_data:
                        csv_content = StringIO()
                        writer = csv.DictWriter(csv_content, fieldnames=table_data[0].keys())
                        writer.writeheader()
                        writer.writerows(table_data)
                        zipf.writestr(f"{table_name}.csv", csv_content.getvalue())
            return zip_path
        else:
            # 单表数据
            if data:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
    
    def _generate_excel_file(self, file_path: str, data: Union[List[Dict], Dict]):
        """生成Excel文件"""
        if isinstance(data, dict):
            # 多表数据，创建多个工作表
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for table_name, table_data in data.items():
                    if table_data:
                        df = pd.DataFrame(table_data)
                        df.to_excel(writer, sheet_name=table_name, index=False)
        else:
            # 单表数据
            if data:
                df = pd.DataFrame(data)
                df.to_excel(file_path, index=False)
    
    def _generate_json_file(self, file_path: str, data: Union[List[Dict], Dict]):
        """生成JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2, default=str)
    
    def _compress_file(self, file_path: str, password: Optional[str] = None) -> str:
        """压缩文件"""
        zip_path = file_path + '.zip'
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(file_path, os.path.basename(file_path))
            if password:
                zipf.setpassword(password.encode())
        
        # 删除原文件
        os.remove(file_path)
        return zip_path
    
    def create_system_backup(self, request: SystemBackupRequest) -> SystemBackup:
        """创建系统备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"system_backup_{timestamp}.sql"
        
        if request.compress:
            backup_filename += '.gz'
        
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        # 执行数据库备份
        self._create_database_backup(backup_path, request)
        
        # 计算文件校验和
        checksum = self._calculate_file_checksum(backup_path)
        
        # 创建备份记录
        backup = SystemBackup(
            backup_type="full" if request.include_user_data else "system",
            file_path=backup_path,
            file_size=os.path.getsize(backup_path),
            checksum=checksum,
            include_user_data=request.include_user_data,
            include_system_logs=request.include_system_logs,
            include_market_data=request.include_market_data,
            compress=request.compress,
            encrypt=request.encrypt,
            expires_at=datetime.utcnow() + timedelta(days=30)  # 30天后过期
        )
        
        self.db.add(backup)
        self.db.commit()
        self.db.refresh(backup)
        
        return backup
    
    def _create_database_backup(self, backup_path: str, request: SystemBackupRequest):
        """创建数据库备份"""
        # 这里应该根据实际数据库类型实现备份逻辑
        # 示例：PostgreSQL备份
        import subprocess
        
        cmd = [
            "pg_dump",
            f"--host={settings.DATABASE_HOST}",
            f"--port={settings.DATABASE_PORT}",
            f"--username={settings.DATABASE_USER}",
            f"--dbname={settings.DATABASE_NAME}",
            "--no-password",
            "--verbose",
            "--clean",
            "--no-acl",
            "--no-owner"
        ]
        
        if not request.include_user_data:
            # 排除用户数据表
            user_tables = ["orders", "positions", "transactions", "strategies", "backtests"]
            for table in user_tables:
                cmd.extend(["--exclude-table", table])
        
        if not request.include_system_logs:
            cmd.extend(["--exclude-table", "system_logs"])
        
        if not request.include_market_data:
            cmd.extend(["--exclude-table", "market_data", "--exclude-table", "kline_data"])
        
        # 执行备份
        with open(backup_path, 'w') as f:
            subprocess.run(cmd, stdout=f, check=True, env={
                "PGPASSWORD": settings.DATABASE_PASSWORD
            })
        
        # 压缩文件
        if request.compress:
            import gzip
            with open(backup_path, 'rb') as f_in:
                with gzip.open(backup_path + '.gz', 'wb') as f_out:
                    f_out.writelines(f_in)
            os.remove(backup_path)
    
    def _calculate_file_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def get_system_logs(self, query: SystemLogQuery) -> List[SystemLog]:
        """获取系统日志"""
        db_query = self.db.query(SystemLog)
        
        if query.start_date:
            db_query = db_query.filter(SystemLog.timestamp >= query.start_date)
        if query.end_date:
            db_query = db_query.filter(SystemLog.timestamp <= query.end_date)
        if query.level:
            db_query = db_query.filter(SystemLog.level == query.level.value)
        if query.module:
            db_query = db_query.filter(SystemLog.module == query.module)
        if query.user_id:
            db_query = db_query.filter(SystemLog.user_id == query.user_id)
        if query.message_contains:
            db_query = db_query.filter(SystemLog.message.contains(query.message_contains))
        
        return db_query.order_by(SystemLog.timestamp.desc()).offset(query.offset).limit(query.limit).all()
    
    def get_system_metrics(self) -> SystemMetricsSchema:
        """获取系统指标"""
        # 获取系统资源使用情况
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 获取数据库连接数（这里需要根据实际数据库实现）
        active_connections = self._get_active_connections()
        
        # 获取请求统计（从日志或缓存中获取）
        request_stats = self._get_request_stats()
        
        metrics = SystemMetricsSchema(
            cpu_usage=cpu_percent,
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            active_connections=active_connections,
            request_count=request_stats.get('total_requests', 0),
            error_count=request_stats.get('error_count', 0),
            response_time_avg=request_stats.get('avg_response_time', 0),
            timestamp=datetime.utcnow()
        )
        
        # 保存指标到数据库
        db_metrics = SystemMetrics(
            cpu_usage=int(metrics.cpu_usage),
            memory_usage=int(metrics.memory_usage),
            disk_usage=int(metrics.disk_usage),
            active_connections=metrics.active_connections,
            request_count=metrics.request_count,
            error_count=metrics.error_count,
            response_time_avg=int(metrics.response_time_avg)
        )
        
        self.db.add(db_metrics)
        self.db.commit()
        
        return metrics
    
    def _get_active_connections(self) -> int:
        """获取活跃数据库连接数"""
        try:
            result = self.db.execute(text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"))
            return result.scalar() or 0
        except:
            return 0
    
    def _get_request_stats(self) -> Dict[str, int]:
        """获取请求统计"""
        # 这里应该从Redis或其他缓存中获取实时统计
        # 暂时返回模拟数据
        return {
            'total_requests': 1000,
            'error_count': 10,
            'avg_response_time': 150
        }
    
    def generate_performance_report(self, start_date: datetime, end_date: datetime) -> PerformanceReport:
        """生成性能报告"""
        # 获取时间范围内的系统指标
        metrics_query = self.db.query(SystemMetrics).filter(
            SystemMetrics.timestamp >= start_date,
            SystemMetrics.timestamp <= end_date
        )
        
        metrics_data = metrics_query.all()
        
        if not metrics_data:
            raise ValueError("No metrics data found for the specified time range")
        
        # 计算平均指标
        avg_metrics = SystemMetricsSchema(
            cpu_usage=sum(m.cpu_usage for m in metrics_data) / len(metrics_data),
            memory_usage=sum(m.memory_usage for m in metrics_data) / len(metrics_data),
            disk_usage=sum(m.disk_usage for m in metrics_data) / len(metrics_data),
            active_connections=sum(m.active_connections for m in metrics_data) / len(metrics_data),
            request_count=sum(m.request_count for m in metrics_data),
            error_count=sum(m.error_count for m in metrics_data),
            response_time_avg=sum(m.response_time_avg for m in metrics_data) / len(metrics_data),
            timestamp=datetime.utcnow()
        )
        
        # 获取慢查询
        slow_queries = self._get_slow_queries(start_date, end_date)
        
        # 获取错误统计
        error_summary = self._get_error_summary(start_date, end_date)
        
        # 生成优化建议
        recommendations = self._generate_recommendations(avg_metrics, slow_queries, error_summary)
        
        # 生成图表数据
        charts_data = self._generate_charts_data(metrics_data)
        
        return PerformanceReport(
            report_id=f"perf_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.utcnow(),
            time_range={"start": start_date, "end": end_date},
            metrics=avg_metrics,
            slow_queries=slow_queries,
            error_summary=error_summary,
            recommendations=recommendations,
            charts_data=charts_data
        )
    
    def _get_slow_queries(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """获取慢查询"""
        # 这里应该从数据库的慢查询日志中获取数据
        # 暂时返回模拟数据
        return [
            {
                "query": "SELECT * FROM orders WHERE created_at > ?",
                "duration": 2.5,
                "count": 15,
                "avg_duration": 2.1
            }
        ]
    
    def _get_error_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """获取错误统计"""
        error_logs = self.db.query(SystemLog).filter(
            SystemLog.timestamp >= start_date,
            SystemLog.timestamp <= end_date,
            SystemLog.level == "ERROR"
        ).all()
        
        error_summary = {}
        for log in error_logs:
            module = log.module
            error_summary[module] = error_summary.get(module, 0) + 1
        
        return error_summary
    
    def _generate_recommendations(self, metrics: SystemMetricsSchema, slow_queries: List[Dict], error_summary: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if metrics.cpu_usage > 80:
            recommendations.append("CPU使用率过高，建议优化计算密集型操作或增加服务器资源")
        
        if metrics.memory_usage > 85:
            recommendations.append("内存使用率过高，建议检查内存泄漏或增加内存容量")
        
        if metrics.disk_usage > 90:
            recommendations.append("磁盘空间不足，建议清理日志文件或扩展存储空间")
        
        if slow_queries:
            recommendations.append("发现慢查询，建议优化SQL语句或添加索引")
        
        if metrics.error_count > 100:
            recommendations.append("错误数量较多，建议检查应用程序逻辑和异常处理")
        
        return recommendations
    
    def _generate_charts_data(self, metrics_data: List[SystemMetrics]) -> Dict[str, Any]:
        """生成图表数据"""
        timestamps = [m.timestamp.isoformat() for m in metrics_data]
        
        return {
            "cpu_usage": {
                "timestamps": timestamps,
                "values": [m.cpu_usage for m in metrics_data]
            },
            "memory_usage": {
                "timestamps": timestamps,
                "values": [m.memory_usage for m in metrics_data]
            },
            "response_time": {
                "timestamps": timestamps,
                "values": [m.response_time_avg for m in metrics_data]
            }
        }
    
    def check_data_integrity(self) -> DataIntegrityCheckSchema:
        """检查数据完整性"""
        check_id = f"integrity_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 创建检查记录
        check_record = DataIntegrityCheck(
            check_id=check_id,
            status="running"
        )
        self.db.add(check_record)
        self.db.commit()
        
        try:
            # 获取所有表
            inspector = inspect(self.db.bind)
            tables = inspector.get_table_names()
            
            check_record.total_tables = len(tables)
            issues = []
            
            for table in tables:
                # 检查表的完整性
                table_issues = self._check_table_integrity(table)
                if table_issues:
                    issues.extend(table_issues)
                
                check_record.checked_tables += 1
                self.db.commit()
            
            check_record.issues_found = len(issues)
            check_record.issues = issues
            check_record.recommendations = self._generate_integrity_recommendations(issues)
            check_record.status = "completed"
            check_record.completed_at = datetime.utcnow()
            
        except Exception as e:
            check_record.status = "failed"
            check_record.issues = [{"error": str(e)}]
        
        self.db.commit()
        
        return DataIntegrityCheckSchema(
            check_id=check_record.check_id,
            started_at=check_record.started_at,
            completed_at=check_record.completed_at,
            status=check_record.status,
            total_tables=check_record.total_tables,
            checked_tables=check_record.checked_tables,
            issues_found=check_record.issues_found,
            issues=check_record.issues or [],
            recommendations=check_record.recommendations or []
        )
    
    def _check_table_integrity(self, table_name: str) -> List[Dict[str, Any]]:
        """检查单个表的完整性"""
        issues = []
        
        try:
            # 检查表是否存在重复记录
            if table_name in ["orders", "positions", "transactions"]:
                result = self.db.execute(text(f"""
                    SELECT COUNT(*) as duplicate_count 
                    FROM (
                        SELECT id, COUNT(*) 
                        FROM {table_name} 
                        GROUP BY id 
                        HAVING COUNT(*) > 1
                    ) duplicates
                """))
                
                duplicate_count = result.scalar()
                if duplicate_count > 0:
                    issues.append({
                        "table": table_name,
                        "type": "duplicate_records",
                        "count": duplicate_count,
                        "description": f"发现 {duplicate_count} 条重复记录"
                    })
            
            # 检查外键约束
            if table_name in ["orders", "positions", "transactions", "strategies"]:
                result = self.db.execute(text(f"""
                    SELECT COUNT(*) as orphan_count
                    FROM {table_name} t
                    LEFT JOIN users u ON t.user_id = u.id
                    WHERE u.id IS NULL
                """))
                
                orphan_count = result.scalar()
                if orphan_count > 0:
                    issues.append({
                        "table": table_name,
                        "type": "orphan_records",
                        "count": orphan_count,
                        "description": f"发现 {orphan_count} 条孤立记录（用户不存在）"
                    })
        
        except Exception as e:
            issues.append({
                "table": table_name,
                "type": "check_error",
                "description": f"检查表时出错: {str(e)}"
            })
        
        return issues
    
    def _generate_integrity_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """生成数据完整性修复建议"""
        recommendations = []
        
        for issue in issues:
            if issue.get("type") == "duplicate_records":
                recommendations.append(f"清理 {issue['table']} 表中的重复记录")
            elif issue.get("type") == "orphan_records":
                recommendations.append(f"修复 {issue['table']} 表中的孤立记录")
            elif issue.get("type") == "check_error":
                recommendations.append(f"修复 {issue['table']} 表的检查错误")
        
        return recommendations