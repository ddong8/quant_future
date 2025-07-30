#!/usr/bin/env python3
"""
Docker Compose 配置验证脚本
验证 docker-compose.yml 配置的正确性和完整性
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class ComposeConfigValidator:
    """Docker Compose 配置验证器"""
    
    def __init__(self, compose_file: str = "docker-compose.yml"):
        self.compose_file = Path(compose_file)
        self.config = None
        self.errors = []
        self.warnings = []
        
    def load_config(self) -> bool:
        """加载 docker-compose.yml 配置"""
        try:
            if not self.compose_file.exists():
                self.errors.append(f"配置文件不存在: {self.compose_file}")
                return False
            
            if not HAS_YAML:
                self.warnings.append("未安装 PyYAML，跳过 YAML 解析验证")
                return True
                
            with open(self.compose_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
                
            if not self.config:
                self.errors.append("配置文件为空或格式错误")
                return False
                
            return True
            
        except Exception as e:
            if HAS_YAML:
                self.errors.append(f"YAML 格式错误: {e}")
            else:
                self.warnings.append(f"无法解析 YAML 文件: {e}")
            return not HAS_YAML  # 如果没有 yaml 库，继续执行其他检查
        except Exception as e:
            self.errors.append(f"加载配置文件失败: {e}")
            return False
    
    def validate_services(self) -> bool:
        """验证服务配置"""
        if not self.config:
            self.warnings.append("跳过服务配置验证（配置未加载）")
            return True
            
        if 'services' not in self.config:
            self.errors.append("缺少 services 配置")
            return False
            
        services = self.config['services']
        required_services = ['postgres', 'redis', 'influxdb', 'db-init', 'backend', 'frontend']
        
        # 检查必需的服务
        for service in required_services:
            if service not in services:
                self.errors.append(f"缺少必需的服务: {service}")
        
        # 验证每个服务的配置
        for service_name, service_config in services.items():
            self._validate_service_config(service_name, service_config)
            
        return len(self.errors) == 0
    
    def _validate_service_config(self, service_name: str, config: Dict[str, Any]):
        """验证单个服务配置"""
        
        # 检查容器名称
        if 'container_name' not in config:
            self.warnings.append(f"服务 {service_name} 缺少 container_name")
        
        # 检查环境变量
        if 'environment' in config:
            self._validate_environment_variables(service_name, config['environment'])
        
        # 检查依赖关系
        if 'depends_on' in config:
            self._validate_dependencies(service_name, config['depends_on'])
        
        # 检查健康检查
        if service_name in ['postgres', 'redis', 'influxdb', 'backend', 'frontend']:
            if 'healthcheck' not in config:
                self.warnings.append(f"服务 {service_name} 缺少健康检查配置")
        
        # 检查卷挂载
        if 'volumes' in config:
            self._validate_volumes(service_name, config['volumes'])
    
    def _validate_environment_variables(self, service_name: str, env_vars: List[str]):
        """验证环境变量配置"""
        required_env_vars = {
            'db-init': [
                'DATABASE_URL', 'REDIS_URL', 'INFLUXDB_URL', 
                'SECRET_KEY', 'DB_INIT_TIMEOUT'
            ],
            'backend': [
                'DATABASE_URL', 'REDIS_URL', 'SECRET_KEY', 
                'JWT_ALGORITHM', 'DEBUG'
            ],
            'frontend': [
                'VITE_API_BASE_URL', 'NODE_ENV'
            ]
        }
        
        if service_name in required_env_vars:
            env_dict = {}
            for env_var in env_vars:
                if '=' in env_var:
                    key, _ = env_var.split('=', 1)
                    env_dict[key] = True
            
            for required_var in required_env_vars[service_name]:
                if required_var not in env_dict:
                    self.warnings.append(
                        f"服务 {service_name} 缺少环境变量: {required_var}"
                    )
    
    def _validate_dependencies(self, service_name: str, dependencies: Dict[str, Any]):
        """验证服务依赖关系"""
        services = self.config['services']
        
        for dep_service, dep_config in dependencies.items():
            if dep_service not in services:
                self.errors.append(
                    f"服务 {service_name} 依赖的服务 {dep_service} 不存在"
                )
            
            # 检查依赖条件
            if isinstance(dep_config, dict) and 'condition' in dep_config:
                condition = dep_config['condition']
                valid_conditions = [
                    'service_started', 'service_healthy', 
                    'service_completed_successfully'
                ]
                if condition not in valid_conditions:
                    self.errors.append(
                        f"服务 {service_name} 的依赖条件无效: {condition}"
                    )
    
    def _validate_volumes(self, service_name: str, volumes: List[str]):
        """验证卷挂载配置"""
        for volume in volumes:
            if ':' in volume:
                host_path, container_path = volume.split(':', 1)
                
                # 检查主机路径是否存在（相对路径）
                if not host_path.startswith('/') and not host_path.startswith('~'):
                    if '/' in host_path and not Path(host_path).exists():
                        self.warnings.append(
                            f"服务 {service_name} 的卷挂载路径可能不存在: {host_path}"
                        )
    
    def validate_networks(self) -> bool:
        """验证网络配置"""
        if not self.config:
            self.warnings.append("跳过网络配置验证（配置未加载）")
            return True
            
        if 'networks' not in self.config:
            self.warnings.append("未定义自定义网络")
            return True
        
        networks = self.config['networks']
        
        # 检查网络配置
        for network_name, network_config in networks.items():
            if not isinstance(network_config, dict):
                continue
                
            if 'name' in network_config:
                # 验证网络名称格式
                name = network_config['name']
                if not name.replace('_', '').replace('-', '').isalnum():
                    self.warnings.append(f"网络名称可能包含无效字符: {name}")
        
        return True
    
    def validate_volumes_definition(self) -> bool:
        """验证卷定义"""
        if not self.config:
            self.warnings.append("跳过卷配置验证（配置未加载）")
            return True
            
        if 'volumes' not in self.config:
            self.warnings.append("未定义命名卷")
            return True
        
        volumes = self.config['volumes']
        expected_volumes = [
            'postgres_data', 'redis_data', 'influxdb_data', 'db_init_status'
        ]
        
        for volume in expected_volumes:
            if volume not in volumes:
                self.warnings.append(f"缺少预期的卷定义: {volume}")
        
        return True
    
    def validate_environment_file(self) -> bool:
        """验证环境变量文件"""
        env_files = ['.env', '.env.template']
        
        for env_file in env_files:
            if Path(env_file).exists():
                try:
                    with open(env_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 检查关键环境变量
                    required_vars = [
                        'DATABASE_URL', 'REDIS_URL', 'SECRET_KEY',
                        'POSTGRES_PASSWORD', 'INFLUXDB_ADMIN_TOKEN'
                    ]
                    
                    for var in required_vars:
                        if var not in content:
                            self.warnings.append(
                                f"环境文件 {env_file} 缺少变量: {var}"
                            )
                            
                except Exception as e:
                    self.warnings.append(f"读取环境文件 {env_file} 失败: {e}")
        
        if not any(Path(f).exists() for f in env_files):
            self.warnings.append("未找到环境变量文件 (.env 或 .env.template)")
        
        return True
    
    def validate_docker_compose_syntax(self) -> bool:
        """使用 docker-compose 验证语法"""
        try:
            result = subprocess.run(
                ['docker-compose', 'config', '--quiet'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.errors.append(f"Docker Compose 语法错误: {result.stderr}")
                return False
                
            return True
            
        except subprocess.TimeoutExpired:
            self.warnings.append("Docker Compose 语法验证超时")
            return True
        except FileNotFoundError:
            self.warnings.append("未找到 docker-compose 命令，跳过语法验证")
            return True
        except Exception as e:
            self.warnings.append(f"Docker Compose 语法验证失败: {e}")
            return True
    
    def run_validation(self) -> bool:
        """运行完整验证"""
        print("🔍 开始验证 Docker Compose 配置...")
        
        # 加载配置
        if not self.load_config():
            return False
        
        # 执行各项验证
        validations = [
            ("服务配置", self.validate_services),
            ("网络配置", self.validate_networks),
            ("卷配置", self.validate_volumes_definition),
            ("环境变量文件", self.validate_environment_file),
            ("语法检查", self.validate_docker_compose_syntax),
        ]
        
        for name, validation_func in validations:
            print(f"  验证 {name}...")
            validation_func()
        
        return len(self.errors) == 0
    
    def print_results(self):
        """打印验证结果"""
        print("\n" + "="*60)
        print("验证结果")
        print("="*60)
        
        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ 配置验证通过，未发现问题")
        elif not self.errors:
            print(f"\n✅ 配置基本正确，但有 {len(self.warnings)} 个警告需要注意")
        else:
            print(f"\n❌ 配置验证失败，请修复 {len(self.errors)} 个错误")
        
        print("\n" + "="*60)


def main():
    """主函数"""
    validator = ComposeConfigValidator()
    
    success = validator.run_validation()
    validator.print_results()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())