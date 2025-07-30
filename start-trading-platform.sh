#!/bin/bash

# 量化交易平台启动脚本
# 提供完整的环境检查和启动流程

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

# 检查必需的命令
check_requirements() {
    log_info "检查系统要求..."
    
    local missing_commands=()
    
    if ! command -v docker &> /dev/null; then
        missing_commands+=("docker")
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing_commands+=("docker-compose")
    fi
    
    if [ ${#missing_commands[@]} -ne 0 ]; then
        log_error "缺少必需的命令: ${missing_commands[*]}"
        log_error "请安装 Docker 和 Docker Compose"
        exit 1
    fi
    
    log_success "系统要求检查通过"
}

# 检查环境变量文件
check_env_file() {
    log_info "检查环境变量配置..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.template" ]; then
            log_warning ".env 文件不存在，从模板创建..."
            cp .env.template .env
            log_success "已创建 .env 文件，请根据需要修改配置"
        else
            log_error ".env 和 .env.template 文件都不存在"
            exit 1
        fi
    else
        log_success "环境变量文件存在"
    fi
}

# 检查 Docker 服务状态
check_docker_service() {
    log_info "检查 Docker 服务状态..."
    
    if ! docker info &> /dev/null; then
        log_error "Docker 服务未运行，请启动 Docker"
        exit 1
    fi
    
    log_success "Docker 服务正常运行"
}

# 清理旧容器和卷（可选）
cleanup_containers() {
    if [ "$1" = "--clean" ]; then
        log_info "清理旧容器和卷..."
        
        # 停止并删除容器
        docker-compose down --remove-orphans 2>/dev/null || true
        
        # 删除相关卷（谨慎操作）
        if [ "$2" = "--volumes" ]; then
            log_warning "删除数据卷（这将删除所有数据）..."
            docker-compose down -v 2>/dev/null || true
        fi
        
        log_success "清理完成"
    fi
}

# 构建和启动服务
start_services() {
    log_info "构建和启动服务..."
    
    # 构建镜像
    log_info "构建 Docker 镜像..."
    docker-compose build --no-cache
    
    # 启动服务
    log_info "启动服务..."
    docker-compose up -d
    
    log_success "服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    local max_wait=120
    local wait_time=0
    local check_interval=5
    
    while [ $wait_time -lt $max_wait ]; do
        if curl -f http://localhost:8000/api/v1/health/ &> /dev/null; then
            log_success "后端服务已就绪"
            break
        fi
        
        log_info "等待后端服务就绪... (${wait_time}s/${max_wait}s)"
        sleep $check_interval
        wait_time=$((wait_time + check_interval))
    done
    
    if [ $wait_time -ge $max_wait ]; then
        log_error "后端服务在 ${max_wait} 秒内未就绪"
        log_info "查看服务日志："
        docker-compose logs backend
        exit 1
    fi
    
    # 检查前端服务
    wait_time=0
    while [ $wait_time -lt $max_wait ]; do
        if curl -f http://localhost:3000/ &> /dev/null; then
            log_success "前端服务已就绪"
            break
        fi
        
        log_info "等待前端服务就绪... (${wait_time}s/${max_wait}s)"
        sleep $check_interval
        wait_time=$((wait_time + check_interval))
    done
    
    if [ $wait_time -ge $max_wait ]; then
        log_warning "前端服务在 ${max_wait} 秒内未就绪，但可能仍在启动中"
    fi
}

# 显示服务状态
show_status() {
    log_info "服务状态："
    docker-compose ps
    
    echo ""
    log_info "服务访问地址："
    echo "  前端应用: http://localhost:3000"
    echo "  后端 API: http://localhost:8000"
    echo "  API 文档: http://localhost:8000/docs"
    echo "  PostgreSQL: localhost:5432"
    echo "  Redis: localhost:6379"
    echo "  InfluxDB: http://localhost:8086"
}

# 显示日志
show_logs() {
    if [ -n "$1" ]; then
        docker-compose logs -f "$1"
    else
        docker-compose logs -f
    fi
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    docker-compose down
    log_success "服务已停止"
}

# 显示帮助信息
show_help() {
    echo "量化交易平台启动脚本"
    echo ""
    echo "用法: $0 [选项] [命令]"
    echo ""
    echo "命令:"
    echo "  start          启动所有服务（默认）"
    echo "  stop           停止所有服务"
    echo "  restart        重启所有服务"
    echo "  status         显示服务状态"
    echo "  logs [服务名]   显示日志"
    echo "  help           显示此帮助信息"
    echo ""
    echo "选项:"
    echo "  --clean        启动前清理旧容器"
    echo "  --volumes      同时删除数据卷（与 --clean 一起使用）"
    echo ""
    echo "示例:"
    echo "  $0                    # 启动所有服务"
    echo "  $0 start --clean     # 清理后启动"
    echo "  $0 logs backend      # 查看后端日志"
    echo "  $0 stop              # 停止所有服务"
}

# 主函数
main() {
    local command="start"
    local clean_flag=""
    local volumes_flag=""
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            start|stop|restart|status|logs|help)
                command="$1"
                shift
                ;;
            --clean)
                clean_flag="--clean"
                shift
                ;;
            --volumes)
                volumes_flag="--volumes"
                shift
                ;;
            *)
                if [ "$command" = "logs" ] && [ -z "$2" ]; then
                    # logs 命令的服务名参数
                    show_logs "$1"
                    exit 0
                else
                    log_error "未知参数: $1"
                    show_help
                    exit 1
                fi
                ;;
        esac
    done
    
    case $command in
        start)
            check_requirements
            check_env_file
            check_docker_service
            cleanup_containers "$clean_flag" "$volumes_flag"
            start_services
            wait_for_services
            show_status
            ;;
        stop)
            stop_services
            ;;
        restart)
            stop_services
            sleep 2
            check_requirements
            check_env_file
            check_docker_service
            start_services
            wait_for_services
            show_status
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        help)
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"