#!/bin/bash

# 启动脚本
set -e

echo "启动量化交易平台..."

# 等待数据库就绪
echo "等待数据库连接..."
while ! nc -z ${DATABASE_HOST:-db} ${DATABASE_PORT:-5432}; do
    echo "等待PostgreSQL启动..."
    sleep 2
done

# 等待Redis就绪
echo "等待Redis连接..."
while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
    echo "等待Redis启动..."
    sleep 2
done

# 等待InfluxDB就绪
echo "等待InfluxDB连接..."
while ! nc -z ${INFLUXDB_HOST:-influxdb} ${INFLUXDB_PORT:-8086}; do
    echo "等待InfluxDB启动..."
    sleep 2
done

# 创建日志目录
mkdir -p /var/log/supervisor
mkdir -p /app/logs

# 数据库迁移
echo "执行数据库迁移..."
cd /app/backend
python -m alembic upgrade head

# 初始化数据
echo "初始化数据..."
python init_db.py

# 启动supervisor
echo "启动服务..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf