"""
统一的API响应格式
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi import status
import time


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "操作成功"
    timestamp: float
    request_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            # 自定义JSON编码器
        }


class SuccessResponse(BaseResponse):
    """成功响应模型"""
    data: Optional[Any] = None
    
    def __init__(self, data: Any = None, message: str = "操作成功", **kwargs):
        super().__init__(
            success=True,
            message=message,
            data=data,
            timestamp=time.time(),
            **kwargs
        )


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    success: bool = False
    error_code: str
    details: Optional[Dict[str, Any]] = None
    
    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            success=False,
            message=message,
            error_code=error_code,
            details=details,
            timestamp=time.time(),
            **kwargs
        )


class PaginatedResponse(SuccessResponse):
    """分页响应模型"""
    pagination: Dict[str, Any]
    
    def __init__(
        self,
        data: List[Any],
        total: int,
        page: int = 1,
        page_size: int = 20,
        message: str = "查询成功",
        **kwargs
    ):
        # 计算分页信息
        total_pages = (total + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1
        
        pagination = {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev,
        }
        
        super().__init__(
            data=data,
            message=message,
            pagination=pagination,
            **kwargs
        )


# 响应创建函数
def success_response(
    data: Any = None,
    message: str = "操作成功",
    status_code: int = status.HTTP_200_OK,
    headers: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    """创建成功响应"""
    response_data = SuccessResponse(data=data, message=message)
    
    return JSONResponse(
        status_code=status_code,
        content=response_data.dict(),
        headers=headers or {},
    )


def error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    headers: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    """创建错误响应"""
    response_data = ErrorResponse(
        error_code=error_code,
        message=message,
        details=details,
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data.dict(),
        headers=headers or {},
    )


def paginated_response(
    data: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: str = "查询成功",
    status_code: int = status.HTTP_200_OK,
    headers: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    """创建分页响应"""
    response_data = PaginatedResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
        message=message,
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data.dict(),
        headers=headers or {},
    )


def created_response(
    data: Any = None,
    message: str = "创建成功",
    headers: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    """创建资源创建成功响应"""
    return success_response(
        data=data,
        message=message,
        status_code=status.HTTP_201_CREATED,
        headers=headers,
    )


def updated_response(
    data: Any = None,
    message: str = "更新成功",
    headers: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    """创建资源更新成功响应"""
    return success_response(
        data=data,
        message=message,
        status_code=status.HTTP_200_OK,
        headers=headers,
    )


def deleted_response(
    message: str = "删除成功",
    headers: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    """创建资源删除成功响应"""
    return success_response(
        data=None,
        message=message,
        status_code=status.HTTP_200_OK,
        headers=headers,
    )


def no_content_response(
    headers: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    """创建无内容响应"""
    return JSONResponse(
        status_code=status.HTTP_204_NO_CONTENT,
        content=None,
        headers=headers or {},
    )


# 常用状态码响应
def bad_request_response(message: str = "请求参数错误") -> JSONResponse:
    """400 错误请求"""
    return error_response(
        error_code="BAD_REQUEST",
        message=message,
        status_code=status.HTTP_400_BAD_REQUEST,
    )


def unauthorized_response(message: str = "未授权访问") -> JSONResponse:
    """401 未授权"""
    return error_response(
        error_code="UNAUTHORIZED",
        message=message,
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


def forbidden_response(message: str = "禁止访问") -> JSONResponse:
    """403 禁止访问"""
    return error_response(
        error_code="FORBIDDEN",
        message=message,
        status_code=status.HTTP_403_FORBIDDEN,
    )


def not_found_response(message: str = "资源未找到") -> JSONResponse:
    """404 未找到"""
    return error_response(
        error_code="NOT_FOUND",
        message=message,
        status_code=status.HTTP_404_NOT_FOUND,
    )


def conflict_response(message: str = "资源冲突") -> JSONResponse:
    """409 冲突"""
    return error_response(
        error_code="CONFLICT",
        message=message,
        status_code=status.HTTP_409_CONFLICT,
    )


def internal_server_error_response(message: str = "服务器内部错误") -> JSONResponse:
    """500 服务器内部错误"""
    return error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )