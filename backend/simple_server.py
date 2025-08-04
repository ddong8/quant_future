#!/usr/bin/env python3
"""
简化的后端服务器用于测试前端集成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uvicorn

# 创建FastAPI应用
app = FastAPI(title="简化测试服务器")

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

# 安全认证
security = HTTPBearer()

# 模拟用户数据
mock_users = {
    "testuser": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "phone": None,
        "avatar_url": None,
        "role": "trader",
        "is_active": True,
        "is_verified": True,
        "created_at": "2024-01-01T00:00:00",
        "last_login_at": None,
    }
}

# 模拟token验证
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证token"""
    token = credentials.credentials
    # 简单的token验证，实际应用中应该验证JWT
    if token == "test_token":
        return mock_users["testuser"]
    raise HTTPException(status_code=401, detail="Invalid token")

# 登录请求模型
class LoginRequest(BaseModel):
    username: str
    password: str

# 登录端点
@app.post("/api/v1/auth/login")
async def login(request: LoginRequest):
    """用户登录"""
    if request.username == "testuser" and request.password == "password":
        return {
            "success": True,
            "data": {
                "access_token": "test_token",
                "refresh_token": "test_refresh_token",
                "user_id": 1,
                "username": "testuser",
                "role": "trader"
            },
            "message": "登录成功"
        }
    else:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

# 用户资料端点
@app.get("/api/user/profile")
async def get_user_profile(current_user: dict = Depends(verify_token)):
    """获取用户资料"""
    return {
        "success": True,
        "data": current_user,
        "message": "获取用户资料成功"
    }

# 仪表板摘要端点
@app.get("/api/dashboard/summary")
async def get_dashboard_summary(current_user: dict = Depends(verify_token)):
    """获取仪表板摘要"""
    dashboard_data = {
        "user": {
            "id": current_user["id"],
            "username": current_user["username"],
            "role": current_user["role"],
        },
        "stats": {
            "total_strategies": 5,
            "active_positions": 3,
            "total_orders": 12,
            "account_balance": 100000.0,
        },
        "recent_activities": [
            {
                "id": 1,
                "type": "order",
                "description": "买入铜期货",
                "timestamp": "2024-01-01T10:00:00"
            }
        ],
        "market_status": "open",
        "notifications": [
            {
                "id": 1,
                "type": "info",
                "message": "市场开盘",
                "timestamp": "2024-01-01T09:00:00"
            }
        ],
    }
    
    return {
        "success": True,
        "data": dashboard_data,
        "message": "获取仪表板摘要成功"
    }

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "服务运行正常"}

if __name__ == "__main__":
    print("🚀 启动简化测试服务器...")
    print("📍 服务地址: http://localhost:8001")
    print("📖 API文档: http://localhost:8001/docs")
    print("🔐 测试账号: testuser / password")
    
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )