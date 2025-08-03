"""
角色和权限数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..core.database import Base


class Permission(Base):
    """权限模型"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)
    resource = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    is_system = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Permission(name='{self.name}', display_name='{self.display_name}')>"


class Role(Base):
    """角色模型"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, default=list)
    is_system = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    user_assignments = relationship("UserRoleAssignment", back_populates="role", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Role(name='{self.name}', display_name='{self.display_name}')>"

    @property
    def user_count(self) -> int:
        """获取拥有此角色的用户数量"""
        return len([assignment for assignment in self.user_assignments if assignment.is_active])

    def has_permission(self, permission: str) -> bool:
        """检查角色是否拥有指定权限"""
        if not self.is_active:
            return False
        return permission in (self.permissions or [])

    def add_permission(self, permission: str) -> None:
        """添加权限"""
        if not self.permissions:
            self.permissions = []
        if permission not in self.permissions:
            self.permissions.append(permission)

    def remove_permission(self, permission: str) -> None:
        """移除权限"""
        if self.permissions and permission in self.permissions:
            self.permissions.remove(permission)


class UserRoleAssignment(Base):
    """用户角色分配模型"""
    __tablename__ = "user_role_assignments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at = Column(DateTime, server_default=func.now())
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    reason = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)

    # 关系
    user = relationship("User", foreign_keys=[user_id], back_populates="role_assignments")
    role = relationship("Role", back_populates="user_assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])

    def __repr__(self):
        return f"<UserRoleAssignment(user_id={self.user_id}, role_id={self.role_id})>"

    @property
    def is_expired(self) -> bool:
        """检查分配是否已过期"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """检查分配是否有效（激活且未过期）"""
        return self.is_active and not self.is_expired


# 权限常量
class PermissionConstants:
    """权限常量定义"""
    
    # 用户管理权限
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_MANAGE = "user:manage"
    USER_MANAGE_ROLES = "user:manage_roles"
    
    # 角色管理权限
    ROLE_VIEW = "role:view"
    ROLE_CREATE = "role:create"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"
    ROLE_ASSIGN = "role:assign"
    
    # 策略管理权限
    STRATEGY_VIEW = "strategy:view"
    STRATEGY_CREATE = "strategy:create"
    STRATEGY_UPDATE = "strategy:update"
    STRATEGY_DELETE = "strategy:delete"
    STRATEGY_EXECUTE = "strategy:execute"
    
    # 交易权限
    TRADE_VIEW = "trade:view"
    TRADE_CREATE = "trade:create"
    TRADE_UPDATE = "trade:update"
    TRADE_DELETE = "trade:delete"
    TRADE_EXECUTE = "trade:execute"
    
    # 持仓权限
    POSITION_VIEW = "position:view"
    POSITION_READ = "position:read"
    POSITION_CREATE = "position:create"
    POSITION_UPDATE = "position:update"
    POSITION_DELETE = "position:delete"
    POSITION_MANAGE = "position:manage"
    
    # 账户管理权限
    ACCOUNT_VIEW = "account:view"
    ACCOUNT_CREATE = "account:create"
    ACCOUNT_UPDATE = "account:update"
    ACCOUNT_DELETE = "account:delete"
    ACCOUNT_MANAGE = "account:manage"
    
    # 风险管理权限
    RISK_VIEW = "risk:view"
    RISK_CREATE = "risk:create"
    RISK_UPDATE = "risk:update"
    RISK_DELETE = "risk:delete"
    RISK_MANAGE = "risk:manage"
    
    # 系统管理权限
    SYSTEM_VIEW = "system:view"
    SYSTEM_MANAGE = "system:manage"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    ADMIN_ALL = "admin:all"
    
    # 报告权限
    REPORT_VIEW = "report:view"
    REPORT_CREATE = "report:create"
    REPORT_EXPORT = "report:export"
    
    # 数据管理权限
    DATA_VIEW = "data:view"
    DATA_CREATE = "data:create"
    DATA_UPDATE = "data:update"
    DATA_DELETE = "data:delete"
    DATA_MANAGE = "data:manage"
    DATA_EXPORT = "data:export"
    DATA_IMPORT = "data:import"


# 角色常量
class RoleConstants:
    """角色常量定义"""
    
    # 系统角色
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    TRADER = "trader"
    ANALYST = "analyst"
    VIEWER = "viewer"
    
    # 角色显示名称
    ROLE_DISPLAY_NAMES = {
        SUPER_ADMIN: "超级管理员",
        ADMIN: "管理员",
        TRADER: "交易员",
        ANALYST: "分析师",
        VIEWER: "查看者"
    }
    
    # 默认角色权限
    DEFAULT_PERMISSIONS = {
        SUPER_ADMIN: [
            # 拥有所有权限
            PermissionConstants.USER_MANAGE,
            PermissionConstants.ROLE_VIEW,
            PermissionConstants.ROLE_CREATE,
            PermissionConstants.ROLE_UPDATE,
            PermissionConstants.ROLE_DELETE,
            PermissionConstants.ROLE_ASSIGN,
            PermissionConstants.STRATEGY_VIEW,
            PermissionConstants.STRATEGY_CREATE,
            PermissionConstants.STRATEGY_UPDATE,
            PermissionConstants.STRATEGY_DELETE,
            PermissionConstants.STRATEGY_EXECUTE,
            PermissionConstants.TRADE_VIEW,
            PermissionConstants.TRADE_CREATE,
            PermissionConstants.TRADE_UPDATE,
            PermissionConstants.TRADE_DELETE,
            PermissionConstants.TRADE_EXECUTE,
            PermissionConstants.ACCOUNT_MANAGE,
            PermissionConstants.RISK_MANAGE,
            PermissionConstants.SYSTEM_MANAGE,
            PermissionConstants.REPORT_VIEW,
            PermissionConstants.REPORT_CREATE,
            PermissionConstants.REPORT_EXPORT,
        ],
        ADMIN: [
            PermissionConstants.USER_VIEW,
            PermissionConstants.USER_CREATE,
            PermissionConstants.USER_UPDATE,
            PermissionConstants.ROLE_VIEW,
            PermissionConstants.STRATEGY_VIEW,
            PermissionConstants.STRATEGY_CREATE,
            PermissionConstants.STRATEGY_UPDATE,
            PermissionConstants.TRADE_VIEW,
            PermissionConstants.TRADE_CREATE,
            PermissionConstants.TRADE_UPDATE,
            PermissionConstants.ACCOUNT_VIEW,
            PermissionConstants.ACCOUNT_CREATE,
            PermissionConstants.ACCOUNT_UPDATE,
            PermissionConstants.RISK_VIEW,
            PermissionConstants.RISK_CREATE,
            PermissionConstants.RISK_UPDATE,
            PermissionConstants.SYSTEM_VIEW,
            PermissionConstants.REPORT_VIEW,
            PermissionConstants.REPORT_CREATE,
            PermissionConstants.REPORT_EXPORT,
        ],
        TRADER: [
            PermissionConstants.STRATEGY_VIEW,
            PermissionConstants.STRATEGY_CREATE,
            PermissionConstants.STRATEGY_UPDATE,
            PermissionConstants.TRADE_VIEW,
            PermissionConstants.TRADE_CREATE,
            PermissionConstants.TRADE_UPDATE,
            PermissionConstants.TRADE_EXECUTE,
            PermissionConstants.ACCOUNT_VIEW,
            PermissionConstants.RISK_VIEW,
            PermissionConstants.REPORT_VIEW,
        ],
        ANALYST: [
            PermissionConstants.STRATEGY_VIEW,
            PermissionConstants.TRADE_VIEW,
            PermissionConstants.ACCOUNT_VIEW,
            PermissionConstants.RISK_VIEW,
            PermissionConstants.REPORT_VIEW,
            PermissionConstants.REPORT_CREATE,
            PermissionConstants.REPORT_EXPORT,
        ],
        VIEWER: [
            PermissionConstants.STRATEGY_VIEW,
            PermissionConstants.TRADE_VIEW,
            PermissionConstants.ACCOUNT_VIEW,
            PermissionConstants.RISK_VIEW,
            PermissionConstants.REPORT_VIEW,
        ]
    }