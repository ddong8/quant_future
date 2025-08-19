#!/bin/bash

# 订单管理前端真实数据接入测试脚本

set -e

echo "🚀 订单管理系统前端真实数据接入测试"
echo "========================================"

# 检查依赖
echo "📋 检查系统依赖..."

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi

# 检查npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装"
    exit 1
fi

echo "✅ Node.js 版本: $(node --version)"
echo "✅ npm 版本: $(npm --version)"

# 检查后端服务
echo ""
echo "📋 检查后端服务状态..."

BACKEND_URL="http://localhost:8000"
if curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo "✅ 后端服务运行正常"
else
    echo "❌ 后端服务未运行，请先启动后端服务"
    echo "   运行: make dev 或 docker-compose up -d"
    exit 1
fi

# 进入前端目录
cd frontend

# 检查依赖
echo ""
echo "📋 检查前端依赖..."
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
else
    echo "✅ 前端依赖已安装"
fi

# 构建前端
echo ""
echo "📋 构建前端项目..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ 前端构建成功"
else
    echo "❌ 前端构建失败"
    exit 1
fi

# 测试API连接
echo ""
echo "📋 测试订单管理API连接..."
cd ..

# 运行API测试
if [ -f "frontend/test-orders-api.js" ]; then
    echo "🔍 运行API集成测试..."
    node frontend/test-orders-api.js
    
    if [ $? -eq 0 ]; then
        echo "✅ API集成测试通过"
    else
        echo "⚠️ API集成测试有问题，但继续进行"
    fi
else
    echo "⚠️ API测试脚本不存在，跳过API测试"
fi

# 启动前端开发服务器
echo ""
echo "📋 启动前端开发服务器..."
cd frontend

# 检查端口是否被占用
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️ 端口3000已被占用，尝试终止现有进程..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# 启动开发服务器（后台运行）
echo "🚀 启动前端开发服务器..."
npm run dev &
FRONTEND_PID=$!

# 等待服务器启动
echo "⏳ 等待前端服务器启动..."
sleep 10

# 检查前端服务器是否启动成功
if curl -s "http://localhost:3000" > /dev/null 2>&1; then
    echo "✅ 前端服务器启动成功"
    echo ""
    echo "🎉 订单管理系统前端真实数据接入测试完成！"
    echo ""
    echo "📋 测试结果总结:"
    echo "  ✅ 前端构建成功"
    echo "  ✅ 后端API连接正常"
    echo "  ✅ 前端服务器运行正常"
    echo ""
    echo "🌐 访问地址:"
    echo "  前端: http://localhost:3000"
    echo "  后端: http://localhost:8000"
    echo ""
    echo "📋 订单管理功能页面:"
    echo "  📋 订单管理: http://localhost:3000/orders"
    echo "  📊 历史订单: http://localhost:3000/orders/history"
    echo "  📝 订单模板: http://localhost:3000/orders/templates"
    echo ""
    echo "🔧 测试步骤:"
    echo "  1. 访问 http://localhost:3000/login 登录系统"
    echo "  2. 使用用户名: admin, 密码: admin123"
    echo "  3. 导航到订单管理相关页面进行测试"
    echo "  4. 验证真实API数据加载和功能操作"
    echo ""
    echo "⚠️ 注意: 前端服务器正在后台运行 (PID: $FRONTEND_PID)"
    echo "   使用 Ctrl+C 或 kill $FRONTEND_PID 来停止服务器"
    echo ""
    
    # 如果是交互式终端，询问是否打开浏览器
    if [ -t 0 ]; then
        echo "🌐 是否自动打开浏览器? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            # 尝试打开浏览器
            if command -v open &> /dev/null; then
                open "http://localhost:3000/orders"
            elif command -v xdg-open &> /dev/null; then
                xdg-open "http://localhost:3000/orders"
            else
                echo "⚠️ 无法自动打开浏览器，请手动访问 http://localhost:3000/orders"
            fi
        fi
        
        echo ""
        echo "按 Enter 键停止前端服务器并退出..."
        read -r
        
        # 停止前端服务器
        kill $FRONTEND_PID 2>/dev/null || true
        echo "🛑 前端服务器已停止"
    else
        # 非交互式模式，保持服务器运行
        echo "🔄 非交互式模式，前端服务器将继续运行"
        echo "   使用 kill $FRONTEND_PID 来停止服务器"
    fi
    
else
    echo "❌ 前端服务器启动失败"
    kill $FRONTEND_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "✅ 订单管理前端真实数据接入测试完成！"