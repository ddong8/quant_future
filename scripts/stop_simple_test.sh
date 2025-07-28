#!/bin/bash

echo "正在停止量化交易平台演示服务..."

# 停止API服务器
if [ -f "api_pid.txt" ]; then
    API_PID=$(cat api_pid.txt)
    kill $API_PID 2>/dev/null || true
    rm -f api_pid.txt
    echo "✅ API服务器已停止"
fi

# 停止前端服务器
if [ -f "frontend_pid.txt" ]; then
    FRONTEND_PID=$(cat frontend_pid.txt)
    kill $FRONTEND_PID 2>/dev/null || true
    rm -f frontend_pid.txt
    echo "✅ 前端服务器已停止"
fi

# 清理临时文件
rm -f backend/mock_app.py
echo "✅ 临时文件已清理"

echo "🎉 演示服务已完全停止"
