#!/usr/bin/env python3
"""
测试API路由的简单脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.testclient import TestClient

# 创建一个简化的FastAPI应用来测试路由
app = FastAPI()

# 模拟用户数据
mock_user = {
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

# 模拟仪表板数据
mock_dashboard = {
    "user": {
        "id": 1,
        "username": "testuser",
        "role": "trader",
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

@app.get("/api/user/profile")
async def get_user_profile():
    """获取用户资料"""
    return {
        "success": True,
        "data": mock_user,
        "message": "获取用户资料成功"
    }

@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    """获取仪表板摘要"""
    return {
        "success": True,
        "data": mock_dashboard,
        "message": "获取仪表板摘要成功"
    }

if __name__ == "__main__":
    client = TestClient(app)
    
    print("测试用户资料API...")
    response = client.get("/api/user/profile")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()
    
    print("测试仪表板摘要API...")
    response = client.get("/api/dashboard/summary")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()
    
    print("API路由测试完成！")