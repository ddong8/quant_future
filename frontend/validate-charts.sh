#!/bin/bash

# 图表组件功能验证脚本

echo "🔍 开始验证图表组件功能..."
echo ""

# 测试计数器
PASSED=0
FAILED=0
ERRORS=()

# 测试函数
test_file() {
    local name="$1"
    local file="$2"
    
    echo "📋 测试: $name"
    
    if [ -f "$file" ]; then
        echo "✅ 通过: $name"
        ((PASSED++))
    else
        echo "❌ 失败: $name - 文件不存在: $file"
        ((FAILED++))
        ERRORS+=("$name")
    fi
    echo ""
}

# 测试内容函数
test_content() {
    local name="$1"
    local file="$2"
    local pattern="$3"
    
    echo "📋 测试: $name"
    
    if [ -f "$file" ]; then
        if grep -q "$pattern" "$file"; then
            echo "✅ 通过: $name"
            ((PASSED++))
        else
            echo "❌ 失败: $name - 未找到模式: $pattern"
            ((FAILED++))
            ERRORS+=("$name")
        fi
    else
        echo "❌ 失败: $name - 文件不存在: $file"
        ((FAILED++))
        ERRORS+=("$name")
    fi
    echo ""
}

echo "🚀 开始执行测试..."
echo ""

# 1. 测试 ECharts 配置文件存在
test_file "ECharts 配置文件存在" "src/utils/echarts.ts"

# 2. 测试 ECharts 配置内容
test_content "ECharts 配置包含必要组件" "src/utils/echarts.ts" "use\|CanvasRenderer\|LineChart"

# 3. 测试 main.ts 中的 ECharts 导入
test_content "main.ts 中正确导入 ECharts" "src/main.ts" "./utils/echarts"

# 4. 测试 RealTimeChart 组件存在
test_file "RealTimeChart 组件存在" "src/components/RealTimeChart.vue"

# 5. 测试 RealTimeChart 组件使用 vue-echarts
test_content "RealTimeChart 使用 vue-echarts" "src/components/RealTimeChart.vue" "vue-echarts\|v-chart"

# 6. 测试 DashboardView 使用图表组件
test_content "DashboardView 使用图表组件" "src/views/dashboard/DashboardView.vue" "RealTimeChart\|v-chart"

# 7. 测试 package.json 中的依赖
test_content "package.json 包含 echarts 依赖" "package.json" "echarts"
test_content "package.json 包含 vue-echarts 依赖" "package.json" "vue-echarts"

# 8. 测试 vite 配置
test_content "vite 配置包含 ECharts 优化" "vite.config.ts" "echarts.*vue-echarts"

# 9. 测试简化 vite 配置
test_content "简化 vite 配置包含 ECharts" "vite.config.simple.ts" "echarts"

# 10. 测试其他图表组件
test_file "BacktestResultReport 组件存在" "src/components/BacktestResultReport.vue"
test_file "StrategyPerformanceMonitor 组件存在" "src/components/StrategyPerformanceMonitor.vue"
test_file "BacktestTradeRecords 组件存在" "src/components/BacktestTradeRecords.vue"

# 11. 测试 Dockerfile
test_file "Dockerfile 存在" "Dockerfile"
test_content "Dockerfile 包含必要构建步骤" "Dockerfile" "npm ci\|sass-embedded"

# 12. 测试 .dockerignore
test_file ".dockerignore 文件存在" ".dockerignore"

# 输出测试结果
echo "📊 测试结果汇总:"
echo "=================================================="
echo "✅ 通过: $PASSED"
echo "❌ 失败: $FAILED"

if [ $FAILED -eq 0 ]; then
    echo "📈 成功率: 100.0%"
else
    TOTAL=$((PASSED + FAILED))
    SUCCESS_RATE=$(echo "scale=1; $PASSED * 100 / $TOTAL" | bc -l)
    echo "📈 成功率: ${SUCCESS_RATE}%"
fi

if [ ${#ERRORS[@]} -gt 0 ]; then
    echo ""
    echo "❌ 失败的测试:"
    for i in "${!ERRORS[@]}"; do
        echo "  $((i+1)). ${ERRORS[i]}"
    done
fi

echo ""
echo "=================================================="

if [ $FAILED -eq 0 ]; then
    echo "🎉 所有图表组件测试通过！"
    exit 0
else
    echo "⚠️  部分测试失败，请检查上述错误"
    exit 1
fi