#!/bin/bash

echo "🔍 测试量化交易平台前后端集成"
echo "=================================="

# 测试后端健康检查
echo "1. 测试后端健康检查..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ 后端健康检查通过"
else
    echo "❌ 后端健康检查失败"
    exit 1
fi

# 测试前端页面
echo "2. 测试前端页面..."
FRONTEND_RESPONSE=$(curl -s http://localhost:3000)
if echo "$FRONTEND_RESPONSE" | grep -q "量化交易平台"; then
    echo "✅ 前端页面加载成功"
else
    echo "❌ 前端页面加载失败"
    exit 1
fi

# 测试API端点
echo "3. 测试API端点..."
API_ENDPOINTS=(
    "/info"
    "/api/v1/market/instruments"
    "/api/v1/strategies"
    "/api/v1/accounts"
)

for endpoint in "${API_ENDPOINTS[@]}"; do
    echo "   测试 $endpoint..."
    RESPONSE=$(curl -s "http://localhost:8000$endpoint")
    if echo "$RESPONSE" | grep -q "success"; then
        echo "   ✅ $endpoint 正常"
    else
        echo "   ❌ $endpoint 失败"
    fi
done

# 测试登录API
echo 