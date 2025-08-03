#!/bin/bash

# 量化交易平台 Docker Compose 启动脚本
echo "🐳 使用 Docker Compose 启动量化交易平台..."

# 检查 Docker 和 Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    echo "📦 安装指南: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    echo "📦 安装指南: https://docs.docker.com/compose/install/"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs uploads data/postgres data/redis nginx/ssl

# 设置权限
chmod +x backend/docker-entrypoint.sh

# 检查环境配置
if [ ! -f "backend/.env" ]; then
    echo "📝 创建后端环境配置..."
    cat > backend/.env << EOF
DATABASE_URL=postgresql://trading_user:trading_password@postgres:5432/trading_platform
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key-change-this-in-production-$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost", "http://127.0.0.1"]
EOF
fi

if [ ! -f "frontend/.env" ]; then
    echo "📝 创建前端环境配置..."
    cat > frontend/.env << EOF
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
VITE_APP_TITLE=量化交易平台
VITE_APP_VERSION=1.0.0
VITE_ENABLE_MOCK=false
VITE_ENABLE_DEBUG=true
EOF
fi

# 选择启动模式
echo "🚀 选择启动模式:"
echo "1) 开发模式 (包含数据库管理工具)"
echo "2) 生产模式 (包含 Nginx 反向代理)"
echo "3) 基础模式 (仅核心服务)"

read -p "请选择模式 (1-3, 默认: 3): " mode
mode=${mode:-3}

case $mode in
    1)
        echo "🔧 启动开发模式..."
        docker-compose --profile dev up -d
        ;;
    2)
        echo "🚀 启动生产模式..."
        docker-compose --profile production up -d
        ;;
    3)
        echo "⚡ 启动基础模式..."
        docker-compose up -d postgres redis backend frontend
        ;;
    *)
        echo "❌ 无效选项，使用基础模式..."
        docker-compose up -d postgres redis backend frontend
        ;;
esac

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 显示访问信息
echo ""
echo "🎉 量化交易平台启动成功！"
echo ""
echo "📊 服务地址："

if [ "$mode" = "2" ]; then
    echo "   主应用:   http://localhost"
    echo "   前端应用: http://localhost:3000"
    echo "   后端API:  http://localhost:8000"
else
    echo "   前端应用: http://localhost:3000"
    echo "   后端API:  http://localhost:8000"
fi

echo "   API文档:  http://localhost:8000/docs"

if [ "$mode" = "1" ]; then
    echo "   数据库管理: http://localhost:8080"
    echo "     - 服务器: postgres"
    echo "     - 用户名: trading_user"
    echo "     - 密码: trading_password"
    echo "     - 数据库: trading_platform"
fi

echo ""
echo "📝 默认管理员账户："
echo "   用户名: admin"
echo "   密码: admin123"
echo ""
echo "🔧 管理命令："
echo "   查看日志: docker-compose logs -f [service_name]"
echo "   停止服务: docker-compose down"
echo "   重启服务: docker-compose restart [service_name]"
echo "   查看状态: docker-compose ps"
echo ""
echo "📋 常用服务名："
echo "   - postgres (数据库)"
echo "   - redis (缓存)"
echo "   - backend (后端API)"
echo "   - frontend (前端应用)"
if [ "$mode" = "2" ]; then
    echo "   - nginx (反向代理)"
fi
if [ "$mode" = "1" ]; then
    echo "   - adminer (数据库管理)"
fi

echo ""
echo "🎯 快速开始："
echo "1. 访问前端应用: http://localhost:3000"
echo "2. 使用默认账户登录"
echo "3. 开始使用量化交易平台！"