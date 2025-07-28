"""
性能优化中间件
"""
import time
import gzip
import json
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from app.core.logging import logger
from app.core.cache import api_cache, rate_limit_cache
from app.core.performance import performance_monitor


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 记录请求开始
        request_id = id(request)
        performance_monitor.record_metric(f"request_{request_id}_start", start_time)
        
        try:
            response = await call_next(request)
            
            # 计算响应时间
            process_time = time.time() - start_time
            
            # 添加性能头
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = str(request_id)
            
            # 记录性能指标
            performance_monitor.record_metric("request_duration", process_time)
            performance_monitor.record_metric(f"endpoint_{request.url.path}_duration", process_time)
            
            # 记录慢请求
            if process_time > self.slow_request_threshold:
                logger.warning(
                    f"慢请求检测: {request.method} {request.url.path} - {process_time:.3f}s"
                )
                performance_monitor.record_metric("slow_requests", 1)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"请求处理异常: {request.method} {request.url.path} - {str(e)}")
            performance_monitor.record_metric("request_errors", 1)
            raise


class CompressionMiddleware(BaseHTTPMiddleware):
    """响应压缩中间件"""
    
    def __init__(self, app, minimum_size: int = 1024):
        super().__init__(app)
        self.minimum_size = minimum_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 检查是否支持压缩
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return response
        
        # 检查响应类型
        content_type = response.headers.get("content-type", "")
        if not self._should_compress(content_type):
            return response
        
        # 获取响应内容
        if hasattr(response, 'body'):
            body = response.body
        elif isinstance(response, JSONResponse):
            body = response.body
        else:
            return response
        
        # 检查内容大小
        if len(body) < self.minimum_size:
            return response
        
        # 压缩内容
        compressed_body = gzip.compress(body)
        
        # 创建压缩响应
        compressed_response = Response(
            content=compressed_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )
        
        compressed_response.headers["content-encoding"] = "gzip"
        compressed_response.headers["content-length"] = str(len(compressed_body))
        
        return compressed_response
    
    def _should_compress(self, content_type: str) -> bool:
        """判断是否应该压缩"""
        compressible_types = [
            "application/json",
            "application/javascript",
            "text/css",
            "text/html",
            "text/plain",
            "text/xml",
            "application/xml"
        ]
        
        return any(ct in content_type.lower() for ct in compressible_types)


class CacheMiddleware(BaseHTTPMiddleware):
    """API响应缓存中间件"""
    
    def __init__(self, app, default_ttl: int = 300):
        super().__init__(app)
        self.default_ttl = default_ttl
        self.cacheable_methods = {"GET"}
        self.cache_headers = {
            "Cache-Control": "public, max-age=300",
            "Vary": "Accept-Encoding"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 只缓存GET请求
        if request.method not in self.cacheable_methods:
            return await call_next(request)
        
        # 检查是否应该缓存
        if not self._should_cache(request):
            return await call_next(request)
        
        # 生成缓存键
        cache_key = self._generate_cache_key(request)
        
        # 尝试从缓存获取
        cached_response = api_cache.get_cached_response(cache_key)
        if cached_response:
            logger.debug(f"缓存命中: {cache_key}")
            response = JSONResponse(content=cached_response["content"])
            response.headers.update(cached_response["headers"])
            response.headers["X-Cache"] = "HIT"
            return response
        
        # 执行请求
        response = await call_next(request)
        
        # 缓存响应
        if response.status_code == 200 and isinstance(response, JSONResponse):
            cache_data = {
                "content": json.loads(response.body.decode()),
                "headers": dict(response.headers)
            }
            
            ttl = self._get_cache_ttl(request)
            api_cache.cache_response(cache_key, cache_data, ttl)
            
            response.headers["X-Cache"] = "MISS"
            response.headers.update(self.cache_headers)
        
        return response
    
    def _should_cache(self, request: Request) -> bool:
        """判断是否应该缓存"""
        # 不缓存认证相关请求
        if "auth" in request.url.path:
            return False
        
        # 不缓存包含查询参数的请求（除了分页）
        query_params = dict(request.query_params)
        allowed_params = {"page", "limit", "offset"}
        
        if query_params and not set(query_params.keys()).issubset(allowed_params):
            return False
        
        return True
    
    def _generate_cache_key(self, request: Request) -> str:
        """生成缓存键"""
        user_id = getattr(request.state, "user_id", "anonymous")
        path = request.url.path
        query = str(request.query_params)
        
        return api_cache.generate_api_key(path, user_id, {"query": query})
    
    def _get_cache_ttl(self, request: Request) -> int:
        """获取缓存TTL"""
        # 根据不同端点设置不同的缓存时间
        path = request.url.path
        
        if "/market/" in path:
            return 60  # 市场数据缓存1分钟
        elif "/strategies/" in path:
            return 300  # 策略数据缓存5分钟
        elif "/backtests/" in path:
            return 600  # 回测数据缓存10分钟
        
        return self.default_ttl


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(self, app, default_limit: int = 100, window: int = 60):
        super().__init__(app)
        self.default_limit = default_limit
        self.window = window
        self.rate_limits = {
            "/api/v1/auth/login": (5, 300),  # 登录限制：5次/5分钟
            "/api/v1/auth/register": (3, 3600),  # 注册限制：3次/小时
            "/api/v1/orders/": (50, 60),  # 下单限制：50次/分钟
            "/api/v1/market/": (200, 60),  # 市场数据：200次/分钟
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取客户端标识
        client_id = self._get_client_id(request)
        
        # 获取限流配置
        limit, window = self._get_rate_limit(request.url.path)
        
        # 生成限流键
        rate_key = f"rate_limit:{client_id}:{request.url.path}"
        
        # 检查限流
        if not rate_limit_cache.check_rate_limit(rate_key, limit, window):
            remaining = rate_limit_cache.get_remaining_requests(rate_key, limit)
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "limit": limit,
                    "window": window,
                    "remaining": remaining
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Window": str(window),
                    "X-RateLimit-Remaining": str(remaining),
                    "Retry-After": str(window)
                }
            )
        
        # 执行请求
        response = await call_next(request)
        
        # 添加限流头
        remaining = rate_limit_cache.get_remaining_requests(rate_key, limit)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Window"] = str(window)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        # 优先使用用户ID
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # 使用IP地址
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"
        
        return f"ip:{request.client.host}"
    
    def _get_rate_limit(self, path: str) -> tuple[int, int]:
        """获取路径的限流配置"""
        for pattern, (limit, window) in self.rate_limits.items():
            if pattern in path:
                return limit, window
        
        return self.default_limit, self.window


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss:; "
                "font-src 'self' data:; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 添加安全头
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        return response


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """健康检查中间件"""
    
    def __init__(self, app, health_endpoint: str = "/health"):
        super().__init__(app)
        self.health_endpoint = health_endpoint
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path == self.health_endpoint:
            # 简单的健康检查响应
            health_data = {
                "status": "healthy",
                "timestamp": time.time(),
                "version": "1.0.0"
            }
            
            return JSONResponse(content=health_data)
        
        return await call_next(request)