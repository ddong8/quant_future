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
    BaseCustomException,
    BusinessLogicError,
    SystemError,
    ValidationError,
    create_error_response,
)
from .api.v1 import api_router
from .core.dependencies import get_current_user, get_db
from .core.response import success_response, error_response
from .models.user import User
from sqlalchemy.orm import Session
from fastapi import Depends


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    try:
        print("🚀 开始启动应用...")

        # 等待数据库就绪
        from .services.health_check_service import health_checker

        print("⏳ 等待数据库就绪...")

        db_ready = await health_checker.wait_for_database_ready(
            max_wait_time=settings.DB_INIT_TIMEOUT, check_interval=2
        )

        if not db_ready:
            raise SystemError("数据库未在指定时间内就绪")

        print("✅ 数据库已就绪")

        # 初始化数据库
        print("🔧 初始化数据库结构...")
        db_manager.init_database()

        # 执行全面健康检查
        print("🏥 执行健康检查...")
        health_result = await health_checker.perform_comprehensive_health_check()

        if health_result["overall_status"] == "critical":
            raise SystemError(f"关键服务健康检查失败: {health_result}")

        if health_result["overall_status"] == "warning":
            print(f"⚠️  部分服务存在警告: {health_result['summary']}")

        # 启动市场数据服务
        print("📈 启动市场数据服务...")
        from .services.market_service import market_service

        await market_service.initialize()

        # 启动实时数据推送服务
        print("📡 启动实时数据推送服务...")
        from .services.realtime_service import realtime_service

        await realtime_service.start()

        # 启动定时任务调度器
        print("⏰ 启动定时任务调度器...")
        from .services.scheduler_service import scheduler_service

        scheduler_service.start()

        print("✅ 应用启动成功")
        print(f"📊 整体健康状态: {health_result['overall_status']}")
        print(f"🕐 总启动时间: {health_result['total_response_time_ms']:.2f}ms")
        print("🌐 应用已准备好接收请求")

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
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://mini.ihasy.com:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加受信任主机中间件
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "*.trading.com"]
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


@app.exception_handler(BaseCustomException)
async def base_custom_exception_handler(request: Request, exc: BaseCustomException):
    """基础自定义异常处理器"""
    return create_error_response(
        error_code=exc.error_code,
        error_message=exc.message,
        details=exc.details,
        status_code=exc.status_code,
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
    # 确保异常信息可以被JSON序列化
    exception_details = None
    if settings.DEBUG:
        try:
            exception_details = {"exception": str(exc), "type": exc.__class__.__name__}
        except Exception:
            exception_details = {"exception": "无法序列化异常信息"}

    return create_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        error_message="服务器内部错误",
        details=exception_details,
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

# 兼容性路由函数定义
async def legacy_user_profile(
    current_user: User,
    db: Session,
):
    """兼容性路由：获取用户资料"""
    try:
        # 返回用户基本信息
        profile_data = {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "phone": current_user.phone,
            "avatar_url": current_user.avatar_url,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        }
        
        return success_response(
            data=profile_data,
            message="获取用户资料成功"
        )
        
    except Exception as e:
        return error_response(
            error_code="USER_PROFILE_ERROR",
            message=f"获取用户资料失败: {str(e)}"
        )


async def legacy_dashboard_summary(
    current_user: User,
    db: Session,
):
    """兼容性路由：获取仪表板摘要"""
    try:
        # 返回基本的仪表板数据
        summary_data = {
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "role": current_user.role,
            },
            "stats": {
                "total_strategies": 0,
                "active_positions": 0,
                "total_orders": 0,
                "account_balance": 0.0,
            },
            "recent_activities": [],
            "market_status": "closed",
            "notifications": [],
        }
        
        return success_response(
            data=summary_data,
            message="获取仪表板摘要成功"
        )
        
    except Exception as e:
        return error_response(
            error_code="DASHBOARD_ERROR",
            message=f"获取仪表板摘要失败: {str(e)}"
        )

# 在API路由中也添加兼容性路由
@app.get("/api/v1/user/profile")
async def api_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """API路由：获取用户资料"""
    return await legacy_user_profile(current_user, db)

@app.get("/api/v1/dashboard/summary")
async def api_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """API路由：获取仪表板摘要"""
    return await legacy_dashboard_summary(current_user, db)

# 注册WebSocket路由
from .websocket.routes import router as websocket_router

app.include_router(websocket_router, prefix="/api/v1/ws")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

# 兼容性路由 - 为前端旧的API路径提供支持
@app.get("/api/user/profile")
async def legacy_user_profile_route(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """兼容性路由：获取用户资料"""
    return await legacy_user_profile(current_user, db)


@app.get("/api/dashboard/summary")
async def legacy_dashboard_summary_route(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """兼容性路由：获取仪表板摘要"""
    return await legacy_dashboard_summary(current_user, db)