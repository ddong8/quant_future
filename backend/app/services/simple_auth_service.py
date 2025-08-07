"""
简化的认证服务，使用原生SQL避免ORM关系问题
"""
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import Request
import logging

from ..core.security import security_manager, jwt_manager
from ..core.exceptions import AuthenticationError
from ..schemas.auth import LoginRequest, TokenResponse

logger = logging.getLogger(__name__)


class SimpleAuthService:
    """简化的认证服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(
        self,
        login_data: LoginRequest,
        request: Optional[Request] = None
    ) -> TokenResponse:
        """用户认证登录"""
        # 使用原生SQL查询用户
        result = self.db.execute(
            text('SELECT id, username, hashed_password, role, is_active FROM users WHERE username = :username'),
            {'username': login_data.username}
        ).fetchone()
        
        if not result:
            raise AuthenticationError("用户名或密码错误")
        
        user_id, username, hashed_password, role, is_active = result
        
        # 验证密码
        if not security_manager.verify_password(login_data.password, hashed_password):
            raise AuthenticationError("用户名或密码错误")
        
        # 检查用户状态
        if not is_active:
            raise AuthenticationError("用户账户已被禁用")
        
        # 生成JWT令牌
        access_token = jwt_manager.create_access_token(
            data={"sub": str(user_id), "username": username, "role": role}
        )
        
        refresh_token = jwt_manager.create_refresh_token(
            data={"sub": str(user_id), "username": username}
        )
        
        # 更新用户最后登录时间
        self.db.execute(
            text('UPDATE users SET last_login_at = :now WHERE id = :user_id'),
            {'now': datetime.utcnow(), 'user_id': user_id}
        )
        
        self.db.commit()
        
        logger.info(f"用户登录成功: {username}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=60 * 30,  # 30分钟
            user_id=user_id,
            username=username,
            role=role,
        )