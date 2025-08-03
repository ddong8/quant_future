#!/bin/bash

# 量化交易平台重启脚本
echo "🔄 重启量化交易平台..."

# 停止现有服务
./stop.sh

# 等待进程完全停止
sleep 3

# 启动服务
./start.sh