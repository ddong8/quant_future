"""
API v1 路由模块
"""
from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .strategies import router as strategies_router
from .market import router as market_router
from .trading import router as trading_router
from .backtest import router as backtest_router
from .risk import router as risk_router
from .system import router as system_router
from .websocket import router as websocket_router

# 创建API路由器
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(users_router, prefix="/users", tags=["用户管理"])
api_router.include_router(strategies_router, prefix="/strategies", tags=["策略管理"])
api_router.include_router(market_router, prefix="/market", tags=["市场数据"])
api_router.include_router(trading_router, prefix="/trading", tags=["交易执行"])
api_router.include_router(backtest_router, prefix="/backtest", tags=["回测系统"])
api_router.include_router(risk_router, prefix="/risk", tags=["风险管理"])
api_router.include_router(system_router, prefix="/system", tags=["系统管理"])
api_router.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])