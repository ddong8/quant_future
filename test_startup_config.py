#!/usr/bin/env python3
"""
启动配置测试脚本
在不启动容器的情况下验证启动相关的配置
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any

class StartupConfigTester:
    """启动配置测试器"""
    
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
    
    def test_startup_scripts(self) -> bool:
        """测试启动脚本"""
        print("\n🔍 测试启动脚本...")
        
        scripts = [
            'start-trading-platform.sh',
            'validate_startup.py',
            'validate_all_configs.py',
            'validate_compose_config.py'
        ]
        
        missing_scripts = []
        for script in scripts:
            script_path = self.project_root / script
            if not script_path.exists():
                missing_scripts.append(script)
            else:
                # 检查是否可执行
                if not os.access(script_path, os.X_OK):
                    self.log_warning(f"脚本 {script} 不可执行")
        
        if missing_scripts:
            self.log_error(f"缺少启动脚本: {', '.join(missing_scripts)}")
        else:
            self.log_success("所有启动脚本都存在")
        
        return len(missing_scripts) == 0
    
    def test_health_check_config(self) -> bool:
        """测试健康检查配置"""
        print("\n🔍 测试健康检查配置...")
        
        # 检查后端健康检查文件
        health_files = [
            'backend/app/api/v1/health.py',
            'backend/app/services/health_check_service.py'
        ]
        
        missing_files = []
        for file_path in health_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.log_error(f"缺少健康检查文件: {', '.join(missing_files)}")
        else:
            self.log_success("健康检查文件都存在")
        
        # 检查健康检查端点配置
        health_api_file = self.project_root / 'backend/app/api/v1/health.py'
        if health_api_file.exists():
            try:
                with open(health_api_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                required_endpoints = [
                    '@router.get("/")',
                    '@router.get("/readiness")',
                    '@router.get("/liveness")',
                    '@router.get("/detailed")'
                ]
                
                missing_endpoints = []
                for endpoint in required_endpoints:
                    if endpoint not in content:
                        missing_endpoints.append(endpoint)
                
                if missing_endpoints:
                    self.log_warning(f"可能缺少健康检查端点: {', '.join(missing_endpoints)}")
                else:
                    self.log_success("健康检查端点配置完整")
                    
            except Exception as e:
                self.log_error(f"读取健康检查配置失败: {e}")
        
        return len(missing_files) == 0
    
    def test_docker_health_checks(self) -> bool:
        """测试Docker健康检查配置"""
        print("\n🔍 测试Docker健康检查配置...")
        
        compose_file = self.project_root / 'docker-compose.yml'
        if not compose_file.exists():
            self.log_error("docker-compose.yml 文件不存在")
            return False
        
        try:
            with open(compose_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查健康检查配置
            services_with_healthcheck = ['postgres', 'redis', 'influxdb', 'backend', 'frontend']
            missing_healthchecks = []
            
            for service in services_with_healthcheck:
                service_pattern = f"  {service}:"
                healthcheck_pattern = "healthcheck:"
                
                if service_pattern in content:
                    # 找到服务定义后，检查是否有健康检查
                    service_start = content.find(service_pattern)
                    # 查找下一个服务或文件结束
                    next_service_start = service_start + len(service_pattern)
                    next_service = content.find("\n  ", next_service_start)
                    while next_service != -1 and content[next_service:next_service+4] == "\n   ":
                        next_service = content.find("\n  ", next_service + 1)
                    
                    if next_service == -1:
                        next_service = len(content)
                    
                    service_section = content[service_start:next_service]
                    if healthcheck_pattern not in service_section:
                        missing_healthchecks.append(service)
            
            if missing_healthchecks:
                self.log_warning(f"服务缺少健康检查配置: {', '.join(missing_healthchecks)}")
            else:
                self.log_success("所有服务都配置了健康检查")
            
            # 检查依赖关系配置
            if "depends_on:" in content and "condition:" in content:
                self.log_success("服务依赖关系配置正确")
            else:
                self.log_warning("服务依赖关系配置可能不完整")
            
            return True
            
        except Exception as e:
            self.log_error(f"读取Docker配置失败: {e}")
            return False
    
    def test_initialization_config(self) -> bool:
        """测试初始化配置"""
        print("\n🔍 测试初始化配置...")
        
        # 检查初始化脚本
        init_files = [
            'backend/init_db.py',
            'backend/run_init.py',
            'backend/Dockerfile.init'
        ]
        
        missing_files = []
        for file_path in init_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.log_error(f"缺少初始化文件: {', '.join(missing_files)}")
        else:
            self.log_success("初始化文件都存在")
        
        # 检查docker-compose中的初始化容器配置
        compose_file = self.project_root / 'docker-compose.yml'
        if compose_file.exists():
            try:
                with open(compose_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if "db-init:" in content:
                    self.log_success("Docker Compose包含初始化容器配置")
                else:
                    self.log_error("Docker Compose缺少初始化容器配置")
                
                if "service_completed_successfully" in content:
                    self.log_success("初始化容器依赖配置正确")
                else:
                    self.log_warning("初始化容器依赖配置可能不正确")
                    
            except Exception as e:
                self.log_error(f"检查初始化配置失败: {e}")
        
        return len(missing_files) == 0
    
    def test_network_config(self) -> bool:
        """测试网络配置"""
        print("\n🔍 测试网络配置...")
        
        # 检查前端代理配置
        vite_config = self.project_root / 'frontend/vite.config.ts'
        if vite_config.exists():
            try:
                with open(vite_config, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if "proxy:" in content and "backend:8000" in content:
                    self.log_success("前端代理配置正确")
                else:
                    self.log_warning("前端代理配置可能不正确")
                    
            except Exception as e:
                self.log_error(f"检查前端代理配置失败: {e}")
        
        # 检查nginx配置
        nginx_config = self.project_root / 'frontend/nginx.conf'
        if nginx_config.exists():
            try:
                with open(nginx_config, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if "backend:8000" in content:
                    self.log_success("Nginx代理配置正确")
                else:
                    self.log_warning("Nginx代理配置可能不正确")
                    
            except Exception as e:
                self.log_error(f"检查Nginx配置失败: {e}")
        
        return True
    
    def test_validation_tools(self) -> bool:
        """测试验证工具"""
        print("\n🔍 测试验证工具...")
        
        validation_tools = [
            'validate_all_configs.py',
            'validate_compose_config.py',
            'validate_startup.py',
            'backend/validate_models_simple.py',
            'frontend/validate-charts.sh'
        ]
        
        missing_tools = []
        for tool in validation_tools:
            tool_path = self.project_root / tool
            if not tool_path.exists():
                missing_tools.append(tool)
        
        if missing_tools:
            self.log_warning(f"缺少验证工具: {', '.join(missing_tools)}")
        else:
            self.log_success("所有验证工具都存在")
        
        return len(missing_tools) <= 1  # 允许缺少一个工具
    
    def run_test(self) -> bool:
        """运行完整测试"""
        print("🚀 开始启动配置测试...\n")
        
        tests = [
            ("启动脚本", self.test_startup_scripts),
            ("健康检查配置", self.test_health_check_config),
            ("Docker健康检查", self.test_docker_health_checks),
            ("初始化配置", self.test_initialization_config),
            ("网络配置", self.test_network_config),
            ("验证工具", self.test_validation_tools),
        ]
        
        results = []
        for name, test_func in tests:
            try:
                result = test_func()
                results.append(result)
            except Exception as e:
                self.log_error(f"{name} 测试时发生错误: {e}")
                results.append(False)
        
        return all(results)
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*60)
        print("启动配置测试摘要")
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
            print("\n🎉 所有启动配置测试通过")
        elif not self.errors:
            print(f"\n✅ 启动配置基本正确，但有 {len(self.warnings)} 个警告需要注意")
        else:
            print(f"\n❌ 启动配置测试失败，请修复 {len(self.errors)} 个错误")
        
        print("\n" + "="*60)


def main():
    """主函数"""
    tester = StartupConfigTester()
    
    success = tester.run_test()
    tester.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())