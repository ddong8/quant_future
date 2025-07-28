#!/bin/bash

# 停止量化交易平台服务

echo "正在停止量化交易平台服务..."

# 停止前端服务器
if [ -f "frontend_pid.txt" ]; then
    FRONTEND_PID=$(cat frontend_pid.txt)
    kill $FRONTEND_PID 2>/dev/null || true
    rm -f frontend_pid.txt
    echo "✅ 前端服务器已停止"
fi

# 停止Docker服务
docker-compose down 2>/dev/null || true
echo "✅ Docker服务已停止"

# 清理临时文件
rm -f backend/test_app.py
echo "✅ 临时文件已清理"

echo "🎉 所有服务已停止"