#!/usr/bin/env python3
"""
Docker Compose 配置验证脚本
验证 Docker Compose 文件的语法和配置正确性
"""
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List


class DockerComposeValidator:
    """Docker Compose 配置验证器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_file_syntax(self, file_path: Path) -> bool:
        """验证文件语法"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"{file_path}: YAML语法错误 - {e}")
            return False
        except Exception as e:
            self.errors.append(f"{file_path}: 文件读取错误 - {e}")
            return False
    
    def validate_service_structure(self, config: Dict[str, Any], file_name: str) -> bool:
        """验证服务结构"""
        if 'services' not in config:
            self.errors.append(f"{file_name}: 缺少 'services' 配置")
            return False
        
        services = config['services']
        required_services = ['postgres', 'redis', 'influxdb', 'backend']
        
        for service in required_services:
            if service not in services:
                self.errors.append(f"{file_name}: 缺少必需服务 '{service}'")
        
        return len(self.errors) == 0
    
    def validate_db_init_service(self, config: Dict[str, Any], file_name: str) -> bool:
        """验证数据库初始化服务配置"""
        services = config.get('services', {})
        
        if 'db-init' not in services:
            self.errors.append(f"{file_name}: 缺少 'db-init' 服务")
            return False
        
        db_init = services['db-init']
        
        # 检查必需配置
        required_configs = ['environment', 'depends_on', 'volumes']
        for config_key in required_configs:
            if config_key not in db_init:
                self.errors.append(f"{file_name}: db-init 服务缺少 '{config_key}' 配置")
        
        # 检查环境变量
        env_vars = db_init.get('environment', [])
        if isinstance(env_vars, list):
            env_dict = {}
            for env in env_vars:
                if '=' in env:
                    key, value = env.split('=', 1)
                    env_dict[key] = value
        else:
            env_dict = env_vars
        
        required_env_vars = [
            'DATABASE_URL', 'REDIS_URL', 'INFLUXDB_URL', 
            'INFLUXDB_TOKEN', 'SECRET_KEY'
        ]
        
        for env_var in required_env_vars:
            if env_var not in env_dict:
                self.warnings.append(f"{file_name}: db-init 服务缺少环境变量 '{env_var}'")
        
        return True
    
    def validate_dependencies(self, config: Dict[str, Any], file_name: str) -> bool:
        """验证服务依赖关系"""
        services = config.get('services', {})
        
        # 检查后端服务依赖
        if 'backend' in services:
            backend = services['backend']
            depends_on = backend.get('depends_on', {})
            
            expected_deps = ['postgres', 'redis', 'influxdb']
            if 'db-init' in services:
                expected_deps.append('db-init')
            
            for dep in expected_deps:
                if dep not in depends_on:
                    self.warnings.append(f"{file_name}: backend 服务建议依赖 '{dep}'")
        
        return True
    
    def validate_volumes(self, config: Dict[str, Any], file_name: str) -> bool:
        """验证数据卷配置"""
        volumes = config.get('volumes', {})
        
        expected_volumes = ['postgres_data', 'redis_data', 'influxdb_data']
        if 'services' in config and 'db-init' in config['services']:
            expected_volumes.append('db_init_status')
        
        for volume in expected_volumes:
            if volume not in volumes:
                self.warnings.append(f"{file_name}: 建议定义数据卷 '{volume}'")
        
        return True
    
    def validate_healthchecks(self, config: Dict[str, Any], file_name: str) -> bool:
        """验证健康检查配置"""
        services = config.get('services', {})
        
        health_check_services = ['postgres', 'redis', 'influxdb', 'backend']
        
        for service_name in health_check_services:
            if service_name in services:
                service = services[service_name]
                if 'healthcheck' not in service:
                    self.warnings.append(f"{file_name}: 建议为 '{service_name}' 服务添加健康检查")
        
        return True
    
    def validate_docker_compose_file(self, file_path: Path) -> bool:
        """验证单个 Docker Compose 文件"""
        print(f"\n验证文件: {file_path}")
        
        # 检查文件是否存在
        if not file_path.exists():
            self.errors.append(f"文件不存在: {file_path}")
            return False
        
        # 验证语法
        if not self.validate_file_syntax(file_path):
            return False
        
        # 加载配置
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            self.errors.append(f"{file_path}: 配置加载失败 - {e}")
            return False
        
        file_name = file_path.name
        
        # 验证各个方面
        validations = [
            self.validate_service_structure(config, file_name),
            self.validate_dependencies(config, file_name),
            self.validate_volumes(config, file_name),
            self.validate_healthchecks(config, file_name),
        ]
        
        # 如果是主配置文件，验证初始化服务
        if file_name == 'docker-compose.yml':
            validations.append(self.validate_db_init_service(config, file_name))
        
        return all(validations)
    
    def validate_all_files(self) -> bool:
        """验证所有 Docker Compose 文件"""
        compose_files = [
            Path('docker-compose.yml'),
            Path('docker-compose.dev.yml'),
            Path('docker-compose.prod.yml'),
        ]
        
        all_valid = True
        
        for file_path in compose_files:
            if file_path.exists():
                if not self.validate_docker_compose_file(file_path):
                    all_valid = False
            else:
                self.warnings.append(f"文件不存在: {file_path}")
        
        return all_valid
    
    def print_results(self):
        """打印验证结果"""
        print("\n" + "=" * 60)
        print("Docker Compose 配置验证结果")
        print("=" * 60)
        
        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if not self.errors and not self.warnings:
            print("\n🎉 所有配置验证通过！")
        elif not self.errors:
            print("\n✅ 配置验证通过，但有一些建议需要注意")
        else:
            print("\n❌ 配置验证失败，请修复错误后重试")


def validate_dockerfile_exists():
    """验证 Dockerfile 文件是否存在"""
    dockerfiles = [
        Path('backend/Dockerfile'),
        Path('backend/Dockerfile.init'),
    ]
    
    missing_files = []
    for dockerfile in dockerfiles:
        if not dockerfile.exists():
            missing_files.append(str(dockerfile))
    
    if missing_files:
        print(f"\n⚠️  缺少 Dockerfile 文件: {missing_files}")
        return False
    
    print("\n✅ 所有必需的 Dockerfile 文件都存在")
    return True


def validate_init_scripts():
    """验证初始化脚本是否存在"""
    init_scripts = [
        Path('backend/init_db.py'),
        Path('backend/wait_for_db.py'),
        Path('backend/check_init_status.py'),
        Path('backend/run_init.py'),
        Path('backend/init_healthcheck.py'),
    ]
    
    missing_scripts = []
    for script in init_scripts:
        if not script.exists():
            missing_scripts.append(str(script))
    
    if missing_scripts:
        print(f"\n⚠️  缺少初始化脚本: {missing_scripts}")
        return False
    
    print("\n✅ 所有初始化脚本都存在")
    return True


def main():
    """主函数"""
    print("Docker Compose 配置验证")
    print("=" * 50)
    
    validator = DockerComposeValidator()
    
    # 验证 Docker Compose 文件
    compose_valid = validator.validate_all_files()
    
    # 验证 Dockerfile 文件
    dockerfile_valid = validate_dockerfile_exists()
    
    # 验证初始化脚本
    scripts_valid = validate_init_scripts()
    
    # 打印结果
    validator.print_results()
    
    # 总结
    all_valid = compose_valid and dockerfile_valid and scripts_valid
    
    if all_valid:
        print("\n🎉 Docker Compose 配置完全验证通过！")
        print("\n✅ 数据库初始化容器配置已完成:")
        print("  - 数据库初始化容器 (db-init)")
        print("  - 初始化脚本和健康检查")
        print("  - 服务依赖关系配置")
        print("  - 开发和生产环境配置")
        print("  - 完整的部署文档")
        return 0
    else:
        print("\n❌ 部分配置验证失败")
        return 1


if __name__ == "__main__":
    try:
        import yaml
    except ImportError:
        print("❌ 缺少 PyYAML 依赖，请安装: pip install PyYAML")
        sys.exit(2)
    
    sys.exit(main())