"""
认证服务
"""
from typing import Optional, Tuple, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import Request
import logging

from ..models import User, UserSession, UserRole
from ..core.security import (
    security_manager,
    jwt_manager,
    email_manager,
    TokenBlacklist,
)
from ..core.exceptions import (
    AuthenticationError,
    ValidationError,
    ConflictError,
    NotFoundError,
)
from ..core.database import get_redis_client
from ..schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest,
    UserProfile,
    SessionInfo,
)

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = get_redis_client()
        self.token_blacklist = TokenBlacklist(self.redis_client)
    
    def register_user(
        self,
        register_data: RegisterRequest,
        request: Optional[Request] = None
    ) -> UserProfile:
        """用户注册"""
        # 检查用户名是否已存在
        existing_user = self.db.query(User).filter(
            User.username == register_data.username
        ).first()
        if existing_user:
            raise ConflictError("用户名已存在")
        
        # 检查邮箱是否已存在
        existing_email = self.db.query(User).filter(
            User.email == register_data.email
        ).first()
        if existing_email:
            raise ConflictError("邮箱已被注册")
        
        # 创建新用户
        hashed_password = security_manager.get_password_hash(register_data.password)
        
        new_user = User(
            username=register_data.username,
            email=register_data.email,
            hashed_password=hashed_password,
            full_name=register_data.full_name,
            phone=register_data.phone,
            role=UserRole.TRADER,  # 默认角色为交易员
            is_active=True,
            is_verified=False,
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        # 发送验证邮件
        try:
            verification_token = security_manager.generate_random_token()
            # 将验证令牌存储到Redis，24小时过期
            self.redis_client.setex(
                f"email_verification:{verification_token}",
                86400,  # 24小时
                str(new_user.id)
            )
            
            email_manager.send_verification_email(
                new_user.email,
                verification_token
            )
        except Exception as e:
            logger.warning(f"发送验证邮件失败: {e}")
        
        logger.info(f"用户注册成功: {new_user.username}")
        
        return UserProfile.from_orm(new_user)
    
    def authenticate_user(
        self,
        login_data: LoginRequest,
        request: Optional[Request] = None
    ) -> TokenResponse:
        """用户认证登录"""
        # 查找用户
        user = self.db.query(User).filter(
            User.username == login_data.username
        ).first()
        
        if not user:
            raise AuthenticationError("用户名或密码错误")
        
        # 验证密码
        if not security_manager.verify_password(login_data.password, user.hashed_password):
            raise AuthenticationError("用户名或密码错误")
        
        # 检查用户状态
        if not user.is_active:
            raise AuthenticationError("用户账户已被禁用")
        
        # 生成JWT令牌
        access_token = jwt_manager.create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role}
        )
        
        refresh_token = jwt_manager.create_refresh_token(
            data={"sub": str(user.id), "username": user.username}
        )
        
        # 创建用户会话记录
        session = UserSession(
            user_id=user.id,
            session_token=security_manager.hash_token(access_token),
            refresh_token=security_manager.hash_token(refresh_token),
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            expires_at=datetime.utcnow() + timedelta(days=7),  # 会话7天过期
        )
        
        self.db.add(session)
        
        # 更新用户最后登录时间
        user.last_login_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(f"用户登录成功: {user.username}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=60 * 30,  # 30分钟
            user_id=user.id,
            username=user.username,
            role=user.role,
        )
    
    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """刷新访问令牌"""
        try:
            # 验证刷新令牌
            payload = jwt_manager.verify_token(refresh_token, "refresh")
            user_id = int(payload.get("sub"))
            
            # 检查令牌是否在黑名单中
            if self.token_blacklist.is_blacklisted(refresh_token):
                raise AuthenticationError("刷新令牌已失效")
            
            # 查找用户
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                raise AuthenticationError("用户不存在或已被禁用")
            
            # 验证会话
            session = self.db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.refresh_token == security_manager.hash_token(refresh_token),
                UserSession.is_active == True,
            ).first()
            
            if not session:
                raise AuthenticationError("会话不存在或已失效")
            
            # 生成新的访问令牌
            new_access_token = jwt_manager.create_access_token(
                data={"sub": str(user.id), "username": user.username, "role": user.role}
            )
            
            # 更新会话记录
            session.session_token = security_manager.hash_token(new_access_token)
            session.last_accessed_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"令牌刷新成功: {user.username}")
            
            return TokenResponse(
                access_token=new_access_token,
                refresh_token=refresh_token,  # 刷新令牌保持不变
                expires_in=60 * 30,  # 30分钟
                user_id=user.id,
                username=user.username,
                role=user.role,
            )
            
        except Exception as e:
            logger.error(f"令牌刷新失败: {e}")
            raise AuthenticationError("刷新令牌无效")
    
    def logout_user(
        self,
        user_id: int,
        access_token: str,
        all_sessions: bool = False
    ) -> bool:
        """用户登出"""
        try:
            # 将访问令牌加入黑名单
            token_expiry = jwt_manager.get_token_expiry(access_token)
            if token_expiry:
                self.token_blacklist.add_token(access_token, token_expiry)
            
            if all_sessions:
                # 登出所有会话
                sessions = self.db.query(UserSession).filter(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True,
                ).all()
                
                for session in sessions:
                    session.is_active = False
                    # 将刷新令牌也加入黑名单
                    if session.expires_at > datetime.utcnow():
                        # 这里需要反向查找原始令牌，简化处理直接设置会话无效
                        pass
            else:
                # 只登出当前会话
                session = self.db.query(UserSession).filter(
                    UserSession.user_id == user_id,
                    UserSession.session_token == security_manager.hash_token(access_token),
                    UserSession.is_active == True,
                ).first()
                
                if session:
                    session.is_active = False
            
            self.db.commit()
            
            logger.info(f"用户登出成功: user_id={user_id}, all_sessions={all_sessions}")
            return True
            
        except Exception as e:
            logger.error(f"用户登出失败: {e}")
            return False
    
    def verify_email(self, token: str) -> bool:
        """验证邮箱"""
        try:
            # 从Redis获取用户ID
            user_id_str = self.redis_client.get(f"email_verification:{token}")
            if not user_id_str:
                raise ValidationError("验证令牌无效或已过期")
            
            user_id = int(user_id_str)
            
            # 更新用户验证状态
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise NotFoundError("用户不存在")
            
            user.is_verified = True
            self.db.commit()
            
            # 删除验证令牌
            self.redis_client.delete(f"email_verification:{token}")
            
            logger.info(f"邮箱验证成功: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"邮箱验证失败: {e}")
            raise ValidationError("邮箱验证失败")
    
    def request_password_reset(self, email: str) -> bool:
        """请求密码重置"""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            # 为了安全，不透露用户是否存在
            return True
        
        try:
            # 生成重置令牌
            reset_token = security_manager.generate_random_token()
            
            # 存储到Redis，1小时过期
            self.redis_client.setex(
                f"password_reset:{reset_token}",
                3600,  # 1小时
                str(user.id)
            )
            
            # 发送重置邮件
            email_manager.send_password_reset_email(user.email, reset_token)
            
            logger.info(f"密码重置邮件已发送: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"发送密码重置邮件失败: {e}")
            return False
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """重置密码"""
        try:
            # 从Redis获取用户ID
            user_id_str = self.redis_client.get(f"password_reset:{token}")
            if not user_id_str:
                raise ValidationError("重置令牌无效或已过期")
            
            user_id = int(user_id_str)
            
            # 更新用户密码
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise NotFoundError("用户不存在")
            
            user.hashed_password = security_manager.get_password_hash(new_password)
            self.db.commit()
            
            # 删除重置令牌
            self.redis_client.delete(f"password_reset:{token}")
            
            # 使所有会话失效
            self.db.query(UserSession).filter(
                UserSession.user_id == user_id
            ).update({"is_active": False})
            self.db.commit()
            
            logger.info(f"密码重置成功: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"密码重置失败: {e}")
            raise ValidationError("密码重置失败")
    
    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """修改密码"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("用户不存在")
        
        # 验证当前密码
        if not security_manager.verify_password(current_password, user.hashed_password):
            raise AuthenticationError("当前密码错误")
        
        # 更新密码
        user.hashed_password = security_manager.get_password_hash(new_password)
        self.db.commit()
        
        logger.info(f"密码修改成功: {user.username}")
        return True
    
    def get_user_sessions(self, user_id: int) -> List[SessionInfo]:
        """获取用户会话列表"""
        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
        ).order_by(UserSession.last_accessed_at.desc()).all()
        
        return [SessionInfo.from_orm(session) for session in sessions]
    
    def revoke_session(self, user_id: int, session_id: int) -> bool:
        """撤销指定会话"""
        session = self.db.query(UserSession).filter(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
        ).first()
        
        if session:
            session.is_active = False
            self.db.commit()
            return True
        
        return False