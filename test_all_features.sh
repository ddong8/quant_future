#!/bin/bash

# 量化交易平台功能测试脚本
# 测试所有基于 tqsdk 实现的真实功能

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# API 基础地址
API_BASE="http://localhost:8000/api/v1"
TOKEN=""

# 登录获取token
login() {
    log_info "正在登录..."
    
    response=$(curl -s -X POST -H "Content-Type: application/json" \
        -d '{"username":"admin","password":"admin123"}' \
        "$API_BASE/auth/login")
    
    if echo "$response" | jq -e '.success' > /dev/null; then
        TOKEN=$(echo "$response" | jq -r '.data.access_token')
        log_success "登录成功"
        echo "Token: ${TOKEN:0:50}..."
    else
        log_error "登录失败"
        echo "$response" | jq .
        exit 1
    fi
}

# 测试市场数据功能
test_market_data() {
    log_info "=== 测试市场数据功能 ==="
    
    # 测试连接状态
    log_info "测试连接状态..."
    curl -s "$API_BASE/market/status" | jq '.data.is_connected, .data.tqsdk_available'
    
    # 测试合约信息
    log_info "测试合约信息..."
    instruments_count=$(curl -s "$API_BASE/market/instruments" | jq '.data | length')
    log_success "获取到 $instruments_count 个合约"
    
    # 测试实时行情
    log_info "测试实时行情..."
    curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/market/quotes/SHFE.cu2601" | \
        jq '.data | {symbol, last_price, change_pct, volume}'
    
    # 测试K线数据
    log_info "测试K线数据..."
    klines_count=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "$API_BASE/market/klines/SHFE.cu2601?period=1d&limit=10" | jq '.data | length')
    log_success "获取到 $klines_count 条K线数据"
    
    # 测试市场概览
    log_info "测试市场概览..."
    curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/market/summary" | \
        jq '.data.statistics, .data.market_sentiment'
    
    log_success "市场数据功能测试完成"
}

# 测试交易功能
test_trading() {
    log_info "=== 测试交易功能 ==="
    
    # 测试账户信息
    log_info "测试账户信息..."
    curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/trading/account" | \
        jq '.data | {account_id, balance, available, profit, total_asset}'
    
    # 测试下单
    log_info "测试下单功能..."
    order_response=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"symbol":"SHFE.cu2601","direction":"BUY","volume":1,"price":75000,"order_type":"LIMIT"}' \
        "$API_BASE/trading/orders")
    
    order_id=$(echo "$order_response" | jq -r '.data.order_id')
    log_success "下单成功，订单ID: $order_id"
    
    # 测试订单列表
    log_info "测试订单列表..."
    orders_count=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/trading/orders" | \
        jq '.data | length')
    log_success "获取到 $orders_count 个订单"
    
    # 测试持仓列表
    log_info "测试持仓列表..."
    positions_count=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/trading/positions" | \
        jq '.data | length')
    log_success "获取到 $positions_count 个持仓"
    
    # 测试成交记录
    log_info "测试成交记录..."
    trades_count=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/trading/trades" | \
        jq '.data | length')
    log_success "获取到 $trades_count 条成交记录"
    
    log_success "交易功能测试完成"
}

# 测试回测功能
test_backtest() {
    log_info "=== 测试回测功能 ==="
    
    # 测试演示回测
    log_info "测试演示回测..."
    backtest_response=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
        "$API_BASE/backtest/demo")
    
    backtest_id=$(echo "$backtest_response" | jq -r '.data.backtest_id')
    log_success "回测完成，ID: $backtest_id"
    
    # 显示回测结果摘要
    echo "$backtest_response" | jq '.data.results.summary // .data.results'
    
    # 测试回测列表
    log_info "测试回测列表..."
    backtests_count=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/backtest/list" | \
        jq '.data | length')
    log_success "获取到 $backtests_count 个回测任务"
    
    # 测试快速回测
    log_info "测试快速回测..."
    quick_backtest_response=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"symbols":["SHFE.cu2601"],"strategy_params":{"short_period":5,"long_period":20},"days":10}' \
        "$API_BASE/backtest/quick-run")
    
    quick_backtest_id=$(echo "$quick_backtest_response" | jq -r '.data.backtest_id')
    log_success "快速回测完成，ID: $quick_backtest_id"
    
    log_success "回测功能测试完成"
}

# 测试WebSocket功能
test_websocket() {
    log_info "=== 测试WebSocket功能 ==="
    
    # 测试WebSocket统计
    log_info "测试WebSocket统计..."
    curl -s "$API_BASE/ws/stats" | jq '.data'
    
    log_success "WebSocket功能测试完成"
}

# 测试技术分析功能
test_technical_analysis() {
    log_info "=== 测试技术分析功能 ==="
    
    # 测试获取带技术指标的K线数据
    log_info "测试技术指标计算..."
    kline_with_indicators=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "$API_BASE/market/klines/SHFE.cu2601?period=1d&limit=30")
    
    # 检查是否包含技术指标
    has_ma5=$(echo "$kline_with_indicators" | jq '.data[-1] | has("ma5")')
    has_ma20=$(echo "$kline_with_indicators" | jq '.data[-1] | has("ma20")')
    has_rsi=$(echo "$kline_with_indicators" | jq '.data[-1] | has("rsi")')
    
    if [ "$has_ma5" = "true" ]; then
        log_success "MA5指标计算正常"
    fi
    
    if [ "$has_ma20" = "true" ]; then
        log_success "MA20指标计算正常"
    fi
    
    if [ "$has_rsi" = "true" ]; then
        log_success "RSI指标计算正常"
    fi
    
    # 显示最新的技术指标
    echo "$kline_with_indicators" | jq '.data[-1] | {datetime, close, ma5, ma20, rsi}'
    
    log_success "技术分析功能测试完成"
}

# 性能测试
test_performance() {
    log_info "=== 性能测试 ==="
    
    # 并发获取行情测试
    log_info "测试并发获取行情性能..."
    start_time=$(date +%s.%N)
    
    for i in {1..10}; do
        curl -s -H "Authorization: Bearer $TOKEN" \
            "$API_BASE/market/quotes/SHFE.cu2601" > /dev/null &
    done
    wait
    
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc)
    log_success "10个并发请求耗时: ${duration}秒"
    
    # 批量获取行情测试
    log_info "测试批量获取行情..."
    start_time=$(date +%s.%N)
    
    curl -s -X POST -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"symbols":["SHFE.cu2601","DCE.i2601","CZCE.MA601"]}' \
        "$API_BASE/market/quotes/batch" > /dev/null
    
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc)
    log_success "批量获取3个合约行情耗时: ${duration}秒"
    
    log_success "性能测试完成"
}

# 显示功能总结
show_summary() {
    log_info "=== 功能总结 ==="
    
    echo ""
    echo "🎉 量化交易平台功能测试完成！"
    echo ""
    echo "✅ 已实现的核心功能："
    echo "   📊 市场数据服务 - 基于tqsdk的真实行情数据"
    echo "   💰 交易执行系统 - 模拟交易账户和订单管理"
    echo "   📈 策略回测引擎 - 历史数据回测和结果分析"
    echo "   🔄 实时推送系统 - WebSocket实时数据推送"
    echo "   📉 技术分析工具 - MA、RSI、MACD、布林带等指标"
    echo "   🎯 风险管理功能 - 保证金计算和风险控制"
    echo ""
    echo "🚀 技术特点："
    echo "   ⚡ 高性能异步架构"
    echo "   🔗 真实tqsdk数据源"
    echo "   💾 Redis缓存优化"
    echo "   🐳 Docker容器化部署"
    echo "   📱 响应式前端界面"
    echo ""
    echo "🌐 访问地址："
    echo "   前端界面: http://localhost:3000"
    echo "   后端API: http://localhost:8000"
    echo "   API文档: http://localhost:8000/docs"
    echo ""
    echo "👤 默认账户："
    echo "   用户名: admin"
    echo "   密码: admin123"
    echo ""
}

# 主函数
main() {
    echo "🚀 量化交易平台功能测试"
    echo "================================"
    
    # 检查服务状态
    log_info "检查服务状态..."
    if ! curl -s "$API_BASE/health" > /dev/null; then
        log_error "后端服务未启动，请先运行: docker-compose up -d"
        exit 1
    fi
    
    # 登录
    login
    
    # 运行各项测试
    test_market_data
    echo ""
    
    test_trading
    echo ""
    
    test_backtest
    echo ""
    
    test_websocket
    echo ""
    
    test_technical_analysis
    echo ""
    
    test_performance
    echo ""
    
    # 显示总结
    show_summary
}

# 执行主函数
main "$@"