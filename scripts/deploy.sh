#!/bin/bash

# 量化交易平台部署脚本
# 支持Docker和Kubernetes部署

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

# 检查依赖
check_dependencies() {
    log_info "检查部署依赖..."
    
    if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        if ! command -v docker &> /dev/null; then
            log_error "Docker未安装"
            exit 1
        fi
        
        if ! command -v docker-compose &> /dev/null; then
            log_error "Docker Compose未安装"
            exit 1
        fi
    elif [ "$DEPLOYMENT_TYPE" = "k8s" ]; then
        if ! command -v kubectl &> /dev/null; then
            log_error "kubectl未安装"
            exit 1
        fi
        
        if ! kubectl cluster-info &> /dev/null; then
            log_error "无法连接到Kubernetes集群"
            exit 1
        fi
    fi
    
    log_success "依赖检查完成"
}

# 构建镜像
build_image() {
    log_info "构建应用镜像..."
    
    # 生成版本标签
    VERSION=${VERSION:-$(git rev-parse --short HEAD)}
    IMAGE_TAG="quant-trading:${VERSION}"
    
    log_info "构建镜像: $IMAGE_TAG"
    docker build -t $IMAGE_TAG .
    docker tag $IMAGE_TAG quant-trading:latest
    
    log_success "镜像构建完成: $IMAGE_TAG"
}

# Docker部署
deploy_docker() {
    log_info "开始Docker部署..."
    
    # 检查环境变量文件
    if [ ! -f ".env" ]; then
        log_warning "未找到.env文件，创建默认配置"
        cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
INFLUXDB_TOKEN=$(openssl rand -hex 32)
ENVIRONMENT=production
EOF
    fi
    
    # 停止现有服务
    log_info "停止现有服务..."
    docker-compose down
    
    # 启动服务
    log_info "启动服务..."
    docker-compose up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        log_success "Docker部署完成"
        log_info "应用访问地址: http://localhost"
        log_info "API文档地址: http://localhost:8000/docs"
        log_info "Grafana监控: http://localhost:3000 (admin/admin123)"
    else
        log_error "部署失败，请检查日志"
        docker-compose logs
        exit 1
    fi
}

# Kubernetes部署
deploy_k8s() {
    log_info "开始Kubernetes部署..."
    
    # 创建命名空间和配置
    log_info "创建命名空间和配置..."
    kubectl apply -f k8s/namespace.yaml
    
    # 部署数据库
    log_info "部署PostgreSQL数据库..."
    kubectl apply -f k8s/postgres.yaml
    
    # 等待数据库就绪
    log_info "等待数据库就绪..."
    kubectl wait --for=condition=ready pod -l app=postgres -n quant-trading --timeout=300s
    
    # 部署Redis
    log_info "部署Redis缓存..."
    kubectl apply -f k8s/redis.yaml
    
    # 部署InfluxDB
    log_info "部署InfluxDB..."
    kubectl apply -f k8s/influxdb.yaml
    
    # 部署应用
    log_info "部署应用..."
    kubectl apply -f k8s/app.yaml
    
    # 等待应用就绪
    log_info "等待应用就绪..."
    kubectl wait --for=condition=available deployment/quant-trading-app -n quant-trading --timeout=300s
    
    # 获取服务信息
    SERVICE_IP=$(kubectl get service quant-trading-service -n quant-trading -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ -z "$SERVICE_IP" ]; then
        SERVICE_IP=$(kubectl get service quant-trading-service -n quant-trading -o jsonpath='{.spec.clusterIP}')
        log_info "应用访问地址: http://$SERVICE_IP (集群内部)"
    else
        log_info "应用访问地址: http://$SERVICE_IP"
    fi
    
    log_success "Kubernetes部署完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        HEALTH_URL="http://localhost:8000/health"
    else
        # K8s部署需要端口转发或使用服务IP
        kubectl port-forward service/quant-trading-service 8000:8000 -n quant-trading &
        PF_PID=$!
        sleep 5
        HEALTH_URL="http://localhost:8000/health"
    fi
    
    # 检查API健康状态
    for i in {1..10}; do
        if curl -f $HEALTH_URL > /dev/null 2>&1; then
            log_success "健康检查通过"
            [ "$DEPLOYMENT_TYPE" = "k8s" ] && kill $PF_PID 2>/dev/null || true
            return 0
        fi
        log_info "等待服务启动... ($i/10)"
        sleep 10
    done
    
    log_error "健康检查失败"
    [ "$DEPLOYMENT_TYPE" = "k8s" ] && kill $PF_PID 2>/dev/null || true
    exit 1
}

# 数据库迁移
run_migrations() {
    log_info "执行数据库迁移..."
    
    if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        docker-compose exec app python -m alembic upgrade head
    else
        kubectl exec -it deployment/quant-trading-app -n quant-trading -- python -m alembic upgrade head
    fi
    
    log_success "数据库迁移完成"
}

# 显示帮助信息
show_help() {
    cat << EOF
量化交易平台部署脚本

用法: $0 [选项] <命令>

命令:
  deploy          部署应用
  health-check    健康检查
  migrate         数据库迁移
  help            显示帮助信息

选项:
  -t, --type      部署类型 (docker|k8s) [默认: docker]
  -v, --version   版本标签 [默认: git commit hash]
  -e, --env       环境 (dev|staging|prod) [默认: prod]
  -h, --help      显示帮助信息

示例:
  $0 -t docker deploy
  $0 -t k8s -v v1.0.0 deploy
  $0 health-check
EOF
}

# 主函数
main() {
    # 默认参数
    DEPLOYMENT_TYPE="docker"
    ENVIRONMENT="prod"
    COMMAND=""
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                DEPLOYMENT_TYPE="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            deploy|health-check|migrate|help)
                COMMAND="$1"
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 检查命令
    if [ -z "$COMMAND" ]; then
        log_error "请指定命令"
        show_help
        exit 1
    fi
    
    # 验证部署类型
    if [ "$DEPLOYMENT_TYPE" != "docker" ] && [ "$DEPLOYMENT_TYPE" != "k8s" ]; then
        log_error "不支持的部署类型: $DEPLOYMENT_TYPE"
        exit 1
    fi
    
    log_info "部署配置: 类型=$DEPLOYMENT_TYPE, 环境=$ENVIRONMENT, 版本=${VERSION:-latest}"
    
    # 执行命令
    case $COMMAND in
        deploy)
            check_dependencies
            build_image
            if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
                deploy_docker
            else
                deploy_k8s
            fi
            run_migrations
            health_check
            ;;
        health-check)
            health_check
            ;;
        migrate)
            run_migrations
            ;;
        help)
            show_help
            ;;
        *)
            log_error "未知命令: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"