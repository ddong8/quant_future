#!/bin/bash

# 量化交易平台环境设置脚本
echo "⚙️  设置量化交易平台环境..."

# 创建必要的目录
echo "📁 创建项目目录..."
mkdir -p logs
mkdir -p data
mkdir -p backups
mkdir -p uploads

# 设置权限
echo "🔐 设置文件权限..."
chmod +x start.sh
chmod +x stop.sh
chmod +x restart.sh
chmod +x logs.sh

# 创建环境配置文件
echo "📝 创建环境配置..."

# 后端环境配置
cat > backend/.env << EOF
# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/trading_platform
TEST_DATABASE_URL=postgresql://postgres:password@localhost:5432/trading_platform_test

# JWT配置
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 邮件配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# 应用配置
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=INFO

# 市场数据配置
MARKET_DATA_PROVIDER=mock
API_KEY=your-market-data-api-key

# 文件上传配置
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760

# 安全配置
CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]
EOF

# 前端环境配置
cat > frontend/.env << EOF
# API配置
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000

# 应用配置
VITE_APP_TITLE=量化交易平台
VITE_APP_VERSION=1.0.0

# 功能开关
VITE_ENABLE_MOCK=true
VITE_ENABLE_DEBUG=true

# 第三方服务
VITE_SENTRY_DSN=
VITE_GOOGLE_ANALYTICS_ID=
EOF

# 创建数据库初始化脚本
cat > init_db.sql << EOF
-- 创建数据库
CREATE DATABASE trading_platform;
CREATE DATABASE trading_platform_test;

-- 创建用户
CREATE USER trading_user WITH PASSWORD 'trading_password';

-- 授权
GRANT ALL PRIVILEGES ON DATABASE trading_platform TO trading_user;
GRANT ALL PRIVILEGES ON DATABASE trading_platform_test TO trading_user;
EOF

echo "✅ 环境设置完成！"
echo ""
echo "📋 下一步操作："
echo "1. 配置数据库连接 (编辑 backend/.env)"
echo "2. 安装数据库: psql -U postgres -f init_db.sql"
echo "3. 启动服务: ./start.sh"
echo ""
echo "📖 配置文件位置："
echo "   后端配置: backend/.env"
echo "   前端配置: frontend/.env"
echo "   数据库初始化: init_db.sql"