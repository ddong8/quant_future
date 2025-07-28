"""
FastAPI应用主入口
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import time
import uuid
from contextlib import asynccontextmanager

from .core.config import settings
from .core.database_manager import db_manager
from .core.middleware import (
    LoggingMiddleware,
    RequestIDMiddleware,
    ErrorHandlingMiddleware,
)
from .core.exceptions import (
    BusinessLogicError,
    SystemError,
    ValidationError,
    create_error_response,
)
from .api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    try:
        # 初始化数据库
        db_manager.init_database()
        
        # 健康检查
        health = db_manager.health_check()
        if not all(health.values()):
            raise SystemError(f"数据库健康检查失败: {health}")
        
        # 启动市场数据服务
        from .services.market_service import market_service
        await market_service.initialize()
        
        # 启动实时数据推送服务
        from .services.realtime_service import realtime_service
        await realtime_service.start()
        
        # 启动定时任务调度器
        from .services.scheduler_service import scheduler_service
        await scheduler_service.start()
        
        print("✅ 应用启动成功")
        print(f"📊 数据库状态: {health}")
        print("📡 实时数据服务已启动")
        print("⏰ 定时任务调度器已启动")
        
    except Exception as e:
        print(f"❌ 应用启动失败: {e}")
        raise
    
    yield
    
    # 关闭时执行
    try:
        # 停止定时任务调度器
        from .services.scheduler_service import scheduler_service
        await scheduler_service.stop()
        
        # 停止实时数据推送服务
        from .services.realtime_service import realtime_service
        await realtime_service.stop()
        
        # 关闭数据库连接
        from .core.influxdb import influx_manager
        influx_manager.close()
        
        print("✅ 应用关闭成功")
    except Exception as e:
        print(f"❌ 应用关闭时出错: {e}")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于tqsdk、FastAPI和Vue.js的量化交易平台",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加受信任主机中间件
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.trading.com"]
    )

# 添加自定义中间件
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)


# 全局异常处理器
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP异常处理器"""
    return create_error_response(
        error_code=f"HTTP_{exc.status_code}",
        error_message=exc.detail,
        status_code=exc.status_code,
        request=request,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    return create_error_response(
        error_code="VALIDATION_ERROR",
        error_message="请求参数验证失败",
        details={"validation_errors": exc.errors()},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        request=request,
    )


@app.exception_handler(BusinessLogicError)
async def business_logic_exception_handler(request: Request, exc: BusinessLogicError):
    """业务逻辑异常处理器"""
    return create_error_response(
        error_code=exc.error_code,
        error_message=exc.message,
        details=exc.details,
        status_code=exc.status_code,
        request=request,
    )


@app.exception_handler(SystemError)
async def system_exception_handler(request: Request, exc: SystemError):
    """系统异常处理器"""
    return create_error_response(
        error_code=exc.error_code,
        error_message=exc.message,
        details=exc.details,
        status_code=exc.status_code,
        request=request,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    return create_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        error_message="服务器内部错误",
        details={"exception": str(exc)} if settings.DEBUG else None,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request=request,
    )


# 健康检查端点
@app.get("/health", tags=["系统"])
async def health_check():
    """系统健康检查"""
    health_status = db_manager.health_check()
    
    return {
        "status": "healthy" if all(health_status.values()) else "unhealthy",
        "timestamp": time.time(),
        "version": settings.APP_VERSION,
        "services": health_status,
    }


# 系统信息端点
@app.get("/info", tags=["系统"])
async def system_info():
    """系统信息"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "timestamp": time.time(),
    }


# 注册API路由
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )