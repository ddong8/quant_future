"""
风险控制自动化执行API接口
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from ...core.dependencies import get_current_user
from app.models.user import User
from app.schemas.risk import (
    RiskCheckRequest, RiskCheckResult, RiskControlActionRequest,
    RiskControlActionResult, EmergencyRiskControlRequest,
    RiskMonitoringStatus, RiskControlConfig
)
from app.services.risk_control_service import RiskControlService, RiskControlAction
from app.core.permissions import require_permission

router = APIRouter()


@router.post("/check-order", response_model=RiskCheckResult)
async def check_order_risk(
    request: RiskCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """订单提交前风险检查"""
    service = RiskControlService(db)
    
    # 检查用户权限
    if request.user_id != current_user.id:
        require_permission(current_user, "risk:check:others")
    
    return await service.check_order_risk(request.user_id, request.order_data)


@router.post("/execute-action", response_model=RiskControlActionResult)
async def execute_risk_action(
    request: RiskControlActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行风险控制动作"""
    # 只有管理员或风控人员可以手动执行风险控制动作
    require_permission(current_user, "risk:control:execute")
    
    service = RiskControlService(db)
    
    try:
        action = RiskControlAction(request.action)
        success = await service.execute_risk_action(
            request.user_id, 
            action, 
            request.context
        )
        
        return RiskControlActionResult(
            success=success,
            action=request.action,
            user_id=request.user_id,
            executed_at=datetime.utcnow(),
            message="风险控制动作执行成功" if success else "风险控制动作执行失败"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无效的风险控制动作: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行风险控制动作失败: {str(e)}")


@router.post("/emergency-control", response_model=RiskControlActionResult)
async def emergency_risk_control(
    request: EmergencyRiskControlRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """紧急风险控制"""
    # 只有管理员可以触发紧急风险控制
    require_permission(current_user, "risk:emergency:control")
    
    service = RiskControlService(db)
    
    try:
        success = await service.emergency_risk_control(request.user_id, request.reason)
        
        return RiskControlActionResult(
            success=success,
            action="emergency_control",
            user_id=request.user_id,
            executed_at=datetime.utcnow(),
            message="紧急风险控制执行成功" if success else "紧急风险控制执行失败"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"紧急风险控制失败: {str(e)}")


@router.post("/monitor/{user_id}")
async def start_risk_monitoring(
    user_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """启动实时风险监控"""
    # 检查权限
    if user_id != current_user.id:
        require_permission(current_user, "risk:monitor:others")
    
    service = RiskControlService(db)
    
    # 在后台任务中启动监控
    background_tasks.add_task(service.monitor_real_time_risk, user_id)
    
    return {"message": f"已启动用户 {user_id} 的实时风险监控"}


@router.get("/monitoring-status/{user_id}", response_model=RiskMonitoringStatus)
async def get_monitoring_status(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取风险监控状态"""
    # 检查权限
    if user_id != current_user.id:
        require_permission(current_user, "risk:monitor:view")
    
    # 这里应该从缓存或状态存储中获取监控状态
    # 暂时返回模拟数据
    return RiskMonitoringStatus(
        user_id=user_id,
        is_monitoring=True,
        last_check_time=datetime.utcnow(),
        risk_level="low",
        active_rules_count=5,
        triggered_actions_count=0
    )


@router.get("/config", response_model=RiskControlConfig)
async def get_risk_control_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取风险控制配置"""
    require_permission(current_user, "risk:config:read")
    
    # 从配置中获取风险控制参数
    service = RiskControlService(db)
    
    return RiskControlConfig(
        max_position_size_ratio=service.config["max_position_size_ratio"],
        max_daily_loss_ratio=service.config["max_daily_loss_ratio"],
        margin_call_ratio=service.config["margin_call_ratio"],
        liquidation_ratio=service.config["liquidation_ratio"],
        max_order_value_ratio=service.config["max_order_value_ratio"],
        auto_risk_control_enabled=True,
        emergency_control_enabled=True
    )


@router.put("/config", response_model=RiskControlConfig)
async def update_risk_control_config(
    config: RiskControlConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新风险控制配置"""
    require_permission(current_user, "risk:config:write")
    
    service = RiskControlService(db)
    
    # 更新配置
    service.config.update({
        "max_position_size_ratio": config.max_position_size_ratio,
        "max_daily_loss_ratio": config.max_daily_loss_ratio,
        "margin_call_ratio": config.margin_call_ratio,
        "liquidation_ratio": config.liquidation_ratio,
        "max_order_value_ratio": config.max_order_value_ratio
    })
    
    # 这里应该将配置保存到数据库或配置文件
    # 暂时只更新内存中的配置
    
    return config


@router.get("/actions/history")
async def get_risk_actions_history(
    user_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    action_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取风险控制动作历史"""
    # 检查权限
    if user_id and user_id != current_user.id:
        require_permission(current_user, "risk:actions:view_all")
    elif not user_id:
        require_permission(current_user, "risk:actions:view_all")
        
    from app.models.risk import RiskEvent
    
    query = db.query(RiskEvent).filter(RiskEvent.event_type == "risk_action")
    
    if user_id:
        query = query.filter(RiskEvent.user_id == user_id)
    
    if start_date:
        query = query.filter(RiskEvent.created_at >= start_date)
    
    if end_date:
        query = query.filter(RiskEvent.created_at <= end_date)
    
    if action_type:
        query = query.filter(RiskEvent.data["action"].astext == action_type)
    
    total = query.count()
    events = query.order_by(RiskEvent.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "events": [
            {
                "id": event.id,
                "user_id": event.user_id,
                "action": event.data.get("action"),
                "context": event.data.get("context"),
                "success": event.data.get("success"),
                "error": event.data.get("error"),
                "created_at": event.created_at,
                "severity": event.severity,
                "description": event.description
            }
            for event in events
        ]
    }


@router.get("/statistics")
async def get_risk_control_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取风险控制统计信息"""
    require_permission(current_user, "risk:statistics:view")
    
    from app.models.risk import RiskEvent
    from sqlalchemy import func, and_
    
    # 设置默认时间范围（最近30天）
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # 统计风险事件
    risk_events_query = db.query(RiskEvent).filter(
        and_(
            RiskEvent.created_at >= start_date,
            RiskEvent.created_at <= end_date
        )
    )
    
    # 按事件类型统计
    event_type_stats = db.query(
        RiskEvent.event_type,
        func.count(RiskEvent.id).label('count')
    ).filter(
        and_(
            RiskEvent.created_at >= start_date,
            RiskEvent.created_at <= end_date
        )
    ).group_by(RiskEvent.event_type).all()
    
    # 按严重程度统计
    severity_stats = db.query(
        RiskEvent.severity,
        func.count(RiskEvent.id).label('count')
    ).filter(
        and_(
            RiskEvent.created_at >= start_date,
            RiskEvent.created_at <= end_date
        )
    ).group_by(RiskEvent.severity).all()
    
    # 统计风险控制动作
    action_events = risk_events_query.filter(RiskEvent.event_type == "risk_action").all()
    
    action_stats = {}
    success_count = 0
    failure_count = 0
    
    for event in action_events:
        action = event.data.get("action", "unknown")
        success = event.data.get("success", False)
        
        if action not in action_stats:
            action_stats[action] = {"total": 0, "success": 0, "failure": 0}
        
        action_stats[action]["total"] += 1
        if success:
            action_stats[action]["success"] += 1
            success_count += 1
        else:
            action_stats[action]["failure"] += 1
            failure_count += 1
    
    return {
        "time_range": {
            "start_date": start_date,
            "end_date": end_date
        },
        "total_events": risk_events_query.count(),
        "event_type_distribution": {
            event_type: count for event_type, count in event_type_stats
        },
        "severity_distribution": {
            severity: count for severity, count in severity_stats
        },
        "risk_actions": {
            "total_actions": len(action_events),
            "success_rate": success_count / len(action_events) if action_events else 0,
            "action_breakdown": action_stats
        }
    }


@router.post("/test-scenario")
async def test_risk_scenario(
    scenario_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """测试风险控制场景"""
    # 只有管理员可以测试风险场景
    require_permission(current_user, "risk:test:scenario")
    
    service = RiskControlService(db)
    
    scenario_type = scenario_data.get("type")
    user_id = scenario_data.get("user_id", current_user.id)
    
    try:
        if scenario_type == "order_risk_check":
            # 测试订单风险检查
            order_data = scenario_data.get("order_data", {})
            result = await service.check_order_risk(user_id, order_data)
            return {"scenario": "order_risk_check", "result": result}
            
        elif scenario_type == "margin_call":
            # 测试保证金追缴
            success = await service.execute_risk_action(
                user_id,
                RiskControlAction.MARGIN_CALL,
                {"reason": "测试场景", "test": True}
            )
            return {"scenario": "margin_call", "success": success}
            
        elif scenario_type == "emergency_control":
            # 测试紧急风险控制
            success = await service.emergency_risk_control(
                user_id, 
                "测试紧急风险控制场景"
            )
            return {"scenario": "emergency_control", "success": success}
            
        else:
            raise HTTPException(status_code=400, detail="不支持的测试场景类型")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试场景执行失败: {str(e)}")


@router.get("/health")
async def risk_control_health_check(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """风险控制系统健康检查"""
    require_permission(current_user, "risk:health:check")
    
    try:
        service = RiskControlService(db)
        
        # 检查各个组件的状态
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "components": {
                "risk_engine": "healthy",
                "notification_service": "healthy",
                "websocket_manager": "healthy",
                "database": "healthy"
            },
            "config": service.config,
            "active_monitoring_sessions": 0  # 这里应该从实际状态获取
        }
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }