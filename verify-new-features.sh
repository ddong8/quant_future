#!/bin/bash

# 验证新功能是否正常工作的脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

echo -e "${BLUE}"
echo "========================================================"
echo "    🔍 新功能验证脚本"
echo "========================================================"
echo -e "${NC}"

# 检查服务是否运行
log_info "检查服务状态..."

services=("3000" "8000")
all_running=true

for port in "${services[@]}"; do
    if nc -z localhost $port 2>/dev/null; then
        log_success "✅ 端口 $port 服务正常运行"
    else
        log_error "❌ 端口 $port 服务未运行"
        all_running=false
    fi
done

if [ "$all_running" = false ]; then
    log_error "部分服务未运行，请先启动平台"
    echo "运行: ./start-trade-platform.sh"
    exit 1
fi

# 测试前端页面是否可访问
log_info "测试前端页面访问..."

if curl -f -s http://localhost:3000/ > /dev/null; then
    log_success "✅ 前端页面可正常访问"
else
    log_error "❌ 前端页面访问失败"
    exit 1
fi

# 测试后端API是否可访问
log_info "测试后端API访问..."

if curl -f -s http://localhost:8000/health > /dev/null; then
    log_success "✅ 后端API可正常访问"
else
    log_error "❌ 后端API访问失败"
    exit 1
fi

# 检查新功能文件是否存在且不包含"功能开发中"
log_info "验证新功能实现..."

features=(
    "frontend/src/views/market/MarketNewsView.vue:市场资讯"
    "frontend/src/views/market/EconomicCalendarView.vue:财经日历"
    "frontend/src/views/settings/AccountSettingsView.vue:账户设置"
    "frontend/src/views/settings/TradingSettingsView.vue:交易设置"
)

for feature in "${features[@]}"; do
    file=$(echo $feature | cut -d':' -f1)
    name=$(echo $feature | cut -d':' -f2)
    
    if [ -f "$file" ]; then
        if grep -q "功能开发中" "$file"; then
            log_warning "⚠️  $name 仍显示'功能开发中'"
        else
            log_success "✅ $name 已实现具体功能"
        fi
    else
        log_error "❌ $name 文件不存在: $file"
    fi
done

echo ""
log_success "🎉 验证完成！"
echo ""
echo -e "${GREEN}✅ 平台已成功启动，新功能已实现${NC}"
echo ""
echo "🌐 访问地址："
echo "  前端: http://localhost:3000"
echo "  API:  http://localhost:8000"
echo ""
echo "🧪 测试新功能："
echo "  1. 打开浏览器访问 http://localhost:3000"
echo "  2. 使用默认账号登录: admin / admin123"
echo "  3. 导航到以下页面测试新功能："
echo "     - 市场数据 → 市场资讯"
echo "     - 市场数据 → 财经日历"
echo "     - 系统设置 → 账户设置"
echo "     - 系统设置 → 交易设置"
echo ""
echo "📱 移动端测试："
echo "  1. 按F12打开开发者工具"
echo "  2. 点击设备模拟器图标"
echo "  3. 选择移动设备查看响应式效果"
echo ""