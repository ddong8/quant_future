"""
自定义异常类和错误处理
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)


class BaseCustomException(Exception):
    """自定义异常基类"""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class BusinessLogicError(BaseCustomException):
    """业务逻辑错误"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "BUSINESS_LOGIC_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class ValidationError(BaseCustomException):
    """数据验证错误"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class AuthenticationError(BaseCustomException):
    """认证错误"""
    
    def __init__(
        self,
        message: str = "认证失败",
        error_code: str = "AUTHENTICATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class AuthorizationError(BaseCustomException):
    """授权错误"""
    
    def __init__(
        self,
        message: str = "权限不足",
        error_code: str = "AUTHORIZATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class NotFoundError(BaseCustomException):
    """资源未找到错误"""
    
    def __init__(
        self,
        message: str = "资源未找到",
        error_code: str = "NOT_FOUND_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ConflictError(BaseCustomException):
    """资源冲突错误"""
    
    def __init__(
        self,
        message: str = "资源冲突",
        error_code: str = "CONFLICT_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class SystemError(BaseCustomException):
    """系统错误"""
    
    def __init__(
        self,
        message: str = "系统错误",
        error_code: str = "SYSTEM_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class ExternalServiceError(BaseCustomException):
    """外部服务错误"""
    
    def __init__(
        self,
        message: str = "外部服务错误",
        error_code: str = "EXTERNAL_SERVICE_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )


class RateLimitError(BaseCustomException):
    """速率限制错误"""
    
    def __init__(
        self,
        message: str = "请求频率超过限制",
        error_code: str = "RATE_LIMIT_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )


class InsufficientFundsError(BaseCustomException):
    """资金不足错误"""
    
    def __init__(
        self,
        message: str = "资金不足",
        error_code: str = "INSUFFICIENT_FUNDS_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


def create_error_response(
    error_code: str,
    error_message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> JSONResponse:
    """创建统一的错误响应"""
    
    # 获取请求ID
    request_id = "unknown"
    if request and hasattr(request.state, "request_id"):
        request_id = request.state.request_id
    
    # 构建错误响应
    error_response = {
        "error_code": error_code,
        "error_message": error_message,
        "request_id": request_id,
        "timestamp": time.time(),
    }
    
    # 添加详细信息
    if details:
        error_response["details"] = details
    
    # 记录错误日志
    log_data = {
        "error_code": error_code,
        "error_message": error_message,
        "status_code": status_code,
        "request_id": request_id,
    }
    
    if request:
        log_data.update({
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else "unknown",
        })
    
    if details:
        log_data["details"] = details
    
    # 根据状态码选择日志级别
    if status_code >= 500:
        logger.error(f"Server error: {error_message}", extra=log_data)
    elif status_code >= 400:
        logger.warning(f"Client error: {error_message}", extra=log_data)
    else:
        logger.info(f"Error response: {error_message}", extra=log_data)
    
    return JSONResponse(
        status_code=status_code,
        content=error_response,
        headers={"X-Request-ID": request_id}
    )


# 常用错误响应快捷函数
def validation_error(message: str, details: Optional[Dict[str, Any]] = None) -> ValidationError:
    """创建验证错误"""
    return ValidationError(message=message, details=details)


def not_found_error(resource: str, identifier: str = "") -> NotFoundError:
    """创建资源未找到错误"""
    message = f"{resource}未找到"
    if identifier:
        message += f": {identifier}"
    return NotFoundError(message=message)


def authentication_error(message: str = "认证失败") -> AuthenticationError:
    """创建认证错误"""
    return AuthenticationError(message=message)


def authorization_error(message: str = "权限不足") -> AuthorizationError:
    """创建授权错误"""
    return AuthorizationError(message=message)


def business_logic_error(message: str, error_code: str = "BUSINESS_LOGIC_ERROR") -> BusinessLogicError:
    """创建业务逻辑错误"""
    return BusinessLogicError(message=message, error_code=error_code)


def system_error(message: str = "系统错误") -> SystemError:
    """创建系统错误"""
    return SystemError(message=message)


# 为了向后兼容，添加别名
PermissionError = AuthorizationError