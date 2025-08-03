"""
通知管理API接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...services.notification_service import NotificationService
from ...schemas.notification import (
    NotificationCreate, NotificationBatchCreate, NotificationResponse,
    NotificationPreferenceUpdate, NotificationPreferenceResponse,
    NotificationRuleCreate, NotificationRuleResponse,
    NotificationStats, NotificationMarkReadRequest,
    NotificationBatchDeleteRequest, NotificationTestRequest,
    NotificationSearchRequest, NotificationSearchResponse,
    NotificationType, NotificationChannel, NotificationStatus,
    NotificationPriority
)

router = APIRouter()

# ==================== 通知消息管理 ====================

@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建通知消息"""
    try:
        service = NotificationService(db)
        notification = service.create_notification(notification_data)
        return notification
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/batch")
async def batch_create_notifications(
    batch_data: NotificationBatchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量创建通知"""
    try:
        service = NotificationService(db)
        result = service.batch_create_notifications(batch_data)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=dict)
async def get_user_notifications(
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户通知列表"""
    try:
        service = NotificationService(db)
        result = service.get_user_notifications(
            current_user.id, limit, skip, unread_only
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/search", response_model=NotificationSearchResponse)
async def search_notifications(
    search_request: NotificationSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """搜索通知"""
    try:
        service = NotificationService(db)
        # TODO: 实现搜索功能
        result = service.search_notifications(current_user.id, search_request)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/mark-read")
async def mark_notifications_read(
    request: NotificationMarkReadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """标记通知为已读"""
    try:
        service = NotificationService(db)
        updated_count = service.mark_notifications_read(
            current_user.id, request.notification_ids
        )
        return {"message": f"已标记{updated_count}条通知为已读"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """标记所有通知为已读"""
    try:
        service = NotificationService(db)
        # TODO: 实现标记所有通知为已读
        updated_count = service.mark_all_notifications_read(current_user.id)
        return {"message": f"已标记{updated_count}条通知为已读"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/")
async def delete_notifications(
    request: NotificationBatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量删除通知"""
    try:
        service = NotificationService(db)
        deleted_count = service.delete_notifications(
            current_user.id, 
            request.notification_ids,
            request.delete_type == "hard"
        )
        return {"message": f"已删除{deleted_count}条通知"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/all")
async def delete_all_notifications(
    delete_type: str = Query("soft", pattern="^(soft|hard)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除所有通知"""
    try:
        service = NotificationService(db)
        # TODO: 实现删除所有通知
        deleted_count = service.delete_all_notifications(
            current_user.id, delete_type == "hard"
        )
        return {"message": f"已删除{deleted_count}条通知"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== 通知偏好管理 ====================

@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取通知偏好设置"""
    try:
        service = NotificationService(db)
        preferences = service.get_user_preferences(current_user.id)
        return preferences
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    preference_data: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新通知偏好设置"""
    try:
        service = NotificationService(db)
        preferences = service.update_user_preferences(
            current_user.id, preference_data
        )
        return preferences
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== 通知规则管理 ====================

@router.post("/rules", response_model=NotificationRuleResponse)
async def create_notification_rule(
    rule_data: NotificationRuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建通知规则"""
    try:
        service = NotificationService(db)
        rule = service.create_notification_rule(current_user.id, rule_data)
        return rule
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/rules", response_model=List[NotificationRuleResponse])
async def get_notification_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取通知规则列表"""
    try:
        service = NotificationService(db)
        rules = service.get_user_notification_rules(current_user.id)
        return rules
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/rules/{rule_id}")
async def update_notification_rule(
    rule_id: int,
    rule_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新通知规则"""
    try:
        service = NotificationService(db)
        # TODO: 实现更新通知规则
        rule = service.update_notification_rule(current_user.id, rule_id, rule_data)
        return rule
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/rules/{rule_id}")
async def delete_notification_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除通知规则"""
    try:
        service = NotificationService(db)
        # TODO: 实现删除通知规则
        success = service.delete_notification_rule(current_user.id, rule_id)
        if success:
            return {"message": "通知规则删除成功"}
        else:
            raise HTTPException(status_code=404, detail="通知规则不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== 通知模板管理 ====================

@router.get("/templates")
async def get_notification_templates(
    type_filter: Optional[NotificationType] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取通知模板列表"""
    try:
        service = NotificationService(db)
        templates = service.get_templates(type_filter)
        return templates
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/templates/{template_code}")
async def get_notification_template(
    template_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取通知模板详情"""
    try:
        service = NotificationService(db)
        template = service.get_template_by_code(template_code)
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/templates/test")
async def test_notification_template(
    test_request: NotificationTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """测试通知模板"""
    try:
        service = NotificationService(db)
        # TODO: 实现模板测试
        result = service.test_template(
            test_request.template_code,
            test_request.channel,
            test_request.variables,
            current_user.id,
            test_request.recipient
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== 通知统计 ====================

@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取通知统计"""
    try:
        service = NotificationService(db)
        stats = service.get_notification_stats(current_user.id, days)
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取未读通知数量"""
    try:
        service = NotificationService(db)
        count = service._get_unread_count(current_user.id)
        return {"unread_count": count}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== 通知导出 ====================

@router.post("/export")
async def export_notifications(
    export_request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出通知数据"""
    try:
        service = NotificationService(db)
        # TODO: 实现通知导出
        result = service.export_notifications(current_user.id, export_request)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== 系统管理接口 ====================

@router.post("/cleanup")
async def cleanup_notifications(
    days: int = Query(30, ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清理过期通知"""
    try:
        # TODO: 检查管理员权限
        service = NotificationService(db)
        # TODO: 实现通知清理
        cleaned_count = service.cleanup_notifications(days)
        return {"message": f"已清理{cleaned_count}条过期通知"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/system/stats")
async def get_system_notification_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统通知统计"""
    try:
        # TODO: 检查管理员权限
        service = NotificationService(db)
        # TODO: 实现系统统计
        stats = service.get_system_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))