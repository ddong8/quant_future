#!/bin/bash

# 量化交易平台日志查看脚本
echo "📋 查看量化交易平台日志..."

# 创建日志目录
mkdir -p logs

echo "选择要查看的日志："
echo "1) 后端日志"
echo "2) 前端日志"
echo "3) 数据库日志"
echo "4) 系统日志"
echo "5) 实时日志监控"

read -p "请输入选项 (1-5): " choice

case $choice in
    1)
        echo "📊 后端服务日志："
        if [ -f "logs/backend.log" ]; then
            tail -f logs/backend.log
        else
            echo "后端日志文件不存在"
        fi
        ;;
    2)
        echo "🎨 前端服务日志："
        if [ -f "logs/frontend.log" ]; then
            tail -f logs/frontend.log
        else
            echo "前端日志文件不存在"
        fi
        ;;
    3)
        echo "🗄️  数据库日志："
        if [ -f "logs/database.log" ]; then
            tail -f logs/database.log
        else
            echo "数据库日志文件不存在"
        fi
        ;;
    4)
        echo "🖥️  系统日志："
        if [ -f "logs/system.log" ]; then
            tail -f logs/system.log
        else
            echo "系统日志文件不存在"
        fi
        ;;
    5)
        echo "📡 实时日志监控："
        echo "监控所有日志文件..."
        tail -f logs/*.log 2>/dev/null || echo "没有找到日志文件"
        ;;
    *)
        echo "❌ 无效选项"
        ;;
esac