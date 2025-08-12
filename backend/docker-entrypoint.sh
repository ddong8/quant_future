#!/bin/bash
set -e

echo "🚀 启动量化交易平台后端服务..."

# 等待数据库就绪
echo "⏳ 等待数据库连接..."
while ! python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.close()
    print('✅ 数据库连接成功')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    exit(1)
"; do
  echo "⏳ 等待数据库启动..."
  sleep 2
done

# 运行数据库迁移
echo "🗄️  执行数据库迁移..."
alembic upgrade head

# 初始化角色权限
echo "👤 初始化角色权限..."
python -m app.scripts.init_roles_permissions || echo "⚠️  角色权限初始化失败，可能已存在"

# 创建示例数据（开发环境）
if [ "$ENVIRONMENT" = "development" ]; then
    echo "📊 创建示例数据..."
    python -c "
import asyncio
from app.core.database import get_db
from app.services.sample_data_service import create_sample_data

async def main():
    try:
        db = next(get_db())
        await create_sample_data(db)
        print('✅ 示例数据创建成功')
    except Exception as e:
        print(f'⚠️  示例数据创建失败: {e}')

if __name__ == '__main__':
    asyncio.run(main())
" || echo "⚠️  示例数据创建失败"
fi

echo "🎉 后端服务启动完成！"

# 启动应用
exec python mock_app.py