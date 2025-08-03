"""
角色和权限管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...core.permissions import require_permission
from ...models.user import User
from ...models.role import PermissionConstants
from ...services.role_service import RoleService
from ...schemas.role import (
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionCreate, PermissionUpdate, PermissionResponse,
    UserRoleAssignmentCreate, UserRoleAssignmentUpdate, UserRoleAssignmentResponse,
    RolePermissionBatch, UserRoleBatch,
    PermissionCheckRequest, PermissionCheckResponse,
    RoleStatsResponse, PermissionStatsResponse,
    UserPermissionSummary
)
from ...core.response import success_response, error_response

router = APIRouter(prefix="/roles", tags=["角色权限管理"])

# 角色管理路由
@router.post("/", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_MANAGE_ROLES)
async def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建角色"""
    try:
        role_service = RoleService(db)
        role = role_service.create_role(role_data, current_user.id)
        return success_response(data=role.to_dict(), message="角色创建成功")
    except Exception as e:
        return error_response(message=str(e))

@router.get("/", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_VIEW)
async def get_roles(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    is_system: Optional[bool] = Query(None, description="是否系统角色"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色列表"""
    try:
        role_service = RoleService(db)
        roles, total = role_service.get_roles(
            skip=skip,
            limit=limit,
            is_active=is_active,
            is_system=is_system,
            search=search
        )
        
        return success_response(
            data={
                "items": [role.to_dict() for role in roles],
                "total": total,
                "skip": skip,
                "limit": limit
            },
            message="获取角色列表成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/{role_id}", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_VIEW)
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色详情"""
    try:
        role_service = RoleService(db)
        role = role_service.get_role(role_id)
        return success_response(data=role.to_dict(), message="获取角色详情成功")
    except Exception as e:
        return error_response(message=str(e))

@router.put("/{role_id}", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_MANAGE_ROLES)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新角色"""
    try:
        role_service = RoleService(db)
        role = role_service.update_role(role_id, role_data)
        return success_response(data=role.to_dict(), message="角色更新成功")
    except Exception as e:
        return error_response(message=str(e))

@router.delete("/{role_id}", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_MANAGE_ROLES)
async def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除角色"""
    try:
        role_service = RoleService(db)
        role_service.delete_role(role_id)
        return success_response(message="角色删除成功")
    except Exception as e:
        return error_response(message=str(e))

# 权限管理路由
@router.post("/permissions", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_MANAGE_ROLES)
async def create_permission(
    permission_data: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建权限"""
    try:
        role_service = RoleService(db)
        permission = role_service.create_permission(permission_data)
        return success_response(data=permission.to_dict(), message="权限创建成功")
    except Exception as e:
        return error_response(message=str(e))

@router.get("/permissions", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_VIEW)
async def get_permissions(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    category: Optional[str] = Query(None, description="权限分类"),
    resource: Optional[str] = Query(None, description="资源类型"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取权限列表"""
    try:
        role_service = RoleService(db)
        permissions, total = role_service.get_permissions(
            skip=skip,
            limit=limit,
            category=category,
            resource=resource,
            is_active=is_active,
            search=search
        )
        
        return success_response(
            data={
                "items": [permission.to_dict() for permission in permissions],
                "total": total,
                "skip": skip,
                "limit": limit
            },
            message="获取权限列表成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/permissions/{permission_id}", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_VIEW)
async def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取权限详情"""
    try:
        role_service = RoleService(db)
        permission = role_service.get_permission(permission_id)
        return success_response(data=permission.to_dict(), message="获取权限详情成功")
    except Exception as e:
        return error_response(message=str(e))

@router.put("/permissions/{permission_id}", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_MANAGE_ROLES)
async def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新权限"""
    try:
        role_service = RoleService(db)
        permission = role_service.update_permission(permission_id, permission_data)
        return success_response(data=permission.to_dict(), message="权限更新成功")
    except Exception as e:
        return error_response(message=str(e))

@router.delete("/permissions/{permission_id}", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_MANAGE_ROLES)
async def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除权限"""
    try:
        role_service = RoleService(db)
        role_service.delete_permission(permission_id)
        return success_response(message="权限删除成功")
    except Exception as e:
        return error_response(message=str(e))

# 用户角色分配路由
@router.post("/users/{user_id}/roles/{role_id}", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_MANAGE_ROLES)
async def assign_role_to_user(
    user_id: int,
    role_id: int,
    assignment_data: UserRoleAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为用户分配角色"""
    try:
        role_service = RoleService(db)
        assignment = role_service.assign_role_to_user(
            user_id, role_id, assignment_data, current_user.id
        )
        return success_response(data=assignment.to_dict(), message="角色分配成功")
    except Exception as e:
        return error_response(message=str(e))

@router.delete("/users/{user_id}/roles/{role_id}", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_MANAGE_ROLES)
async def revoke_role_from_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """撤销用户角色"""
    try:
        role_service = RoleService(db)
        role_service.revoke_role_from_user(user_id, role_id)
        return success_response(message="角色撤销成功")
    except Exception as e:
        return error_response(message=str(e))

@router.get("/users/{user_id}/roles", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_VIEW)
async def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户角色"""
    try:
        role_service = RoleService(db)
        roles = role_service.get_user_roles(user_id)
        return success_response(
            data=[role.to_dict() for role in roles],
            message="获取用户角色成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/{role_id}/users", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_VIEW)
async def get_role_users(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色用户"""
    try:
        role_service = RoleService(db)
        users = role_service.get_role_users(role_id)
        return success_response(
            data=[user.to_dict() for user in users],
            message="获取角色用户成功"
        )
    except Exception as e:
        return error_response(message=str(e))

# 权限检查路由
@router.post("/check-permission", response_model=Dict[str, Any])
async def check_user_permission(
    request: PermissionCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查用户权限"""
    try:
        role_service = RoleService(db)
        
        # 只能检查自己的权限，除非有管理权限
        if request.user_id != current_user.id and not current_user.has_permission(PermissionConstants.USER_VIEW):
            return error_response(message="无权限检查其他用户权限")
        
        permissions_result = role_service.check_user_permissions(request.user_id, request.permissions)
        has_all = all(permissions_result.values())
        
        return success_response(
            data={
                "user_id": request.user_id,
                "permissions": permissions_result,
                "has_all": has_all
            },
            message="权限检查完成"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/users/{user_id}/permissions", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_VIEW)
async def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户所有权限"""
    try:
        role_service = RoleService(db)
        permissions = role_service.get_user_permissions(user_id)
        return success_response(data=permissions, message="获取用户权限成功")
    except Exception as e:
        return error_response(message=str(e))

@router.get("/users/{user_id}/summary", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_VIEW)
async def get_user_permission_summary(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户权限摘要"""
    try:
        role_service = RoleService(db)
        
        # 获取用户信息
        from ...services.user_service import UserService
        user_service = UserService(db)
        user = user_service.get_user(user_id)
        
        # 获取角色和权限
        roles = role_service.get_user_roles(user_id)
        permissions = role_service.get_user_permissions(user_id)
        
        summary = {
            "user_id": user.id,
            "username": user.username,
            "roles": [role.to_dict() for role in roles],
            "permissions": permissions,
            "effective_permissions": permissions,
            "last_updated": user.updated_at
        }
        
        return success_response(data=summary, message="获取用户权限摘要成功")
    except Exception as e:
        return error_response(message=str(e))

# 批量操作路由
@router.post("/batch/assign-roles", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_MANAGE_ROLES)
async def batch_assign_roles(
    batch_data: UserRoleBatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量分配角色"""
    try:
        role_service = RoleService(db)
        results = role_service.batch_assign_roles(batch_data, current_user.id)
        return success_response(data=results, message="批量角色操作完成")
    except Exception as e:
        return error_response(message=str(e))

@router.post("/batch/update-permissions", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_MANAGE_ROLES)
async def batch_update_role_permissions(
    batch_data: RolePermissionBatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量更新角色权限"""
    try:
        role_service = RoleService(db)
        results = role_service.batch_update_role_permissions(batch_data)
        return success_response(data=results, message="批量权限更新完成")
    except Exception as e:
        return error_response(message=str(e))

# 统计信息路由
@router.get("/stats/roles", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_VIEW)
async def get_role_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色统计信息"""
    try:
        role_service = RoleService(db)
        stats = role_service.get_role_stats()
        return success_response(data=stats, message="获取角色统计成功")
    except Exception as e:
        return error_response(message=str(e))

@router.get("/stats/permissions", response_model=Dict[str, Any])
@require_permission(PermissionConstants.USER_VIEW)
async def get_permission_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取权限统计信息"""
    try:
        role_service = RoleService(db)
        stats = role_service.get_permission_stats()
        return success_response(data=stats, message="获取权限统计成功")
    except Exception as e:
        return error_response(message=str(e))

# 系统初始化路由
@router.post("/initialize", response_model=Dict[str, Any])
@require_permission(PermissionConstants.ADMIN_ALL)
async def initialize_system_roles_and_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """初始化系统角色和权限"""
    try:
        role_service = RoleService(db)
        role_service.initialize_system_roles_and_permissions()
        return success_response(message="系统角色和权限初始化成功")
    except Exception as e:
        return error_response(message=str(e))