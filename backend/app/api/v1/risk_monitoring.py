"""
实时风险监控API接口
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...services.risk_monitoring_service import RiskMonitoringService

router = APIRouter()

@router.get("/metrics")
async def get_real_time_risk_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取实时风险指标"""
    try:
        service = RiskMonitoringService(db)
        metrics = service.calculate_real_time_risk_metrics(current_user.id)
        
        if not metrics:
            raise HTTPException(status_code=404, detail="无法获取风险指标")
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取风险指标失败: {str(e)}")

@router.get("/alerts")
async def get_risk_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取风险预警"""
    try:
        service = RiskMonitoringService(db)
        alerts = service.check_risk_alerts(current_user.id)
        
        return {
            'alerts': alerts,
            'count': len(alerts),
            'has_high_risk': any(alert['severity'] == 'HIGH' for alert in alerts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取风险预警失败: {str(e)}")

@router.post("/events")
async def record_risk_event(
    event_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """记录风险事件"""
    try:
        service = RiskMonitoringService(db)
        
        event = service.record_risk_event(current_user.id, event_data)
        
        if not event:
            raise HTTPException(status_code=400, detail="记录风险事件失败")
        
        return {"message": "风险事件记录成功", "event_id": event.id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录风险事件失败: {str(e)}")

@router.get("/events")
async def get_risk_events(
    days: int = Query(30, ge=1, le=365, description="查询天数"),
    event_type: Optional[str] = Query(None, description="事件类型筛选"),
    severity: Optional[str] = Query(None, description="严重程度筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取风险事件"""
    try:
        service = RiskMonitoringService(db)
        events = service.get_risk_events(
            user_id=current_user.id,
            days=days,
            event_type=event_type,
            severity=severity
        )
        
        return {
            'events': events,
            'count': len(events)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取风险事件失败: {str(e)}")

@router.put("/events/{event_id}/resolve")
async def resolve_risk_event(
    event_id: int,
    resolution_data: dict = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """解决风险事件"""
    try:
        service = RiskMonitoringService(db)
        
        resolution_note = resolution_data.get('resolution_note') if resolution_data else None
        success = service.resolve_risk_event(
            user_id=current_user.id,
            event_id=event_id,
            resolution_note=resolution_note
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="风险事件不存在")
        
        return {"message": "风险事件已解决"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解决风险事件失败: {str(e)}")

@router.get("/statistics")
async def get_risk_statistics(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取风险统计"""
    try:
        service = RiskMonitoringService(db)
        statistics = service.get_risk_statistics(current_user.id, days)
        
        return statistics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取风险统计失败: {str(e)}")

@router.get("/dashboard")
async def get_risk_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取风险仪表板数据"""
    try:
        service = RiskMonitoringService(db)
        
        # 获取实时风险指标
        metrics = service.calculate_real_time_risk_metrics(current_user.id)
        
        # 获取风险预警
        alerts = service.check_risk_alerts(current_user.id)
        
        # 获取最近的风险事件
        recent_events = service.get_risk_events(current_user.id, days=7)
        
        # 获取风险统计
        statistics = service.get_risk_statistics(current_user.id, days=30)
        
        return {
            'metrics': metrics,
            'alerts': {
                'items': alerts,
                'count': len(alerts),
                'has_high_risk': any(alert['severity'] == 'HIGH' for alert in alerts)
            },
            'recent_events': {
                'items': recent_events[:10],  # 最近10个事件
                'count': len(recent_events)
            },
            'statistics': statistics,
            'last_updated': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取风险仪表板失败: {str(e)}")

@router.post("/monitor/start")
async def start_risk_monitoring(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """启动风险监控"""
    try:
        # 添加后台任务进行风险监控
        background_tasks.add_task(monitor_user_risk, current_user.id, db)
        
        return {"message": "风险监控已启动"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动风险监控失败: {str(e)}")

async def monitor_user_risk(user_id: int, db: Session):
    """后台风险监控任务"""
    try:
        service = RiskMonitoringService(db)
        
        # 检查风险预警
        alerts = service.check_risk_alerts(user_id)
        
        # 记录高风险事件
        for alert in alerts:
            if alert['severity'] == 'HIGH':
                event_data = {
                    'event_type': alert['type'],
                    'severity': alert['severity'],
                    'title': alert['title'],
                    'description': alert['message'],
                    'risk_value': alert['value'],
                    'threshold_value': alert['threshold']
                }
                service.record_risk_event(user_id, event_data)
        
        # 这里可以添加通知逻辑
        # 例如发送邮件、短信或推送通知
        
    except Exception as e:
        logger.error(f"后台风险监控失败: {e}")

@router.get("/health")
async def get_monitoring_health():
    """获取监控系统健康状态"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }