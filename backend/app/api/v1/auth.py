"""
认证相关API路由
"""
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from typing import List

from ...core.dependencies import get_database, get_current_user
from ...core.response import (
    success_response,
    created_response,
    error_response,
)
from ...core.exceptions import ValidationError
from ...services.auth_service import AuthService
from ...schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest,
    EmailVerificationRequest,
    UserProfile,
    SessionInfo,
    LogoutRequest,
)
from ...models import User

router = APIRouter()


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register(
    register_data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_database),
):
    """用户注册"""
    auth_service = AuthService(db)
    user_profile = auth_service.register_user(register_data, request)
    
    return created_response(
        data=user_profile.dict(),
        message="注册成功，请查收验证邮件"
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_database),
):
    """用户登录"""
    auth_service = AuthService(db)
    token_response = auth_service.authenticate_user(login_data, request)
    
    return success_response(
        data=token_response.dict(),
        message="登录成功"
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_database),
):
    """刷新访问令牌"""
    auth_service = AuthService(db)
    token_response = auth_service.refresh_token(refresh_data.refresh_token)
    
    return success_response(
        data=token_response.dict(),
        message="令牌刷新成功"
    )


@router.post("/logout")
async def logout(
    logout_data: LogoutRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """用户登出"""
    # 从请求头获取访问令牌
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise ValidationError("无效的认证头")
    
    access_token = authorization.split(" ")[1]
    
    auth_service = AuthService(db)
    success = auth_service.logout_user(
        current_user.id,
        access_token,
        logout_data.all_sessions
    )
    
    if success:
        return success_response(message="登出成功")
    else:
        return error_response("LOGOUT_FAILED", "登出失败")


@router.post("/verify-email")
async def verify_email(
    verification_data: EmailVerificationRequest,
    db: Session = Depends(get_database),
):
    """验证邮箱"""
    auth_service = AuthService(db)
    success = auth_service.verify_email(verification_data.token)
    
    if success:
        return success_response(message="邮箱验证成功")
    else:
        return error_response("VERIFICATION_FAILED", "邮箱验证失败")


@router.post("/password-reset/request")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_database),
):
    """请求密码重置"""
    auth_service = AuthService(db)
    auth_service.request_password_reset(reset_request.email)
    
    return success_response(
        message="如果邮箱存在，重置链接已发送到您的邮箱"
    )


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_database),
):
    """确认密码重置"""
    auth_service = AuthService(db)
    success = auth_service.reset_password(
        reset_confirm.token,
        reset_confirm.new_password
    )
    
    if success:
        return success_response(message="密码重置成功")
    else:
        return error_response("RESET_FAILED", "密码重置失败")


@router.post("/change-password")
async def change_password(
    change_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """修改密码"""
    auth_service = AuthService(db)
    success = auth_service.change_password(
        current_user.id,
        change_data.current_password,
        change_data.new_password
    )
    
    if success:
        return success_response(message="密码修改成功")
    else:
        return error_response("CHANGE_PASSWORD_FAILED", "密码修改失败")


@router.get("/profile", response_model=UserProfile)
async def get_profile(
    current_user: User = Depends(get_current_user),
):
    """获取用户资料"""
    user_profile = UserProfile.from_orm(current_user)
    
    return success_response(
        data=user_profile.dict(),
        message="获取用户资料成功"
    )


@router.get("/sessions", response_model=List[SessionInfo])
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """获取用户会话列表"""
    auth_service = AuthService(db)
    sessions = auth_service.get_user_sessions(current_user.id)
    
    return success_response(
        data=[session.dict() for session in sessions],
        message="获取会话列表成功"
    )


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
):
    """撤销指定会话"""
    auth_service = AuthService(db)
    success = auth_service.revoke_session(current_user.id, session_id)
    
    if success:
        return success_response(message="会话撤销成功")
    else:
        return error_response("REVOKE_FAILED", "会话撤销失败")