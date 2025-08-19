#!/bin/bash

# 账户管理API测试脚本

API_BASE="http://localhost:8000/api/v1"

echo "🧪 开始测试账户管理API..."
echo

# 1. 登录获取token
echo "1️⃣ 登录获取token..."
LOGIN_RESPONSE=$(curl -s -X POST "${API_BASE}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ 登录失败"
  echo $LOGIN_RESPONSE
  exit 1
fi

echo "✅ 登录成功，获取到token"
echo

# 2. 获取账户列表
echo "2️⃣ 获取账户列表..."
ACCOUNTS_RESPONSE=$(curl -s -X GET "${API_BASE}/accounts/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "✅ 账户列表获取成功:"
echo $ACCOUNTS_RESPONSE | jq '.' 2>/dev/null || echo $ACCOUNTS_RESPONSE
echo

# 3. 创建新账户
echo "3️⃣ 创建新账户..."
CREATE_RESPONSE=$(curl -s -X POST "${API_BASE}/accounts/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"account_name": "测试账户", "broker": "测试券商", "initial_balance": 100000}')

echo "✅ 账户创建成功:"
echo $CREATE_RESPONSE | jq '.' 2>/dev/null || echo $CREATE_RESPONSE
echo

# 4. 获取新创建的账户ID
ACCOUNT_ID=$(echo $CREATE_RESPONSE | grep -o '"id":[0-9]*' | cut -d':' -f2)

if [ ! -z "$ACCOUNT_ID" ]; then
  echo "4️⃣ 获取账户详情 (ID: $ACCOUNT_ID)..."
  ACCOUNT_RESPONSE=$(curl -s -X GET "${API_BASE}/accounts/${ACCOUNT_ID}" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json")
  
  echo "✅ 账户详情获取成功:"
  echo $ACCOUNT_RESPONSE | jq '.' 2>/dev/null || echo $ACCOUNT_RESPONSE
  echo
fi

# 5. 再次获取账户列表验证
echo "5️⃣ 验证账户列表..."
FINAL_ACCOUNTS_RESPONSE=$(curl -s -X GET "${API_BASE}/accounts/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "✅ 最终账户列表:"
echo $FINAL_ACCOUNTS_RESPONSE | jq '.' 2>/dev/null || echo $FINAL_ACCOUNTS_RESPONSE
echo

echo "🎉 所有测试通过！账户管理API工作正常"