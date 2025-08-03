"""
角色管理服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from ..models.role import Role, Permission, UserRoleAssignment, PermissionConstants, RoleConstants
from ..models.user import User
from ..schemas.role import (
    RoleCreate, RoleUpdate, PermissionCreate, PermissionUpdate,
    UserRoleAssignmentCreate, UserRoleAssignmentUpdate,
    RolePermissionBatch, UserRoleBatch
)
from ..core.exceptions import ValidationError, NotFoundError, ConflictError

class RoleService:
    """角色管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # 角色管理
    def create_role(self, role_data: RoleCreate, creator_id: int) -> Role:
        """创建角色"""
        # 检查角色名称是否已存在
        existing_role = self.db.query(Role).filter(Role.name == role_data.name).first()
        if existing_role:
            raise ConflictError(f"角色名称 '{role_data.name}' 已存在")
        
        # 验证权限是否存在
        if role_data.permissions:
            self._validate_permissions(role_data.permissions)
        
        role = Role(
            name=role_data.name,
            display_name=role_data.display_name,
            description=role_data.description,
            permissions=role_data.permissions,
            is_active=role_data.is_active,
            priority=role_data.priority,
            config=role_data.config,
            created_by=creator_id
        )
        
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def get_role(self, role_id: int) -> Role:
        """获取角色"""
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFoundError(f"角色 ID {role_id} 不存在")
        return role
    
    def get_role_by_name(self, name: str) -> Optional[Role]:
        """根据名称获取角色"""
        return self.db.query(Role).filter(Role.name == name).first()
    
    def get_roles(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        is_system: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Role], int]:
        """获取角色列表"""
        query = self.db.query(Role)
        
        # 过滤条件
        if is_active is not None:
            query = query.filter(Role.is_active == is_active)
        if is_system is not None:
            query = query.filter(Role.is_system == is_system)
        if search:
            query = query.filter(
                or_(
                    Role.name.ilike(f"%{search}%"),
                    Role.display_name.ilike(f"%{search}%"),
                    Role.description.ilike(f"%{search}%")
                )
            )
        
        # 获取总数
        total = query.count()
        
        # 分页和排序
        roles = query.order_by(Role.priority.desc(), Role.created_at.desc()).offset(skip).limit(limit).all()
        
        return roles, total
    
    def update_role(self, role_id: int, role_data: RoleUpdate) -> Role:
        """更新角色"""
        role = self.get_role(role_id)
        
        # 检查是否为系统角色
        if role.is_system:
            raise ValidationError("系统角色不能修改")
        
        # 验证权限
        if role_data.permissions is not None:
            self._validate_permissions(role_data.permissions)
        
        # 更新字段
        update_data = role_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(role, field, value)
        
        role.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def delete_role(self, role_id: int) -> bool:
        """删除角色"""
        role = self.get_role(role_id)
        
        # 检查是否为系统角色
        if role.is_system:
            raise ValidationError("系统角色不能删除")
        
        # 检查是否有用户使用该角色
        user_count = self.db.query(UserRoleAssignment).filter(
            and_(
                UserRoleAssignment.role_id == role_id,
                UserRoleAssignment.is_active == True
            )
        ).count()
        
        if user_count > 0:
            raise ValidationError(f"角色正在被 {user_count} 个用户使用，无法删除")
        
        self.db.delete(role)
        self.db.commit()
        return True
    
    # 权限管理
    def create_permission(self, permission_data: PermissionCreate) -> Permission:
        """创建权限"""
        # 检查权限名称是否已存在
        existing_permission = self.db.query(Permission).filter(
            Permission.name == permission_data.name
        ).first()
        if existing_permission:
            raise ConflictError(f"权限名称 '{permission_data.name}' 已存在")
        
        permission = Permission(**permission_data.dict())
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        return permission
    
    def get_permission(self, permission_id: int) -> Permission:
        """获取权限"""
        permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
        if not permission:
            raise NotFoundError(f"权限 ID {permission_id} 不存在")
        return permission
    
    def get_permissions(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        resource: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Permission], int]:
        """获取权限列表"""
        query = self.db.query(Permission)
        
        # 过滤条件
        if category:
            query = query.filter(Permission.category == category)
        if resource:
            query = query.filter(Permission.resource == resource)
        if is_active is not None:
            query = query.filter(Permission.is_active == is_active)
        if search:
            query = query.filter(
                or_(
                    Permission.name.ilike(f"%{search}%"),
                    Permission.display_name.ilike(f"%{search}%"),
                    Permission.description.ilike(f"%{search}%")
                )
            )
        
        # 获取总数
        total = query.count()
        
        # 分页和排序
        permissions = query.order_by(
            Permission.category, Permission.resource, Permission.action
        ).offset(skip).limit(limit).all()
        
        return permissions, total
    
    def update_permission(self, permission_id: int, permission_data: PermissionUpdate) -> Permission:
        """更新权限"""
        permission = self.get_permission(permission_id)
        
        # 检查是否为系统权限
        if permission.is_system:
            raise ValidationError("系统权限不能修改")
        
        # 更新字段
        update_data = permission_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(permission, field, value)
        
        permission.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(permission)
        return permission
    
    def delete_permission(self, permission_id: int) -> bool:
        """删除权限"""
        permission = self.get_permission(permission_id)
        
        # 检查是否为系统权限
        if permission.is_system:
            raise ValidationError("系统权限不能删除")
        
        # 检查是否有角色使用该权限
        roles_with_permission = self.db.query(Role).filter(
            Role.permissions.contains([permission.name])
        ).count()
        
        if roles_with_permission > 0:
            raise ValidationError(f"权限正在被 {roles_with_permission} 个角色使用，无法删除")
        
        self.db.delete(permission)
        self.db.commit()
        return True
    
    # 用户角色分配
    def assign_role_to_user(
        self,
        user_id: int,
        role_id: int,
        assignment_data: UserRoleAssignmentCreate,
        assigner_id: int
    ) -> UserRoleAssignment:
        """为用户分配角色"""
        # 验证用户和角色是否存在
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError(f"用户 ID {user_id} 不存在")
        
        role = self.get_role(role_id)
        if not role.is_active:
            raise ValidationError("不能分配未激活的角色")
        
        # 检查是否已经分配
        existing_assignment = self.db.query(UserRoleAssignment).filter(
            and_(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.role_id == role_id,
                UserRoleAssignment.is_active == True
            )
        ).first()
        
        if existing_assignment:
            raise ConflictError("用户已经拥有该角色")
        
        assignment = UserRoleAssignment(
            user_id=user_id,
            role_id=role_id,
            expires_at=assignment_data.expires_at,
            reason=assignment_data.reason,
            notes=assignment_data.notes,
            assigned_by=assigner_id
        )
        
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment
    
    def revoke_role_from_user(self, user_id: int, role_id: int) -> bool:
        """撤销用户角色"""
        assignment = self.db.query(UserRoleAssignment).filter(
            and_(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.role_id == role_id,
                UserRoleAssignment.is_active == True
            )
        ).first()
        
        if not assignment:
            raise NotFoundError("用户角色分配不存在")
        
        assignment.is_active = False
        self.db.commit()
        return True
    
    def get_user_roles(self, user_id: int) -> List[Role]:
        """获取用户角色"""
        return self.db.query(Role).join(UserRoleAssignment).filter(
            and_(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.is_active == True,
                Role.is_active == True
            )
        ).order_by(Role.priority.desc()).all()
    
    def get_role_users(self, role_id: int) -> List[User]:
        """获取角色用户"""
        return self.db.query(User).join(UserRoleAssignment).filter(
            and_(
                UserRoleAssignment.role_id == role_id,
                UserRoleAssignment.is_active == True,
                User.is_active == True
            )
        ).all()
    
    # 权限检查
    def check_user_permission(self, user_id: int, permission: str) -> bool:
        """检查用户权限"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return False
        
        return user.has_permission(permission)
    
    def check_user_permissions(self, user_id: int, permissions: List[str]) -> Dict[str, bool]:
        """批量检查用户权限"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return {perm: False for perm in permissions}
        
        result = {}
        for permission in permissions:
            result[permission] = user.has_permission(permission)
        
        return result
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """获取用户所有权限"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return []
        
        return user.get_all_permissions()
    
    # 批量操作
    def batch_assign_roles(self, batch_data: UserRoleBatch, assigner_id: int) -> Dict[str, Any]:
        """批量分配角色"""
        results = {
            'success': [],
            'failed': [],
            'total': len(batch_data.user_ids) * len(batch_data.role_ids)
        }
        
        for user_id in batch_data.user_ids:
            for role_id in batch_data.role_ids:
                try:
                    if batch_data.action == 'assign':
                        assignment_data = UserRoleAssignmentCreate(
                            user_id=user_id,
                            role_id=role_id,
                            expires_at=batch_data.expires_at,
                            reason=batch_data.reason
                        )
                        self.assign_role_to_user(user_id, role_id, assignment_data, assigner_id)
                    elif batch_data.action == 'revoke':
                        self.revoke_role_from_user(user_id, role_id)
                    
                    results['success'].append({'user_id': user_id, 'role_id': role_id})
                except Exception as e:
                    results['failed'].append({
                        'user_id': user_id,
                        'role_id': role_id,
                        'error': str(e)
                    })
        
        return results
    
    def batch_update_role_permissions(self, batch_data: RolePermissionBatch) -> Dict[str, Any]:
        """批量更新角色权限"""
        results = {
            'success': [],
            'failed': [],
            'total': len(batch_data.role_ids)
        }
        
        # 验证权限
        self._validate_permissions(batch_data.permissions)
        
        for role_id in batch_data.role_ids:
            try:
                role = self.get_role(role_id)
                
                if role.is_system:
                    raise ValidationError("系统角色不能修改权限")
                
                current_permissions = set(role.permissions or [])
                new_permissions = set(batch_data.permissions)
                
                if batch_data.action == 'add':
                    updated_permissions = list(current_permissions | new_permissions)
                elif batch_data.action == 'remove':
                    updated_permissions = list(current_permissions - new_permissions)
                elif batch_data.action == 'replace':
                    updated_permissions = list(new_permissions)
                
                role.permissions = updated_permissions
                role.updated_at = datetime.now()
                
                results['success'].append({'role_id': role_id, 'permissions': updated_permissions})
            except Exception as e:
                results['failed'].append({
                    'role_id': role_id,
                    'error': str(e)
                })
        
        self.db.commit()
        return results
    
    # 统计信息
    def get_role_stats(self) -> Dict[str, Any]:
        """获取角色统计信息"""
        total_roles = self.db.query(Role).count()
        active_roles = self.db.query(Role).filter(Role.is_active == True).count()
        system_roles = self.db.query(Role).filter(Role.is_system == True).count()
        custom_roles = total_roles - system_roles
        
        return {
            'total_roles': total_roles,
            'active_roles': active_roles,
            'system_roles': system_roles,
            'custom_roles': custom_roles
        }
    
    def get_permission_stats(self) -> Dict[str, Any]:
        """获取权限统计信息"""
        total_permissions = self.db.query(Permission).count()
        active_permissions = self.db.query(Permission).filter(Permission.is_active == True).count()
        system_permissions = self.db.query(Permission).filter(Permission.is_system == True).count()
        
        # 按分类统计
        category_stats = self.db.query(
            Permission.category,
            func.count(Permission.id)
        ).group_by(Permission.category).all()
        
        # 按资源统计
        resource_stats = self.db.query(
            Permission.resource,
            func.count(Permission.id)
        ).group_by(Permission.resource).all()
        
        return {
            'total_permissions': total_permissions,
            'active_permissions': active_permissions,
            'system_permissions': system_permissions,
            'permissions_by_category': dict(category_stats),
            'permissions_by_resource': dict(resource_stats)
        }
    
    # 初始化系统角色和权限
    def initialize_system_roles_and_permissions(self):
        """初始化系统角色和权限"""
        # 创建系统权限
        self._create_system_permissions()
        # 创建系统角色
        self._create_system_roles()
    
    def _create_system_permissions(self):
        """创建系统权限"""
        permissions_data = [
            # 用户管理权限
            {'name': PermissionConstants.USER_VIEW, 'display_name': '查看用户', 'category': '用户管理', 'resource': 'user', 'action': 'view'},
            {'name': PermissionConstants.USER_CREATE, 'display_name': '创建用户', 'category': '用户管理', 'resource': 'user', 'action': 'create'},
            {'name': PermissionConstants.USER_UPDATE, 'display_name': '更新用户', 'category': '用户管理', 'resource': 'user', 'action': 'update'},
            {'name': PermissionConstants.USER_DELETE, 'display_name': '删除用户', 'category': '用户管理', 'resource': 'user', 'action': 'delete'},
            {'name': PermissionConstants.USER_MANAGE_ROLES, 'display_name': '管理用户角色', 'category': '用户管理', 'resource': 'user', 'action': 'manage_roles'},
            
            # 策略管理权限
            {'name': PermissionConstants.STRATEGY_VIEW, 'display_name': '查看策略', 'category': '策略管理', 'resource': 'strategy', 'action': 'view'},
            {'name': PermissionConstants.STRATEGY_CREATE, 'display_name': '创建策略', 'category': '策略管理', 'resource': 'strategy', 'action': 'create'},
            {'name': PermissionConstants.STRATEGY_UPDATE, 'display_name': '更新策略', 'category': '策略管理', 'resource': 'strategy', 'action': 'update'},
            {'name': PermissionConstants.STRATEGY_DELETE, 'display_name': '删除策略', 'category': '策略管理', 'resource': 'strategy', 'action': 'delete'},
            {'name': PermissionConstants.STRATEGY_PUBLISH, 'display_name': '发布策略', 'category': '策略管理', 'resource': 'strategy', 'action': 'publish'},
            {'name': PermissionConstants.STRATEGY_EXECUTE, 'display_name': '执行策略', 'category': '策略管理', 'resource': 'strategy', 'action': 'execute'},
            
            # 回测管理权限
            {'name': PermissionConstants.BACKTEST_VIEW, 'display_name': '查看回测', 'category': '回测管理', 'resource': 'backtest', 'action': 'view'},
            {'name': PermissionConstants.BACKTEST_CREATE, 'display_name': '创建回测', 'category': '回测管理', 'resource': 'backtest', 'action': 'create'},
            {'name': PermissionConstants.BACKTEST_UPDATE, 'display_name': '更新回测', 'category': '回测管理', 'resource': 'backtest', 'action': 'update'},
            {'name': PermissionConstants.BACKTEST_DELETE, 'display_name': '删除回测', 'category': '回测管理', 'resource': 'backtest', 'action': 'delete'},
            {'name': PermissionConstants.BACKTEST_EXECUTE, 'display_name': '执行回测', 'category': '回测管理', 'resource': 'backtest', 'action': 'execute'},
            
            # 订单管理权限
            {'name': PermissionConstants.ORDER_VIEW, 'display_name': '查看订单', 'category': '订单管理', 'resource': 'order', 'action': 'view'},
            {'name': PermissionConstants.ORDER_CREATE, 'display_name': '创建订单', 'category': '订单管理', 'resource': 'order', 'action': 'create'},
            {'name': PermissionConstants.ORDER_UPDATE, 'display_name': '更新订单', 'category': '订单管理', 'resource': 'order', 'action': 'update'},
            {'name': PermissionConstants.ORDER_DELETE, 'display_name': '删除订单', 'category': '订单管理', 'resource': 'order', 'action': 'delete'},
            {'name': PermissionConstants.ORDER_EXECUTE, 'display_name': '执行订单', 'category': '订单管理', 'resource': 'order', 'action': 'execute'},
            {'name': PermissionConstants.ORDER_CANCEL, 'display_name': '取消订单', 'category': '订单管理', 'resource': 'order', 'action': 'cancel'},
            
            # 其他权限...
            {'name': PermissionConstants.ADMIN_ALL, 'display_name': '管理员权限', 'category': '系统管理', 'resource': 'admin', 'action': '*'},
        ]
        
        for perm_data in permissions_data:
            existing = self.db.query(Permission).filter(Permission.name == perm_data['name']).first()
            if not existing:
                permission = Permission(
                    **perm_data,
                    is_system=True,
                    description=f"系统权限: {perm_data['display_name']}"
                )
                self.db.add(permission)
        
        self.db.commit()
    
    def _create_system_roles(self):
        """创建系统角色"""
        roles_data = [
            {
                'name': RoleConstants.SUPER_ADMIN,
                'display_name': '超级管理员',
                'description': '拥有所有权限的超级管理员',
                'permissions': [PermissionConstants.ADMIN_ALL],
                'priority': 1000
            },
            {
                'name': RoleConstants.ADMIN,
                'display_name': '管理员',
                'description': '系统管理员，拥有大部分管理权限',
                'permissions': [
                    PermissionConstants.USER_VIEW, PermissionConstants.USER_CREATE,
                    PermissionConstants.USER_UPDATE, PermissionConstants.USER_MANAGE_ROLES,
                    PermissionConstants.STRATEGY_VIEW, PermissionConstants.STRATEGY_CREATE,
                    PermissionConstants.STRATEGY_UPDATE, PermissionConstants.STRATEGY_PUBLISH,
                    PermissionConstants.BACKTEST_VIEW, PermissionConstants.BACKTEST_CREATE,
                    PermissionConstants.BACKTEST_EXECUTE,
                    PermissionConstants.ORDER_VIEW, PermissionConstants.ORDER_CREATE,
                    PermissionConstants.ORDER_UPDATE, PermissionConstants.ORDER_CANCEL
                ],
                'priority': 900
            },
            {
                'name': RoleConstants.TRADER,
                'display_name': '交易员',
                'description': '专业交易员，拥有交易相关权限',
                'permissions': [
                    PermissionConstants.STRATEGY_VIEW, PermissionConstants.STRATEGY_EXECUTE,
                    PermissionConstants.BACKTEST_VIEW, PermissionConstants.BACKTEST_CREATE,
                    PermissionConstants.BACKTEST_EXECUTE,
                    PermissionConstants.ORDER_VIEW, PermissionConstants.ORDER_CREATE,
                    PermissionConstants.ORDER_UPDATE, PermissionConstants.ORDER_CANCEL,
                    PermissionConstants.POSITION_VIEW, PermissionConstants.ACCOUNT_VIEW
                ],
                'priority': 700
            },
            {
                'name': RoleConstants.STRATEGY_DEVELOPER,
                'display_name': '策略开发者',
                'description': '策略开发人员，专注于策略开发和回测',
                'permissions': [
                    PermissionConstants.STRATEGY_VIEW, PermissionConstants.STRATEGY_CREATE,
                    PermissionConstants.STRATEGY_UPDATE, PermissionConstants.STRATEGY_DELETE,
                    PermissionConstants.BACKTEST_VIEW, PermissionConstants.BACKTEST_CREATE,
                    PermissionConstants.BACKTEST_UPDATE, PermissionConstants.BACKTEST_DELETE,
                    PermissionConstants.BACKTEST_EXECUTE
                ],
                'priority': 600
            },
            {
                'name': RoleConstants.VIEWER,
                'display_name': '只读用户',
                'description': '只读权限用户，只能查看数据',
                'permissions': [
                    PermissionConstants.STRATEGY_VIEW,
                    PermissionConstants.BACKTEST_VIEW,
                    PermissionConstants.ORDER_VIEW,
                    PermissionConstants.POSITION_VIEW,
                    PermissionConstants.ACCOUNT_VIEW
                ],
                'priority': 100
            }
        ]
        
        for role_data in roles_data:
            existing = self.db.query(Role).filter(Role.name == role_data['name']).first()
            if not existing:
                role = Role(
                    **role_data,
                    is_system=True
                )
                self.db.add(role)
        
        self.db.commit()
    
    def _validate_permissions(self, permissions: List[str]):
        """验证权限是否存在"""
        if not permissions:
            return
        
        existing_permissions = self.db.query(Permission.name).filter(
            Permission.name.in_(permissions)
        ).all()
        existing_names = {perm.name for perm in existing_permissions}
        
        invalid_permissions = set(permissions) - existing_names
        if invalid_permissions:
            raise ValidationError(f"以下权限不存在: {', '.join(invalid_permissions)}")