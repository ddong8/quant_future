"""
数据导出API接口
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from ...core.dependencies import get_current_user
from app.models.user import User
from app.schemas.data_export import (
    DataExportTaskCreate, DataExportTask, SystemBackupRequest, SystemBackupInfo,
    SystemLogQuery, SystemLogEntry, SystemMetrics, PerformanceReport,
    DataIntegrityCheck as DataIntegrityCheckSchema
)
from app.services.data_export_service import DataExportService
from app.core.permissions import require_permission

router = APIRouter()


@router.post("/export", response_model=DataExportTask)
async def create_export_task(
    request: DataExportTaskCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建数据导出任务"""
    service = DataExportService(db)
    return service.create_export_task(current_user.id, request)


@router.get("/export/tasks", response_model=List[DataExportTask])
async def get_export_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取导出任务列表"""
    service = DataExportService(db)
    return service.get_export_tasks(current_user.id, skip, limit)


@router.get("/export/tasks/{task_id}", response_model=DataExportTask)
async def get_export_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取导出任务详情"""
    service = DataExportService(db)
    task = service.get_export_task(task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Export task not found")
    return task


@router.post("/export/tasks/{task_id}/cancel")
async def cancel_export_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消导出任务"""
    service = DataExportService(db)
    success = service.cancel_export_task(task_id, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel this task")
    return {"message": "Task cancelled successfully"}


@router.get("/export/download/{task_id}")
async def download_export_file(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下载导出文件"""
    service = DataExportService(db)
    task = service.get_export_task(task_id, current_user.id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Export task not found")
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Export task not completed")
    
    if not task.file_path or not os.path.exists(task.file_path):
        raise HTTPException(status_code=404, detail="Export file not found")
    
    # 检查文件是否过期
    if task.expires_at and datetime.utcnow() > task.expires_at:
        raise HTTPException(status_code=410, detail="Export file has expired")
    
    filename = os.path.basename(task.file_path)
    return FileResponse(
        path=task.file_path,
        filename=filename,
        media_type='application/octet-stream'
    )


@router.post("/backup", response_model=SystemBackupInfo)
async def create_system_backup(
    request: SystemBackupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建系统备份（仅管理员）"""
    require_permission(current_user, "system:backup")
    
    service = DataExportService(db)
    return service.create_system_backup(request)


@router.get("/logs", response_model=List[SystemLogEntry])
async def get_system_logs(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    level: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    message_contains: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统日志（仅管理员）"""
    require_permission(current_user, "system:logs:read")
    
    query = SystemLogQuery(
        start_date=start_date,
        end_date=end_date,
        level=level,
        module=module,
        user_id=user_id,
        message_contains=message_contains,
        limit=limit,
        offset=offset
    )
    
    service = DataExportService(db)
    return service.get_system_logs(query)


@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统指标（仅管理员）"""
    require_permission(current_user, "system:metrics:read")
    
    service = DataExportService(db)
    return service.get_system_metrics()


@router.get("/performance-report", response_model=PerformanceReport)
async def generate_performance_report(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成性能报告（仅管理员）"""
    require_permission(current_user, "system:reports:read")
    
    if end_date <= start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    
    if (end_date - start_date).days > 30:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 30 days")
    
    service = DataExportService(db)
    return service.generate_performance_report(start_date, end_date)


@router.post("/integrity-check", response_model=DataIntegrityCheckSchema)
async def check_data_integrity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """检查数据完整性（仅管理员）"""
    require_permission(current_user, "system:integrity:check")
    
    service = DataExportService(db)
    return service.check_data_integrity()


@router.get("/storage-usage")
async def get_storage_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取存储使用情况（仅管理员）"""
    require_permission(current_user, "system:storage:read")
    
    import os
    import psutil
    
    # 获取磁盘使用情况
    disk_usage = psutil.disk_usage('/')
    
    # 获取数据库大小
    try:
        result = db.execute(text("SELECT pg_database_size(current_database())"))
        db_size = result.scalar()
    except:
        db_size = 0
    
    # 获取上传文件大小
    upload_dir = os.path.join(settings.UPLOAD_DIR)
    upload_size = 0
    if os.path.exists(upload_dir):
        for dirpath, dirnames, filenames in os.walk(upload_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                upload_size += os.path.getsize(filepath)
    
    return {
        "disk_total": disk_usage.total,
        "disk_used": disk_usage.used,
        "disk_free": disk_usage.free,
        "disk_percent": disk_usage.percent,
        "database_size": db_size,
        "upload_files_size": upload_size,
        "timestamp": datetime.utcnow()
    }


@router.delete("/cleanup/expired-exports")
async def cleanup_expired_exports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清理过期的导出文件（仅管理员）"""
    require_permission(current_user, "system:cleanup")
    
    from app.models.data_export import DataExportTask
    import os
    
    # 查找过期的导出任务
    expired_tasks = db.query(DataExportTask).filter(
        DataExportTask.expires_at < datetime.utcnow(),
        DataExportTask.file_path.isnot(None)
    ).all()
    
    cleaned_count = 0
    freed_space = 0
    
    for task in expired_tasks:
        if task.file_path and os.path.exists(task.file_path):
            file_size = os.path.getsize(task.file_path)
            os.remove(task.file_path)
            freed_space += file_size
            cleaned_count += 1
        
        # 清空文件路径
        task.file_path = None
        task.download_url = None
    
    db.commit()
    
    return {
        "cleaned_files": cleaned_count,
        "freed_space_bytes": freed_space,
        "freed_space_mb": round(freed_space / 1024 / 1024, 2)
    }


@router.get("/system-info")
async def get_system_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统信息（仅管理员）"""
    require_permission(current_user, "system:info:read")
    
    import platform
    import psutil
    from app.core.config import settings
    
    # 获取系统信息
    system_info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
        "boot_time": datetime.fromtimestamp(psutil.boot_time()),
        "application_version": getattr(settings, 'VERSION', '1.0.0'),
        "database_url": settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'hidden',
        "redis_url": getattr(settings, 'REDIS_URL', 'not configured'),
        "environment": getattr(settings, 'ENVIRONMENT', 'development')
    }
    
    # 获取数据库统计
    try:
        db_stats = {}
        
        # 获取表数量和记录数
        tables = ['users', 'orders', 'positions', 'transactions', 'strategies', 'backtests']
        for table in tables:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                db_stats[f"{table}_count"] = result.scalar()
            except:
                db_stats[f"{table}_count"] = 0
        
        system_info["database_stats"] = db_stats
    except:
        system_info["database_stats"] = {}
    
    return system_info


# 导入必要的模块
import os
from sqlalchemy import text
from app.core.config import settings