"""
风险报告和分析API接口
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import json

from app.core.database import get_db
from ...core.dependencies import get_current_user
from app.models.user import User
from app.schemas.risk import (
    RiskReportRequest, RiskReportResponse, RiskAnalysisRequest,
    RiskAnalysisResponse, ReportScheduleConfig
)
from app.services.risk_report_service import RiskReportService, ReportType
from app.core.permissions import require_permission

router = APIRouter()


@router.post("/generate", response_model=Dict[str, Any])
async def generate_risk_report(
    request: RiskReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成风险报告"""
    # 检查权限
    if request.user_id != current_user.id:
        require_permission(current_user, "risk:reports:generate_others")
    
    service = RiskReportService(db)
    
    try:
        report_type = ReportType(request.report_type)
        
        # 验证日期范围
        if request.end_date <= request.start_date:
            raise HTTPException(status_code=400, detail="结束日期必须晚于开始日期")
        
        if (request.end_date - request.start_date).days > 365:
            raise HTTPException(status_code=400, detail="报告时间范围不能超过365天")
        
        # 生成报告
        report = await service.generate_risk_report(
            request.user_id,
            report_type,
            request.start_date,
            request.end_date,
            request.custom_config
        )
        
        return report
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无效的报告类型: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成风险报告失败: {str(e)}")


@router.get("/templates")
async def get_report_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取报告模板"""
    templates = [
        {
            "id": "daily_summary",
            "name": "日度风险摘要",
            "description": "包含关键风险指标和事件的日度报告",
            "report_type": "daily",
            "sections": [
                "executive_summary",
                "risk_metrics",
                "risk_events",
                "recommendations"
            ]
        },
        {
            "id": "weekly_analysis",
            "name": "周度风险分析",
            "description": "详细的周度风险分析报告，包含趋势分析",
            "report_type": "weekly",
            "sections": [
                "executive_summary",
                "risk_metrics",
                "position_analysis",
                "trend_analysis",
                "recommendations"
            ]
        },
        {
            "id": "monthly_comprehensive",
            "name": "月度综合报告",
            "description": "全面的月度风险报告，包含所有分析维度",
            "report_type": "monthly",
            "sections": [
                "executive_summary",
                "risk_metrics",
                "risk_events",
                "position_analysis",
                "risk_attribution",
                "trend_analysis",
                "recommendations"
            ]
        },
        {
            "id": "custom_analysis",
            "name": "自定义分析",
            "description": "根据用户需求定制的风险分析报告",
            "report_type": "custom",
            "sections": "configurable"
        }
    ]
    
    return {"templates": templates}


@router.get("/history")
async def get_report_history(
    user_id: Optional[int] = None,
    report_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取报告历史"""
    # 检查权限
    if user_id and user_id != current_user.id:
        require_permission(current_user, "risk:reports:view_others")
    
    # 这里应该从数据库查询报告历史
    # 暂时返回模拟数据
    reports = [
        {
            "report_id": f"risk_report_{current_user.id}_20240120_090000",
            "user_id": current_user.id,
            "report_type": "daily",
            "generated_at": "2024-01-20T09:00:00Z",
            "period": {
                "start_date": "2024-01-19T00:00:00Z",
                "end_date": "2024-01-20T00:00:00Z"
            },
            "risk_score": 35.2,
            "status": "completed"
        }
    ]
    
    return {
        "total": len(reports),
        "reports": reports[skip:skip+limit]
    }


@router.get("/{report_id}")
async def get_report_detail(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取报告详情"""
    # 这里应该从数据库查询具体报告
    # 暂时返回模拟数据
    if not report_id.startswith("risk_report_"):
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # 检查权限（从report_id中提取user_id）
    try:
        user_id = int(report_id.split("_")[2])
        if user_id != current_user.id:
            require_permission(current_user, "risk:reports:view_others")
    except (IndexError, ValueError):
        raise HTTPException(status_code=400, detail="无效的报告ID")
    
    # 返回模拟报告数据
    report = {
        "report_id": report_id,
        "user_id": user_id,
        "report_type": "daily",
        "generated_at": datetime.utcnow().isoformat(),
        "executive_summary": {
            "risk_score": 35.2,
            "risk_level": "中",
            "total_events": 3,
            "critical_events": 0,
            "high_events": 1
        }
    }
    
    return report


@router.post("/{report_id}/export")
async def export_report(
    report_id: str,
    format: str = Query("pdf", pattern="^(pdf|excel|json)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出报告"""
    # 检查权限
    try:
        user_id = int(report_id.split("_")[2])
        if user_id != current_user.id:
            require_permission(current_user, "risk:reports:export_others")
    except (IndexError, ValueError):
        raise HTTPException(status_code=400, detail="无效的报告ID")
    
    # 获取报告数据
    # 这里应该从数据库获取实际报告数据
    report_data = {
        "report_id": report_id,
        "generated_at": datetime.utcnow().isoformat(),
        "content": "报告内容..."
    }
    
    if format == "json":
        # 返回JSON格式
        json_data = json.dumps(report_data, ensure_ascii=False, indent=2)
        return StreamingResponse(
            io.StringIO(json_data),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={report_id}.json"}
        )
    elif format == "excel":
        # 生成Excel文件
        # 这里应该使用pandas或openpyxl生成Excel
        excel_data = b"Excel content placeholder"
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={report_id}.xlsx"}
        )
    elif format == "pdf":
        # 生成PDF文件
        # 这里应该使用reportlab或其他PDF库生成PDF
        pdf_data = b"PDF content placeholder"
        return StreamingResponse(
            io.BytesIO(pdf_data),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={report_id}.pdf"}
        )


@router.post("/schedule")
async def schedule_reports(
    config: ReportScheduleConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """配置定期报告"""
    # 检查权限
    if config.user_id != current_user.id:
        require_permission(current_user, "risk:reports:schedule_others")
    
    # 这里应该将调度配置保存到数据库
    # 并设置定时任务
    
    return {
        "message": "报告调度配置已保存",
        "config": config.dict()
    }


@router.get("/schedule/{user_id}")
async def get_report_schedule(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取报告调度配置"""
    # 检查权限
    if user_id != current_user.id:
        require_permission(current_user, "risk:reports:view_schedule_others")
    
    # 这里应该从数据库查询调度配置
    schedule_config = {
        "user_id": user_id,
        "daily_enabled": True,
        "weekly_enabled": True,
        "monthly_enabled": True,
        "email_delivery": True,
        "notification_delivery": True
    }
    
    return schedule_config


@router.post("/analyze")
async def analyze_risk_data(
    request: RiskAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行风险数据分析"""
    # 检查权限
    if request.user_id != current_user.id:
        require_permission(current_user, "risk:analysis:others")
    
    service = RiskReportService(db)
    
    try:
        # 收集分析数据
        base_data = await service._collect_base_data(
            request.user_id,
            request.start_date,
            request.end_date
        )
        
        analysis_results = {}
        
        # 根据请求的分析类型执行相应分析
        if "risk_metrics" in request.analysis_types:
            analysis_results["risk_metrics"] = await service._analyze_risk_metrics(base_data)
        
        if "position_analysis" in request.analysis_types:
            analysis_results["position_analysis"] = await service._analyze_position_risk(base_data)
        
        if "risk_attribution" in request.analysis_types:
            analysis_results["risk_attribution"] = await service._perform_risk_attribution(base_data)
        
        if "trend_analysis" in request.analysis_types:
            analysis_results["trend_analysis"] = await service._analyze_risk_trends(base_data)
        
        return {
            "analysis_id": f"analysis_{request.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "user_id": request.user_id,
            "period": {
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat()
            },
            "analysis_types": request.analysis_types,
            "results": analysis_results,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"风险分析失败: {str(e)}")


@router.get("/insights/summary")
async def get_risk_insights_summary(
    user_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取风险洞察摘要"""
    target_user_id = user_id or current_user.id
    
    # 检查权限
    if target_user_id != current_user.id:
        require_permission(current_user, "risk:insights:view_others")
    
    service = RiskReportService(db)
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 收集数据
        base_data = await service._collect_base_data(target_user_id, start_date, end_date)
        
        # 生成洞察摘要
        insights = {
            "user_id": target_user_id,
            "period_days": days,
            "risk_score": await service._calculate_risk_score(base_data),
            "key_findings": await service._extract_key_findings(base_data),
            "recommendations": await service._generate_recommendations(base_data),
            "trend_summary": "风险水平保持稳定",  # 简化实现
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取风险洞察失败: {str(e)}")


@router.post("/batch-generate")
async def batch_generate_reports(
    user_ids: List[int],
    report_type: str,
    start_date: datetime,
    end_date: datetime,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量生成报告"""
    # 只有管理员可以批量生成报告
    require_permission(current_user, "risk:reports:batch_generate")
    
    if len(user_ids) > 100:
        raise HTTPException(status_code=400, detail="批量生成报告的用户数量不能超过100")
    
    service = RiskReportService(db)
    
    # 在后台任务中执行批量生成
    async def batch_generate_task():
        try:
            report_type_enum = ReportType(report_type)
            results = []
            
            for user_id in user_ids:
                try:
                    report = await service.generate_risk_report(
                        user_id, report_type_enum, start_date, end_date
                    )
                    results.append({
                        "user_id": user_id,
                        "status": "success",
                        "report_id": report["report_id"]
                    })
                except Exception as e:
                    results.append({
                        "user_id": user_id,
                        "status": "failed",
                        "error": str(e)
                    })
            
            # 这里可以发送批量生成完成的通知
            logger.info(f"批量生成报告完成，成功: {len([r for r in results if r['status'] == 'success'])}, 失败: {len([r for r in results if r['status'] == 'failed'])}")
            
        except Exception as e:
            logger.error(f"批量生成报告失败: {str(e)}")
    
    background_tasks.add_task(batch_generate_task)
    
    return {
        "message": f"已启动批量生成任务，将为{len(user_ids)}个用户生成{report_type}报告",
        "user_count": len(user_ids),
        "report_type": report_type
    }