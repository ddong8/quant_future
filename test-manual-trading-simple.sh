#!/bin/bash

# 简单的手动交易页面测试脚本

echo "🧪 测试手动交易页面修复效果..."
echo ""

# 测试前端服务
echo "1. 测试前端服务..."
if curl -f http://localhost:3000/ > /dev/null 2>&1; then
    echo "   ✅ 前端服务正常运行"
else
    echo "   ❌ 前端服务无法访问"
    exit 1
fi

# 测试后端服务
echo "2. 测试后端服务..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ 后端服务正常运行"
else
    echo "   ❌ 后端服务无法访问"
    exit 1
fi

# 测试API端点
echo "3. 测试关键API端点..."

# 测试健康检查
health_response=$(curl -s http://localhost:8000/health)
if echo "$health_response" | grep -q "healthy"; then
    echo "   ✅ 健康检查API正常"
else
    echo "   ⚠️  健康检查API响应异常"
fi

# 测试WebSocket端点（检查是否可以连接）
echo "4. 测试WebSocket连接..."
if nc -z localhost 8000 2>/dev/null; then
    echo "   ✅ WebSocket端口可访问"
else
    echo "   ❌ WebSocket端口无法访问"
fi

echo ""
echo "🎉 基础服务测试完成！"
echo ""
echo "📋 手动测试建议："
echo "1. 打开浏览器访问: http://localhost:3000"
echo "2. 登录系统（admin / admin123）"
echo "3. 导航到手动交易页面"
echo "4. 检查以下内容："
echo "   - 页面是否正常加载（无白屏）"
echo "   - 控制台是否无JavaScript错误"
echo "   - WebSocket连接状态是否显示"
echo "   - 刷新按钮是否工作"
echo "   - 各组件是否正常渲染"
echo ""
echo "🔍 如果发现问题，请查看浏览器控制台和网络面板"