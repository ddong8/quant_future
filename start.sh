#!/bin/bash

# 量化交易平台启动脚本
echo "🚀 启动量化交易平台..."

# 检查必要的依赖
echo "📋 检查系统依赖..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装 Python 3.8+"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    echo "📦 请安装 Node.js 16+ :"
    echo "   macOS: brew install node"
    echo "   Ubuntu: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs"
    echo "   或访问: https://nodejs.org/"
    echo ""
    echo "🔧 如果只想启动后端服务，请运行: ./start-backend.sh"
    exit 1
fi

# 检查 PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL 未安装，请确保数据库服务可用"
fi

echo "✅ 系统依赖检查完成"

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"

# 启动后端服务
echo "🔧 启动后端服务..."
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 安装后端依赖..."
pip install -r requirements.txt

# 数据库迁移
echo "🗄️  执行数据库迁移..."
alembic upgrade head

# 初始化角色权限
echo "👤 初始化角色权限..."
python -m app.scripts.init_roles_permissions

# 启动后端服务（后台运行）
echo "🚀 启动 FastAPI 服务器..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 等待后端启动
sleep 5

# 启动前端服务
echo "🎨 启动前端服务..."
cd ../frontend

# 安装依赖
echo "📦 安装前端依赖..."
npm install

# 启动前端开发服务器（后台运行）
echo "🚀 启动 Vue.js 开发服务器..."
npm run dev &
FRONTEND_PID=$!

# 等待前端启动
sleep 10

echo ""
echo "🎉 量化交易平台启动成功！"
echo ""
echo "📊 服务地址："
echo "   前端应用: http://localhost:5173"
echo "   后端API:  http://localhost:8000"
echo "   API文档:  http://localhost:8000/docs"
echo ""
echo "🔧 管理命令："
echo "   停止服务: ./stop.sh"
echo "   查看日志: ./logs.sh"
echo "   重启服务: ./restart.sh"
echo ""
echo "📝 默认管理员账户："
echo "   用户名: admin"
echo "   密码: admin123"
echo ""

# 保存进程ID
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# 等待用户输入来停止服务
echo "按 Ctrl+C 停止所有服务..."
trap 'echo "🛑 正在停止服务..."; kill $BACKEND_PID $FRONTEND_PID; exit' INT

# 保持脚本运行
wait