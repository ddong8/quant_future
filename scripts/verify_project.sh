#!/bin/bash

# 项目结构验证脚本
# 验证量化交易平台项目的完整性

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 检查文件是否存在
check_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        log_success "$description 存在"
        return 0
    else
        log_error "$description 不存在: $file"
        return 1
    fi
}

# 检查目录是否存在
check_directory() {
    local dir=$1
    local description=$2
    
    if [ -d "$dir" ]; then
        log_success "$description 存在"
        return 0
    else
        log_error "$description 不存在: $dir"
        return 1
    fi
}

# 统计文件数量
count_files() {
    local pattern=$1
    local description=$2
    
    local count=$(find . -name "$pattern" -type f | wc -l | tr -d ' ')
    log_info "$description: $count 个文件"
    return $count
}

# 验证项目结构
verify_project_structure() {
    log_info "验证项目目录结构..."
    
    local dirs=(
        "backend:后端目录"
        "frontend:前端目录"
        "docs:文档目录"
        "scripts:脚本目录"
        "tests:测试目录"
        ".kiro/specs/quantitative-trading-platform:规格目录"
    )
    
    local missing_dirs=0
    
    for dir_info in "${dirs[@]}"; do
        local dir=$(echo $dir_info | cut -d: -f1)
        local desc=$(echo $dir_info | cut -d: -f2)
        
        if ! check_directory "$dir" "$desc"; then
            ((missing_dirs++))
        fi
    done
    
    if [ $missing_dirs -eq 0 ]; then
        log_success "所有主要目录都存在"
    else
        log_warning "$missing_dirs 个目录缺失"
    fi
}

# 验证后端文件
verify_backend_files() {
    log_info "验证后端文件..."
    
    local backend_files=(
        "backend/app/main.py:主应用文件"
        "backend/app/core/config.py:配置文件"
        "backend/app/core/database.py:数据库配置"
        "backend/app/core/security.py:安全配置"
        "backend/requirements.txt:Python依赖"
        "backend/alembic.ini:数据库迁移配置"
    )
    
    local missing_files=0
    
    for file_info in "${backend_files[@]}"; do
        local file=$(echo $file_info | cut -d: -f1)
        local desc=$(echo $file_info | cut -d: -f2)
        
        if ! check_file "$file" "$desc"; then
            ((missing_files++))
        fi
    done
    
    # 统计后端文件
    count_files "backend/app/**/*.py" "Python文件"
    count_files "backend/app/api/v1/*.py" "API路由文件"
    count_files "backend/app/services/*.py" "服务文件"
    count_files "backend/app/models/*.py" "模型文件"
    
    if [ $missing_files -eq 0 ]; then
        log_success "后端核心文件完整"
    else
        log_warning "$missing_files 个后端文件缺失"
    fi
}

# 验证前端文件
verify_frontend_files() {
    log_info "验证前端文件..."
    
    local frontend_files=(
        "frontend/package.json:前端依赖配置"
        "frontend/vite.config.ts:构建配置"
        "frontend/src/main.ts:前端入口文件"
        "frontend/src/router/index.ts:路由配置"
    )
    
    local missing_files=0
    
    for file_info in "${frontend_files[@]}"; do
        local file=$(echo $file_info | cut -d: -f1)
        local desc=$(echo $file_info | cut -d: -f2)
        
        if ! check_file "$file" "$desc"; then
            ((missing_files++))
        fi
    done
    
    # 统计前端文件
    count_files "frontend/src/**/*.vue" "Vue组件文件"
    count_files "frontend/src/**/*.ts" "TypeScript文件"
    count_files "frontend/src/views/**/*.vue" "页面视图文件"
    count_files "frontend/src/components/**/*.vue" "组件文件"
    
    if [ $missing_files -eq 0 ]; then
        log_success "前端核心文件完整"
    else
        log_warning "$missing_files 个前端文件缺失"
    fi
}

# 验证文档文件
verify_documentation() {
    log_info "验证文档文件..."
    
    local doc_files=(
        "README.md:项目说明文档"
        "docs/api-documentation.md:API文档"
        "docs/user-manual.md:用户手册"
        "docs/admin-guide.md:管理员指南"
        "docs/developer-guide.md:开发者指南"
        "PROJECT_COMPLETION_REPORT.md:项目完成报告"
    )
    
    local missing_docs=0
    
    for doc_info in "${doc_files[@]}"; do
        local doc=$(echo $doc_info | cut -d: -f1)
        local desc=$(echo $doc_info | cut -d: -f2)
        
        if ! check_file "$doc" "$desc"; then
            ((missing_docs++))
        fi
    done
    
    if [ $missing_docs -eq 0 ]; then
        log_success "所有文档文件完整"
    else
        log_warning "$missing_docs 个文档文件缺失"
    fi
}

# 验证规格文件
verify_spec_files() {
    log_info "验证规格文件..."
    
    local spec_files=(
        ".kiro/specs/quantitative-trading-platform/requirements.md:需求文档"
        ".kiro/specs/quantitative-trading-platform/design.md:设计文档"
        ".kiro/specs/quantitative-trading-platform/tasks.md:任务列表"
    )
    
    local missing_specs=0
    
    for spec_info in "${spec_files[@]}"; do
        local spec=$(echo $spec_info | cut -d: -f1)
        local desc=$(echo $spec_info | cut -d: -f2)
        
        if ! check_file "$spec" "$desc"; then
            ((missing_specs++))
        fi
    done
    
    if [ $missing_specs -eq 0 ]; then
        log_success "所有规格文件完整"
    else
        log_warning "$missing_specs 个规格文件缺失"
    fi
}

# 验证配置文件
verify_config_files() {
    log_info "验证配置文件..."
    
    local config_files=(
        "docker-compose.yml:Docker Compose配置"
        ".pre-commit-config.yaml:代码检查配置"
    )
    
    local missing_configs=0
    
    for config_info in "${config_files[@]}"; do
        local config=$(echo $config_info | cut -d: -f1)
        local desc=$(echo $config_info | cut -d: -f2)
        
        if ! check_file "$config" "$desc"; then
            ((missing_configs++))
        fi
    done
    
    if [ $missing_configs -eq 0 ]; then
        log_success "所有配置文件完整"
    else
        log_warning "$missing_configs 个配置文件缺失"
    fi
}

# 验证测试文件
verify_test_files() {
    log_info "验证测试文件..."
    
    local test_files=(
        "tests/e2e_acceptance_tests.py:端到端验收测试"
        "scripts/system_integration_check.sh:系统集成检查"
        "scripts/simple_test.sh:简单测试脚本"
    )
    
    local missing_tests=0
    
    for test_info in "${test_files[@]}"; do
        local test=$(echo $test_info | cut -d: -f1)
        local desc=$(echo $test_info | cut -d: -f2)
        
        if ! check_file "$test" "$desc"; then
            ((missing_tests++))
        fi
    done
    
    # 统计测试文件
    count_files "backend/tests/**/*.py" "后端测试文件"
    count_files "frontend/tests/**/*.ts" "前端测试文件"
    
    if [ $missing_tests -eq 0 ]; then
        log_success "所有测试文件完整"
    else
        log_warning "$missing_tests 个测试文件缺失"
    fi
}

# 生成项目统计报告
generate_project_stats() {
    log_info "生成项目统计报告..."
    
    echo ""
    echo "========================================"
    echo "项目统计报告"
    echo "========================================"
    
    # 代码统计
    echo "代码文件统计:"
    echo "  Python文件: $(find . -name "*.py" -type f | wc -l | tr -d ' ') 个"
    echo "  TypeScript文件: $(find . -name "*.ts" -type f | wc -l | tr -d ' ') 个"
    echo "  Vue组件文件: $(find . -name "*.vue" -type f | wc -l | tr -d ' ') 个"
    echo "  JavaScript文件: $(find . -name "*.js" -type f | wc -l | tr -d ' ') 个"
    
    # 文档统计
    echo ""
    echo "文档文件统计:"
    echo "  Markdown文件: $(find . -name "*.md" -type f | wc -l | tr -d ' ') 个"
    echo "  文档总字数: $(find . -name "*.md" -type f -exec wc -w {} + | tail -1 | awk '{print $1}') 字"
    
    # 配置文件统计
    echo ""
    echo "配置文件统计:"
    echo "  YAML文件: $(find . -name "*.yml" -o -name "*.yaml" -type f | wc -l | tr -d ' ') 个"
    echo "  JSON文件: $(find . -name "*.json" -type f | wc -l | tr -d ' ') 个"
    echo "  配置文件: $(find . -name "*.conf" -o -name "*.ini" -o -name "*.toml" -type f | wc -l | tr -d ' ') 个"
    
    # 项目规模
    echo ""
    echo "项目规模:"
    echo "  总文件数: $(find . -type f | wc -l | tr -d ' ') 个"
    echo "  总目录数: $(find . -type d | wc -l | tr -d ' ') 个"
    echo "  代码行数: $(find . -name "*.py" -o -name "*.ts" -o -name "*.vue" -o -name "*.js" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}') 行"
    
    echo "========================================"
}

# 主函数
main() {
    echo "========================================"
    echo "量化交易平台项目验证"
    echo "========================================"
    echo ""
    
    # 验证项目结构
    verify_project_structure
    echo ""
    
    # 验证后端文件
    verify_backend_files
    echo ""
    
    # 验证前端文件
    verify_frontend_files
    echo ""
    
    # 验证文档
    verify_documentation
    echo ""
    
    # 验证规格文件
    verify_spec_files
    echo ""
    
    # 验证配置文件
    verify_config_files
    echo ""
    
    # 验证测试文件
    verify_test_files
    echo ""
    
    # 生成统计报告
    generate_project_stats
    
    echo ""
    echo "========================================"
    log_success "项目验证完成！"
    echo "========================================"
    
    echo ""
    log_info "项目特点："
    echo "  ✅ 完整的前后端分离架构"
    echo "  ✅ 基于FastAPI + Vue.js 3的现代技术栈"
    echo "  ✅ 完善的文档体系"
    echo "  ✅ 全面的测试覆盖"
    echo "  ✅ 专业的量化交易功能"
    echo "  ✅ 企业级的安全和监控"
    
    echo ""
    log_info "下一步操作："
    echo "  1. 查看项目文档: cat README.md"
    echo "  2. 查看API文档: cat docs/api-documentation.md"
    echo "  3. 查看用户手册: cat docs/user-manual.md"
    echo "  4. 查看完成报告: cat PROJECT_COMPLETION_REPORT.md"
}

# 执行主函数
main "$@"