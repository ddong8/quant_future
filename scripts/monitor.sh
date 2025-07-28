#!/bin/bash

# 量化交易平台监控脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
DEPLOYMENT_TYPE="${DEPLOYMENT_TYPE:-docker}"
CHECK_INTERVAL="${CHECK_INTERVAL:-30}"
ALERT_WEBHOOK="${ALERT_WEBHOOK:-}"
LOG_FILE="${LOG_FILE:-./logs/monitor.log}"

# 日志函数
log_info() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1"
    echo -e "${BLUE}$msg${NC}"
    echo "$msg" >> "$LOG_FILE"
}

log_success() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $1"
    echo -e "${GREEN}$msg${NC}"
    echo "$msg" >> "$LOG_FILE"
}

log_warning() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING] $1"
    echo -e "${YELLOW}$msg${NC}"
    echo "$msg" >> "$LOG_FILE"
}

log_error() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1"
    echo -e "${RED}$msg${NC}"
    echo "$msg" >> "$LOG_FILE"
}

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 检查服务状态
check_service_status() {
    local service_name="$1"
    local expected_status="$2"
    
    if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        local status=$(docker-compose ps "$service_name" --format "table {{.State}}" | tail -n +2)
        if [ "$status" = "$expected_status" ]; then
            log_success "$service_name 服务状态正常: $status"
            return 0
        else
            log_error "$service_name 服务状态异常: $status (期望: $expected_status)"
            return 1
        fi
    else
        local status=$(kubectl get pods -n quant-trading -l app="$service_name" -o jsonpath='{.items[0].status.phase}')
        if [ "$status" = "Running" ]; then
            log_success "$service_name 服务状态正常: $status"
            return 0
        else
            log_error "$service_name 服务状态异常: $status"
            return 1
        fi
    fi
}

# 检查HTTP端点
check_http_endpoint() {
    local url="$1"
    local expected_code="${2:-200}"
    local timeout="${3:-10}"
    
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$timeout" "$url" || echo "000")
    
    if [ "$response_code" = "$expected_code" ]; then
        log_success "HTTP检查通过: $url (状态码: $response_code)"
        return 0
    else
        log_error "HTTP检查失败: $url (状态码: $response_code, 期望: $expected_code)"
        return 1
    fi
}

# 检查数据库连接
check_database() {
    log_info "检查数据库连接..."
    
    if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        if docker-compose exec -T db pg_isready -U postgres > /dev/null 2>&1; then
            log_success "PostgreSQL数据库连接正常"
            return 0
        else
            log_error "PostgreSQL数据库连接失败"
            return 1
        fi
    else
        if kubectl exec -n quant-trading statefulset/postgres -- pg_isready -U postgres > /dev/null 2>&1; then
            log_success "PostgreSQL数据库连接正常"
            return 0
        else
            log_error "PostgreSQL数据库连接失败"
            return 1
        fi
    fi
}

# 检查Redis连接
check_redis() {
    log_info "检查Redis连接..."
    
    if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
            log_success "Redis连接正常"
            return 0
        else
            log_error "Redis连接失败"
            return 1
        fi
    else
        if kubectl exec -n quant-trading deployment/redis -- redis-cli ping | grep -q "PONG"; then
            log_success "Redis连接正常"
            return 0
        else
            log_error "Redis连接失败"
            return 1
        fi
    fi
}

# 检查InfluxDB连接
check_influxdb() {
    log_info "检查InfluxDB连接..."
    
    if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        local url="http://localhost:8086/health"
    else
        # 使用端口转发检查
        kubectl port-forward service/influxdb-service 8086:8086 -n quant-trading &
        local pf_pid=$!
        sleep 2
        local url="http://localhost:8086/health"
    fi
    
    if check_http_endpoint "$url" "200" "5"; then
        log_success "InfluxDB连接正常"
        [ "$DEPLOYMENT_TYPE" = "k8s" ] && kill $pf_pid 2>/dev/null || true
        return 0
    else
        log_error "InfluxDB连接失败"
        [ "$DEPLOYMENT_TYPE" = "k8s" ] && kill $pf_pid 2>/dev/null || true
        return 1
    fi
}

# 检查应用健康状态
check_app_health() {
    log_info "检查应用健康状态..."
    
    if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        local health_url="http://localhost:8000/health"
        local ready_url="http://localhost:8000/ready"
    else
        kubectl port-forward service/quant-trading-service 8000:8000 -n quant-trading &
        local pf_pid=$!
        sleep 2
        local health_url="http://localhost:8000/health"
        local ready_url="http://localhost:8000/ready"
    fi
    
    local health_ok=true
    
    if ! check_http_endpoint "$health_url" "200" "10"; then
        health_ok=false
    fi
    
    if ! check_http_endpoint "$ready_url" "200" "10"; then
        health_ok=false
    fi
    
    [ "$DEPLOYMENT_TYPE" = "k8s" ] && kill $pf_pid 2>/dev/null || true
    
    if [ "$health_ok" = true ]; then
        log_success "应用健康检查通过"
        return 0
    else
        log_error "应用健康检查失败"
        return 1
    fi
}

# 检查系统资源
check_system_resources() {
    log_info "检查系统资源..."
    
    # 检查磁盘使用率
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 80 ]; then
        log_warning "磁盘使用率过高: ${disk_usage}%"
    else
        log_success "磁盘使用率正常: ${disk_usage}%"
    fi
    
    # 检查内存使用率
    local memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$memory_usage" -gt 80 ]; then
        log_warning "内存使用率过高: ${memory_usage}%"
    else
        log_success "内存使用率正常: ${memory_usage}%"
    fi
    
    # 检查CPU负载
    local cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local cpu_cores=$(nproc)
    local load_percentage=$(echo "$cpu_load * 100 / $cpu_cores" | bc -l | cut -d. -f1)
    
    if [ "$load_percentage" -gt 80 ]; then
        log_warning "CPU负载过高: ${load_percentage}%"
    else
        log_success "CPU负载正常: ${load_percentage}%"
    fi
}

# 检查容器资源使用
check_container_resources() {
    if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        log_info "检查容器资源使用..."
        
        # 获取容器统计信息
        docker-compose ps --format "table {{.Name}}\t{{.State}}" | tail -n +2 | while read -r line; do
            local container_name=$(echo "$line" | awk '{print $1}')
            local container_state=$(echo "$line" | awk '{print $2}')
            
            if [ "$container_state" = "Up" ]; then
                local stats=$(docker stats "$container_name" --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}")
                log_info "$container_name 资源使用: $stats"
            fi
        done
    else
        log_info "检查Pod资源使用..."
        kubectl top pods -n quant-trading 2>/dev/null || log_warning "无法获取Pod资源使用情况（需要metrics-server）"
    fi
}

# 检查日志错误
check_logs_for_errors() {
    log_info "检查应用日志错误..."
    
    local error_count=0
    
    if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        # 检查最近5分钟的错误日志
        error_count=$(docker-compose logs --since=5m app 2>/dev/null | grep -i "error\|exception\|failed" | wc -l)
    else
        # 检查K8s日志
        error_count=$(kubectl logs -n quant-trading deployment/quant-trading-app --since=5m 2>/dev/null | grep -i "error\|exception\|failed" | wc -l)
    fi
    
    if [ "$error_count" -gt 10 ]; then
        log_warning "发现 $error_count 个错误日志条目（最近5分钟）"
    else
        log_success "错误日志数量正常: $error_count 个（最近5分钟）"
    fi
}

# 发送告警
send_alert() {
    local message="$1"
    local severity="${2:-warning}"
    
    if [ -n "$ALERT_WEBHOOK" ]; then
        local color="warning"
        [ "$severity" = "error" ] && color="danger"
        [ "$severity" = "success" ] && color="good"
        
        curl -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{
                \"text\": \"量化交易平台监控告警\",
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"fields\": [
                        {\"title\": \"时间\", \"value\": \"$(date)\", \"short\": true},
                        {\"title\": \"严重程度\", \"value\": \"$severity\", \"short\": true},
                        {\"title\": \"消息\", \"value\": \"$message\", \"short\": false}
                    ]
                }]
            }" 2>/dev/null || log_warning "告警发送失败"
    fi
}

# 生成监控报告
generate_report() {
    local report_file="./reports/monitor_report_$(date +%Y%m%d_%H%M%S).html"
    mkdir -p "$(dirname "$report_file")"
    
    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>量化交易平台监控报告</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 10px; border-radius: 5px; }
        .success { color: green; }
        .warning { color: orange; }
        .error { color: red; }
        .section { margin: 20px 0; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>量化交易平台监控报告</h1>
        <p>生成时间: $(date)</p>
        <p>部署类型: $DEPLOYMENT_TYPE</p>
    </div>
    
    <div class="section">
        <h2>系统状态概览</h2>
        <table>
            <tr><th>检查项</th><th>状态</th><th>详情</th></tr>
EOF
    
    # 这里可以添加更多的报告内容
    echo "        </table>" >> "$report_file"
    echo "    </div>" >> "$report_file"
    echo "</body></html>" >> "$report_file"
    
    log_info "监控报告已生成: $report_file"
}

# 执行完整检查
run_full_check() {
    log_info "开始完整系统检查..."
    
    local failed_checks=0
    
    # 检查各个组件
    check_database || ((failed_checks++))
    check_redis || ((failed_checks++))
    check_influxdb || ((failed_checks++))
    check_app_health || ((failed_checks++))
    
    # 检查系统资源
    check_system_resources
    check_container_resources
    check_logs_for_errors
    
    # 根据检查结果发送告警
    if [ "$failed_checks" -eq 0 ]; then
        log_success "所有检查通过"
        send_alert "系统运行正常" "success"
    elif [ "$failed_checks" -le 2 ]; then
        log_warning "$failed_checks 个检查失败"
        send_alert "$failed_checks 个组件检查失败" "warning"
    else
        log_error "$failed_checks 个检查失败"
        send_alert "系统存在严重问题，$failed_checks 个组件检查失败" "error"
    fi
    
    return $failed_checks
}

# 持续监控模式
continuous_monitor() {
    log_info "启动持续监控模式，检查间隔: ${CHECK_INTERVAL}秒"
    
    while true; do
        run_full_check
        sleep "$CHECK_INTERVAL"
    done
}

# 显示帮助
show_help() {
    cat << EOF
量化交易平台监控脚本

用法: $0 [选项] [命令]

命令:
  check           执行一次完整检查
  monitor         持续监控模式
  report          生成监控报告
  help            显示帮助信息

选项:
  -t, --type      部署类型 (docker|k8s) [默认: docker]
  -i, --interval  检查间隔（秒） [默认: 30]
  -l, --log       日志文件路径 [默认: ./logs/monitor.log]
  -w, --webhook   告警Webhook URL
  -h, --help      显示帮助信息

示例:
  $0 check
  $0 -t k8s -i 60 monitor
  $0 -w https://hooks.slack.com/... check
EOF
}

# 主函数
main() {
    local command="check"
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                DEPLOYMENT_TYPE="$2"
                shift 2
                ;;
            -i|--interval)
                CHECK_INTERVAL="$2"
                shift 2
                ;;
            -l|--log)
                LOG_FILE="$2"
                shift 2
                ;;
            -w|--webhook)
                ALERT_WEBHOOK="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            check|monitor|report|help)
                command="$1"
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 执行命令
    case $command in
        check)
            run_full_check
            ;;
        monitor)
            continuous_monitor
            ;;
        report)
            generate_report
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

# 信号处理
trap 'log_info "监控脚本退出"; exit 0' SIGINT SIGTERM

# 执行主函数
main "$@"