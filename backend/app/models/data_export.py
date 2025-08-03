"""
数据导出相关的数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, BigInteger, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class DataExportTask(Base):
    """数据导出任务表"""
    __tablename__ = "data_export_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    export_type = Column(String(50), nullable=False)
    format = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    progress = Column(Integer, default=0)
    file_path = Column(String(500))
    file_size = Column(BigInteger)
    download_url = Column(String(500))
    error_message = Column(Text)
    filters = Column(JSON)
    include_fields = Column(JSON)
    exclude_fields = Column(JSON)
    compress = Column(Boolean, default=False)
    password_protect = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))


class SystemBackup(Base):
    """系统备份表"""
    __tablename__ = "system_backups"
    
    id = Column(Integer, primary_key=True, index=True)
    backup_type = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    checksum = Column(String(64), nullable=False)
    include_user_data = Column(Boolean, default=True)
    include_system_logs = Column(Boolean, default=False)
    include_market_data = Column(Boolean, default=False)
    compress = Column(Boolean, default=True)
    encrypt = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))


class SystemLog(Base):
    """系统日志表"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    level = Column(String(20), nullable=False, index=True)
    module = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)
    user_id = Column(Integer, index=True)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    request_id = Column(String(100), index=True)
    extra_data = Column(JSON)


class SystemMetrics(Base):
    """系统指标表"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    cpu_usage = Column(Integer, nullable=False)  # 存储为百分比整数
    memory_usage = Column(Integer, nullable=False)  # 存储为百分比整数
    disk_usage = Column(Integer, nullable=False)  # 存储为百分比整数
    active_connections = Column(Integer, nullable=False)
    request_count = Column(Integer, nullable=False)
    error_count = Column(Integer, nullable=False)
    response_time_avg = Column(Integer, nullable=False)  # 存储为毫秒


class DataIntegrityCheck(Base):
    """数据完整性检查表"""
    __tablename__ = "data_integrity_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    check_id = Column(String(100), unique=True, nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    status = Column(String(20), nullable=False, default="running")
    total_tables = Column(Integer, default=0)
    checked_tables = Column(Integer, default=0)
    issues_found = Column(Integer, default=0)
    issues = Column(JSON)
    recommendations = Column(JSON)