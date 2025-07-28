#!/bin/bash

# 量化交易平台系统集成检查脚本
# 验证所有系统组件是否正常工作

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

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 命令未找到"
        return 1
    fi
    return 0
}

# 检查端口是否开放
check_port() {
    local port=$1
    local service=$2
    
    if nc -z localhost $port 2>/dev/null; then
        log_success "$service (端口 $port) 正在运行"
        return 0
    else
        log_error "$service (端口 $port) 未运行"
        return 1
    fi
}

# 检查HTTP服务
check_http_service() {
    local url=$1
    local service=$2
    local expected_status=${3:-200}
    
    local status=$(curl -s -o /dev/null -w "%{http_code}" $url)
    
    if [ "$status" = "$expected_status" ]; then
        log_success "$service HTTP服务正常 (状态码: $status)"
        return 0
    else
        log_error "$service HTTP服务异常 (状态码: $status)"
        return 1
    fi
}

# 检查数据库连接
check_database() {
    local db_type=$1
    local connection_string=$2
    
    case $db_type in
        "postgresql")
            if psql "$connection_string" -c "SELECT 1;" &>/dev/null; then
                log_success "PostgreSQL 数据库连接正常"
                return 0
            else
                log_error "PostgreSQL 数据库连接失败"
                return 1
            fi
            ;;
        "redis")
            if redis-cli ping &>/dev/null; then
                log_success "Redis 连接正常"
                return 0
            else
                log_error "Redis 连接失败"
                return 1
            fi
            ;;
        *)
            log_error "未知的数据库类型: $db_type"
            return 1
            ;;
    esac
}

# 检查Docker容器状态
check_docker_containers() {
    log_info "检查Docker容器状态..."
    
    local containers=("postgres" "redis" "influxdb" "backend" "frontend")
    local all_running=true
    
    for container in "${containers[@]}"; do
        if docker-compose ps | grep -q "$container.*Up"; then
            log_success "容器 $container 正在运行"
        else
            log_error "容器 $container 未运行"
            all_running=false
        fi
    done
    
    return $all_running
}

# 检查系统资源
check_system_resources() {
    log_info "检查系统资源..."
    
    # 检查磁盘空间
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $disk_usage -lt 90 ]; then
        log_success "磁盘空间充足 (使用率: ${disk_usage}%)"
    else
        log_warning "磁盘空间不足 (使用率: ${disk_usage}%)"
    fi
    
    # 检查内存使用
    local mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ $mem_usage -lt 90 ]; then
        log_success "内存使用正常 (使用率: ${mem_usage}%)"
    else
        log_warning "内存使用率较高 (使用率: ${mem_usage}%)"
    fi
    
    # 检查CPU负载
    local cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local cpu_cores=$(nproc)
    local load_ratio=$(echo "$cpu_load / $cpu_cores" | bc -l)
    
    if (( $(echo "$load_ratio < 0.8" | bc -l) )); then
        log_success "CPU负载正常 (负载: $cpu_load, 核心数: $cpu_cores)"
    else
        log_warning "CPU负载较高 (负载: $cpu_load, 核心数: $cpu_cores)"
    fi
}

# 检查网络连接
check_network_connectivity() {
    log_info "检查网络连接..."
    
    # 检查内部服务连接
    local services=(
        "http://localhost:8000/health:后端健康检查"
        "http://localhost:3000:前端服务"
        "http://localhost:8086/health:InfluxDB健康检查"
    )
    
    for service in "${services[@]}"; do
        local url=$(echo $service | cut -d: -f1)
        local name=$(echo $service | cut -d: -f2)
        
        if curl -s --max-time 10 $url > /dev/null; then
            log_success "$name 连接正常"
        else
            log_error "$name 连接失败"
        fi
    done
}

# 检查日志文件
check_log_files() {
    log_info "检查日志文件..."
    
    local log_dirs=("/var/log/trading" "./logs")
    
    for log_dir in "${log_dirs[@]}"; do
        if [ -d "$log_dir" ]; then
            local log_files=$(find $log_dir -name "*.log" -type f)
            if [ -n "$log_files" ]; then
                log_success "找到日志文件: $log_dir"
                
                # 检查最近的错误日志
                local recent_errors=$(find $log_dir -name "*.log" -type f -exec grep -l "ERROR\|CRITICAL" {} \; 2>/dev/null | head -5)
                if [ -n "$recent_errors" ]; then
                    log_warning "发现错误日志文件:"
                    echo "$recent_errors"
                fi
            else
                log_warning "日志目录 $log_dir 中没有日志文件"
            fi
        else
            log_warning "日志目录 $log_dir 不存在"
        fi
    done
}

# 检查配置文件
check_configuration_files() {
    log_info "检查配置文件..."
    
    local config_files=(
        "backend/.env:后端环境配置"
        "frontend/.env:前端环境配置"
        "docker-compose.yml:Docker Compose配置"
        "nginx.conf:Nginx配置"
    )
    
    for config in "${config_files[@]}"; do
        local file=$(echo $config | cut -d: -f1)
        local name=$(echo $config | cut -d: -f2)
        
        if [ -f "$file" ]; then
            log_success "$name 文件存在"
        else
            log_error "$name 文件不存在: $file"
        fi
    done
}

# 运行基本功能测试
run_basic_functionality_tests() {
    log_info "运行基本功能测试..."
    
    # 测试API端点
    local api_endpoints=(
        "http://localhost:8000/health:系统健康检查"
        "http://localhost:8000/info:系统信息"
        "http://localhost:8000/api/v1/market/instruments:合约列表"
    )
    
    for endpoint in "${api_endpoints[@]}"; do
        local url=$(echo $endpoint | cut -d: -f1)
        local name=$(echo $endpoint | cut -d: -f2)
        
        local response=$(curl -s --max-time 10 -w "%{http_code}" $url)
        local status_code="${response: -3}"
        
        if [ "$status_code" = "200" ] || [ "$status_code" = "401" ]; then
            log_success "$name API响应正常"
        else
            log_error "$name API响应异常 (状态码: $status_code)"
        fi
    done
}

# 检查安全配置
check_security_configuration() {
    log_info "检查安全配置..."
    
    # 检查防火墙状态
    if command -v ufw &> /dev/null; then
        if ufw status | grep -q "Status: active"; then
            log_success "防火墙已启用"
        else
            log_warning "防火墙未启用"
        fi
    fi
    
    # 检查SSL证书（如果配置了HTTPS）
    if [ -f "/etc/ssl/certs/trading-platform.crt" ]; then
        local cert_expiry=$(openssl x509 -in /etc/ssl/certs/trading-platform.crt -noout -enddate | cut -d= -f2)
        log_info "SSL证书到期时间: $cert_expiry"
    fi
    
    # 检查敏感文件权限
    local sensitive_files=(
        "backend/.env"
        "docker-compose.yml"
    )
    
    for file in "${sensitive_files[@]}"; do
        if [ -f "$file" ]; then
            local permissions=$(stat -c "%a" "$file")
            if [ "$permissions" = "600" ] || [ "$permissions" = "644" ]; then
                log_success "$file 权限设置正确 ($permissions)"
            else
                log_warning "$file 权限可能过于宽松 ($permissions)"
            fi
        fi
    done
}

# 生成集成检查报告
generate_integration_report() {
    local report_file="system_integration_report.txt"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    cat > $report_file << EOF
量化交易平台系统集成检查报告
========================================
检查时间: $timestamp
系统信息: $(uname -a)
Docker版本: $(docker --version)
Docker Compose版本: $(docker-compose --version)

检查结果:
EOF
    
    # 重新运行检查并记录结果
    {
        echo "1. Docker容器状态检查"
        check_docker_containers
        echo ""
        
        echo "2. 网络连接检查"
        check_network_connectivity
        echo ""
        
        echo "3. 系统资源检查"
        check_system_resources
        echo ""
        
        echo "4. 基本功能测试"
        run_basic_functionality_tests
        echo ""
        
        echo "5. 安全配置检查"
        check_security_configuration
        echo ""
    } >> $report_file 2>&1
    
    log_success "集成检查报告已生成: $report_file"
}

# 主函数
main() {
    echo "========================================"
    echo "量化交易平台系统集成检查"
    echo "========================================"
    echo ""
    
    # 检查必要的命令
    local required_commands=("docker" "docker-compose" "curl" "nc")
    for cmd in "${required_commands[@]}"; do
        if ! check_command $cmd; then
            log_error "缺少必要的命令: $cmd"
            exit 1
        fi
    done
    
    # 执行各项检查
    log_info "开始系统集成检查..."
    echo ""
    
    # 1. 检查Docker容器
    check_docker_containers
    echo ""
    
    # 2. 检查端口
    log_info "检查服务端口..."
    check_port 5432 "PostgreSQL"
    check_port 6379 "Redis"
    check_port 8086 "InfluxDB"
    check_port 8000 "后端API服务"
    check_port 3000 "前端服务"
    echo ""
    
    # 3. 检查HTTP服务
    log_info "检查HTTP服务..."
    check_http_service "http://localhost:8000/health" "后端API"
    check_http_service "http://localhost:3000" "前端服务"
    echo ""
    
    # 4. 检查网络连接
    check_network_connectivity
    echo ""
    
    # 5. 检查系统资源
    check_system_resources
    echo ""
    
    # 6. 检查配置文件
    check_configuration_files
    echo ""
    
    # 7. 检查日志文件
    check_log_files
    echo ""
    
    # 8. 运行基本功能测试
    run_basic_functionality_tests
    echo ""
    
    # 9. 检查安全配置
    check_security_configuration
    echo ""
    
    # 10. 生成报告
    generate_integration_report
    
    echo ""
    echo "========================================"
    log_success "系统集成检查完成"
    echo "========================================"
}

# 执行主函数
main "$@"