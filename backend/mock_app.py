from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
import json

app = FastAPI(
    title="量化交易平台API",
    version="1.0.0",
    description="基于tqsdk、FastAPI和Vue.js的量化交易平台"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# 数据模型
class User(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class Strategy(BaseModel):
    id: int
    name: str
    description: str
    status: str
    created_at: str

class Quote(BaseModel):
    symbol: str
    last_price: float
    bid_price: float
    ask_price: float
    volume: int
    timestamp: str

class BacktestResult(BaseModel):
    id: int
    strategy_id: int
    status: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float

# 模拟数据
mock_users = [
    {"id": 1, "username": "admin", "email": "admin@trading.com", "role": "admin", "password": "admin123"},
    {"id": 2, "username": "trader1", "email": "trader1@trading.com", "role": "trader", "password": "trader123"},
]

mock_strategies = [
    {"id": 1, "name": "均线策略", "description": "基于移动平均线的交易策略", "status": "active", "created_at": "2024-01-01T10:00:00Z"},
    {"id": 2, "name": "RSI策略", "description": "基于RSI指标的交易策略", "status": "paused", "created_at": "2024-01-02T10:00:00Z"},
]

mock_quotes = [
    {"symbol": "SHFE.cu2401", "last_price": 68500.0, "bid_price": 68490.0, "ask_price": 68510.0, "volume": 12345, "timestamp": datetime.now().isoformat()},
    {"symbol": "SHFE.au2312", "last_price": 450.5, "bid_price": 450.0, "ask_price": 451.0, "volume": 8765, "timestamp": datetime.now().isoformat()},
]

# 基础端点
@app.get("/")
async def root():
    return {
        "message": "量化交易平台API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "用户认证与权限管理",
            "市场数据管理",
            "策略开发与管理",
            "回测系统",
            "实盘交易执行",
            "风险管理",
            "监控与报告",
            "数据存储与备份"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "api": "healthy",
            "database": "healthy",
            "cache": "healthy",
            "market_data": "healthy"
        }
    }

@app.get("/info")
async def system_info():
    return {
        "name": "量化交易平台",
        "version": "1.0.0",
        "debug": True,
        "timestamp": datetime.now().isoformat()
    }

# 认证相关API
@app.post("/api/v1/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = None
    for u in mock_users:
        if u["username"] == form_data.username and u["password"] == form_data.password:
            user = u
            break
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "access_token": "mock-jwt-token-" + user["username"],
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "is_active": True
        }
    }

@app.get("/api/v1/auth/profile")
async def get_profile(token: str = Depends(oauth2_scheme)):
    return {
        "id": 1,
        "username": "admin",
        "email": "admin@trading.com",
        "role": "admin",
        "is_active": True
    }

# 用户管理API
@app.get("/api/v1/users")
async def get_users():
    return {
        "success": True,
        "data": {
            "items": [{"id": u["id"], "username": u["username"], "email": u["email"], "role": u["role"]} for u in mock_users],
            "total": len(mock_users),
            "page": 1,
            "size": 20
        }
    }

# 策略管理API
@app.get("/api/v1/strategies")
async def get_strategies():
    return {
        "success": True,
        "data": {
            "items": mock_strategies,
            "total": len(mock_strategies),
            "page": 1,
            "size": 20
        }
    }

@app.post("/api/v1/strategies")
async def create_strategy():
    new_strategy = {
        "id": len(mock_strategies) + 1,
        "name": "新策略",
        "description": "用户创建的新策略",
        "status": "draft",
        "created_at": datetime.now().isoformat()
    }
    mock_strategies.append(new_strategy)
    return {"success": True, "data": new_strategy}

# 市场数据API
@app.get("/api/v1/market/instruments")
async def get_instruments():
    return {
        "success": True,
        "data": [
            {"symbol": "SHFE.cu2401", "name": "沪铜2401", "exchange": "SHFE"},
            {"symbol": "SHFE.au2312", "name": "沪金2312", "exchange": "SHFE"},
            {"symbol": "DCE.i2401", "name": "铁矿石2401", "exchange": "DCE"},
        ]
    }

@app.get("/api/v1/market/quotes/{symbol}")
async def get_quote(symbol: str):
    quote = next((q for q in mock_quotes if q["symbol"] == symbol), None)
    if not quote:
        raise HTTPException(status_code=404, detail="合约不存在")
    
    # 模拟价格波动
    import random
    quote["last_price"] += random.uniform(-10, 10)
    quote["timestamp"] = datetime.now().isoformat()
    
    return {"success": True, "data": quote}

# 回测API
@app.post("/api/v1/backtests")
async def create_backtest():
    return {
        "success": True,
        "data": {
            "id": 1,
            "strategy_id": 1,
            "status": "running",
            "created_at": datetime.now().isoformat()
        }
    }

@app.get("/api/v1/backtests/{backtest_id}")
async def get_backtest_result(backtest_id: int):
    return {
        "success": True,
        "data": {
            "id": backtest_id,
            "strategy_id": 1,
            "status": "completed",
            "results": {
                "total_return": 0.15,
                "sharpe_ratio": 1.2,
                "max_drawdown": 0.08,
                "win_rate": 0.65,
                "total_trades": 50
            },
            "equity_curve": [
                {"date": "2024-01-01", "equity": 100000.0},
                {"date": "2024-01-02", "equity": 101000.0},
                {"date": "2024-01-03", "equity": 102500.0},
            ]
        }
    }

# 交易API
@app.get("/api/v1/accounts")
async def get_account():
    return {
        "success": True,
        "data": {
            "account_id": "123456789",
            "balance": 100000.0,
            "available": 86320.0,
            "margin": 13680.0,
            "frozen_margin": 0.0,
            "realized_pnl": 500.0,
            "unrealized_pnl": 200.0,
            "updated_at": datetime.now().isoformat()
        }
    }

@app.post("/api/v1/orders")
async def create_order():
    return {
        "success": True,
        "data": {
            "id": "order_" + str(int(datetime.now().timestamp())),
            "symbol": "SHFE.cu2401",
            "direction": "BUY",
            "volume": 1,
            "price": 68500.0,
            "status": "submitted",
            "created_at": datetime.now().isoformat()
        }
    }

@app.get("/api/v1/orders")
async def get_orders():
    return {
        "success": True,
        "data": {
            "items": [
                {
                    "id": "order_001",
                    "symbol": "SHFE.cu2401",
                    "direction": "BUY",
                    "volume": 1,
                    "price": 68500.0,
                    "status": "filled",
                    "created_at": "2024-01-01T10:00:00Z"
                }
            ],
            "total": 1,
            "page": 1,
            "size": 20
        }
    }

# 风险管理API
@app.get("/api/v1/risk/config")
async def get_risk_config():
    return {
        "success": True,
        "data": {
            "max_daily_loss": 5000.0,
            "max_position_ratio": 0.3,
            "max_single_order_amount": 10000.0,
            "stop_loss_ratio": 0.05
        }
    }

@app.get("/api/v1/risk/status")
async def get_risk_status():
    return {
        "success": True,
        "data": {
            "daily_pnl": 200.0,
            "position_ratio": 0.15,
            "risk_level": "low",
            "alerts": []
        }
    }

# 监控API
@app.get("/api/v1/monitoring/status")
async def get_monitoring_status():
    return {
        "success": True,
        "data": {
            "cpu_usage": 25.5,
            "memory_usage": 45.2,
            "disk_usage": 60.1,
            "network_status": "healthy"
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动量化交易平台模拟API服务器...")
    print("📊 API文档: http://localhost:8000/docs")
    print("🔍 健康检查: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
