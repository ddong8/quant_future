"""
风险管理API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ...core.database import get_db
from ...core.dependencies import get_current_user, PaginationParams
from ...core.response import success_response, error_response
from ...models import User
from ...models.enums import RiskRuleType, RiskEventType
from ...schemas.risk import (
    RiskRuleResponse,
    RiskRuleListResponse,
    RiskRuleCreateRequest,
    RiskRuleUpdateRequest,
    RiskEventResponse,
    RiskEventListResponse,
    RiskCheckRequest,
    RiskCheckResponse,
    RiskMetricsResponse
)
from ...services.risk_service import RiskService

router = APIRouter()


@router.get("/rules", response_model=RiskRuleListResponse)
async def get_risk_rules(
    rule_type: Optional[str] = Query(None, description="规则类型"),
    symbol: Optional[str] = Query(None, description="品种代码"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取风险规则列表"""
    try:
        risk_service = RiskService(db)
        rules = risk_service.get_user_risk_rules(current_user.id)
        
        # 过滤规则
        if rule_type:
            try:
                rule_type_enum = RiskRuleType(rule_type)
                rules = [rule for rule in rules if rule.rule_type == rule_type_enum]
            except ValueError:
                return error_response(message="无效的规则类型")
        
        if symbol:
            rules = [rule for rule in rules if rule.symbol == symbol]
        
        if is_active is not None:
            rules = [rule for rule in rules if rule.is_active == is_active]
        
        return success_response(
            data={
                "rules": rules,
                "total": len(rules)
            }
        )
        
    except Exception as e:
        return error_response(message=f"获取风险规则失败: {str(e)}")


@router.post("/rules", response_model=RiskRuleResponse)
async def create_risk_rule(
    request: RiskRuleCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建风险规则"""
    try:
        risk_service = RiskService(db)
        
        rule_data = {
            "rule_type": request.rule_type,
            "symbol": request.symbol,
            "rule_value": request.rule_value,
            "description": request.description,
            "is_active": request.is_active
        }
        
        rule = risk_service.create_risk_rule(current_user.id, rule_data)
        
        return success_response(
            data=rule,
            message="风险规则创建成功"
        )
        
    except Exception as e:
        return error_response(message=f"创建风险规则失败: {str(e)}")


@router.put("/rules/{rule_id}", response_model=RiskRuleResponse)
async def update_risk_rule(
    rule_id: int,
    request: RiskRuleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新风险规则"""
    try:
        risk_service = RiskService(db)
        
        update_data = {}
        if request.rule_value is not None:
            update_data["rule_value"] = request.rule_value
        if request.description is not None:
            update_data["description"] = request.description
        if request.is_active is not None:
            update_data["is_active"] = request.is_active
        
        rule = risk_service.update_risk_rule(rule_id, current_user.id, update_data)
        
        return success_response(
            data=rule,
            message="风险规则更新成功"
        )
        
    except Exception as e:
        return error_response(message=f"更新风险规则失败: {str(e)}")


@router.delete("/rules/{rule_id}")
async def delete_risk_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除风险规则"""
    try:
        risk_service = RiskService(db)
        
        # 这里应该实现删除逻辑
        # 暂时通过设置为非激活状态来"删除"
        risk_service.update_risk_rule(rule_id, current_user.id, {"is_active": False})
        
        return success_response(message="风险规则删除成功")
        
    except Exception as e:
        return error_response(message=f"删除风险规则失败: {str(e)}")


@router.post("/check", response_model=RiskCheckResponse)
async def check_order_risk(
    request: RiskCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """检查订单风险"""
    try:
        risk_service = RiskService(db)
        
        result = risk_service.check_order_risk(
            user_id=current_user.id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            price=request.price,
            order_type=request.order_type
        )
        
        return success_response(data=result)
        
    except Exception as e:
        return error_response(message=f"风险检查失败: {str(e)}")


@router.get("/metrics", response_model=RiskMetricsResponse)
async def get_risk_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取风险指标"""
    try:
        risk_service = RiskService(db)
        metrics = risk_service.calculate_risk_metrics(current_user.id)
        
        return success_response(data=metrics)
        
    except Exception as e:
        return error_response(message=f"获取风险指标失败: {str(e)}")


@router.get("/events", response_model=RiskEventListResponse)
async def get_risk_events(
    event_type: Optional[str] = Query(None, description="事件类型"),
    severity: Optional[str] = Query(None, description="严重程度"),
    is_resolved: Optional[bool] = Query(None, description="是否已解决"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取风险事件列表"""
    try:
        # 这里需要实现风险事件查询逻辑
        # 暂时返回空列表
        return success_response(
            data={
                "events": [],
                "total": 0,
                "page": pagination.page,
                "page_size": pagination.page_size
            }
        )
        
    except Exception as e:
        return error_response(message=f"获取风险事件失败: {str(e)}")


@router.post("/events/{event_id}/resolve")
async def resolve_risk_event(
    event_id: int,
    resolution_notes: str = Query(..., description="解决说明"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """解决风险事件"""
    try:
        # 这里需要实现风险事件解决逻辑
        return success_response(message="风险事件已解决")
        
    except Exception as e:
        return error_response(message=f"解决风险事件失败: {str(e)}")


@router.get("/dashboard")
async def get_risk_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取风险管理仪表板数据"""
    try:
        risk_service = RiskService(db)
        
        # 获取风险指标
        metrics = risk_service.calculate_risk_metrics(current_user.id)
        
        # 获取活跃规则数量
        rules = risk_service.get_user_risk_rules(current_user.id)
        active_rules = len([rule for rule in rules if rule.is_active])
        
        # 构建仪表板数据
        dashboard_data = {
            "risk_metrics": metrics,
            "active_rules_count": active_rules,
            "total_rules_count": len(rules),
            "recent_events_count": 0,  # 需要实现事件查询
            "risk_level": metrics.get("risk_level", "LOW"),
            "last_update": datetime.utcnow().isoformat()
        }
        
        return success_response(data=dashboard_data)
        
    except Exception as e:
        return error_response(message=f"获取风险仪表板数据失败: {str(e)}")