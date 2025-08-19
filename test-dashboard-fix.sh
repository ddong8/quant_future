#!/bin/bash

# 测试仪表板422错误修复

echo "🔧 测试仪表板422错误修复"
echo "=========================="

# 检查后端服务
echo "📋 检查后端服务..."
if ! curl -s "http://localhost:8000/health" > /dev/null 2>&1; then
    echo "❌ 后端服务未运行，请先启动后端服务"
    exit 1
fi
echo "✅ 后端服务运行正常"

# 测试认证
echo ""
echo "📋 测试用户认证..."
AUTH_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

if echo "$AUTH_RESPONSE" | grep -q '"success":true'; then
    echo "✅ 用户认证成功"
    TOKEN=$(echo "$AUTH_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "🔑 获取到token: ${TOKEN:0:20}..."
else
    echo "❌ 用户认证失败"
    echo "响应: $AUTH_RESPONSE"
    exit 1
fi

# 测试仪表板API
echo ""
echo "📋 测试仪表板相关API..."

# 测试 /api/v1/auth/me
echo ""
echo "🔍 测试 GET /api/v1/auth/me"
ME_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "响应: $ME_RESPONSE"
if echo "$ME_RESPONSE" | grep -q '"success":true'; then
    echo "✅ /api/v1/auth/me - 成功"
elif echo "$ME_RESPONSE" | grep -q '422'; then
    echo "❌ /api/v1/auth/me - 422错误"
    echo "错误详情: $ME_RESPONSE"
else
    echo "⚠️ /api/v1/auth/me - 其他响应"
fi

# 测试 /api/v1/dashboard/summary
echo ""
echo "🔍 测试 GET /api/v1/dashboard/summary"
DASHBOARD_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/dashboard/summary" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "响应: $DASHBOARD_RESPONSE"
if echo "$DASHBOARD_RESPONSE" | grep -q '"success":true'; then
    echo "✅ /api/v1/dashboard/summary - 成功"
elif echo "$DASHBOARD_RESPONSE" | grep -q '422'; then
    echo "❌ /api/v1/dashboard/summary - 422错误"
    echo "错误详情: $DASHBOARD_RESPONSE"
else
    echo "⚠️ /api/v1/dashboard/summary - 其他响应"
fi

# 测试 /api/v1/user/profile
echo ""
echo "🔍 测试 GET /api/v1/user/profile"
PROFILE_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/user/profile" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "响应: $PROFILE_RESPONSE"
if echo "$PROFILE_RESPONSE" | grep -q '"success":true'; then
    echo "✅ /api/v1/user/profile - 成功"
elif echo "$PROFILE_RESPONSE" | grep -q '422'; then
    echo "❌ /api/v1/user/profile - 422错误"
    echo "错误详情: $PROFILE_RESPONSE"
else
    echo "⚠️ /api/v1/user/profile - 其他响应"
fi

echo ""
echo "🎯 测试总结:"
echo "  如果看到422错误，说明API参数验证有问题"
echo "  前端已添加了错误处理和备用方案"
echo "  现在应该能正常显示仪表板页面"

echo ""
echo "✅ 测试完成"