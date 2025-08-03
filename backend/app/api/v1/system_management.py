"""
系统管理API接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...services.system_management_service import SystemManagementService
from ...schemas.system_management import (
    DataExportRequest, DataExportTaskResponse, DataExportListResponse,
    SystemBackupRequest, SystemBackupResponse,
    SystemLogQuery, SystemLogListResponse, SystemLogStats,
    SystemMetricQuery, SystemMetricResponse, SystemMetricSeries,
    SystemAlertResponse, SystemAlertAcknowledge, SystemAlertResolve,
    SystemConfigurationResponse, SystemConfigurationUpdate,
    SystemMaintenanceWindowRequest, SystemMaintenanceWindowResponse,
    SystemHealthCheck, SystemPerformanceReport, SystemOptimizationReport,
    DataCleanupRequest, DataCleanupResponse, SystemStatistics
)

router = APIRouter()

# ==================== 数据导出管理 ====================

@router.post("/exports", response_model=DataExportTaskResponse)
async def create_export_task(
    request: DataExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建数据导出任务"""
    try:
        service = SystemManagementService(db)
        task = service.create_export_task(current_user.id, request)
        return task
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/exports", response_model=DataExportListResponse)
async def get_export_tasks(
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取导出任务列表"""
    try:
        service = SystemManagementService(db)
        result = service.get_export_tasks(current_user.id, limit, skip)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/exports/{task_id}", response_model=DataExportTaskResponse)
async def get_export_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取导出任务详情"""
    try:
        service = SystemManagementService(db)
        task = service.get_export_task(task_id, current_user.id)
        if not task:
            raise HTTPException(status_code=404, detail="导出任务不存在")
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/exports/{task_id}")
async def cancel_export_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消导出任务"""
    try:
        service = SystemManagementService(db)
        success = service.cancel_export_task(task_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="导出任务不存在或无法取消")
        return {"message": "导出任务已取消"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/exports/download/{task_id}")
async def download_export_file(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下载导出文件"""
    try:
        service = SystemManagementService(db)
        task = service.get_export_task(task_id, current_user.id)
        
        if not task:
            raise HTTPException(status_code=404, detail="导出任务不存在")
        
        if task['status'] != 'completed':
            raise HTTPException(status_code=400, detail="导出任务未完成")
        
        if not task['file_path'] or not os.path.exists(task['file_path']):
            raise HTTPException(status_code=404, detail="导出文件不存在")
        
        return FileResponse(
            path=task['file_path'],
            filename=task['file_name'],
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== 系统备份管理 ====================

@router.post("/backups", response_model=SystemBackupResponse)
async def create_backup(
    request: SystemBackupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建系统备份"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        backup = service.create_backup(request, current_user.id)
        return backup
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/backups")
async def get_backups(
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取备份列表"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        # TODO: 实现获取备份列表
        result = service.get_backups(limit, skip)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/backups/{backup_id}")
async def get_backup(
    backup_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取备份详情"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        # TODO: 实现获取备份详情
        backup = service.get_backup(backup_id)
        if not backup:
            raise HTTPException(status_code=404, detail="备份不存在")
        return backup
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== 系统日志管理 ====================

@router.post("/logs/search", response_model=SystemLogListResponse)
async def search_system_logs(
    query: SystemLogQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """搜索系统日志"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        result = service.get_system_logs(query)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/logs/stats", response_model=SystemLogStats)
async def get_system_log_stats(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统日志统计"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        stats = service.get_system_log_stats(days)
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== 系统监控 ====================

@router.get("/health", response_model=SystemHealthCheck)
async def get_system_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统健康状态"""
    try:
        service = SystemManagementService(db)
        health = service.get_system_health()
        return health
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/performance", response_model=SystemPerformanceReport)
async def get_performance_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统性能报告"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        report = service.get_performance_report()
        return report
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/metrics")
async def get_system_metrics(
    query: SystemMetricQuery = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统指标"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        # TODO: 实现获取系统指标
        metrics = service.get_system_metrics(query)
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/optimization", response_model=SystemOptimizationReport)
async def get_optimization_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统优化建议"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        # TODO: 实现获取优化建议
        report = service.get_optimization_suggestions()
        return report
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== 系统告警管理 ====================

@router.get("/alerts")
async def get_system_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统告警列表"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        # TODO: 实现获取告警列表
        result = service.get_system_alerts(status, severity, limit, skip)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/alerts/acknowledge")
async def acknowledge_alerts(
    request: SystemAlertAcknowledge,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """确认系统告警"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        # TODO: 实现确认告警
        result = service.acknowledge_alerts(request.alert_ids, current_user.id, request.notes)
        return {"message": f"已确认{len(request.alert_ids)}个告警"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/alerts/resolve")
async def resolve_alerts(
    request: SystemAlertResolve,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """解决系统告警"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        # TODO: 实现解决告警
        result = service.resolve_alerts(request.alert_ids, current_user.id, request.resolution_notes)
        return {"message": f"已解决{len(request.alert_ids)}个告警"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== 系统配置管理 ====================

@router.get("/configurations")
async def get_system_configurations(
    group: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统配置列表"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        # TODO: 实现获取配置列表
        configs = service.get_system_configurations(group)
        return configs
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/configurations/{config_key}")
async def update_system_configuration(
    config_key: str,
    request: SystemConfigurationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新系统配置"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        # TODO: 实现更新配置
        config = service.update_system_configuration(config_key, request.config_value, current_user.id, request.notes)
        return config
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== 系统维护管理 ====================

@router.post("/maintenance", response_model=SystemMaintenanceWindowResponse)
async def create_maintenance_window(
    request: SystemMaintenanceWindowRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建系统维护窗口"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        # TODO: 实现创建维护窗口
        window = service.create_maintenance_window(request, current_user.id)
        return window
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/maintenance")
async def get_maintenance_windows(
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统维护窗口列表"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        # TODO: 实现获取维护窗口列表
        windows = service.get_maintenance_windows(status)
        return windows
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== 数据清理 ====================

@router.post("/cleanup", response_model=DataCleanupResponse)
async def cleanup_data(
    request: DataCleanupRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行数据清理"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        # TODO: 实现数据清理
        cleanup_id = service.start_data_cleanup(request, current_user.id)
        
        # 在后台执行清理任务
        background_tasks.add_task(service.execute_data_cleanup, cleanup_id)
        
        return DataCleanupResponse(
            cleanup_id=cleanup_id,
            status="started",
            total_records=0,
            cleaned_records=0,
            freed_space=0,
            started_at=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/cleanup/{cleanup_id}")
async def get_cleanup_status(
    cleanup_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取数据清理状态"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        # TODO: 实现获取清理状态
        status = service.get_cleanup_status(cleanup_id)
        if not status:
            raise HTTPException(status_code=404, detail="清理任务不存在")
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== 系统统计 ====================

@router.get("/statistics", response_model=SystemStatistics)
async def get_system_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统统计信息"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        # TODO: 实现获取系统统计
        stats = service.get_system_statistics()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== 系统工具 ====================

@router.post("/tools/cache/clear")
async def clear_system_cache(
    cache_type: str = Query("all"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清理系统缓存"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        # TODO: 实现清理缓存
        result = service.clear_system_cache(cache_type)
        return {"message": f"已清理{cache_type}缓存", "details": result}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tools/database/optimize")
async def optimize_database(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """优化数据库"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        # TODO: 实现数据库优化
        result = service.optimize_database()
        return {"message": "数据库优化完成", "details": result}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tools/restart")
async def restart_system_service(
    service_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重启系统服务"""
    try:
        # TODO: 检查管理员权限
        service = SystemManagementService(db)
        # TODO: 实现服务重启
        result = service.restart_service(service_name)
        return {"message": f"服务{service_name}重启完成", "details": result}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))