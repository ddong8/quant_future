"""
结构化日志记录器
提供统一的结构化日志记录功能
"""

import asyncio
import inspect
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar
from functools import wraps

from app.core.logging import get_logger
from app.services.log_management_service import log_management_service

# 上下文变量用于存储请求相关信息
request_context: ContextVar[Dict[str, Any]] = ContextVar('request_context', default={})


class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(name)
    
    async def _log_to_database(
        self,
        level: str,
        message: str,
        extra_data: Dict[str, Any] = None
    ):
        """记录日志到数据库"""
        try:
            # 获取调用栈信息
            frame = inspect.currentframe()
            caller_frame = frame.f_back.f_back  # 跳过当前方法和调用方法
            
            module = caller_frame.f_globals.get('__name__', 'unknown')
            function = caller_frame.f_code.co_name
            line_number = caller_frame.f_lineno
            
            # 获取请求上下文
            context = request_context.get({})
            
            # 合并额外数据
            combined_extra = {
                **(extra_data or {}),
                **context
            }
            
            # 异步记录到数据库
            await log_management_service.create_log_entry(
                level=level,
                message=message,
                logger_name=self.name,
                module=module,
                function=function,
                line_number=line_number,
                user_id=context.get('user_id'),
                request_id=context.get('request_id'),
                extra_data=combined_extra
            )
            
        except Exception as e:
            # 记录日志失败不应该影响主业务
            self.logger.error(f"记录结构化日志失败: {e}")
    
    def debug(self, message: str, **kwargs):
        """调试日志"""
        self.logger.debug(message, extra=kwargs)
        asyncio.create_task(self._log_to_database('DEBUG', message, kwargs))
    
    def info(self, message: str, **kwargs):
        """信息日志"""
        self.logger.info(message, extra=kwargs)
        asyncio.create_task(self._log_to_database('INFO', message, kwargs))
    
    def warning(self, message: str, **kwargs):
        """警告日志"""
        self.logger.warning(message, extra=kwargs)
        asyncio.create_task(self._log_to_database('WARNING', message, kwargs))
    
    def error(self, message: str, exception: Exception = None, **kwargs):
        """错误日志"""
        extra_data = kwargs.copy()
        
        if exception:
            extra_data.update({
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'traceback': traceback.format_exc()
            })
        
        self.logger.error(message, extra=extra_data)
        asyncio.create_task(self._log_to_database('ERROR', message, extra_data))
    
    def critical(self, message: str, exception: Exception = None, **kwargs):
        """严重错误日志"""
        extra_data = kwargs.copy()
        
        if exception:
            extra_data.update({
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'traceback': traceback.format_exc()
            })
        
        self.logger.critical(message, extra=extra_data)
        asyncio.create_task(self._log_to_database('CRITICAL', message, extra_data))
    
    def log_user_action(
        self,
        user_id: int,
        action: str,
        resource: str = None,
        resource_id: str = None,
        details: Dict[str, Any] = None
    ):
        """记录用户操作日志"""
        message = f"用户操作: {action}"
        if resource:
            message += f" - {resource}"
        if resource_id:
            message += f"#{resource_id}"
        
        extra_data = {
            'log_type': 'user_action',
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'resource_id': resource_id,
            'details': details or {}
        }
        
        self.info(message, **extra_data)
    
    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time: float,
        user_id: int = None,
        request_size: int = None,
        response_size: int = None
    ):
        """记录API请求日志"""
        message = f"API请求: {method} {path} - {status_code} ({response_time:.3f}s)"
        
        extra_data = {
            'log_type': 'api_request',
            'method': method,
            'path': path,
            'status_code': status_code,
            'response_time': response_time,
            'user_id': user_id,
            'request_size': request_size,
            'response_size': response_size
        }
        
        if status_code >= 400:
            self.warning(message, **extra_data)
        else:
            self.info(message, **extra_data)
    
    def log_business_event(
        self,
        event_type: str,
        event_name: str,
        user_id: int = None,
        data: Dict[str, Any] = None
    ):
        """记录业务事件日志"""
        message = f"业务事件: {event_type} - {event_name}"
        
        extra_data = {
            'log_type': 'business_event',
            'event_type': event_type,
            'event_name': event_name,
            'user_id': user_id,
            'data': data or {}
        }
        
        self.info(message, **extra_data)
    
    def log_system_event(
        self,
        event_type: str,
        component: str,
        status: str,
        details: Dict[str, Any] = None
    ):
        """记录系统事件日志"""
        message = f"系统事件: {component} - {event_type} ({status})"
        
        extra_data = {
            'log_type': 'system_event',
            'event_type': event_type,
            'component': component,
            'status': status,
            'details': details or {}
        }
        
        if status in ['error', 'failed', 'critical']:
            self.error(message, **extra_data)
        elif status in ['warning', 'degraded']:
            self.warning(message, **extra_data)
        else:
            self.info(message, **extra_data)
    
    def log_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = None,
        tags: Dict[str, str] = None
    ):
        """记录性能指标日志"""
        message = f"性能指标: {metric_name} = {value}"
        if unit:
            message += f" {unit}"
        
        extra_data = {
            'log_type': 'performance_metric',
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            'tags': tags or {}
        }
        
        self.info(message, **extra_data)


def get_structured_logger(name: str) -> StructuredLogger:
    """获取结构化日志记录器"""
    return StructuredLogger(name)


def set_request_context(
    request_id: str = None,
    user_id: int = None,
    ip_address: str = None,
    user_agent: str = None,
    **kwargs
):
    """设置请求上下文"""
    context = {
        'request_id': request_id,
        'user_id': user_id,
        'ip_address': ip_address,
        'user_agent': user_agent,
        'timestamp': datetime.utcnow().isoformat(),
        **kwargs
    }
    
    # 过滤None值
    context = {k: v for k, v in context.items() if v is not None}
    
    request_context.set(context)


def clear_request_context():
    """清除请求上下文"""
    request_context.set({})


def log_execution_time(logger: StructuredLogger = None):
    """装饰器：记录函数执行时间"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            func_logger = logger or get_structured_logger(func.__module__)
            
            try:
                result = await func(*args, **kwargs)
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                func_logger.log_performance_metric(
                    metric_name=f"{func.__name__}_execution_time",
                    value=execution_time,
                    unit="seconds",
                    tags={'function': func.__name__, 'module': func.__module__}
                )
                
                return result
                
            except Exception as e:
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                func_logger.error(
                    f"函数执行失败: {func.__name__}",
                    exception=e,
                    execution_time=execution_time
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            func_logger = logger or get_structured_logger(func.__module__)
            
            try:
                result = func(*args, **kwargs)
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                func_logger.log_performance_metric(
                    metric_name=f"{func.__name__}_execution_time",
                    value=execution_time,
                    unit="seconds",
                    tags={'function': func.__name__, 'module': func.__module__}
                )
                
                return result
                
            except Exception as e:
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                func_logger.error(
                    f"函数执行失败: {func.__name__}",
                    exception=e,
                    execution_time=execution_time
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_api_call(logger: StructuredLogger = None):
    """装饰器：记录API调用"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_logger = logger or get_structured_logger(func.__module__)
            start_time = datetime.utcnow()
            
            # 提取请求信息
            request = None
            for arg in args:
                if hasattr(arg, 'method') and hasattr(arg, 'url'):
                    request = arg
                    break
            
            try:
                result = await func(*args, **kwargs)
                
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                if request:
                    func_logger.log_api_request(
                        method=request.method,
                        path=str(request.url.path),
                        status_code=200,  # 假设成功
                        response_time=response_time
                    )
                
                return result
                
            except Exception as e:
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                if request:
                    func_logger.log_api_request(
                        method=request.method,
                        path=str(request.url.path),
                        status_code=500,  # 假设服务器错误
                        response_time=response_time
                    )
                
                func_logger.error(f"API调用失败: {func.__name__}", exception=e)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            # 同步函数的处理逻辑类似
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # 简化的同步版本
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    func_logger = logger or get_structured_logger(func.__module__)
                    func_logger.error(f"API调用失败: {func.__name__}", exception=e)
                    raise
            
            return sync_wrapper
    
    return decorator


class LoggingMiddleware:
    """日志中间件"""
    
    def __init__(self):
        self.logger = get_structured_logger(__name__)
    
    async def __call__(self, request, call_next):
        """处理请求日志"""
        start_time = datetime.utcnow()
        request_id = f"{start_time.timestamp()}-{id(request)}"
        
        # 设置请求上下文
        set_request_context(
            request_id=request_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent')
        )
        
        try:
            response = await call_next(request)
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # 记录API请求日志
            self.logger.log_api_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                response_time=response_time,
                request_size=request.headers.get('content-length'),
                response_size=response.headers.get('content-length')
            )
            
            return response
            
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.log_api_request(
                method=request.method,
                path=request.url.path,
                status_code=500,
                response_time=response_time
            )
            
            self.logger.error("请求处理异常", exception=e)
            raise
        
        finally:
            # 清除请求上下文
            clear_request_context()