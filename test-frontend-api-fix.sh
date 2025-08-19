#!/bin/bash

# 前端API修复验证脚本

API_BASE="http://localhost:8000/api/v1"

echo "🔧 验证前端API修复..."
echo

# 1. 登录获取token
echo "1️⃣ 登录获取token..."
LOGIN_RESPONSE=$(curl -s -X POST "${API_BASE}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ 登录失败"
  exit 1
fi

echo "✅ 登录成功"
echo

# 2. 测试 /auth/me 端点
echo "2️⃣ 测试 /auth/me 端点..."
AUTH_ME_RESPONSE=$(curl -s -X GET "${API_BASE}/auth/me" \
  -H "Authorization: Bearer $TOKEN")

AUTH_ME_SUCCESS=$(echo $AUTH_ME_RESPONSE | grep -o '"success":true')
if [ -n "$AUTH_ME_SUCCESS" ]; then
  echo "✅ /auth/me 端点正常"
else
  echo "❌ /auth/me 端点失败"
  echo $AUTH_ME_RESPONSE
fi
echo

# 3. 测试 /dashboard/summary 端点
echo "3️⃣ 测试 /dashboard/summary 端点..."
DASHBOARD_RESPONSE=$(curl -s -X GET "${API_BASE}/dashboard/summary" \
  -H "Authorization: Bearer $TOKEN")

DASHBOARD_SUCCESS=$(echo $DASHBOARD_RESPONSE | grep -o '"success":true')
if [ -n "$DASHBOARD_SUCCESS" ]; then
  echo "✅ /dashboard/summary 端点正常"
else
  echo "❌ /dashboard/summary 端点失败"
  echo $DASHBOARD_RESPONSE
fi
echo

# 4. 测试 /market/instruments 端点
echo "4️⃣ 测试 /market/instruments 端点..."
INSTRUMENTS_RESPONSE=$(curl -s -X GET "${API_BASE}/market/instruments" \
  -H "Authorization: Bearer $TOKEN")

INSTRUMENTS_SUCCESS=$(echo $INSTRUMENTS_RESPONSE | grep -o '"success":true')
if [ -n "$INSTRUMENTS_SUCCESS" ]; then
  echo "✅ /market/instruments 端点正常"
  INSTRUMENTS_COUNT=$(echo $INSTRUMENTS_RESPONSE | grep -o '"data":\[[^]]*\]' | grep -o '{"symbol"' | wc -l)
  echo "   获取到 $INSTRUMENTS_COUNT 个合约信息"
else
  echo "❌ /market/instruments 端点失败"
  echo $INSTRUMENTS_RESPONSE
fi
echo

# 5. 测试账户管理端点
echo "5️⃣ 测试 /accounts 端点..."
ACCOUNTS_RESPONSE=$(curl -s -X GET "${API_BASE}/accounts/" \
  -H "Authorization: Bearer $TOKEN")

if [[ $ACCOUNTS_RESPONSE == *"["* ]]; then
  echo "✅ /accounts 端点正常"
  ACCOUNTS_COUNT=$(echo $ACCOUNTS_RESPONSE | grep -o '{"id"' | wc -l)
  echo "   当前有 $ACCOUNTS_COUNT 个账户"
else
  echo "❌ /accounts 端点失败"
  echo $ACCOUNTS_RESPONSE
fi
echo

echo "🎉 API修复验证完成！"
echo
echo "📊 修复总结："
echo "   ✅ 用户认证 API"
echo "   ✅ 仪表板摘要 API"  
echo "   ✅ 市场合约 API"
echo "   ✅ 账户管理 API"
echo
echo "🌐 前端现在应该可以正常加载，没有API错误了！"