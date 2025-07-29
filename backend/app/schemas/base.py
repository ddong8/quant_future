"""
基础响应模式
"""
from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    """基础响应模式"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[T] = None
    code: int = 200

class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模式"""
    success: bool = True
    message: str = "获取成功"
    data: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0
    code: int = 200

class ErrorResponse(BaseModel):
    """错误响应模式"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None
    code: int = 400