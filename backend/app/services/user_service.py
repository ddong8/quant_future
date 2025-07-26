"""
用户管理服务
"""
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import logging

from ..models import User, UserSession, UserRole
from ..core.security import security_manager
from ..core.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    AuthorizationError,
)
from ..core.dependencies import PaginationParams, SortParams
from ..schemas.user import (
    UserCreate,
    UserUpdate,
    UserAdminUpdate,
    UserResponse,
    UserListResponse,
    UserStatsResponse,
    UserSearchRequest,
    BatchUserOperation,
    UserPreferences,
)

logger = logging.getLogger(__name__)


class UserService:
    """用户管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(
        self,
        user_data: UserCreate,
        created_by_user_id: Optional[int] = None
    ) -> UserResponse:
        """创建用户"""
        # 检查用户名是否已存在
        existing_user = self.db.query(User).filter(
            User.username == user_data.username
        ).first()
        if existing_user:
            raise ConflictError("用户名已存在")
        
        # 检查邮箱是否已存在
        existing_email = self.db.query(User).filter(
            User.email == user_data.email
        ).first()
        if existing_email:
            raise ConflictError("邮箱已被注册")
        
        # 创建新用户
        hashed_password = security_manager.get_password_hash(user_data.password)
        
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            phone=user_data.phone,
            role=user_data.role,
            is_active=True,
            is_verified=False,
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        logger.info(f"用户创建成功: {new_user.username}, 创建者: {created_by_user_id}")
        
        return UserResponse.from_orm(new_user)
    
    def get_user_by_id(self, user_id: int) -> UserResponse:
        """根据ID获取用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("用户不存在")
        
        return UserResponse.from_orm(user)
    
    def get_user_by_username(self, username: str) -> UserResponse:
        """根据用户名获取用户"""
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            raise NotFoundError("用户不存在")
        
        return UserResponse.from_orm(user)
    
    def update_user(
        self,
        user_id: int,
        user_data: UserUpdate,
        updated_by_user_id: Optional[int] = None
    ) -> UserResponse:
        """更新用户信息"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("用户不存在")
        
        # 检查邮箱是否被其他用户使用
        if user_data.email and user_data.email != user.email:
            existing_email = self.db.query(User).filter(
                and_(User.email == user_data.email, User.id != user_id)
            ).first()
            if existing_email:
                raise ConflictError("邮箱已被其他用户使用")
        
        # 更新用户信息
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"用户信息更新成功: {user.username}, 更新者: {updated_by_user_id}")
        
        return UserResponse.from_orm(user)
    
    def admin_update_user(
        self,
        user_id: int,
        user_data: UserAdminUpdate,
        updated_by_user_id: int
    ) -> UserResponse:
        """管理员更新用户信息"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("用户不存在")
        
        # 检查邮箱是否被其他用户使用
        if user_data.email and user_data.email != user.email:
            existing_email = self.db.query(User).filter(
                and_(User.email == user_data.email, User.id != user_id)
            ).first()
            if existing_email:
                raise ConflictError("邮箱已被其他用户使用")
        
        # 更新用户信息
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"管理员更新用户信息: {user.username}, 管理员: {updated_by_user_id}")
        
        return UserResponse.from_orm(user)
    
    def delete_user(
        self,
        user_id: int,
        deleted_by_user_id: int
    ) -> bool:
        """删除用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("用户不存在")
        
        # 不能删除自己
        if user_id == deleted_by_user_id:
            raise ValidationError("不能删除自己的账户")
        
        # 软删除：设置为非活跃状态
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        # 使所有会话失效
        self.db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).update({"is_active": False})
        
        self.db.commit()
        
        logger.info(f"用户删除成功: {user.username}, 删除者: {deleted_by_user_id}")
        
        return True
    
    def get_users_list(
        self,
        search_params: Optional[UserSearchRequest] = None,
        pagination: Optional[PaginationParams] = None,
        sort_params: Optional[SortParams] = None
    ) -> Tuple[List[UserListResponse], int]:
        """获取用户列表"""
        query = self.db.query(User)
        
        # 应用搜索条件
        if search_params:
            if search_params.keyword:
                keyword = f"%{search_params.keyword}%"
                query = query.filter(
                    or_(
                        User.username.ilike(keyword),
                        User.email.ilike(keyword),
                        User.full_name.ilike(keyword)
                    )
                )
            
            if search_params.role:
                query = query.filter(User.role == search_params.role)
            
            if search_params.is_active is not None:
                query = query.filter(User.is_active == search_params.is_active)
            
            if search_params.is_verified is not None:
                query = query.filter(User.is_verified == search_params.is_verified)
            
            if search_params.created_after:
                query = query.filter(User.created_at >= search_params.created_after)
            
            if search_params.created_before:
                query = query.filter(User.created_at <= search_params.created_before)
        
        # 获取总数
        total = query.count()
        
        # 应用排序
        if sort_params:
            if hasattr(User, sort_params.sort_by):
                sort_column = getattr(User, sort_params.sort_by)
                if sort_params.sort_order == "asc":
                    query = query.order_by(sort_column)
                else:
                    query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(desc(User.created_at))
        
        # 应用分页
        if pagination:
            query = query.offset(pagination.offset).limit(pagination.page_size)
        
        users = query.all()
        user_list = [UserListResponse.from_orm(user) for user in users]
        
        return user_list, total
    
    def get_user_stats(self) -> UserStatsResponse:
        """获取用户统计信息"""
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # 基础统计
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        verified_users = self.db.query(User).filter(User.is_verified == True).count()
        
        # 角色统计
        admin_users = self.db.query(User).filter(User.role == UserRole.ADMIN).count()
        trader_users = self.db.query(User).filter(User.role == UserRole.TRADER).count()
        viewer_users = self.db.query(User).filter(User.role == UserRole.VIEWER).count()
        
        # 新用户统计
        new_users_today = self.db.query(User).filter(User.created_at >= today).count()
        new_users_this_week = self.db.query(User).filter(User.created_at >= week_ago).count()
        new_users_this_month = self.db.query(User).filter(User.created_at >= month_ago).count()
        
        return UserStatsResponse(
            total_users=total_users,
            active_users=active_users,
            verified_users=verified_users,
            admin_users=admin_users,
            trader_users=trader_users,
            viewer_users=viewer_users,
            new_users_today=new_users_today,
            new_users_this_week=new_users_this_week,
            new_users_this_month=new_users_this_month,
        )
    
    def batch_user_operation(
        self,
        operation_data: BatchUserOperation,
        operator_user_id: int
    ) -> Dict[str, Any]:
        """批量用户操作"""
        users = self.db.query(User).filter(User.id.in_(operation_data.user_ids)).all()
        
        if len(users) != len(operation_data.user_ids):
            found_ids = [user.id for user in users]
            missing_ids = [uid for uid in operation_data.user_ids if uid not in found_ids]
            raise NotFoundError(f"以下用户不存在: {missing_ids}")
        
        success_count = 0
        failed_count = 0
        errors = []
        
        for user in users:
            try:
                # 不能对自己执行某些操作
                if user.id == operator_user_id and operation_data.operation in ['deactivate', 'delete']:
                    errors.append(f"不能对自己执行{operation_data.operation}操作")
                    failed_count += 1
                    continue
                
                if operation_data.operation == 'activate':
                    user.is_active = True
                elif operation_data.operation == 'deactivate':
                    user.is_active = False
                    # 使会话失效
                    self.db.query(UserSession).filter(
                        UserSession.user_id == user.id
                    ).update({"is_active": False})
                elif operation_data.operation == 'verify':
                    user.is_verified = True
                elif operation_data.operation == 'delete':
                    user.is_active = False
                    # 使会话失效
                    self.db.query(UserSession).filter(
                        UserSession.user_id == user.id
                    ).update({"is_active": False})
                
                user.updated_at = datetime.utcnow()
                success_count += 1
                
            except Exception as e:
                errors.append(f"用户{user.username}: {str(e)}")
                failed_count += 1
        
        self.db.commit()
        
        logger.info(f"批量用户操作完成: {operation_data.operation}, 成功: {success_count}, 失败: {failed_count}")
        
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors,
        }
    
    def change_user_role(
        self,
        user_id: int,
        new_role: UserRole,
        changed_by_user_id: int
    ) -> UserResponse:
        """修改用户角色"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("用户不存在")
        
        # 不能修改自己的角色
        if user_id == changed_by_user_id:
            raise ValidationError("不能修改自己的角色")
        
        old_role = user.role
        user.role = new_role
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"用户角色修改: {user.username}, {old_role} -> {new_role}, 操作者: {changed_by_user_id}")
        
        return UserResponse.from_orm(user)
    
    def get_user_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户会话列表"""
        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
        ).order_by(desc(UserSession.last_accessed_at)).all()
        
        session_list = []
        for session in sessions:
            session_list.append({
                "id": session.id,
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "created_at": session.created_at,
                "last_accessed_at": session.last_accessed_at,
                "expires_at": session.expires_at,
            })
        
        return session_list
    
    def revoke_user_sessions(
        self,
        user_id: int,
        session_ids: Optional[List[int]] = None
    ) -> int:
        """撤销用户会话"""
        query = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
        )
        
        if session_ids:
            query = query.filter(UserSession.id.in_(session_ids))
        
        revoked_count = query.update({"is_active": False})
        self.db.commit()
        
        logger.info(f"撤销用户会话: user_id={user_id}, 撤销数量: {revoked_count}")
        
        return revoked_count