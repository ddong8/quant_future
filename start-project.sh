#!/bin/bash

# 量化交易平台快速启动脚本
# 使用国内镜像源和优化配置

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

# 检查 Docker 是否运行
check_docker() {
    if ! docker info &> /dev/null; then
        log_error "Docker 服务未运行，请启动 Docker"
        exit 1
    fi
    log_success "Docker 服务正常运行"
}

# 启动数据库服务
start_databases() {
    log_info "启动数据库服务..."
    
    # 启动 PostgreSQL, Redis, InfluxDB
    docker-compose up -d postgres redis influxdb
    
    # 等待服务健康
    log_info "等待数据库服务就绪..."
    sleep 10
    
    # 检查服务状态
    if docker-compose ps | grep -q "healthy"; then
        log_success "数据库服务启动成功"
    else
        log_warning "部分数据库服务可能未完全就绪"
    fi
}

# 启动后端服务
start_backend() {
    log_info "启动后端服务..."
    
    # 检查是否有后端镜像
    if ! docker images | grep -q "quant_future-backend:final"; then
        log_info "构建后端镜像..."
        docker build -t quant_future-backend:final backend/
    fi
    
    # 启动后端容器
    docker run -d --name trading_backend_final --network trading_network -p 8000:8000 \
      -e DATABASE_URL=postgresql://postgres:password@trading_postgres:5432/trading_db \
      -e REDIS_URL=redis://trading_redis:6379/0 \
      -e INFLUXDB_URL=http://trading_influxdb:8086 \
      -e SECRET_KEY=your-super-secret-key-change-this-in-production \
      -e DEBUG=true \
      -e SKIP_INFLUXDB_CHECK=true \
      quant_future-backend:final 2>/dev/null || log_warning "后端容器可能已存在"
    
    # 等待后端启动
    log_info "等待后端服务启动..."
    sleep 15
    
    # 检查后端健康状态
    if curl -f http://localhost:8000/api/v1/health/ &> /dev/null; then
        log_success "后端服务启动成功"
        
        # 初始化数据库数据
        log_info "初始化数据库数据..."
        docker exec trading_backend_final python init_db.py 2>/dev/null || log_warning "数据库可能已初始化"
        log_success "数据库初始化完成"
    else
        log_error "后端服务启动失败"
        docker logs trading_backend_final | tail -10
        exit 1
    fi
}

# 启动前端服务
start_frontend() {
    log_info "启动前端服务..."
    
    # 启动前端开发服务器
    docker run -d --name trading_frontend --network trading_network -p 3000:3000 \
      -v $(pwd)/frontend:/app \
      -w /app \
      -e VITE_API_BASE_URL=http://localhost:8000/api/v1 \
      -e VITE_WS_BASE_URL=ws://localhost:8000/api/v1/ws \
      -e VITE_API_PROXY_TARGET=http://trading_backend_final:8000 \
      -e VITE_WS_PROXY_TARGET=ws://trading_backend_final:8000 \
      node:18-alpine \
      sh -c "npm config set registry https://registry.npmmirror.com && npm install && npm run dev -- --host 0.0.0.0 --port 3000" \
      2>/dev/null || log_warning "前端容器可能已存在"
    
    # 等待前端启动
    log_info "等待前端服务启动（可能需要安装依赖）..."
    sleep 30
    
    # 检查前端是否可访问
    if curl -f http://localhost:3000 &> /dev/null; then
        log_success "前端服务启动成功"
    else
        log_warning "前端服务可能仍在启动中"
    fi
}

# 显示服务状态
show_status() {
    log_info "服务状态："
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    log_info "访问地址："
    echo "  前端应用: http://localhost:3000"
    echo "  后端 API: http://localhost:8000"
    echo "  API 文档: http://localhost:8000/docs"
    echo "  健康检查: http://localhost:8000/api/v1/health/"
}

# 清理函数
cleanup() {
    if [ "$1" = "--clean" ]; then
        log_info "清理现有容器..."
        docker stop trading_frontend trading_backend_final 2>/dev/null || true
        docker rm trading_frontend trading_backend_final 2>/dev/null || true
        docker-compose down 2>/dev/null || true
        log_success "清理完成"
    fi
}

# 主函数
main() {
    echo "🚀 量化交易平台启动脚本"
    echo "=========================="
    
    # 处理参数
    if [ "$1" = "--clean" ]; then
        cleanup --clean
    fi
    
    # 检查环境
    check_docker
    
    # 启动服务
    start_databases
    start_backend
    start_frontend
    
    # 显示状态
    show_status
    
    echo ""
    log_success "🎉 项目启动完成！"
    echo ""
    echo "💡 提示："
    echo "  - 前端可能需要几分钟来安装依赖和启动"
    echo "  - 如果遇到问题，请查看容器日志：docker logs <container_name>"
    echo "  - 要停止所有服务：docker stop \$(docker ps -q)"
    echo "  - 要清理并重新启动：$0 --clean"
}

# 运行主函数
main "$@"