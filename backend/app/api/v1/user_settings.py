"""
用户设置API接口
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...services.user_settings_service import UserSettingsService
from ...schemas.user_settings import (
    UserSettingsResponse, UserSettingsUpdate,
    SecuritySettingsResponse, SecuritySettingsUpdate,
    NotificationSettingsResponse, NotificationSettingsUpdate,
    PasswordChangeRequest, TwoFactorToggleRequest,
    LoginDeviceResponse
)

router = APIRouter()

@router.get("/profile", response_model=Dict[str, Any])
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户个人资料"""
    try:
        service = UserSettingsService(db)
        profile = service.get_user_profile(current_user.id)
        return profile
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/profile")
async def update_user_profile(
    profile_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户个人资料"""
    try:
        service = UserSettingsService(db)
        updated_profile = service.update_user_profile(current_user.id, profile_data)
        return {"message": "个人资料更新成功", "profile": updated_profile}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户设置"""
    try:
        service = UserSettingsService(db)
        settings = service.get_user_settings(current_user.id)
        return settings
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/settings")
async def update_user_settings(
    settings_data: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户设置"""
    try:
        service = UserSettingsService(db)
        updated_settings = service.update_user_settings(current_user.id, settings_data.dict())
        return {"message": "用户设置更新成功", "settings": updated_settings}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/security", response_model=SecuritySettingsResponse)
async def get_security_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取安全设置"""
    try:
        service = UserSettingsService(db)
        security_settings = service.get_security_settings(current_user.id)
        return security_settings
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/security")
async def update_security_settings(
    security_data: SecuritySettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新安全设置"""
    try:
        service = UserSettingsService(db)
        updated_settings = service.update_security_settings(current_user.id, security_data.dict())
        return {"message": "安全设置更新成功", "settings": updated_settings}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    try:
        service = UserSettingsService(db)
        result = service.change_password(
            current_user.id,
            password_data.current_password,
            password_data.new_password
        )
        
        if result:
            return {"message": "密码修改成功"}
        else:
            raise HTTPException(status_code=400, detail="当前密码错误")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/two-factor/toggle")
async def toggle_two_factor(
    toggle_data: TwoFactorToggleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """启用/关闭双因子认证"""
    try:
        service = UserSettingsService(db)
        result = service.toggle_two_factor_auth(current_user.id, toggle_data.enabled)
        
        action = "启用" if toggle_data.enabled else "关闭"
        return {"message": f"双因子认证{action}成功", "enabled": result}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/two-factor/qr-code")
async def get_two_factor_qr_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取双因子认证二维码"""
    try:
        service = UserSettingsService(db)
        qr_code_data = service.generate_two_factor_qr_code(current_user.id)
        return qr_code_data
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/two-factor/verify")
async def verify_two_factor_code(
    verification_data: Dict[str, str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """验证双因子认证码"""
    try:
        service = UserSettingsService(db)
        is_valid = service.verify_two_factor_code(
            current_user.id,
            verification_data.get("code", "")
        )
        
        if is_valid:
            return {"message": "验证成功", "valid": True}
        else:
            return {"message": "验证码错误", "valid": False}
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/notifications", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取通知设置"""
    try:
        service = UserSettingsService(db)
        notification_settings = service.get_notification_settings(current_user.id)
        return notification_settings
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/notifications")
async def update_notification_settings(
    notification_data: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新通知设置"""
    try:
        service = UserSettingsService(db)
        updated_settings = service.update_notification_settings(
            current_user.id, 
            notification_data.dict()
        )
        return {"message": "通知设置更新成功", "settings": updated_settings}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/devices", response_model=List[LoginDeviceResponse])
async def get_login_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取登录设备列表"""
    try:
        service = UserSettingsService(db)
        devices = service.get_login_devices(current_user.id)
        return devices
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/devices/{device_id}")
async def remove_login_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """移除登录设备"""
    try:
        service = UserSettingsService(db)
        result = service.remove_login_device(current_user.id, device_id)
        
        if result:
            return {"message": "设备移除成功"}
        else:
            raise HTTPException(status_code=404, detail="设备不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/devices/logout-all")
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """登出所有设备"""
    try:
        service = UserSettingsService(db)
        count = service.logout_all_devices(current_user.id)
        return {"message": f"已登出{count}个设备"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/activity-log")
async def get_activity_log(
    limit: int = 50,
    skip: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户活动日志"""
    try:
        service = UserSettingsService(db)
        activity_log = service.get_user_activity_log(current_user.id, limit, skip)
        return activity_log
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/export-data")
async def export_user_data(
    export_type: str = "all",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出用户数据"""
    try:
        service = UserSettingsService(db)
        export_result = service.export_user_data(current_user.id, export_type)
        return export_result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/account")
async def delete_account(
    confirmation_data: Dict[str, str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除账户"""
    try:
        # 验证密码
        if not confirmation_data.get("password"):
            raise HTTPException(status_code=400, detail="请输入密码确认")
        
        service = UserSettingsService(db)
        result = service.delete_user_account(
            current_user.id,
            confirmation_data["password"]
        )
        
        if result:
            return {"message": "账户删除成功"}
        else:
            raise HTTPException(status_code=400, detail="密码错误")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== 设置管理增强功能 ====================

@router.get("/categories")
async def get_settings_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取设置分类"""
    try:
        from ...services.settings_management_service import SettingsManagementService
        service = SettingsManagementService(db)
        categories = service.get_settings_categories(current_user.id)
        return categories
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/items")
async def get_settings_items(
    category_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取设置项"""
    try:
        from ...services.settings_management_service import SettingsManagementService
        service = SettingsManagementService(db)
        items = service.get_settings_items(current_user.id, category_id)
        return items
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/values/{settings_item_id}")
async def get_setting_value(
    settings_item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个设置值"""
    try:
        from ...services.settings_management_service import SettingsManagementService
        service = SettingsManagementService(db)
        value = service.get_user_setting_value(current_user.id, settings_item_id)
        return {"value": value}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/values/{settings_item_id}")
async def set_setting_value(
    settings_item_id: int,
    value_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """设置单个设置值"""
    try:
        from ...services.settings_management_service import SettingsManagementService
        service = SettingsManagementService(db)
        result = service.set_user_setting_value(
            current_user.id,
            settings_item_id,
            value_data.get("value"),
            value_data.get("reason"),
            value_data.get("source", "user")
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/batch-update")
async def batch_update_settings(
    settings_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量更新设置"""
    try:
        from ...services.settings_management_service import SettingsManagementService
        service = SettingsManagementService(db)
        result = service.batch_update_settings(
            current_user.id,
            settings_data.get("settings", {}),
            settings_data.get("reason")
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history")
async def get_settings_history(
    settings_item_id: int = None,
    limit: int = 50,
    skip: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取设置历史记录"""
    try:
        from ...services.settings_management_service import SettingsManagementService
        service = SettingsManagementService(db)
        history = service.get_user_settings_history(
            current_user.id, settings_item_id, limit, skip
        )
        return history
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rollback")
async def rollback_setting(
    rollback_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """回滚设置到指定版本"""
    try:
        from ...services.settings_management_service import SettingsManagementService
        service = SettingsManagementService(db)
        result = service.rollback_setting_value(
            current_user.id,
            rollback_data["settings_item_id"],
            rollback_data["target_version"],
            rollback_data.get("reason")
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/templates")
async def get_settings_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取设置模板"""
    try:
        from ...services.settings_management_service import SettingsManagementService
        service = SettingsManagementService(db)
        templates = service.get_settings_templates(current_user.id)
        return templates
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/templates/{template_id}/apply")
async def apply_settings_template(
    template_id: int,
    template_data: Dict[str, str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """应用设置模板"""
    try:
        from ...services.settings_management_service import SettingsManagementService
        service = SettingsManagementService(db)
        result = service.apply_settings_template(
            current_user.id,
            template_id,
            template_data.get("reason") if template_data else None
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/export")
async def export_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出用户设置"""
    try:
        from ...services.settings_management_service import SettingsManagementService
        service = SettingsManagementService(db)
        export_data = service.export_user_settings(current_user.id)
        return export_data
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/import")
async def import_settings(
    import_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导入用户设置"""
    try:
        from ...services.settings_management_service import SettingsManagementService
        service = SettingsManagementService(db)
        result = service.import_user_settings(
            current_user.id,
            import_data.get("settings_data", {}),
            import_data.get("reason")
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))