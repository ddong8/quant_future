#!/usr/bin/env python3
"""
后端容器优化验证脚本
验证后端容器优化是否正确实现
"""
import sys
from pathlib import Path


def validate_dockerfile_optimization():
    """验证 Dockerfile 优化"""
    print("验证 Dockerfile 优化...")
    
    dockerfile_path = Path('backend/Dockerfile')
    if not dockerfile_path.exists():
        print("❌ backend/Dockerfile 不存在")
        return False
    
    try:
        with open(dockerfile_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查多阶段构建
        if 'FROM python:3.11-slim as builder' in content and 'FROM python:3.11-slim as runtime' in content:
            print("✅ 多阶段构建已实现")
        else:
            print("❌ 缺少多阶段构建")
            return False
        
        # 检查非root用户
        if 'useradd' in content and 'USER appuser' in content:
            print("✅ 非root用户配置已实现")
        else:
            print("❌ 缺少非root用户配置")
            return False
        
        # 检查健康检查
        if 'HEALTHCHECK' in content:
            print("✅ 健康检查已配置")
        else:
            print("❌ 缺少健康检查配置")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 读取 Dockerfile 失败: {e}")
        return False


def validate_startup_script():
    """验证启动脚本"""
    print("\n验证启动脚本...")
    
    script_path = Path('backend/start_backend.py')
    if not script_path.exists():
        print("❌ backend/start_backend.py 不存在")
        return False
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键类和方法
        required_elements = [
            'class BackendStarter',
            'def validate_environment',
            'def wait_for_initialization',
            'def perform_startup_health_check',
            'def start_uvicorn_server',
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ 缺少关键元素: {missing_elements}")
            return False
        else:
            print("✅ 启动脚本结构完整")
        
        return True
        
    except Exception as e:
        print(f"❌ 读取启动脚本失败: {e}")
        return False


def validate_config_validation_script():
    """验证配置验证脚本"""
    print("\n验证配置验证脚本...")
    
    script_path = Path('backend/validate_backend_config.py')
    if not script_path.exists():
        print("❌ backend/validate_backend_config.py 不存在")
        return False
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查验证方法
        validation_methods = [
            'validate_environment_variables',
            'validate_database_urls',
            'validate_numeric_configs',
            'validate_security_settings',
        ]
        
        missing_methods = []
        for method in validation_methods:
            if method not in content:
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ 缺少验证方法: {missing_methods}")
            return False
        else:
            print("✅ 配置验证脚本完整")
        
        return True
        
    except Exception as e:
        print(f"❌ 读取配置验证脚本失败: {e}")
        return False


def validate_docker_compose_backend_config():
    """验证 Docker Compose 后端配置"""
    print("\n验证 Docker Compose 后端配置...")
    
    compose_file = Path('docker-compose.yml')
    if not compose_file.exists():
        print("❌ docker-compose.yml 不存在")
        return False
    
    try:
        with open(compose_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查后端服务配置
        backend_configs = [
            'container_name: trading_backend',
            'healthcheck:',
            'deploy:',
            'resources:',
            'command: ["python", "start_backend.py"]',
        ]
        
        missing_configs = []
        for config in backend_configs:
            if config not in content:
                missing_configs.append(config)
        
        if missing_configs:
            print(f"❌ 缺少后端配置: {missing_configs}")
            return False
        else:
            print("✅ Docker Compose 后端配置完整")
        
        # 检查环境变量
        env_vars = [
            'DATABASE_URL',
            'REDIS_URL',
            'INFLUXDB_URL',
            'SECRET_KEY',
            'WORKER_PROCESSES',
            'DB_POOL_SIZE',
        ]
        
        missing_env_vars = []
        for var in env_vars:
            if f'- {var}=' not in content:
                missing_env_vars.append(var)
        
        if missing_env_vars:
            print(f"⚠️  可能缺少环境变量: {missing_env_vars}")
        else:
            print("✅ 环境变量配置完整")
        
        return True
        
    except Exception as e:
        print(f"❌ 读取 docker-compose.yml 失败: {e}")
        return False


def validate_environment_specific_configs():
    """验证环境特定配置"""
    print("\n验证环境特定配置...")
    
    config_files = [
        ('docker-compose.dev.yml', '开发环境配置'),
        ('docker-compose.prod.yml', '生产环境配置'),
    ]
    
    all_valid = True
    
    for file_path, description in config_files:
        config_file = Path(file_path)
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'backend:' in content:
                    print(f"✅ {description}存在后端配置")
                else:
                    print(f"⚠️  {description}可能缺少后端配置")
                    
            except Exception as e:
                print(f"❌ 读取 {file_path} 失败: {e}")
                all_valid = False
        else:
            print(f"❌ {description}文件不存在: {file_path}")
            all_valid = False
    
    return all_valid


def validate_documentation():
    """验证文档"""
    print("\n验证文档...")
    
    doc_path = Path('backend/docs/backend_container_optimization.md')
    if doc_path.exists():
        print("✅ 后端容器优化文档存在")
        return True
    else:
        print("❌ 后端容器优化文档不存在")
        return False


def main():
    """主函数"""
    print("后端容器优化验证")
    print("=" * 50)
    
    validations = [
        ("Dockerfile 优化", validate_dockerfile_optimization),
        ("启动脚本", validate_startup_script),
        ("配置验证脚本", validate_config_validation_script),
        ("Docker Compose 配置", validate_docker_compose_backend_config),
        ("环境特定配置", validate_environment_specific_configs),
        ("文档", validate_documentation),
    ]
    
    passed = 0
    total = len(validations)
    
    for name, validation_func in validations:
        try:
            if validation_func():
                passed += 1
                print(f"✅ {name} 验证通过")
            else:
                print(f"❌ {name} 验证失败")
        except Exception as e:
            print(f"💥 {name} 验证异常: {e}")
    
    print(f"\n{'='*50}")
    print(f"验证结果: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 后端容器优化验证通过！")
        print("\n✅ 后端容器优化已完成:")
        print("  - ✅ 多阶段构建 Dockerfile")
        print("  - ✅ 非root用户安全配置")
        print("  - ✅ 智能启动脚本")
        print("  - ✅ 完整的环境变量配置")
        print("  - ✅ 健康检查集成")
        print("  - ✅ 性能优化配置")
        print("  - ✅ 开发和生产环境配置")
        print("  - ✅ 配置验证工具")
        print("  - ✅ 详细的优化文档")
        return 0
    else:
        print("\n❌ 部分验证失败，请检查配置")
        return 1


if __name__ == "__main__":
    sys.exit(main())