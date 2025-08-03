#!/bin/bash

# 量化交易平台停止脚本
echo "🛑 停止量化交易平台..."

# 停止后端服务
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        echo "🔧 停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
    fi
    rm -f .backend.pid
fi

# 停止前端服务
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null; then
        echo "🎨 停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
    fi
    rm -f .frontend.pid
fi

# 强制停止相关进程
echo "🧹 清理残留进程..."
pkill -f "uvicorn app.main:app"
pkill -f "npm run dev"
pkill -f "vite"

echo "✅ 所有服务已停止"