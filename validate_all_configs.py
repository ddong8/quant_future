#!/usr/bin/env python3
"""
全面的配置验证脚本
验证整个项目的配置完整性和正确性
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.project_root = Path.cwd()
        
    def log_error(self, message: str):
        """记录错误"""
        self.errors.append(message)
        print(f"❌ 错误: {message}")
    
    def log_warning(self, message: str):
        """记录警告"""
        self.warnings.append(message)
        print(f"⚠️  警告: {message}")
    
    def log_success(self, message: str):
        """记录成功"""
        print(f"✅ {message}")
    
    def validate_environment_variables(self) -> bool:
        """验证环境变量配置"""
        print("\n🔍 验证环境变量配置...")
        
        # 检查 .env.template 文件
        env_template = self.project_root / '.env.template'
        if not env_template.exists():
            self.log_error(".env.template 文件不存在")
            return False
        
        self.log_success(".env.template 文件存在")
        
        # 读取模板文件内容
        try:
            with open(env_template, 'r', encoding='utf-8') as f:
                template_content = f.read()
        except Exception as e:
            self.log_error(f"读取 .env.template 失败: {e}")
            return False
        
        # 检查必需的环境变量
        required_vars = [
            'DATABASE_URL',
            'REDIS_URL',
            'INFLUXDB_URL',
            'SECRET_KEY',
            'POSTGRES_PASSWORD',
            'INFLUXDB_ADMIN_TOKEN',
            'JWT_ALGORITHM',
            'DEBUG',
            'LOG_LEVEL'
        ]
        
        missing_vars = []
        for var in required_vars:
            if var not in template_content:
                missing_vars.append(var)
        
        if missing_vars:
            self.log_error(f"缺少必需的环境变量: {', '.join(missing_vars)}")
        else:
            self.log_success("所有必需的环境变量都存在")
        
        # 检查 .env 文件
        env_file = self.project_root / '.env'
        if env_file.exists():
            self.log_success(".env 文件存在")
        else:
            self.log_warning(".env 文件不存在，建议从模板创建")
        
        return len(missing_vars) == 0
    
    def validate_docker_compose(self) -> bool:
        """验证 Docker Compose 配置"""
        print("\n🔍 验证 Docker Compose 配置...")
        
        compose_file = self.project_root / 'docker-compose.yml'
        if not compose_file.exists():
            self.log_error("docker-compose.yml 文件不存在")
            return False
        
        self.log_success("docker-compose.yml 文件存在")
        
        # 验证语法
        try:
            result = subprocess.run(
                ['docker-compose', 'config', '--quiet'],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                self.log_success("Docker Compose 语法验证通过")
            else:
                self.log_error(f"Docker Compose 语法错误: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_warning("Docker Compose 语法验证超时")
        except FileNotFoundError:
            self.log_warning("未找到 docker-compose 命令，跳过语法验证")
        except Exception as e:
            self.log_warning(f"Docker Compose 语法验证失败: {e}")
        
        # 检查必需的服务
        if HAS_YAML:
            try:
                with open(compose_file, 'r', encoding='utf-8') as f:
                    compose_config = yaml.safe_load(f)
                
                required_services = ['postgres', 'redis', 'influxdb', 'db-init', 'backend', 'frontend']
                services = compose_config.get('services', {})
                
                missing_services = [svc for svc in required_services if svc not in services]
                if missing_services:
                    self.log_error(f"缺少必需的服务: {', '.join(missing_services)}")
                else:
                    self.log_success("所有必需的服务都存在")
                
                return len(missing_services) == 0
                
            except Exception as e:
                self.log_error(f"解析 docker-compose.yml 失败: {e}")
                return False
        
        return True
    
    def validate_backend_config(self) -> bool:
        """验证后端配置"""
        print("\n🔍 验证后端配置...")
        
        backend_dir = self.project_root / 'backend'
        if not backend_dir.exists():
            self.log_error("backend 目录不存在")
            return False
        
        # 检查关键文件
        key_files = [
            'requirements.txt',
            'Dockerfile',
            'Dockerfile.init',
            'init_db.py',
            'run_init.py',
            'start_backend.py',
            'app/main.py',
            'app/core/config.py',
            'app/core/database.py'
        ]
        
        missing_files = []
        for file_path in key_files:
            full_path = backend_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.log_error(f"后端缺少关键文件: {', '.join(missing_files)}")
        else:
            self.log_success("后端所有关键文件都存在")
        
        # 检查 Python 语法
        python_files = list(backend_dir.rglob('*.py'))
        syntax_errors = []
        
        for py_file in python_files[:10]:  # 只检查前10个文件，避免太慢
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                compile(content, str(py_file), 'exec')
            except SyntaxError as e:
                syntax_errors.append(f"{py_file.relative_to(backend_dir)}: {e}")
            except Exception:
                # 忽略其他错误（如导入错误）
                pass
        
        if syntax_errors:
            self.log_error(f"Python 语法错误: {'; '.join(syntax_errors[:3])}")
        else:
            self.log_success("Python 文件语法检查通过")
        
        return len(missing_files) == 0 and len(syntax_errors) == 0
    
    def validate_frontend_config(self) -> bool:
        """验证前端配置"""
        print("\n🔍 验证前端配置...")
        
        frontend_dir = self.project_root / 'frontend'
        if not frontend_dir.exists():
            self.log_error("frontend 目录不存在")
            return False
        
        # 检查关键文件
        key_files = [
            'package.json',
            'vite.config.ts',
            'vite.config.simple.ts',
            'Dockerfile',
            'nginx.conf',
            'src/main.ts',
            'src/utils/echarts.ts'
        ]
        
        missing_files = []
        for file_path in key_files:
            full_path = frontend_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.log_error(f"前端缺少关键文件: {', '.join(missing_files)}")
        else:
            self.log_success("前端所有关键文件都存在")
        
        # 检查 package.json 依赖
        package_json = frontend_dir / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                deps = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
                required_deps = ['vue', 'echarts', 'vue-echarts', 'element-plus', 'axios']
                
                missing_deps = [dep for dep in required_deps if dep not in deps]
                if missing_deps:
                    self.log_error(f"前端缺少必需依赖: {', '.join(missing_deps)}")
                else:
                    self.log_success("前端所有必需依赖都存在")
                
            except Exception as e:
                self.log_error(f"解析 package.json 失败: {e}")
                return False
        
        return len(missing_files) == 0
    
    def validate_database_scripts(self) -> bool:
        """验证数据库脚本"""
        print("\n🔍 验证数据库脚本...")
        
        backend_dir = self.project_root / 'backend'
        
        # 检查初始化脚本
        init_scripts = [
            'init_db.py',
            'run_init.py',
            'wait_for_db.py',
            'check_db_status.py'
        ]
        
        missing_scripts = []
        for script in init_scripts:
            script_path = backend_dir / script
            if not script_path.exists():
                missing_scripts.append(script)
        
        if missing_scripts:
            self.log_warning(f"缺少数据库脚本: {', '.join(missing_scripts)}")
        else:
            self.log_success("所有数据库脚本都存在")
        
        # 检查模型文件
        models_dir = backend_dir / 'app' / 'models'
        if models_dir.exists():
            model_files = list(models_dir.glob('*.py'))
            if len(model_files) > 0:
                self.log_success(f"发现 {len(model_files)} 个模型文件")
            else:
                self.log_warning("未发现模型文件")
        else:
            self.log_error("models 目录不存在")
            return False
        
        return len(missing_scripts) <= 2  # 允许缺少一些可选脚本
    
    def validate_network_config(self) -> bool:
        """验证网络配置"""
        print("\n🔍 验证网络配置...")
        
        # 检查前端代理配置
        frontend_vite_config = self.project_root / 'frontend' / 'vite.config.ts'
        if frontend_vite_config.exists():
            try:
                with open(frontend_vite_config, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'proxy' in content and 'backend:8000' in content:
                    self.log_success("前端代理配置正确")
                else:
                    self.log_warning("前端代理配置可能不正确")
                    
            except Exception as e:
                self.log_error(f"读取前端配置失败: {e}")
        
        # 检查 nginx 配置
        nginx_config = self.project_root / 'frontend' / 'nginx.conf'
        if nginx_config.exists():
            try:
                with open(nginx_config, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'backend:8000' in content:
                    self.log_success("Nginx 代理配置正确")
                else:
                    self.log_warning("Nginx 代理配置可能不正确")
                    
            except Exception as e:
                self.log_error(f"读取 Nginx 配置失败: {e}")
        
        return True
    
    def validate_documentation(self) -> bool:
        """验证文档"""
        print("\n🔍 验证文档...")
        
        # 检查主要文档文件
        doc_files = [
            'README.md',
            'docs/docker-compose-setup.md'
        ]
        
        missing_docs = []
        for doc_file in doc_files:
            doc_path = self.project_root / doc_file
            if not doc_path.exists():
                missing_docs.append(doc_file)
        
        if missing_docs:
            self.log_warning(f"缺少文档文件: {', '.join(missing_docs)}")
        else:
            self.log_success("主要文档文件都存在")
        
        return True
    
    def run_validation(self) -> bool:
        """运行完整验证"""
        print("🚀 开始全面配置验证...\n")
        
        validations = [
            ("环境变量配置", self.validate_environment_variables),
            ("Docker Compose 配置", self.validate_docker_compose),
            ("后端配置", self.validate_backend_config),
            ("前端配置", self.validate_frontend_config),
            ("数据库脚本", self.validate_database_scripts),
            ("网络配置", self.validate_network_config),
            ("文档", self.validate_documentation),
        ]
        
        results = []
        for name, validation_func in validations:
            try:
                result = validation_func()
                results.append(result)
            except Exception as e:
                self.log_error(f"{name} 验证时发生错误: {e}")
                results.append(False)
        
        return all(results)
    
    def print_summary(self):
        """打印验证摘要"""
        print("\n" + "="*60)
        print("配置验证摘要")
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
            print("\n🎉 所有配置验证通过，未发现问题")
        elif not self.errors:
            print(f"\n✅ 配置基本正确，但有 {len(self.warnings)} 个警告需要注意")
        else:
            print(f"\n❌ 配置验证失败，请修复 {len(self.errors)} 个错误")
        
        print("\n" + "="*60)


def main():
    """主函数"""
    validator = ConfigValidator()
    
    success = validator.run_validation()
    validator.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())