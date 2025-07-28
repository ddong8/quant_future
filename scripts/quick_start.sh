#!/bin/bash

# 量化交易平台快速启动脚本
# 用于快速启动和测试系统

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    log_success "Docker环境检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p logs
    mkdir -p data/postgres
    mkdir -p data/influxdb
    mkdir -p data/redis
    mkdir -p backups
    
    log_success "目录创建完成"
}

# 创建环境配置文件
create_env_files() {
    log_info "创建环境配置文件..."
    
    # 后端环境配置
    if [ ! -f "backend/.env" ]; then
        cat > backend/.env << 'EOF'
# 应用配置
APP_NAME=量化交易平台
APP_VERSION=1.0.0
DEBUG=true
LOG_LEVEL=INFO

# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/trading_db
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=my-super-secret-auth-token
INFLUXDB_ORG=trading-org
INFLUXDB_BUCKET=market-data

# Redis配置
REDIS_URL=redis://localhost:6379/0

# JWT配置
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30

# tqsdk配置（测试环境）
TQSDK_USERNAME=test_user
TQSDK_PASSWORD=test_password

# 邮件配置（可选）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EOF
        log_success "后端环境配置文件已创建"
    else
        log_info "后端环境配置文件已存在"
    fi
    
    # 前端环境配置
    if [ ! -f "frontend/.env" ]; then
        cat > frontend/.env << 'EOF'
# API配置
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000/api/v1/ws

# 应用配置
VITE_APP_TITLE=量化交易平台
VITE_APP_VERSION=1.0.0

# 功能开关
VITE_ENABLE_MOCK=false
VITE_ENABLE_DEBUG=true
EOF
        log_success "前端环境配置文件已创建"
    else
        log_info "前端环境配置文件已存在"
    fi
}

# 创建Docker Compose文件
create_docker_compose() {
    if [ ! -f "docker-compose.yml" ]; then
        log_info "创建Docker Compose配置文件..."
        
        cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:13
    container_name: trading_postgres
    environment:
      POSTGRES_DB: trading_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./docker/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    container_name: trading_redis
    volumes:
      - ./data/redis:/data
    ports:
      - "6379:6379"
    restart: unless-stopped

  influxdb:
    image: influxdb:2.0
    container_name: trading_influxdb
    environment:
      INFLUXDB_DB: trading
      INFLUXDB_ADMIN_USER: admin
      INFLUXDB_ADMIN_PASSWORD: password
      INFLUXDB_ADMIN_TOKEN: my-super-secret-auth-token
    volumes:
      - ./data/influxdb:/var/lib/influxdb2
    ports:
      - "8086:8086"
    restart: unless-stopped

  backend:
    build: ./backend
    container_name: trading_backend
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/trading_db
      REDIS_URL: redis://redis:6379/0
      INFLUXDB_URL: http://influxdb:8086
    depends_on:
      - postgres
      - redis
      - influxdb
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./logs:/var/log/trading
    restart: unless-stopped

  frontend:
    build: ./frontend
    container_name: trading_frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  influxdb_data:
  redis_data:
EOF
        log_success "Docker Compose配置文件已创建"
    else
        log_info "Docker Compose配置文件已存在"
    fi
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 先启动数据库服务
    log_info "启动数据库服务..."
    docker-compose up -d postgres redis influxdb
    
    # 等待数据库启动
    log_info "等待数据库启动..."
    sleep 10
    
    # 检查数据库连接
    log_info "检查数据库连接..."
    for i in {1..30}; do
        if docker-compose exec -T postgres pg_isready -U postgres &>/dev/null; then
            log_success "PostgreSQL已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "PostgreSQL启动超时"
            exit 1
        fi
        sleep 1
    done
    
    # 启动应用服务
    log_info "启动应用服务..."
    docker-compose up -d backend frontend
    
    log_success "所有服务已启动"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    # 等待后端服务
    log_info "等待后端服务..."
    for i in {1..60}; do
        if curl -s http://localhost:8000/health &>/dev/null; then
            log_success "后端服务已就绪"
            break
        fi
        if [ $i -eq 60 ]; then
            log_error "后端服务启动超时"
            exit 1
        fi
        sleep 2
    done
    
    # 等待前端服务
    log_info "等待前端服务..."
    for i in {1..30}; do
        if curl -s http://localhost:3000 &>/dev/null; then
            log_success "前端服务已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "前端服务启动超时"
            exit 1
        fi
        sleep 2
    done
}

# 显示服务状态
show_status() {
    log_info "服务状态："
    docker-compose ps
    
    echo ""
    log_info "服务访问地址："
    echo "  前端应用: http://localhost:3000"
    echo "  后端API: http://localhost:8000"
    echo "  API文档: http://localhost:8000/docs"
    echo "  系统健康检查: http://localhost:8000/health"
    echo "  InfluxDB: http://localhost:8086"
    
    echo ""
    log_info "默认登录信息："
    echo "  管理员账户: admin / admin123"
    echo "  测试交易员: trader / trader123"
}

# 主函数
main() {
    echo "========================================"
    echo "量化交易平台快速启动"
    echo "========================================"
    echo ""
    
    # 检查环境
    check_docker
    
    # 创建必要文件和目录
    create_directories
    create_env_files
    create_docker_compose
    
    # 启动服务
    start_services
    
    # 等待服务就绪
    wait_for_services
    
    # 显示状态
    show_status
    
    echo ""
    echo "========================================"
    log_success "量化交易平台启动完成！"
    echo "========================================"
    
    echo ""
    log_info "使用以下命令管理服务："
    echo "  查看日志: docker-compose logs -f"
    echo "  停止服务: docker-compose down"
    echo "  重启服务: docker-compose restart"
    echo "  查看状态: docker-compose ps"
}

# 执行主函数
main "$@"