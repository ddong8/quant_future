#!/bin/bash

# 量化交易平台停止脚本

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

# 停止所有服务
stop_services() {
    log_info "停止量化交易平台服务..."
    
    # 停止前端和后端容器
    log_info "停止前端和后端服务..."
    docker stop trading_frontend trading_backend_final 2>/dev/null || log_warning "部分容器可能已停止"
    
    # 停止数据库服务
    log_info "停止数据库服务..."
    docker-compose down 2>/dev/null || log_warning "Docker Compose 服务可能已停止"
    
    log_success "所有服务已停止"
}

# 清理容器
cleanup_containers() {
    if [ "$1" = "--clean" ]; then
        log_info "清理容器..."
        
        # 删除应用容器
        docker rm trading_frontend trading_backend_final 2>/dev/null || true
        
        # 删除数据库容器和卷
        if [ "$2" = "--volumes" ]; then
            log_warning "删除数据卷（这将删除所有数据）..."
            docker-compose down -v 2>/dev/null || true
        else
            docker-compose down 2>/dev/null || true
        fi
        
        log_success "容器清理完成"
    fi
}

# 显示帮助信息
show_help() {
    echo "量化交易平台停止脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --clean          停止并删除容器"
    echo "  --clean --volumes 停止并删除容器和数据卷（危险操作）"
    echo "  --help           显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0               # 仅停止服务"
    echo "  $0 --clean       # 停止并清理容器"
    echo "  $0 --clean --volumes # 停止并清理所有数据（危险）"
}

# 主函数
main() {
    echo "🛑 量化交易平台停止脚本"
    echo "========================"
    
    case "$1" in
        --help)
            show_help
            exit 0
            ;;
        --clean)
            stop_services
            cleanup_containers --clean "$2"
            ;;
        "")
            stop_services
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
    
    echo ""
    log_success "🎯 操作完成！"
    
    # 显示剩余容器
    remaining=$(docker ps -q | wc -l)
    if [ "$remaining" -gt 0 ]; then
        echo ""
        log_info "剩余运行的容器："
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        echo ""
        log_info "没有运行中的容器"
    fi
}

# 运行主函数
main "$@"