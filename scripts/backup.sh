#!/bin/bash

# 量化交易平台备份脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DEPLOYMENT_TYPE="${DEPLOYMENT_TYPE:-docker}"

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

# 创建备份目录
create_backup_dir() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    CURRENT_BACKUP_DIR="$BACKUP_DIR/$timestamp"
    mkdir -p "$CURRENT_BACKUP_DIR"
    log_info "创建备份目录: $CURRENT_BACKUP_DIR"
}

# 备份PostgreSQL数据库
backup_postgres() {
    log_info "备份PostgreSQL数据库..."
    
    if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        docker-compose exec -T db pg_dump -U postgres quantdb > "$CURRENT_BACKUP_DIR/postgres.sql"
    else
        kubectl exec -n quant-trading statefulset/postgres -- pg_dump -U postgres quantdb > "$CURRENT_BACKUP_DIR/postgres.sql"
    fi
    
    # 压缩SQL文件
    gzip "$CURRENT_BACKUP_DIR/postgres.sql"
    log_success "PostgreSQL备份完成"
}

# 备份Redis数据
backup_redis() {
    log_info "备份Redis数据..."
    
    if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        # 触发Redis保存
        docker-compose exec redis redis-cli BGSAVE
        sleep 5
        # 复制RDB文件
        docker cp $(docker-compose ps -q redis):/data/dump.rdb "$CURRENT_BACKUP_DIR/"
    else
        kubectl exec -n quant-trading deployment/redis -- redis-cli BGSAVE
        sleep 5
        kubectl cp quant-trading/$(kubectl get pods -n quant-trading -l app=redis -o jsonpath='{.items[0].metadata.name}'):/data/dump.rdb "$CURRENT_BACKUP_DIR/dump.rdb"
    fi
    
    log_success "Redis备份完成"
}

# 备份InfluxDB数据
backup_influxdb() {
    log_info "备份InfluxDB数据..."
    
    if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        docker-compose exec influxdb influx backup /tmp/backup
        docker cp $(docker-compose ps -q influxdb):/tmp/backup "$CURRENT_BACKUP_DIR/influxdb_backup"
    else
        kubectl exec -n quant-trading statefulset/influxdb -- influx backup /tmp/backup
        kubectl cp quant-trading/$(kubectl get pods -n quant-trading -l app=influxdb -o jsonpath='{.items[0].metadata.name}'):/tmp/backup "$CURRENT_BACKUP_DIR/influxdb_backup"
    fi
    
    log_success "InfluxDB备份完成"
}

# 备份应用数据
backup_app_data() {
    log_info "备份应用数据..."
    
    if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        # 备份日志
        if [ -d "./logs" ]; then
            cp -r ./logs "$CURRENT_BACKUP_DIR/"
        fi
        
        # 备份报告
        if [ -d "./reports" ]; then
            cp -r ./reports "$CURRENT_BACKUP_DIR/"
        fi
        
        # 备份用户上传的文件
        docker cp $(docker-compose ps -q app):/app/data "$CURRENT_BACKUP_DIR/" 2>/dev/null || true
    else
        # K8s环境备份
        kubectl cp quant-trading/$(kubectl get pods -n quant-trading -l app=quant-trading-app -o jsonpath='{.items[0].metadata.name}'):/app/logs "$CURRENT_BACKUP_DIR/" 2>/dev/null || true
        kubectl cp quant-trading/$(kubectl get pods -n quant-trading -l app=quant-trading-app -o jsonpath='{.items[0].metadata.name}'):/app/reports "$CURRENT_BACKUP_DIR/" 2>/dev/null || true
    fi
    
    log_success "应用数据备份完成"
}

# 备份配置文件
backup_configs() {
    log_info "备份配置文件..."
    
    mkdir -p "$CURRENT_BACKUP_DIR/configs"
    
    # 备份Docker配置
    if [ -f "docker-compose.yml" ]; then
        cp docker-compose.yml "$CURRENT_BACKUP_DIR/configs/"
    fi
    
    if [ -f ".env" ]; then
        cp .env "$CURRENT_BACKUP_DIR/configs/"
    fi
    
    # 备份K8s配置
    if [ -d "k8s" ]; then
        cp -r k8s "$CURRENT_BACKUP_DIR/configs/"
    fi
    
    # 备份Nginx配置
    if [ -d "docker" ]; then
        cp -r docker "$CURRENT_BACKUP_DIR/configs/"
    fi
    
    log_success "配置文件备份完成"
}

# 创建备份清单
create_manifest() {
    log_info "创建备份清单..."
    
    cat > "$CURRENT_BACKUP_DIR/manifest.txt" << EOF
备份时间: $(date)
备份类型: $DEPLOYMENT_TYPE
备份内容:
- PostgreSQL数据库
- Redis数据
- InfluxDB数据
- 应用数据（日志、报告等）
- 配置文件

文件列表:
$(find "$CURRENT_BACKUP_DIR" -type f -exec ls -lh {} \;)

总大小: $(du -sh "$CURRENT_BACKUP_DIR" | cut -f1)
EOF
    
    log_success "备份清单创建完成"
}

# 压缩备份
compress_backup() {
    log_info "压缩备份文件..."
    
    cd "$BACKUP_DIR"
    tar -czf "$(basename "$CURRENT_BACKUP_DIR").tar.gz" "$(basename "$CURRENT_BACKUP_DIR")"
    rm -rf "$CURRENT_BACKUP_DIR"
    
    log_success "备份压缩完成: $(basename "$CURRENT_BACKUP_DIR").tar.gz"
}

# 清理旧备份
cleanup_old_backups() {
    log_info "清理 $RETENTION_DAYS 天前的备份..."
    
    find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
    
    log_success "旧备份清理完成"
}

# 验证备份
verify_backup() {
    log_info "验证备份完整性..."
    
    local backup_file="$BACKUP_DIR/$(basename "$CURRENT_BACKUP_DIR").tar.gz"
    
    if [ -f "$backup_file" ]; then
        # 检查压缩文件完整性
        if tar -tzf "$backup_file" > /dev/null 2>&1; then
            log_success "备份文件完整性验证通过"
        else
            log_error "备份文件损坏"
            return 1
        fi
        
        # 显示备份信息
        local size=$(du -sh "$backup_file" | cut -f1)
        log_info "备份文件大小: $size"
        log_info "备份文件路径: $backup_file"
    else
        log_error "备份文件不存在"
        return 1
    fi
}

# 上传到云存储（可选）
upload_to_cloud() {
    if [ -n "$CLOUD_STORAGE_ENABLED" ] && [ "$CLOUD_STORAGE_ENABLED" = "true" ]; then
        log_info "上传备份到云存储..."
        
        local backup_file="$BACKUP_DIR/$(basename "$CURRENT_BACKUP_DIR").tar.gz"
        
        case "$CLOUD_PROVIDER" in
            "aws")
                aws s3 cp "$backup_file" "s3://$S3_BUCKET/backups/"
                ;;
            "gcp")
                gsutil cp "$backup_file" "gs://$GCS_BUCKET/backups/"
                ;;
            "azure")
                az storage blob upload --file "$backup_file" --container-name backups --name "$(basename "$backup_file")"
                ;;
            *)
                log_warning "不支持的云存储提供商: $CLOUD_PROVIDER"
                ;;
        esac
        
        log_success "云存储上传完成"
    fi
}

# 发送通知
send_notification() {
    if [ -n "$NOTIFICATION_WEBHOOK" ]; then
        local backup_file="$BACKUP_DIR/$(basename "$CURRENT_BACKUP_DIR").tar.gz"
        local size=$(du -sh "$backup_file" | cut -f1)
        
        curl -X POST "$NOTIFICATION_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{
                \"text\": \"量化交易平台备份完成\",
                \"attachments\": [{
                    \"color\": \"good\",
                    \"fields\": [
                        {\"title\": \"备份时间\", \"value\": \"$(date)\", \"short\": true},
                        {\"title\": \"备份大小\", \"value\": \"$size\", \"short\": true},
                        {\"title\": \"备份文件\", \"value\": \"$(basename "$backup_file")\", \"short\": false}
                    ]
                }]
            }" 2>/dev/null || log_warning "通知发送失败"
    fi
}

# 显示帮助
show_help() {
    cat << EOF
量化交易平台备份脚本

用法: $0 [选项]

选项:
  -t, --type          部署类型 (docker|k8s) [默认: docker]
  -d, --dir           备份目录 [默认: ./backups]
  -r, --retention     保留天数 [默认: 30]
  -c, --compress      压缩备份 [默认: true]
  -u, --upload        上传到云存储 [默认: false]
  -n, --notify        发送通知 [默认: false]
  -h, --help          显示帮助信息

环境变量:
  CLOUD_STORAGE_ENABLED   启用云存储上传
  CLOUD_PROVIDER          云存储提供商 (aws|gcp|azure)
  S3_BUCKET              AWS S3存储桶
  GCS_BUCKET             GCP存储桶
  NOTIFICATION_WEBHOOK    通知Webhook URL

示例:
  $0 -t docker -d /backup -r 7
  $0 -t k8s --upload --notify
EOF
}

# 主函数
main() {
    local compress=true
    local upload=false
    local notify=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                DEPLOYMENT_TYPE="$2"
                shift 2
                ;;
            -d|--dir)
                BACKUP_DIR="$2"
                shift 2
                ;;
            -r|--retention)
                RETENTION_DAYS="$2"
                shift 2
                ;;
            -c|--compress)
                compress=true
                shift
                ;;
            -u|--upload)
                upload=true
                shift
                ;;
            -n|--notify)
                notify=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    log_info "开始备份 - 部署类型: $DEPLOYMENT_TYPE"
    
    # 执行备份流程
    create_backup_dir
    backup_postgres
    backup_redis
    backup_influxdb
    backup_app_data
    backup_configs
    create_manifest
    
    if [ "$compress" = true ]; then
        compress_backup
        verify_backup
    fi
    
    if [ "$upload" = true ]; then
        upload_to_cloud
    fi
    
    if [ "$notify" = true ]; then
        send_notification
    fi
    
    cleanup_old_backups
    
    log_success "备份完成！"
}

# 执行主函数
main "$@"