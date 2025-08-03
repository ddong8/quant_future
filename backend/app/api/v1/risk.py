"""
风险管理API接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...core.permissions import require_permission
from ...models.user import User
from ...models.risk import RiskRule, RiskEvent, RiskMetrics, RiskLimit
from ...schemas.risk import (
    RiskRuleCreate, RiskRuleUpdate, RiskRuleResponse,
    RiskEventResponse, RiskEventUpdate,
    RiskMetricsResponse,
    RiskLimitCreate, RiskLimitUpdate, RiskLimitResponse
)
from ...services.risk_service import RiskService

router = APIRouter()


# ==================== 风险规则管理 ====================

@router.post("/rules", response_model=RiskRuleResponse)
@require_permission("risk:create")
async def create_risk_rule(
    rule_data: RiskRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建风险规则"""
    risk_service = RiskService(db)
    
    try:
        rule = risk_service.create_risk_rule(
            rule_data.dict(),
            created_by=current_user.id
        )
        return RiskRuleResponse.from_orm(rule)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建风险规则失败: {str(e)}"
        )


@router.get("/rules", response_model=List[RiskRuleResponse])
@require_permission("risk:read")
async def get_risk_rules(
    user_id: Optional[int] = Query(None, description="用户ID"),
    strategy_id: Optional[int] = Query(None, description="策略ID"),
    rule_type: Optional[str] = Query(None, description="规则类型"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取风险规则列表"""
    risk_service = RiskService(db)
    
    rules = risk_service.get_risk_rules(
        user_id=user_id,
        strategy_id=strategy_id,
        rule_type=rule_type,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    
    return [RiskRuleResponse.from_orm(rule) for rule in rules]


@router.get("/rules/{rule_id}", response_model=RiskRuleResponse)
@require_permission("risk:read")
async def get_risk_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个风险规则"""
    risk_service = RiskService(db)
    
    rule = risk_service.get_risk_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="风险规则不存在"
        )
    
    return RiskRuleResponse.from_orm(rule)


@router.put("/rules/{rule_id}", response_model=RiskRuleResponse)
@require_permission("risk:update")
async def update_risk_rule(
    rule_id: int,
    rule_data: RiskRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新风险规则"""
    risk_service = RiskService(db)
    
    rule = risk_service.update_risk_rule(
        rule_id,
        rule_data.dict(exclude_unset=True)
    )
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="风险规则不存在"
        )
    
    return RiskRuleResponse.from_orm(rule)


@router.delete("/rules/{rule_id}")
@require_permission("risk:delete")
async def delete_risk_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除风险规则"""
    risk_service = RiskService(db)
    
    success = risk_service.delete_risk_rule(rule_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="风险规则不存在"
        )
    
    return {"message": "风险规则删除成功"}


# ==================== 风险事件管理 ====================

@router.get("/events", response_model=List[RiskEventResponse])
@require_permission("risk:read")
async def get_risk_events(
    user_id: Optional[int] = Query(None, description="用户ID"),
    strategy_id: Optional[int] = Query(None, description="策略ID"),
    event_type: Optional[str] = Query(None, description="事件类型"),
    severity: Optional[str] = Query(None, description="严重程度"),
    status: Optional[str] = Query(None, description="事件状态"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取风险事件列表"""
    risk_service = RiskService(db)
    
    events = risk_service.get_risk_events(
        user_id=user_id,
        strategy_id=strategy_id,
        event_type=event_type,
        severity=severity,
        status=status,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    
    return [RiskEventResponse.from_orm(event) for event in events]


@router.get("/events/{event_id}", response_model=RiskEventResponse)
@require_permission("risk:read")
async def get_risk_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个风险事件"""
    risk_service = RiskService(db)
    
    event = risk_service.get_risk_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="风险事件不存在"
        )
    
    return RiskEventResponse.from_orm(event)


@router.put("/events/{event_id}/resolve", response_model=RiskEventResponse)
@require_permission("risk:update")
async def resolve_risk_event(
    event_id: int,
    event_data: RiskEventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """解决风险事件"""
    risk_service = RiskService(db)
    
    event = risk_service.resolve_risk_event(
        event_id,
        resolved_by=current_user.id,
        notes=event_data.resolution_notes
    )
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="风险事件不存在"
        )
    
    return RiskEventResponse.from_orm(event)


@router.put("/events/{event_id}/escalate", response_model=RiskEventResponse)
@require_permission("risk:update")
async def escalate_risk_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """升级风险事件"""
    risk_service = RiskService(db)
    
    event = risk_service.escalate_risk_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="风险事件不存在"
        )
    
    return RiskEventResponse.from_orm(event)


# ==================== 风险指标管理 ====================

@router.get("/metrics", response_model=List[RiskMetricsResponse])
@require_permission("risk:read")
async def get_risk_metrics(
    user_id: int = Query(..., description="用户ID"),
    strategy_id: Optional[int] = Query(None, description="策略ID"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    period_type: str = Query("daily", description="周期类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取风险指标历史数据"""
    risk_service = RiskService(db)
    
    metrics = risk_service.get_risk_metrics(
        user_id=user_id,
        strategy_id=strategy_id,
        start_date=start_date,
        end_date=end_date,
        period_type=period_type
    )
    
    return [RiskMetricsResponse.from_orm(metric) for metric in metrics]


@router.post("/metrics/calculate", response_model=RiskMetricsResponse)
@require_permission("risk:create")
async def calculate_risk_metrics(
    user_id: int = Query(..., description="用户ID"),
    strategy_id: Optional[int] = Query(None, description="策略ID"),
    date: Optional[datetime] = Query(None, description="计算日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """计算风险指标"""
    risk_service = RiskService(db)
    
    try:
        metrics = risk_service.calculate_risk_metrics(
            user_id=user_id,
            strategy_id=strategy_id,
            date=date
        )
        return RiskMetricsResponse.from_orm(metrics)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"计算风险指标失败: {str(e)}"
        )


# ==================== 风险监控 ====================

@router.post("/check")
@require_permission("risk:create")
async def check_risk_rules(
    context: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查风险规则"""
    risk_service = RiskService(db)
    
    try:
        events = risk_service.check_risk_rules(context)
        return {
            "message": f"风险检查完成，触发 {len(events)} 个事件",
            "events": [event.to_dict() for event in events]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"风险检查失败: {str(e)}"
        )


# ==================== 风险限额管理 ====================

@router.post("/limits", response_model=RiskLimitResponse)
@require_permission("risk:create")
async def create_risk_limit(
    limit_data: RiskLimitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建风险限额"""
    try:
        limit = RiskLimit(
            user_id=limit_data.user_id,
            strategy_id=limit_data.strategy_id,
            limit_type=limit_data.limit_type,
            limit_name=limit_data.limit_name,
            description=limit_data.description,
            limit_value=limit_data.limit_value,
            is_hard_limit=limit_data.is_hard_limit,
            warning_threshold=limit_data.warning_threshold,
            reset_frequency=limit_data.reset_frequency,
            metadata=limit_data.metadata or {},
            created_by=current_user.id
        )
        
        db.add(limit)
        db.commit()
        db.refresh(limit)
        
        return RiskLimitResponse.from_orm(limit)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建风险限额失败: {str(e)}"
        )


@router.get("/limits", response_model=List[RiskLimitResponse])
@require_permission("risk:read")
async def get_risk_limits(
    user_id: Optional[int] = Query(None, description="用户ID"),
    strategy_id: Optional[int] = Query(None, description="策略ID"),
    limit_type: Optional[str] = Query(None, description="限额类型"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取风险限额列表"""
    query = db.query(RiskLimit)
    
    if user_id is not None:
        query = query.filter(RiskLimit.user_id == user_id)
    
    if strategy_id is not None:
        query = query.filter(RiskLimit.strategy_id == strategy_id)
    
    if limit_type is not None:
        query = query.filter(RiskLimit.limit_type == limit_type)
    
    if is_active is not None:
        query = query.filter(RiskLimit.is_active == is_active)
    
    limits = query.offset(skip).limit(limit).all()
    return [RiskLimitResponse.from_orm(limit) for limit in limits]


@router.get("/limits/{limit_id}", response_model=RiskLimitResponse)
@require_permission("risk:read")
async def get_risk_limit(
    limit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个风险限额"""
    limit = db.query(RiskLimit).filter(RiskLimit.id == limit_id).first()
    if not limit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="风险限额不存在"
        )
    
    return RiskLimitResponse.from_orm(limit)


@router.put("/limits/{limit_id}", response_model=RiskLimitResponse)
@require_permission("risk:update")
async def update_risk_limit(
    limit_id: int,
    limit_data: RiskLimitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新风险限额"""
    limit = db.query(RiskLimit).filter(RiskLimit.id == limit_id).first()
    if not limit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="风险限额不存在"
        )
    
    try:
        for key, value in limit_data.dict(exclude_unset=True).items():
            setattr(limit, key, value)
        
        db.commit()
        db.refresh(limit)
        
        return RiskLimitResponse.from_orm(limit)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新风险限额失败: {str(e)}"
        )


@router.delete("/limits/{limit_id}")
@require_permission("risk:delete")
async def delete_risk_limit(
    limit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除风险限额"""
    limit = db.query(RiskLimit).filter(RiskLimit.id == limit_id).first()
    if not limit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="风险限额不存在"
        )
    
    try:
        db.delete(limit)
        db.commit()
        return {"message": "风险限额删除成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"删除风险限额失败: {str(e)}"
        )


# ==================== 风险报告 ====================

@router.get("/reports/summary")
@require_permission("risk:read")
async def get_risk_summary(
    user_id: int = Query(..., description="用户ID"),
    strategy_id: Optional[int] = Query(None, description="策略ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取风险摘要报告"""
    risk_service = RiskService(db)
    
    try:
        # 获取最新的风险指标
        latest_metrics = risk_service.get_risk_metrics(
            user_id=user_id,
            strategy_id=strategy_id,
            limit=1
        )
        
        # 获取活跃的风险事件
        active_events = risk_service.get_risk_events(
            user_id=user_id,
            strategy_id=strategy_id,
            status="ACTIVE",
            limit=10
        )
        
        # 获取风险限额状态
        risk_limits = db.query(RiskLimit).filter(
            RiskLimit.user_id == user_id,
            RiskLimit.is_active == True
        ).all()
        
        return {
            "latest_metrics": latest_metrics[0].to_dict() if latest_metrics else None,
            "active_events_count": len(active_events),
            "active_events": [event.to_dict() for event in active_events],
            "risk_limits": [limit.to_dict() for limit in risk_limits],
            "summary": {
                "total_events": len(active_events),
                "critical_events": len([e for e in active_events if e.severity == "CRITICAL"]),
                "high_events": len([e for e in active_events if e.severity == "HIGH"]),
                "breached_limits": len([l for l in risk_limits if l.is_breached])
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取风险摘要失败: {str(e)}"
        )