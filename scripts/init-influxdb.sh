#!/bin/bash

# InfluxDB 初始化脚本
# 用于创建组织、存储桶和用户

set -e

echo "🔄 开始初始化 InfluxDB..."

# 等待 InfluxDB 启动
echo "⏳ 等待 InfluxDB 启动..."
until curl -f http://localhost:8086/ping > /dev/null 2>&1; do
    echo "等待 InfluxDB 启动..."
    sleep 2
done

echo "✅ InfluxDB 已启动"

# 设置变量
INFLUX_URL="http://localhost:8086"
INFLUX_TOKEN="my-super-secret-auth-token"
INFLUX_ORG="trading-org"
INFLUX_BUCKET="market-data"
INFLUX_USERNAME="admin"
INFLUX_PASSWORD="admin123456"

# 检查是否已经初始化
echo "🔍 检查 InfluxDB 初始化状态..."
if curl -s "${INFLUX_URL}/api/v2/setup" | grep -q '"allowed":false'; then
    echo "✅ InfluxDB 已经初始化"
else
    echo "🔄 开始初始化 InfluxDB..."
    
    # 执行初始化
    curl -X POST "${INFLUX_URL}/api/v2/setup" \
        -H "Content-Type: application/json" \
        -d "{
            \"username\": \"${INFLUX_USERNAME}\",
            \"password\": \"${INFLUX_PASSWORD}\",
            \"org\": \"${INFLUX_ORG}\",
            \"bucket\": \"${INFLUX_BUCKET}\",
            \"token\": \"${INFLUX_TOKEN}\"
        }"
    
    echo "✅ InfluxDB 初始化完成"
fi

# 验证配置
echo "🔍 验证 InfluxDB 配置..."

# 检查组织
echo "检查组织: ${INFLUX_ORG}"
curl -s -H "Authorization: Token ${INFLUX_TOKEN}" \
    "${INFLUX_URL}/api/v2/orgs" | grep -q "${INFLUX_ORG}" && echo "✅ 组织存在" || echo "❌ 组织不存在"

# 检查存储桶
echo "检查存储桶: ${INFLUX_BUCKET}"
curl -s -H "Authorization: Token ${INFLUX_TOKEN}" \
    "${INFLUX_URL}/api/v2/buckets" | grep -q "${INFLUX_BUCKET}" && echo "✅ 存储桶存在" || echo "❌ 存储桶不存在"

# 创建额外的存储桶（如果需要）
echo "🔄 创建额外的存储桶..."

# 获取组织ID
ORG_ID=$(curl -s -H "Authorization: Token ${INFLUX_TOKEN}" \
    "${INFLUX_URL}/api/v2/orgs" | \
    python3 -c "import sys, json; data=json.load(sys.stdin); print([org['id'] for org in data['orgs'] if org['name']=='${INFLUX_ORG}'][0])")

# 创建系统监控存储桶
SYSTEM_BUCKET="system-metrics"
if ! curl -s -H "Authorization: Token ${INFLUX_TOKEN}" \
    "${INFLUX_URL}/api/v2/buckets" | grep -q "${SYSTEM_BUCKET}"; then
    
    echo "创建系统监控存储桶: ${SYSTEM_BUCKET}"
    curl -X POST "${INFLUX_URL}/api/v2/buckets" \
        -H "Authorization: Token ${INFLUX_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{
            \"orgID\": \"${ORG_ID}\",
            \"name\": \"${SYSTEM_BUCKET}\",
            \"description\": \"系统性能监控数据\",
            \"retentionRules\": [{
                \"type\": \"expire\",
                \"everySeconds\": 2592000
            }]
        }"
    echo "✅ 系统监控存储桶创建完成"
else
    echo "✅ 系统监控存储桶已存在"
fi

# 创建交易记录存储桶
TRADING_BUCKET="trading-records"
if ! curl -s -H "Authorization: Token ${INFLUX_TOKEN}" \
    "${INFLUX_URL}/api/v2/buckets" | grep -q "${TRADING_BUCKET}"; then
    
    echo "创建交易记录存储桶: ${TRADING_BUCKET}"
    curl -X POST "${INFLUX_URL}/api/v2/buckets" \
        -H "Authorization: Token ${INFLUX_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{
            \"orgID\": \"${ORG_ID}\",
            \"name\": \"${TRADING_BUCKET}\",
            \"description\": \"交易记录和策略执行数据\",
            \"retentionRules\": [{
                \"type\": \"expire\",
                \"everySeconds\": 31536000
            }]
        }"
    echo "✅ 交易记录存储桶创建完成"
else
    echo "✅ 交易记录存储桶已存在"
fi

echo "🎉 InfluxDB 初始化完成！"
echo ""
echo "📊 InfluxDB 配置信息:"
echo "  URL: ${INFLUX_URL}"
echo "  组织: ${INFLUX_ORG}"
echo "  主存储桶: ${INFLUX_BUCKET}"
echo "  系统监控存储桶: ${SYSTEM_BUCKET}"
echo "  交易记录存储桶: ${TRADING_BUCKET}"
echo "  Token: ${INFLUX_TOKEN}"
echo ""
echo "🌐 Web UI: http://localhost:8086"
echo "  用户名: ${INFLUX_USERNAME}"
echo "  密码: ${INFLUX_PASSWORD}"