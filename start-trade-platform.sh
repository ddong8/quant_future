#!/bin/bash

# 量化交易平台启动脚本 (支持响应式多终端)
# 提供完整的环境检查、依赖安装和启动流程

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

log_feature() {
    echo -e "${CYAN}[FEATURE]${NC} $1"
}

# 显示启动横幅
show_banner() {
    echo -e "${CYAN}"
    echo "========================================================"
    echo "    📱 量化交易平台 - 多终端响应式版本"
    echo "========================================================"
    echo -e "${NC}"
    echo "✨ 新功能特性："
    echo "  📱 移动端优化 - 完美适配手机和平板"
    echo "  🎨 响应式设计 - 自动适应各种屏幕尺寸"
    echo "  ⚡ 性能监控 - 实时FPS和内存监控"
    echo "  🔄 PWA支持 - 可安装为桌面应用"
    echo "  ♿ 可访问性 - 支持键盘导航和屏幕阅读器"
    echo ""
}

# 检查系统要求
check_system_requirements() {
    log_step "检查系统要求..."
    
    local missing_commands=()
    local os_type=$(uname -s)
    
    # 检查操作系统
    log_info "检测到操作系统: $os_type"
    
    # 检查必需的命令
    if ! command -v docker &> /dev/null; then
        missing_commands+=("docker")
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing_commands+=("docker-compose")
    fi
    
    if ! command -v node &> /dev/null; then
        missing_commands+=("node")
    fi
    
    if ! command -v npm &> /dev/null; then
        missing_commands+=("npm")
    fi
    
    if ! command -v python3 &> /dev/null; then
        missing_commands+=("python3")
    fi
    
    if [ ${#missing_commands[@]} -ne 0 ]; then
        log_error "缺少必需的命令: ${missing_commands[*]}"
        echo ""
        echo "安装指南："
        echo "  macOS: brew install docker docker-compose node python3"
        echo "  Ubuntu: apt-get install docker.io docker-compose nodejs npm python3"
        echo "  CentOS: yum install docker docker-compose nodejs npm python3"
        exit 1
    fi
    
    # 检查版本
    local node_version=$(node --version | cut -d'v' -f2)
    local npm_version=$(npm --version)
    local python_version=$(python3 --version | cut -d' ' -f2)
    
    log_info "Node.js版本: $node_version"
    log_info "npm版本: $npm_version"
    log_info "Python版本: $python_version"
    
    log_success "系统要求检查通过"
}

# 检查Docker服务
check_docker_service() {
    log_step "检查Docker服务状态..."
    
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行"
        echo ""
        echo "启动Docker服务："
        echo "  macOS: 启动Docker Desktop应用"
        echo "  Linux: sudo systemctl start docker"
        exit 1
    fi
    
    log_success "Docker服务正常运行"
}

# 创建必要的目录结构
create_directories() {
    log_step "创建项目目录结构..."
    
    local directories=(
        "logs"
        "data/postgres"
        "data/influxdb"
        "data/redis"
        "backups"
        "uploads"
        "frontend/public/icons"
        "frontend/public/screenshots"
        "frontend/src/assets/images"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "创建目录: $dir"
        fi
    done
    
    log_success "目录结构创建完成"
}

# 检查和创建环境配置文件
setup_environment_files() {
    log_step "设置环境配置文件..."
    
    # 后端环境配置
    if [ ! -f "backend/.env" ]; then
        log_info "创建后端环境配置文件..."
        cat > backend/.env << 'EOF'
# 应用配置
APP_NAME=量化交易平台
APP_VERSION=1.0.0
DEBUG=true
LOG_LEVEL=INFO
ENVIRONMENT=development

# 数据库配置
DATABASE_URL=postgresql://trading_user:trading_password@postgres:5432/trading_platform
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=my-super-secret-auth-token
INFLUXDB_ORG=trading-org
INFLUXDB_BUCKET=market-data

# Redis配置
REDIS_URL=redis://redis:6379/0

# JWT配置
SECRET_KEY=your-super-secret-key-change-this-in-production-environment
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS配置
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"]

# tqsdk配置（测试环境）
TQSDK_USERNAME=test_user
TQSDK_PASSWORD=test_password
SKIP_INFLUXDB_CHECK=true

# 邮件配置（可选）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# 文件上传配置
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=10485760
EOF
        log_success "后端环境配置文件已创建"
    else
        log_info "后端环境配置文件已存在"
    fi
    
    # 前端环境配置
    if [ ! -f "frontend/.env" ]; then
        log_info "创建前端环境配置文件..."
        cat > frontend/.env << 'EOF'
# API配置
VITE_API_BASE_URL=/api
VITE_WS_BASE_URL=/api/v1/ws

# 应用配置
VITE_APP_TITLE=量化交易平台
VITE_APP_VERSION=1.0.0
VITE_APP_DESCRIPTION=专业的量化交易平台，支持策略开发、回测分析、实盘交易

# 功能开关
VITE_ENABLE_MOCK=false
VITE_ENABLE_DEBUG=true
VITE_ENABLE_PWA=true
VITE_ENABLE_PERFORMANCE_MONITOR=true

# PWA配置
VITE_PWA_NAME=量化交易平台
VITE_PWA_SHORT_NAME=量化交易
VITE_PWA_THEME_COLOR=#409EFF
VITE_PWA_BACKGROUND_COLOR=#ffffff

# 响应式配置
VITE_MOBILE_BREAKPOINT=768
VITE_TABLET_BREAKPOINT=1024
VITE_DESKTOP_BREAKPOINT=1200
EOF
        log_success "前端环境配置文件已创建"
    else
        log_info "前端环境配置文件已存在"
    fi
    
    # 根目录环境配置
    if [ ! -f ".env" ]; then
        log_info "创建根目录环境配置文件..."
        cat > .env << 'EOF'
# Docker Compose环境变量
COMPOSE_PROJECT_NAME=trading-platform

# 数据库配置
POSTGRES_DB=trading_platform
POSTGRES_USER=trading_user
POSTGRES_PASSWORD=trading_password

# Redis配置
REDIS_PASSWORD=

# InfluxDB配置
INFLUXDB_ADMIN_USER=admin
INFLUXDB_ADMIN_PASSWORD=admin123
INFLUXDB_ADMIN_TOKEN=my-super-secret-auth-token

# 端口配置
FRONTEND_PORT=3000
BACKEND_PORT=8000
POSTGRES_PORT=5432
REDIS_PORT=6379
INFLUXDB_PORT=8086
NGINX_PORT=80
NGINX_SSL_PORT=443
EOF
        log_success "根目录环境配置文件已创建"
    else
        log_info "根目录环境配置文件已存在"
    fi
}

# 安装前端依赖
install_frontend_dependencies() {
    log_step "安装前端依赖..."
    
    if [ ! -d "frontend/node_modules" ]; then
        log_info "首次安装前端依赖，这可能需要几分钟..."
        cd frontend
        
        # 检查是否有package-lock.json，如果有则使用npm ci
        if [ -f "package-lock.json" ]; then
            npm ci
        else
            npm install
        fi
        
        # 安装PWA相关依赖
        log_info "安装PWA和响应式相关依赖..."
        npm install vite-plugin-pwa@^0.17.4 workbox-window@^7.0.0 --save-dev
        
        cd ..
        log_success "前端依赖安装完成"
    else
        log_info "前端依赖已存在，跳过安装"
        
        # 检查是否需要更新PWA依赖
        cd frontend
        if ! npm list vite-plugin-pwa &> /dev/null; then
            log_info "安装PWA相关依赖..."
            npm install vite-plugin-pwa@^0.17.4 workbox-window@^7.0.0 --save-dev
        fi
        cd ..
    fi
}

# 安装后端依赖
install_backend_dependencies() {
    log_step "检查后端依赖..."
    
    if [ ! -f "backend/requirements.txt" ]; then
        log_warning "后端requirements.txt文件不存在，跳过依赖检查"
        return
    fi
    
    log_info "后端依赖将在Docker容器中安装"
    log_success "后端依赖检查完成"
}

# 创建PWA图标（如果不存在）
create_pwa_icons() {
    log_step "检查PWA图标..."
    
    local icon_dir="frontend/public/icons"
    local icon_sizes=(72 96 128 144 152 192 384 512)
    
    # 检查是否存在任何图标
    local has_icons=false
    for size in "${icon_sizes[@]}"; do
        if [ -f "$icon_dir/icon-${size}x${size}.png" ]; then
            has_icons=true
            break
        fi
    done
    
    if [ "$has_icons" = false ]; then
        log_warning "PWA图标不存在，创建占位符图标..."
        
        # 创建一个简单的SVG图标并转换为PNG（如果有ImageMagick）
        if command -v convert &> /dev/null; then
            # 创建SVG图标
            cat > "$icon_dir/icon.svg" << 'EOF'
<svg width="512" height="512" xmlns="http://www.w3.org/2000/svg">
  <rect width="512" height="512" fill="#409EFF"/>
  <text x="256" y="280" font-family="Arial, sans-serif" font-size="120" fill="white" text-anchor="middle">量化</text>
  <text x="256" y="380" font-family="Arial, sans-serif" font-size="80" fill="white" text-anchor="middle">交易</text>
</svg>
EOF
            
            # 转换为各种尺寸的PNG
            for size in "${icon_sizes[@]}"; do
                convert "$icon_dir/icon.svg" -resize "${size}x${size}" "$icon_dir/icon-${size}x${size}.png"
            done
            
            log_success "PWA图标创建完成"
        else
            log_warning "ImageMagick未安装，无法自动创建图标"
            log_info "请手动添加以下尺寸的图标到 $icon_dir 目录："
            for size in "${icon_sizes[@]}"; do
                echo "  - icon-${size}x${size}.png"
            done
        fi
    else
        log_success "PWA图标已存在"
    fi
}

# 构建前端应用
build_frontend() {
    log_step "构建前端应用..."
    
    cd frontend
    
    # 检查是否使用PWA配置
    if [ -f "vite.config.pwa.ts" ]; then
        log_info "使用PWA配置构建..."
        # 临时重命名配置文件
        if [ -f "vite.config.ts" ]; then
            mv vite.config.ts vite.config.ts.backup
        fi
        mv vite.config.pwa.ts vite.config.ts
    fi
    
    # 构建应用
    npm run build
    
    # 恢复配置文件
    if [ -f "vite.config.ts.backup" ]; then
        mv vite.config.ts vite.config.pwa.ts
        mv vite.config.ts.backup vite.config.ts
    fi
    
    cd ..
    log_success "前端应用构建完成"
}

# 启动Docker服务
start_docker_services() {
    log_step "启动Docker服务..."
    
    # 检查docker-compose.yml是否存在
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.yml文件不存在"
        exit 1
    fi
    
    # 停止现有服务（如果有）
    log_info "停止现有服务..."
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # 构建镜像
    log_info "构建Docker镜像..."
    docker-compose build --no-cache
    
    # 启动服务
    log_info "启动服务..."
    docker-compose up -d
    
    log_success "Docker服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log_step "等待服务就绪..."
    
    local max_wait=180
    local wait_time=0
    local check_interval=5
    
    # 等待数据库服务
    log_info "等待数据库服务..."
    while [ $wait_time -lt $max_wait ]; do
        if docker-compose exec -T postgres pg_isready -U trading_user -d trading_platform &> /dev/null; then
            log_success "PostgreSQL已就绪"
            break
        fi
        
        if [ $wait_time -eq 0 ]; then
            log_info "等待PostgreSQL启动..."
        fi
        
        sleep $check_interval
        wait_time=$((wait_time + check_interval))
        
        if [ $((wait_time % 30)) -eq 0 ]; then
            log_info "PostgreSQL启动中... (${wait_time}s/${max_wait}s)"
        fi
    done
    
    if [ $wait_time -ge $max_wait ]; then
        log_error "PostgreSQL在 ${max_wait} 秒内未就绪"
        show_service_logs "postgres"
        exit 1
    fi
    
    # 等待Redis服务
    log_info "等待Redis服务..."
    wait_time=0
    while [ $wait_time -lt 60 ]; do
        if docker-compose exec -T redis redis-cli ping &> /dev/null; then
            log_success "Redis已就绪"
            break
        fi
        
        sleep $check_interval
        wait_time=$((wait_time + check_interval))
    done
    
    # 等待后端服务
    log_info "等待后端服务..."
    wait_time=0
    while [ $wait_time -lt $max_wait ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "后端服务已就绪"
            break
        fi
        
        if [ $wait_time -eq 0 ]; then
            log_info "等待后端服务启动..."
        fi
        
        sleep $check_interval
        wait_time=$((wait_time + check_interval))
        
        if [ $((wait_time % 30)) -eq 0 ]; then
            log_info "后端服务启动中... (${wait_time}s/${max_wait}s)"
        fi
    done
    
    if [ $wait_time -ge $max_wait ]; then
        log_error "后端服务在 ${max_wait} 秒内未就绪"
        show_service_logs "backend"
        exit 1
    fi
    
    # 等待前端服务
    log_info "等待前端服务..."
    wait_time=0
    while [ $wait_time -lt 120 ]; do
        if curl -f http://localhost:3000/ &> /dev/null; then
            log_success "前端服务已就绪"
            break
        fi
        
        if [ $wait_time -eq 0 ]; then
            log_info "等待前端服务启动..."
        fi
        
        sleep $check_interval
        wait_time=$((wait_time + check_interval))
        
        if [ $((wait_time % 30)) -eq 0 ]; then
            log_info "前端服务启动中... (${wait_time}s/${max_wait}s)"
        fi
    done
    
    if [ $wait_time -ge 120 ]; then
        log_warning "前端服务在120秒内未完全就绪，但可能仍在启动中"
    fi
}

# 显示服务状态
show_service_status() {
    log_step "服务状态检查..."
    
    echo ""
    log_info "Docker容器状态："
    docker-compose ps
    
    echo ""
    log_info "服务健康检查："
    
    # 检查各个服务
    local services=("postgres:5432" "redis:6379" "backend:8000" "frontend:3000")
    
    for service in "${services[@]}"; do
        local name=$(echo $service | cut -d':' -f1)
        local port=$(echo $service | cut -d':' -f2)
        
        if nc -z localhost $port 2>/dev/null; then
            echo -e "  ✅ $name (端口 $port) - ${GREEN}运行中${NC}"
        else
            echo -e "  ❌ $name (端口 $port) - ${RED}未响应${NC}"
        fi
    done
}

# 显示访问信息
show_access_info() {
    echo ""
    echo -e "${CYAN}========================================================"
    echo "🎉 量化交易平台启动成功！"
    echo "========================================================${NC}"
    echo ""
    echo -e "${GREEN}📱 多终端访问地址：${NC}"
    echo "  🖥️  桌面端: http://localhost:3000"
    echo "  📱 移动端: http://localhost:3000 (自动适配)"
    echo "  📊 API接口: http://localhost:8000"
    echo "  📚 API文档: http://localhost:8000/docs"
    echo "  🔍 健康检查: http://localhost:8000/health"
    echo ""
    echo -e "${BLUE}🗄️ 数据库访问：${NC}"
    echo "  🐘 PostgreSQL: localhost:5432"
    echo "  🔴 Redis: localhost:6379"
    echo "  📈 InfluxDB: http://localhost:8086"
    echo ""
    echo -e "${PURPLE}👤 默认登录信息：${NC}"
    echo "  管理员: admin / admin123"
    echo "  交易员: trader / trader123"
    echo ""
    echo -e "${YELLOW}✨ 新功能特性：${NC}"
    echo "  📱 完美的移动端体验"
    echo "  🎨 响应式设计，适配所有设备"
    echo "  ⚡ 实时性能监控"
    echo "  🔄 PWA支持，可安装为应用"
    echo "  ♿ 完整的可访问性支持"
    echo ""
    echo -e "${CYAN}🛠️ 管理命令：${NC}"
    echo "  查看日志: docker-compose logs -f [服务名]"
    echo "  停止服务: docker-compose down"
    echo "  重启服务: docker-compose restart [服务名]"
    echo "  查看状态: docker-compose ps"
    echo ""
    echo -e "${GREEN}🎯 快速测试：${NC}"
    echo "  1. 在桌面浏览器中访问 http://localhost:3000"
    echo "  2. 按F12打开开发者工具，切换到移动设备模式"
    echo "  3. 体验响应式设计和移动端优化"
    echo "  4. 查看右上角的性能监控面板（开发模式）"
    echo ""
}

# 显示服务日志
show_service_logs() {
    local service=$1
    if [ -n "$service" ]; then
        log_info "显示 $service 服务日志："
        docker-compose logs --tail=50 "$service"
    else
        log_info "显示所有服务日志："
        docker-compose logs --tail=20
    fi
}

# 清理函数
cleanup_on_exit() {
    log_info "正在清理..."
    # 这里可以添加清理逻辑
}

# 停止服务
stop_services() {
    log_step "停止所有服务..."
    docker-compose down
    log_success "服务已停止"
}

# 重启服务
restart_services() {
    log_step "重启服务..."
    stop_services
    sleep 3
    start_docker_services
    wait_for_services
    show_service_status
    show_access_info
}

# 显示帮助信息
show_help() {
    echo -e "${CYAN}量化交易平台启动脚本 (响应式多终端版本)${NC}"
    echo ""
    echo "用法: $0 [选项] [命令]"
    echo ""
    echo -e "${GREEN}命令:${NC}"
    echo "  start          启动所有服务（默认）"
    echo "  stop           停止所有服务"
    echo "  restart        重启所有服务"
    echo "  status         显示服务状态"
    echo "  logs [服务名]   显示日志"
    echo "  build          重新构建前端应用"
    echo "  clean          清理并重新启动"
    echo "  help           显示此帮助信息"
    echo ""
    echo -e "${GREEN}选项:${NC}"
    echo "  --no-build     跳过前端构建"
    echo "  --clean        启动前清理旧容器和卷"
    echo "  --dev          开发模式（启用调试功能）"
    echo ""
    echo -e "${GREEN}示例:${NC}"
    echo "  $0                    # 启动所有服务"
    echo "  $0 start --clean     # 清理后启动"
    echo "  $0 build             # 重新构建前端"
    echo "  $0 logs backend      # 查看后端日志"
    echo "  $0 stop              # 停止所有服务"
    echo ""
    echo -e "${YELLOW}新功能:${NC}"
    echo "  📱 自动检测和安装PWA依赖"
    echo "  🎨 响应式设计支持"
    echo "  ⚡ 性能监控集成"
    echo "  🔄 PWA图标自动生成"
}

# 主函数
main() {
    local command="start"
    local no_build=false
    local clean_flag=false
    local dev_mode=false
    
    # 设置退出时清理
    trap cleanup_on_exit EXIT
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            start|stop|restart|status|logs|build|clean|help)
                command="$1"
                shift
                ;;
            --no-build)
                no_build=true
                shift
                ;;
            --clean)
                clean_flag=true
                shift
                ;;
            --dev)
                dev_mode=true
                shift
                ;;
            *)
                if [ "$command" = "logs" ] && [ -z "$2" ]; then
                    show_service_logs "$1"
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
            show_banner
            check_system_requirements
            check_docker_service
            create_directories
            setup_environment_files
            
            if [ "$clean_flag" = true ]; then
                log_info "清理模式：删除旧容器和卷..."
                docker-compose down -v --remove-orphans 2>/dev/null || true
            fi
            
            install_frontend_dependencies
            install_backend_dependencies
            create_pwa_icons
            
            if [ "$no_build" = false ]; then
                build_frontend
            fi
            
            start_docker_services
            wait_for_services
            show_service_status
            show_access_info
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_service_status
            show_access_info
            ;;
        logs)
            show_service_logs
            ;;
        build)
            install_frontend_dependencies
            create_pwa_icons
            build_frontend
            log_success "前端应用重新构建完成"
            ;;
        clean)
            log_step "清理并重新启动..."
            docker-compose down -v --remove-orphans 2>/dev/null || true
            docker system prune -f
            main start --clean
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

# 检查是否以root身份运行（在某些系统上可能需要）
if [ "$EUID" -eq 0 ]; then
    log_warning "检测到以root身份运行，这可能不是最佳实践"
fi

# 运行主函数
main "$@"