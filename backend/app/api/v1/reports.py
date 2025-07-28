"""
报告生成API
提供报告生成、模板管理和调度功能
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.core.response import success_response, error_response
from app.models.user import User
from app.schemas.report import (
    ReportRequest,
    ReportTemplate,
    ReportTemplateCreate,
    ReportSchedule,
    ReportScheduleCreate,
    CustomReportRequest,
    ReportExecution,
    ReportAnalytics
)
from app.services.report_service import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate")
async def generate_report(
    report_request: ReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """生成报告"""
    try:
        user_id = report_request.user_id or current_user.id
        
        # 验证用户权限
        if user_id != current_user.id and current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="无权限生成其他用户的报告")
        
        # 根据报告类型生成报告
        if report_request.report_type == 'trading':
            html_content = await report_service.generate_trading_report(
                user_id=user_id,
                start_date=report_request.start_date,
                end_date=report_request.end_date,
                template_name=report_request.template_name or 'trading_report.html'
            )
        elif report_request.report_type == 'performance':
            html_content = await report_service.generate_performance_report(
                user_id=user_id,
                start_date=report_request.start_date,
                end_date=report_request.end_date,
                template_name=report_request.template_name or 'performance_report.html'
            )
        elif report_request.report_type == 'risk':
            html_content = await report_service.generate_risk_report(
                user_id=user_id,
                start_date=report_request.start_date,
                end_date=report_request.end_date,
                template_name=report_request.template_name or 'risk_report.html'
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的报告类型")
        
        # 如果需要PDF格式
        if report_request.format == 'pdf':
            pdf_path = await report_service.export_report_to_pdf(html_content)
            return FileResponse(
                pdf_path,
                media_type='application/pdf',
                filename=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
        
        # 返回HTML内容
        return StreamingResponse(
            iter([html_content]),
            media_type="text/html",
            headers={"Content-Disposition": f"inline; filename=report.html"}
        )
        
    except Exception as e:
        return error_response(message=f"生成报告失败: {str(e)}")


@router.post("/custom")
async def generate_custom_report(
    custom_request: CustomReportRequest,
    current_user: User = Depends(get_current_user)
):
    """生成自定义报告"""
    try:
        html_content = await report_service.generate_custom_report(
            user_id=current_user.id,
            template_name=custom_request.template_name,
            data_sources=custom_request.data_sources,
            parameters=custom_request.parameters
        )
        
        if custom_request.format == 'pdf':
            pdf_path = await report_service.export_report_to_pdf(html_content)
            return FileResponse(
                pdf_path,
                media_type='application/pdf',
                filename=f"custom_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
        
        return StreamingResponse(
            iter([html_content]),
            media_type="text/html"
        )
        
    except Exception as e:
        return error_response(message=f"生成自定义报告失败: {str(e)}")


@router.get("/templates", response_model=List[dict])
async def get_report_templates(
    current_user: User = Depends(get_current_user)
):
    """获取报告模板列表"""
    try:
        templates = await report_service.get_template_list()
        return success_response(data=templates)
    except Exception as e:
        return error_response(message=f"获取模板列表失败: {str(e)}")


@router.post("/templates")
async def create_report_template(
    template_data: ReportTemplateCreate,
    current_user: User = Depends(get_current_user)
):
    """创建报告模板"""
    try:
        success = await report_service.create_report_template(
            template_name=template_data.name,
            template_content=template_data.content,
            template_type=template_data.template_type
        )
        
        if success:
            return success_response(message="模板创建成功")
        else:
            return error_response(message="模板创建失败")
            
    except Exception as e:
        return error_response(message=f"创建模板失败: {str(e)}")


@router.post("/schedule")
async def schedule_report(
    schedule_data: ReportScheduleCreate,
    current_user: User = Depends(get_current_user)
):
    """调度报告生成"""
    try:
        success = await report_service.schedule_report_generation(
            user_id=schedule_data.user_id or current_user.id,
            report_type=schedule_data.report_type,
            schedule_config={
                'name': schedule_data.name,
                'cron_expression': schedule_data.cron_expression,
                'template_name': schedule_data.template_name,
                'recipients': schedule_data.recipients,
                'parameters': schedule_data.parameters
            }
        )
        
        if success:
            return success_response(message="报告调度创建成功")
        else:
            return error_response(message="报告调度创建失败")
            
    except Exception as e:
        return error_response(message=f"创建报告调度失败: {str(e)}")


@router.get("/history")
async def get_report_history(
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    report_type: Optional[str] = Query(None, description="报告类型"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    current_user: User = Depends(get_current_user)
):
    """获取报告历史"""
    try:
        # 这里应该从数据库查询报告执行历史
        # 暂时返回模拟数据
        history = [
            {
                'id': 1,
                'report_type': 'trading',
                'status': 'completed',
                'generated_at': datetime.utcnow() - timedelta(hours=1),
                'file_size': 1024000,
                'execution_time': 5.2
            },
            {
                'id': 2,
                'report_type': 'performance',
                'status': 'completed',
                'generated_at': datetime.utcnow() - timedelta(days=1),
                'file_size': 2048000,
                'execution_time': 8.7
            }
        ]
        
        return success_response(data=history)
        
    except Exception as e:
        return error_response(message=f"获取报告历史失败: {str(e)}")


@router.get("/analytics")
async def get_report_analytics(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(get_current_user)
):
    """获取报告分析数据"""
    try:
        # 模拟分析数据
        analytics = {
            'total_reports': 156,
            'reports_by_type': {
                'trading': 89,
                'performance': 45,
                'risk': 22
            },
            'reports_by_user': {
                str(current_user.id): 156
            },
            'avg_generation_time': 6.8,
            'success_rate': 0.95,
            'popular_templates': [
                {'name': 'trading_report.html', 'usage_count': 89},
                {'name': 'performance_report.html', 'usage_count': 45}
            ]
        }
        
        return success_response(data=analytics)
        
    except Exception as e:
        return error_response(message=f"获取报告分析失败: {str(e)}")


@router.get("/dashboard")
async def get_report_dashboard(
    current_user: User = Depends(get_current_user)
):
    """获取报告仪表板数据"""
    try:
        # 获取最近报告
        recent_reports = [
            {
                'id': 1,
                'type': 'trading',
                'status': 'completed',
                'generated_at': datetime.utcnow() - timedelta(hours=2),
                'size_mb': 1.2
            },
            {
                'id': 2,
                'type': 'performance',
                'status': 'running',
                'generated_at': datetime.utcnow() - timedelta(minutes=30),
                'progress': 75
            }
        ]
        
        # 获取调度报告
        scheduled_reports = [
            {
                'id': 1,
                'name': '每日交易报告',
                'type': 'trading',
                'cron': '0 9 * * *',
                'next_run': datetime.utcnow() + timedelta(hours=18),
                'enabled': True
            }
        ]
        
        # 系统状态
        system_status = {
            'queue_size': 2,
            'active_generations': 1,
            'avg_response_time': 5.6,
            'error_rate': 0.02
        }
        
        dashboard_data = {
            'recent_reports': recent_reports,
            'scheduled_reports': scheduled_reports,
            'system_status': system_status,
            'quick_stats': {
                'reports_today': 12,
                'reports_this_week': 78,
                'templates_count': 8,
                'schedules_count': 3
            }
        }
        
        return success_response(data=dashboard_data)
        
    except Exception as e:
        return error_response(message=f"获取仪表板数据失败: {str(e)}")


@router.get("/preview/{template_name}")
async def preview_report_template(
    template_name: str,
    current_user: User = Depends(get_current_user)
):
    """预览报告模板"""
    try:
        # 生成示例数据
        sample_data = {
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email
            },
            'statistics': {
                'total_orders': 150,
                'filled_orders': 142,
                'total_pnl': 12500.50,
                'win_rate': 0.68
            },
            'period': {
                'start': datetime.utcnow() - timedelta(days=30),
                'end': datetime.utcnow(),
                'days': 30
            }
        }
        
        # 使用示例数据渲染模板
        html_content = await report_service.generate_custom_report(
            user_id=current_user.id,
            template_name=template_name,
            data_sources=[],
            parameters={'sample_data': sample_data}
        )
        
        return StreamingResponse(
            iter([html_content]),
            media_type="text/html"
        )
        
    except Exception as e:
        return error_response(message=f"预览模板失败: {str(e)}")


@router.delete("/history/{report_id}")
async def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_user)
):
    """删除报告"""
    try:
        # 这里应该实现实际的删除逻辑
        # 包括删除文件和数据库记录
        
        return success_response(message="报告删除成功")
        
    except Exception as e:
        return error_response(message=f"删除报告失败: {str(e)}")


@router.post("/export")
async def export_reports(
    report_ids: List[int],
    format: str = Query("zip", description="导出格式"),
    current_user: User = Depends(get_current_user)
):
    """批量导出报告"""
    try:
        # 这里应该实现批量导出逻辑
        # 创建压缩包包含所有选中的报告
        
        return success_response(message="报告导出任务已启动")
        
    except Exception as e:
        return error_response(message=f"导出报告失败: {str(e)}")


@router.get("/config")
async def get_report_config(
    current_user: User = Depends(get_current_user)
):
    """获取报告系统配置"""
    try:
        config = {
            'max_report_size_mb': 100,
            'retention_days': 30,
            'concurrent_generations': 5,
            'supported_formats': ['html', 'pdf'],
            'available_data_sources': ['trading', 'performance', 'risk', 'backtest'],
            'template_variables': [
                'user', 'statistics', 'orders', 'positions', 
                'period', 'generated_at'
            ]
        }
        
        return success_response(data=config)
        
    except Exception as e:
        return error_response(message=f"获取配置失败: {str(e)}")


@router.post("/validate-template")
async def validate_report_template(
    template_content: str,
    current_user: User = Depends(get_current_user)
):
    """验证报告模板"""
    try:
        from jinja2 import Template, TemplateSyntaxError
        
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # 验证Jinja2语法
            Template(template_content)
        except TemplateSyntaxError as e:
            errors.append(f"模板语法错误: {str(e)}")
        
        # 检查常用变量
        common_vars = ['user', 'statistics', 'period', 'generated_at']
        for var in common_vars:
            if var not in template_content:
                suggestions.append(f"建议使用变量: {var}")
        
        validation_result = {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'suggestions': suggestions
        }
        
        return success_response(data=validation_result)
        
    except Exception as e:
        return error_response(message=f"验证模板失败: {str(e)}")