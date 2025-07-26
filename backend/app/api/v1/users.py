"""
用户管理API路由
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ...core.dependencies import (
    get_database,
    get_current_user,
    require_admin,
    require_trader_or_admin,
    get_pagination_params,
    get_sort_params,
    PaginationParams,
    SortParams,
)
from ...core.response import (
    success_response,
    created_response,
    paginated_response,
    deleted_response,
)
from ...services.user_service import UserService
from ...schemas.user import (
    UserCreate,
    UserUpdate,
    UserAdminUpdate,
    UserResponse,
    UserListResponse,
    UserStatsResponse,
    UserSearchRequest,
    BatchUserOperation,
)
from ...models import User, UserRole

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database),
):
    """创建用户（管理员权限）"""
    user_service = UserService(db)
    user_response = user_service.create_user(user_data, current_user.id)
    
    return created_response(
        data=user_response.dict(),
        message="用户创建成功"
    )


@router.get("/", response_model=List[UserListResponse])
async def get_users_list(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    role: Optional[UserRole] = Query(None, description="用户角色"),
    is_active: Optional[bool] = Query(None, description="是否活跃"),
    is_verified: Optional[bool] = Query(None, description="是否已验证"),
    pagination: PaginationParams = Depends(get_pagination_params),
    sort_params: SortParams = Depends(get_sort_params),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database),
):
    """获取用户列表（管理员权限）"""
    search_params = UserSearchRequest(
        keyword=keyword,
        role=role,
        is_active=is_active,
        is_verified=is_verified,
    )
    
    user_service = UserService(db)
    users, total = user_service.get_users_list(search_params, pagination, sort_params)
    
    return paginated_response(
        data=[user.dict() for user in users],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        message="获取用户列表成功"
    )


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database),
):
    """获取用户统计信息（管理员权限）"""
    user_service = UserService(db)
    stats = user_service.get_user_stats()
    
    return success_response(
        data=stats.dict(),
        message="获取用户统计成功"
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """获取当前用户信息"""
    user_response = UserResponse.from_orm(current_user)
    
    return success_response(
        data=user_response.dict(),
        message="获取用户信息成功"
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """更新当前用户信息"""
    user_service = UserService(db)
    user_response = user_service.update_user(current_user.id, user_data, current_user.id)
    
    return success_response(
        data=user_response.dict(),
        message="用户信息更新成功"
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database),
):
    """根据ID获取用户信息（管理员权限）"""
    user_service = UserService(db)
    user_response = user_service.get_user_by_id(user_id)
    
    return success_response(
        data=user_response.dict(),
        message="获取用户信息成功"
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_by_id(
    user_id: int,
    user_data: UserAdminUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database),
):
    """更新指定用户信息（管理员权限）"""
    user_service = UserService(db)
    user_response = user_service.admin_update_user(user_id, user_data, current_user.id)
    
    return success_response(
        data=user_response.dict(),
        message="用户信息更新成功"
    )


@router.delete("/{user_id}")
async def delete_user_by_id(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database),
):
    """删除指定用户（管理员权限）"""
    user_service = UserService(db)
    success = user_service.delete_user(user_id, current_user.id)
    
    if success:
        return deleted_response(message="用户删除成功")


@router.post("/batch-operation")
async def batch_user_operation(
    operation_data: BatchUserOperation,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database),
):
    """批量用户操作（管理员权限）"""
    user_service = UserService(db)
    result = user_service.batch_user_operation(operation_data, current_user.id)
    
    return success_response(
        data=result,
        message=f"批量操作完成，成功: {result['success_count']}, 失败: {result['failed_count']}"
    )


@router.put("/{user_id}/role")
async def change_user_role(
    user_id: int,
    new_role: UserRole,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database),
):
    """修改用户角色（管理员权限）"""
    user_service = UserService(db)
    user_response = user_service.change_user_role(user_id, new_role, current_user.id)
    
    return success_response(
        data=user_response.dict(),
        message="用户角色修改成功"
    )


@router.get("/{user_id}/sessions")
async def get_user_sessions(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database),
):
    """获取用户会话列表（管理员权限）"""
    user_service = UserService(db)
    sessions = user_service.get_user_sessions(user_id)
    
    return success_response(
        data=sessions,
        message="获取用户会话成功"
    )


@router.delete("/{user_id}/sessions")
async def revoke_user_sessions(
    user_id: int,
    session_ids: Optional[List[int]] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database),
):
    """撤销用户会话（管理员权限）"""
    user_service = UserService(db)
    revoked_count = user_service.revoke_user_sessions(user_id, session_ids)
    
    return success_response(
        data={"revoked_count": revoked_count},
        message=f"成功撤销 {revoked_count} 个会话"
    )


@router.get("/me/sessions")
async def get_my_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """获取当前用户会话列表"""
    user_service = UserService(db)
    sessions = user_service.get_user_sessions(current_user.id)
    
    return success_response(
        data=sessions,
        message="获取会话列表成功"
    )


@router.delete("/me/sessions")
async def revoke_my_sessions(
    session_ids: Optional[List[int]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """撤销当前用户会话"""
    user_service = UserService(db)
    revoked_count = user_service.revoke_user_sessions(current_user.id, session_ids)
    
    return success_response(
        data={"revoked_count": revoked_count},
        message=f"成功撤销 {revoked_count} 个会话"
    )