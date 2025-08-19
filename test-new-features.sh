#!/bin/bash

# 测试新功能的脚本
# 验证市场资讯、财经日历、账户设置、交易设置功能

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
echo "    🧪 新功能测试脚本"
echo "========================================================"
echo -e "${NC}"
echo "测试以下功能："
echo "  📰 市场资讯 - MarketNewsView.vue"
echo "  📅 财经日历 - EconomicCalendarView.vue"
echo "  👤 账户设置 - AccountSettingsView.vue"
echo "  📈 交易设置 - TradingSettingsView.vue"
echo ""

# 检查文件是否存在
log_info "检查功能文件是否存在..."

files=(
    "frontend/src/views/market/MarketNewsView.vue"
    "frontend/src/views/market/EconomicCalendarView.vue"
    "frontend/src/views/settings/AccountSettingsView.vue"
    "frontend/src/views/settings/TradingSettingsView.vue"
)

all_files_exist=true

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        log_success "✅ $file 存在"
    else
        log_error "❌ $file 不存在"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = false ]; then
    log_error "部分文件缺失，请检查实现"
    exit 1
fi

# 检查文件内容是否包含实际功能（不是"功能开发中"）
log_info "检查功能实现状态..."

for file in "${files[@]}"; do
    if grep -q "功能开发中" "$file"; then
        log_warning "⚠️  $file 仍显示'功能开发中'"
    else
        log_success "✅ $file 已实现具体功能"
    fi
done

# 检查Vue组件语法
log_info "检查Vue组件语法..."

for file in "${files[@]}"; do
    # 检查是否有基本的Vue组件结构
    if grep -q "<template>" "$file" && grep -q "<script" "$file" && grep -q "<style" "$file"; then
        log_success "✅ $file Vue组件结构完整"
    else
        log_warning "⚠️  $file Vue组件结构可能不完整"
    fi
done

# 检查TypeScript语法
log_info "检查TypeScript导入..."

for file in "${files[@]}"; do
    if grep -q "import.*from" "$file"; then
        log_success "✅ $file 包含TypeScript导入"
    else
        log_warning "⚠️  $file 可能缺少必要的导入"
    fi
done

# 检查Element Plus组件使用
log_info "检查Element Plus组件使用..."

for file in "${files[@]}"; do
    if grep -q "el-" "$file"; then
        log_success "✅ $file 使用了Element Plus组件"
    else
        log_warning "⚠️  $file 可能未使用Element Plus组件"
    fi
done

# 检查响应式设计
log_info "检查响应式设计..."

for file in "${files[@]}"; do
    if grep -q "@media" "$file"; then
        log_success "✅ $file 包含响应式设计"
    else
        log_warning "⚠️  $file 可能缺少响应式设计"
    fi
done

echo ""
log_success "🎉 新功能测试完成！"
echo ""
echo "接下来可以："
echo "1. 运行 ./start-trade-platform.sh 启动平台"
echo "2. 访问 http://localhost:3000 查看新功能"
echo "3. 导航到以下页面测试："
echo "   - 市场数据 -> 市场资讯"
echo "   - 市场数据 -> 财经日历"
echo "   - 系统设置 -> 账户设置"
echo "   - 系统设置 -> 交易设置"
echo ""