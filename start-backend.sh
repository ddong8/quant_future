#!/bin/bash

# 量化交易平台后端启动脚本
echo "🚀 启动量化交易平台后端..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装 Python 3.8+"
    exit 1
fi

echo "✅ Python 检查完成"

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

# 启动后端服务
echo "🚀 启动 FastAPI 服务器..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo ""
echo "🎉 后端服务启动成功！"
echo ""
echo "📊 服务地址："
echo "   后端API:  http://localhost:8000"
echo "   API文档:  http://localhost:8000/docs"
echo ""
echo "📝 默认管理员账户："
echo "   用户名: admin"
echo "   密码: admin123"
echo ""
echo "🔧 管理命令："
echo "   停止服务: kill $BACKEND_PID"
echo ""

# 保存进程ID
echo $BACKEND_PID > .backend.pid

# 等待用户输入来停止服务
echo "按 Ctrl+C 停止后端服务..."
trap 'echo "🛑 正在停止后端服务..."; kill $BACKEND_PID; exit' INT

# 保持脚本运行
wait