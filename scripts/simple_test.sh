#!/bin/bash

# 简单的系统功能测试脚本
# 验证基本的API功能是否正常

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
API_BASE="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"

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

# 测试HTTP服务
test_http_service() {
    local url=$1
    local service_name=$2
    local expected_status=${3:-200}
    
    log_info "测试 $service_name..."
    
    local response=$(curl -s -w "%{http_code}" -o /dev/null "$url" || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        log_success "$service_name 响应正常 (状态码: $response)"
        return 0
    else
        log_error "$service_name 响应异常 (状态码: $response)"
        return 1
    fi
}

# 测试API端点
test_api_endpoint() {
    local endpoint=$1
    local method=${2:-GET}
    local description=$3
    local expected_status=${4:-200}
    local data=${5:-""}
    
    log_info "测试 $description..."
    
    local curl_cmd="curl -s -w %{http_code} -o /dev/null"
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        curl_cmd="$curl_cmd -X POST -H 'Content-Type: application/json' -d '$data'"
    fi
    
    local response=$(eval "$curl_cmd $API_BASE$endpoint" || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        log_success "$description 测试通过 (状态码: $response)"
        return 0
    else
        log_error "$description 测试失败 (状态码: $response)"
        return 1
    fi
}

# 测试用户认证
test_authentication() {
    log_info "测试用户认证功能..."
    
    # 测试登录（预期会失败，因为没有用户数据）
    local login_data='{"username":"admin","password":"admin123"}'
    local response=$(curl -s -w "%{http_code}" -o /tmp/login_response.json \
        -X POST \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=admin&password=admin123" \
        "$API_BASE/api/v1/auth/login" || echo "000")
    
    if [ "$response" = "200" ] || [ "$response" = "401" ] || [ "$response" = "422" ]; then
        log_success "认证端点响应正常 (状态码: $response)"
        
        # 如果登录成功，测试获取用户信息
        if [ "$response" = "200" ]; then
            local token=$(cat /tmp/login_response.json | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
            if [ -n "$token" ]; then
                local profile_response=$(curl -s -w "%{http_code}" -o /dev/null \
                    -H "Authorization: Bearer $token" \
                    "$API_BASE/api/v1/auth/profile" || echo "000")
                
                if [ "$profile_response" = "200" ]; then
                    log_success "用户信息获取正常"
                else
                    log_warning "用户信息获取失败 (状态码: $profile_response)"
                fi
            fi
        fi
    else
        log_error "认证端点异常 (状态码: $response)"
        return 1
    fi
    
    rm -f /tmp/login_response.json
}

# 测试数据库连接
test_database_connection() {
    log_info "测试数据库连接..."
    
    # 检查PostgreSQL
    if docker-compose exec -T postgres pg_isready -U postgres &>/dev/null; then
        log_success "PostgreSQL 连接正常"
    else
        log_error "PostgreSQL 连接失败"
        return 1
    fi
    
    # 检查Redis
    if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
        log_success "Redis 连接正常"
    else
        log_error "Redis 连接失败"
        return 1
    fi
    
    # 检查InfluxDB
    if curl -s "http://localhost:8086/health" | grep -q "pass"; then
        log_success "InfluxDB 连接正常"
    else
        log_warning "InfluxDB 连接可能有问题"
    fi
}

# 测试容器状态
test_container_status() {
    log_info "检查容器状态..."
    
    local containers=("trading_postgres" "trading_redis" "trading_influxdb" "trading_backend" "trading_frontend")
    local all_running=true
    
    for container in "${containers[@]}"; do
        if docker ps | grep -q "$container"; then
            log_success "容器 $container 正在运行"
        else
            log_error "容器 $container 未运行"
            all_running=false
        fi
    done
    
    if [ "$all_running" = true ]; then
        return 0
    else
        return 1
    fi
}

# 运行基本功能测试
run_basic_tests() {
    log_info "运行基本功能测试..."
    
    local tests_passed=0
    local tests_total=0
    
    # 测试系统健康检查
    ((tests_total++))
    if test_http_service "$API_BASE/health" "系统健康检查"; then
        ((tests_passed++))
    fi
    
    # 测试系统信息
    ((tests_total++))
    if test_http_service "$API_BASE/info" "系统信息"; then
        ((tests_passed++))
    fi
    
    # 测试前端服务
    ((tests_total++))
    if test_http_service "$FRONTEND_URL" "前端服务"; then
        ((tests_passed++))
    fi
    
    # 测试API文档
    ((tests_total++))
    if test_http_service "$API_BASE/docs" "API文档"; then
        ((tests_passed++))
    fi
    
    # 测试认证功能
    ((tests_total++))
    if test_authentication; then
        ((tests_passed++))
    fi
    
    # 测试市场数据端点（预期可能失败）
    ((tests_total++))
    if test_api_endpoint "/api/v1/market/instruments" "GET" "合约列表" "401"; then
        ((tests_passed++))
    fi
    
    echo ""
    log_info "基本功能测试结果: $tests_passed/$tests_total 通过"
    
    if [ $tests_passed -eq $tests_total ]; then
        log_success "所有基本功能测试通过！"
        return 0
    else
        log_warning "部分测试失败，这在初始化阶段是正常的"
        return 1
    fi
}

# 显示系统状态
show_system_status() {
    echo ""
    log_info "系统状态概览："
    echo "----------------------------------------"
    
    # 显示容器状态
    echo "Docker 容器状态:"
    docker-compose ps
    
    echo ""
    echo "服务端口状态:"
    netstat -tuln | grep -E ":(3000|5432|6379|8000|8086)" || echo "  无法获取端口信息"
    
    echo ""
    echo "系统资源使用:"
    echo "  内存使用: $(free -h | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
    echo "  磁盘使用: $(df -h / | awk 'NR==2{print $5}')"
    
    echo ""
    echo "服务访问地址:"
    echo "  前端应用: http://localhost:3000"
    echo "  后端API: http://localhost:8000"
    echo "  API文档: http://localhost:8000/docs"
    echo "  健康检查: http://localhost:8000/health"
}

# 主函数
main() {
    echo "========================================"
    echo "量化交易平台简单测试"
    echo "========================================"
    echo ""
    
    # 检查Docker Compose是否运行
    if ! docker-compose ps | grep -q "Up"; then
        log_error "系统未启动，请先运行 ./scripts/quick_start.sh"
        exit 1
    fi
    
    # 测试容器状态
    test_container_status
    
    # 测试数据库连接
    test_database_connection
    
    # 运行基本功能测试
    run_basic_tests
    
    # 显示系统状态
    show_system_status
    
    echo ""
    echo "========================================"
    log_info "测试完成！"
    echo "========================================"
    
    echo ""
    log_info "如果测试失败，请检查："
    echo "  1. 所有容器是否正常运行: docker-compose ps"
    echo "  2. 查看服务日志: docker-compose logs [service_name]"
    echo "  3. 检查端口是否被占用: netstat -tuln | grep [port]"
    echo "  4. 重启服务: docker-compose restart"
}

# 执行主函数
main "$@"