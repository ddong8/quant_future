"""
角色和权限数据验证模式
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime

class PermissionBase(BaseModel):
    """权限基础模式"""
    name: str = Field(..., description="权限名称")
    display_name: str = Field(..., description="权限显示名称")
    description: Optional[str] = Field(None, description="权限描述")
    category: str = Field(..., description="权限分类")
    resource: str = Field(..., description="资源类型")
    action: str = Field(..., description="操作类型")
    is_active: bool = Field(True, description="是否激活")
    priority: int = Field(0, description="优先级")

class PermissionCreate(PermissionBase):
    """创建权限模式"""
    pass

class PermissionUpdate(BaseModel):
    """更新权限模式"""
    display_name: Optional[str] = Field(None, description="权限显示名称")
    description: Optional[str] = Field(None, description="权限描述")
    category: Optional[str] = Field(None, description="权限分类")
    is_active: Optional[bool] = Field(None, description="是否激活")
    priority: Optional[int] = Field(None, description="优先级")

class PermissionResponse(PermissionBase):
    """权限响应模式"""
    id: int
    is_system: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    """角色基础模式"""
    name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    display_name: str = Field(..., min_length=1, max_length=100, description="角色显示名称")
    description: Optional[str] = Field(None, description="角色描述")
    permissions: List[str] = Field(default_factory=list, description="权限列表")
    is_active: bool = Field(True, description="是否激活")
    priority: int = Field(0, description="角色优先级")
    config: Dict[str, Any] = Field(default_factory=dict, description="角色配置")

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('角色名称不能为空')
        # 检查角色名称格式
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('角色名称只能包含字母、数字、下划线和连字符')
        return v.strip().lower()

    @validator('permissions')
    def validate_permissions(cls, v):
        if not isinstance(v, list):
            raise ValueError('权限必须是列表格式')
        # 去重并过滤空值
        return list(set(filter(None, v)))

class RoleCreate(RoleBase):
    """创建角色模式"""
    pass

class RoleUpdate(BaseModel):
    """更新角色模式"""
    display_name: Optional[str] = Field(None, description="角色显示名称")
    description: Optional[str] = Field(None, description="角色描述")
    permissions: Optional[List[str]] = Field(None, description="权限列表")
    is_active: Optional[bool] = Field(None, description="是否激活")
    priority: Optional[int] = Field(None, description="角色优先级")
    config: Optional[Dict[str, Any]] = Field(None, description="角色配置")

    @validator('permissions')
    def validate_permissions(cls, v):
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('权限必须是列表格式')
            # 去重并过滤空值
            return list(set(filter(None, v)))
        return v

class RoleResponse(RoleBase):
    """角色响应模式"""
    id: int
    is_system: bool
    created_at: datetime
    updated_at: datetime
    user_count: int = Field(0, description="用户数量")

    class Config:
        from_attributes = True

class UserRoleAssignmentBase(BaseModel):
    """用户角色分配基础模式"""
    user_id: int = Field(..., description="用户ID")
    role_id: int = Field(..., description="角色ID")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    reason: Optional[str] = Field(None, max_length=200, description="分配原因")
    notes: Optional[str] = Field(None, description="备注")

class UserRoleAssignmentCreate(UserRoleAssignmentBase):
    """创建用户角色分配模式"""
    pass

class UserRoleAssignmentUpdate(BaseModel):
    """更新用户角色分配模式"""
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_active: Optional[bool] = Field(None, description="是否激活")
    reason: Optional[str] = Field(None, max_length=200, description="分配原因")
    notes: Optional[str] = Field(None, description="备注")

class UserRoleAssignmentResponse(UserRoleAssignmentBase):
    """用户角色分配响应模式"""
    id: int
    assigned_at: datetime
    assigned_by: Optional[int]
    is_active: bool
    is_expired: bool
    is_valid: bool
    role: Optional[RoleResponse]
    assigner: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

class RolePermissionBatch(BaseModel):
    """批量角色权限操作模式"""
    role_ids: List[int] = Field(..., description="角色ID列表")
    permissions: List[str] = Field(..., description="权限列表")
    action: str = Field(..., description="操作类型: add, remove, replace")

    @validator('action')
    def validate_action(cls, v):
        if v not in ['add', 'remove', 'replace']:
            raise ValueError('操作类型必须是 add, remove 或 replace')
        return v

class UserRoleBatch(BaseModel):
    """批量用户角色操作模式"""
    user_ids: List[int] = Field(..., description="用户ID列表")
    role_ids: List[int] = Field(..., description="角色ID列表")
    action: str = Field(..., description="操作类型: assign, revoke")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    reason: Optional[str] = Field(None, max_length=200, description="操作原因")

    @validator('action')
    def validate_action(cls, v):
        if v not in ['assign', 'revoke']:
            raise ValueError('操作类型必须是 assign 或 revoke')
        return v

class PermissionCheckRequest(BaseModel):
    """权限检查请求模式"""
    user_id: int = Field(..., description="用户ID")
    permissions: List[str] = Field(..., description="需要检查的权限列表")

class PermissionCheckResponse(BaseModel):
    """权限检查响应模式"""
    user_id: int
    permissions: Dict[str, bool] = Field(..., description="权限检查结果")
    has_all: bool = Field(..., description="是否拥有所有权限")

class RoleStatsResponse(BaseModel):
    """角色统计响应模式"""
    total_roles: int
    active_roles: int
    system_roles: int
    custom_roles: int
    roles_by_category: Dict[str, int]

class PermissionStatsResponse(BaseModel):
    """权限统计响应模式"""
    total_permissions: int
    active_permissions: int
    system_permissions: int
    permissions_by_category: Dict[str, int]
    permissions_by_resource: Dict[str, int]

class UserPermissionSummary(BaseModel):
    """用户权限摘要"""
    user_id: int
    username: str
    roles: List[RoleResponse]
    permissions: List[str]
    effective_permissions: List[str]
    last_updated: datetime

    class Config:
        from_attributes = True