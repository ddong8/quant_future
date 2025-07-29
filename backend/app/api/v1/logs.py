"""
日志管理API
提供日志查询、分析、导出等功能
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import StringIO

from app.core.dependencies import get_db, get_current_user
from app.core.response import success_response, error_response
from app.models.user import User
from app.schemas.logging import (
    LogEntry,
    LogQuery,
    LogStatistics,
    ErrorPattern,
    LogExportRequest,
    LogHealthStatus,
    LogSearchRequest,
    LogTrendRequest,
    LogTrendResponse,
    LogQueryResponse,
    LogAnalysisRequest,
    LogAnalysisResult,
    LogRotationConfig,
    LogConfigUpdate
)
from app.services.log_management_service import log_management_service

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/", response_model=LogQueryResponse)
async def query_logs(
    level: Optional[str] = Query(None, description="日志级别"),
    logger: Optional[str] = Query(None, description="日志记录器"),
    module: Optional[str] = Query(None, description="模块名称"),
    message: Optional[str] = Query(None, description="消息内容"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    request_id: Optional[str] = Query(None, description="请求ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=1000, description="页大小"),
    current_user: User = Depends(get_current_user)
):
    """查询日志"""
    try:
        query = LogQuery(
            level=level,
            logger=logger,
            module=module,
            message=message,
            user_id=user_id,
            request_id=request_id,
            start_time=start_time,
            end_time=end_time
        )
        
        logs, total = await log_management_service.query_logs(query, page, page_size)
        
        return success_response(data={
            'logs': logs,
            'total': total,
            'page': page,
            'page_size': page_size,
            'has_more': total > page * page_size
        })
    except Exception as e:
        return error_response(message=f"查询日志失败: {str(e)}")


@router.get("/statistics", response_model=LogStatistics)
async def get_log_statistics(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_user)
):
    """获取日志统计信息"""
    try:
        statistics = await log_management_service.get_log_statistics(start_time, end_time)
        return success_response(data=statistics)
    except Exception as e:
        return error_response(message=f"获取日志统计失败: {str(e)}")


@router.get("/error-patterns", response_model=List[ErrorPattern])
async def analyze_error_patterns(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(get_current_user)
):
    """分析错误模式"""
    try:
        patterns = await log_management_service.analyze_error_patterns(
            start_time, end_time, limit
        )
        return success_response(data=patterns)
    except Exception as e:
        return error_response(message=f"分析错误模式失败: {str(e)}")


@router.post("/export")
async def export_logs(
    export_request: LogExportRequest,
    current_user: User = Depends(get_current_user)
):
    """导出日志"""
    try:
        content = await log_management_service.export_logs(
            export_request.query,
            export_request.format,
            export_request.max_records
        )
        
        # 确定文件名和媒体类型
        if export_request.format.lower() == 'json':
            filename = f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            media_type = "application/json"
        else:
            filename = f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            media_type = "text/csv"
        
        return StreamingResponse(
            iter([content]),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        return error_response(message=f"导出日志失败: {str(e)}")


@router.get("/health", response_model=LogHealthStatus)
async def get_log_health_status(
    current_user: User = Depends(get_current_user)
):
    """获取日志系统健康状态"""
    try:
        health_status = await log_management_service.get_log_health_status()
        return success_response(data=health_status)
    except Exception as e:
        return error_response(message=f"获取日志健康状态失败: {str(e)}")


@router.post("/search", response_model=List[LogEntry])
async def search_logs(
    search_request: LogSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """全文搜索日志"""
    try:
        logs = await log_management_service.search_logs_full_text(
            search_request.search_text,
            search_request.start_time,
            search_request.end_time,
            search_request.limit
        )
        return success_response(data=logs)
    except Exception as e:
        return error_response(message=f"搜索日志失败: {str(e)}")


@router.get("/trends", response_model=LogTrendResponse)
async def get_log_trends(
    days: int = Query(7, ge=1, le=30, description="天数"),
    interval: str = Query("hour", description="间隔: hour, day"),
    current_user: User = Depends(get_current_user)
):
    """获取日志趋势数据"""
    try:
        trends = await log_management_service.get_log_trends(days, interval)
        return success_response(data=trends)
    except Exception as e:
        return error_response(message=f"获取日志趋势失败: {str(e)}")


@router.post("/rotate")
async def rotate_logs(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """手动触发日志轮转"""
    try:
        background_tasks.add_task(log_management_service.rotate_logs)
        return success_response(message="日志轮转任务已启动")
    except Exception as e:
        return error_response(message=f"启动日志轮转失败: {str(e)}")


@router.get("/levels")
async def get_log_levels(
    current_user: User = Depends(get_current_user)
):
    """获取可用的日志级别"""
    try:
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        return success_response(data=levels)
    except Exception as e:
        return error_response(message=f"获取日志级别失败: {str(e)}")


@router.get("/modules")
async def get_log_modules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取日志模块列表"""
    try:
        from app.models.system import SystemLog
        from sqlalchemy import distinct
        
        modules = db.query(distinct(SystemLog.module)).filter(
            SystemLog.module.isnot(None)
        ).all()
        
        module_list = [module[0] for module in modules if module[0]]
        
        return success_response(data=module_list)
    except Exception as e:
        return error_response(message=f"获取日志模块失败: {str(e)}")


@router.get("/recent")
async def get_recent_logs(
    minutes: int = Query(60, ge=1, le=1440, description="最近分钟数"),
    level: Optional[str] = Query(None, description="日志级别过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    current_user: User = Depends(get_current_user)
):
    """获取最近的日志"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        query = LogQuery(
            level=level,
            start_time=start_time,
            end_time=end_time
        )
        
        logs, total = await log_management_service.query_logs(query, 1, limit)
        
        return success_response(data={
            'logs': logs,
            'total': total,
            'time_range': f"最近{minutes}分钟"
        })
    except Exception as e:
        return error_response(message=f"获取最近日志失败: {str(e)}")


@router.get("/dashboard")
async def get_log_dashboard(
    current_user: User = Depends(get_current_user)
):
    """获取日志仪表板数据"""
    try:
        # 获取各种统计数据
        statistics = await log_management_service.get_log_statistics()
        error_patterns = await log_management_service.analyze_error_patterns(limit=10)
        health_status = await log_management_service.get_log_health_status()
        trends = await log_management_service.get_log_trends(days=1, interval='hour')
        
        # 获取最近的错误日志
        recent_errors_query = LogQuery(
            level='ERROR',
            start_time=datetime.utcnow() - timedelta(hours=1)
        )
        recent_errors, _ = await log_management_service.query_logs(
            recent_errors_query, 1, 10
        )
        
        dashboard_data = {
            'statistics': statistics,
            'error_patterns': error_patterns,
            'health_status': health_status,
            'trends': trends,
            'recent_errors': recent_errors,
            'summary': {
                'total_logs_today': statistics.total_logs,
                'error_rate': statistics.error_rate,
                'top_error_module': max(statistics.module_counts.items(), key=lambda x: x[1])[0] if statistics.module_counts else None,
                'peak_hour': max(statistics.hourly_counts.items(), key=lambda x: x[1])[0] if statistics.hourly_counts else None
            }
        }
        
        return success_response(data=dashboard_data)
    except Exception as e:
        return error_response(message=f"获取日志仪表板数据失败: {str(e)}")


@router.post("/analyze")
async def analyze_logs(
    analysis_request: LogAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """日志分析"""
    try:
        if analysis_request.analysis_type == 'error_patterns':
            patterns = await log_management_service.analyze_error_patterns(
                analysis_request.start_time,
                analysis_request.end_time,
                analysis_request.parameters.get('limit', 20) if analysis_request.parameters else 20
            )
            
            result = LogAnalysisResult(
                analysis_type='error_patterns',
                results={'patterns': patterns},
                summary=f"发现 {len(patterns)} 个错误模式",
                recommendations=[
                    "关注高频错误模式",
                    "检查影响用户数较多的错误",
                    "优化响应时间较长的操作"
                ],
                generated_at=datetime.utcnow()
            )
            
        elif analysis_request.analysis_type == 'performance':
            # 性能分析逻辑
            statistics = await log_management_service.get_log_statistics(
                analysis_request.start_time,
                analysis_request.end_time
            )
            
            result = LogAnalysisResult(
                analysis_type='performance',
                results={'statistics': statistics},
                summary=f"分析了 {statistics.total_logs} 条日志",
                recommendations=[
                    "监控错误率变化",
                    "优化高频模块性能",
                    "关注用户活动模式"
                ],
                generated_at=datetime.utcnow()
            )
            
        else:
            raise ValueError(f"不支持的分析类型: {analysis_request.analysis_type}")
        
        return success_response(data=result)
    except Exception as e:
        return error_response(message=f"日志分析失败: {str(e)}")


@router.get("/config")
async def get_log_config(
    current_user: User = Depends(get_current_user)
):
    """获取日志配置"""
    try:
        config = {
            'retention_days': log_management_service.log_retention_days,
            'rotation_size_mb': log_management_service.log_rotation_size / (1024 * 1024),
            'log_directory': str(log_management_service.log_directory),
            'auto_rotation': True,
            'compression': True
        }
        
        return success_response(data=config)
    except Exception as e:
        return error_response(message=f"获取日志配置失败: {str(e)}")


@router.put("/config")
async def update_log_config(
    config_update: LogConfigUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新日志配置"""
    try:
        if config_update.retention_days is not None:
            log_management_service.log_retention_days = config_update.retention_days
        
        if config_update.rotation_size_mb is not None:
            log_management_service.log_rotation_size = config_update.rotation_size_mb * 1024 * 1024
        
        return success_response(message="日志配置更新成功")
    except Exception as e:
        return error_response(message=f"更新日志配置失败: {str(e)}")


@router.delete("/cleanup")
async def cleanup_old_logs(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, description="清理多少天前的日志")
):
    """清理旧日志"""
    try:
        async def cleanup_task():
            from app.models.system import SystemLog
            from sqlalchemy import and_
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            with log_management_service.db_manager.get_session() as db:
                deleted_count = db.query(SystemLog).filter(
                    SystemLog.created_at < cutoff_date
                ).delete()
                
                db.commit()
                
                logger.info(f"清理了 {deleted_count} 条旧日志记录")
        
        background_tasks.add_task(cleanup_task)
        
        return success_response(message=f"开始清理 {days} 天前的日志")
    except Exception as e:
        return error_response(message=f"清理旧日志失败: {str(e)}")


@router.get("/user-activity/{user_id}")
async def get_user_log_activity(
    user_id: int,
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_user)
):
    """获取用户日志活动"""
    try:
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=7)
        
        query = LogQuery(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time
        )
        
        logs, total = await log_management_service.query_logs(query, 1, 1000)
        
        # 统计用户活动
        activity_stats = {
            'total_actions': total,
            'error_count': len([log for log in logs if log.level in ['ERROR', 'CRITICAL']]),
            'modules_used': list(set([log.module for log in logs if log.module])),
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            }
        }
        
        return success_response(data={
            'user_id': user_id,
            'activity_stats': activity_stats,
            'recent_logs': logs[:20]  # 最近20条日志
        })
    except Exception as e:
        return error_response(message=f"获取用户日志活动失败: {str(e)}")


@router.get("/request-trace/{request_id}")
async def trace_request_logs(
    request_id: str,
    current_user: User = Depends(get_current_user)
):
    """追踪请求相关的所有日志"""
    try:
        query = LogQuery(request_id=request_id)
        logs, total = await log_management_service.query_logs(query, 1, 1000)
        
        # 按时间排序
        logs.sort(key=lambda x: x.created_at)
        
        # 构建请求追踪信息
        trace_info = {
            'request_id': request_id,
            'total_logs': total,
            'start_time': logs[0].created_at.isoformat() if logs else None,
            'end_time': logs[-1].created_at.isoformat() if logs else None,
            'modules_involved': list(set([log.module for log in logs if log.module])),
            'error_count': len([log for log in logs if log.level in ['ERROR', 'CRITICAL']]),
            'logs': logs
        }
        
        return success_response(data=trace_info)
    except Exception as e:
        return error_response(message=f"追踪请求日志失败: {str(e)}")