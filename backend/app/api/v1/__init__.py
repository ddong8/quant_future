"""
API v1 路由模块
"""
from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .roles import router as roles_router
from .strategies import router as strategies_router
from .market import router as market_router
from .market_quotes import router as market_quotes_router
from .technical_analysis import router as technical_analysis_router
from .market_depth import router as market_depth_router
from .risk_monitoring import router as risk_monitoring_router
from .orders import router as orders_router
from .positions import router as positions_router
from .accounts import router as accounts_router
from .transactions import router as transactions_router
from .user_settings import router as user_settings_router
from .risk_profile import router as risk_profile_router
from .risk import router as risk_router
from .system import router as system_router
from .backtests import router as backtest_router
from .websocket import router as websocket_router
from .monitoring import router as monitoring_router
from .logs import router as logs_router
from .reports import router as reports_router
from .health import router as health_router

# 创建API路由器
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(users_router, prefix="/users", tags=["用户管理"])
api_router.include_router(roles_router, prefix="/roles", tags=["角色权限管理"])
api_router.include_router(strategies_router, prefix="/strategies", tags=["策略管理"])
api_router.include_router(market_router, prefix="/market", tags=["市场数据"])
api_router.include_router(market_quotes_router, prefix="/market", tags=["行情数据"])
api_router.include_router(technical_analysis_router, prefix="/technical", tags=["技术分析"])
api_router.include_router(market_depth_router, prefix="/depth", tags=["市场深度"])
api_router.include_router(risk_monitoring_router, prefix="/risk-monitoring", tags=["风险监控"])
api_router.include_router(orders_router, prefix="/orders", tags=["订单管理"])
api_router.include_router(positions_router, prefix="/positions", tags=["持仓管理"])
api_router.include_router(accounts_router, prefix="/accounts", tags=["账户管理"])
api_router.include_router(transactions_router, prefix="/transactions", tags=["交易流水"])
api_router.include_router(user_settings_router, prefix="/user-settings", tags=["用户设置"])
api_router.include_router(risk_profile_router, prefix="/risk-profile", tags=["风险偏好"])
api_router.include_router(risk_router, prefix="/risk", tags=["风险管理"])
api_router.include_router(system_router, prefix="/system", tags=["系统管理"])
api_router.include_router(backtest_router, prefix="/backtests", tags=["回测系统"])
api_router.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])
api_router.include_router(monitoring_router, prefix="/monitoring", tags=["系统监控"])
api_router.include_router(logs_router, prefix="/logs", tags=["日志管理"])
api_router.include_router(reports_router, prefix="/reports", tags=["报告生成"])
api_router.include_router(health_router, tags=["健康检查"])