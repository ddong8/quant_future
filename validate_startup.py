#!/usr/bin/env python3
"""
启动验证脚本
验证所有容器的正常启动和端到端功能测试
"""

import os
import sys
import time
import json
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio
import websockets

class StartupValidator:
    """启动验证器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.services = {
            'postgres': {'port': 5432, 'type': 'database'},
            'redis': {'port': 6379, 'type': 'database'},
            'influxdb': {'port': 8086, 'type': 'database'},
            'backend': {'port': 8000, 'type': 'api'},
            'frontend': {'port': 3000, 'type': 'web'}
        }
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        
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
    
    def log_info(self, message: str):
        """记录信息"""
        print(f"ℹ️  {message}")
    
    def check_docker_compose_status(self) -> bool:
        """检查 Docker Compose 服务状态"""
        print("\n🔍 检查 Docker Compose 服务状态...")
        
        try:
            result = subprocess.run(
                ['docker-compose', 'ps', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.log_error(f"无法获取服务状态: {result.stderr}")
                return False
            
            # 解析服务状态
            services_status = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        service_info = json.loads(line)
                        services_status.append(service_info)
                    except json.JSONDecodeError:
                        continue
            
            if not services_status:
                self.log_error("未找到运行中的服务")
                return False
            
            # 检查每个服务状态
            all_healthy = True
            for service in services_status:
                name = service.get('Service', 'unknown')
                state = service.get('State', 'unknown')
                status = service.get('Status', 'unknown')
                
                if state == 'running':
                    self.log_success(f"服务 {name} 正在运行")
                else:
                    self.log_error(f"服务 {name} 状态异常: {state} - {status}")
                    all_healthy = False
            
            return all_healthy
            
        except subprocess.TimeoutExpired:
            self.log_error("检查服务状态超时")
            return False
        except FileNotFoundError:
            self.log_error("未找到 docker-compose 命令")
            return False
        except Exception as e:
            self.log_error(f"检查服务状态失败: {e}")
            return False
    
    def wait_for_service(self, service_name: str, port: int, timeout: int = 60) -> bool:
        """等待服务启动"""
        self.log_info(f"等待服务 {service_name} 在端口 {port} 启动...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    self.log_success(f"服务 {service_name} 已启动")
                    return True
                    
            except Exception:
                pass
            
            time.sleep(2)
        
        self.log_error(f"服务 {service_name} 在 {timeout} 秒内未启动")
        return False
    
    def test_backend_health(self) -> bool:
        """测试后端健康检查"""
        print("\n🔍 测试后端健康检查...")
        
        try:
            # 基础健康检查
            response = requests.get(f"{self.base_url}/api/v1/health/", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get('status') in ['healthy', 'warning']:
                    self.log_success("后端基础健康检查通过")
                else:
                    self.log_warning(f"后端健康状态: {health_data.get('status')}")
            else:
                self.log_error(f"后端健康检查失败: HTTP {response.status_code}")
                return False
            
            # 就绪检查
            response = requests.get(f"{self.base_url}/api/v1/health/readiness", timeout=10)
            
            if response.status_code == 200:
                readiness_data = response.json()
                if readiness_data.get('ready'):
                    self.log_success("后端就绪检查通过")
                else:
                    self.log_warning("后端尚未就绪")
            else:
                self.log_warning(f"后端就绪检查返回: HTTP {response.status_code}")
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.log_error(f"后端健康检查请求失败: {e}")
            return False
        except Exception as e:
            self.log_error(f"后端健康检查失败: {e}")
            return False
    
    def test_database_connectivity(self) -> bool:
        """测试数据库连接"""
        print("\n🔍 测试数据库连接...")
        
        try:
            # 测试数据库健康检查端点（需要认证，所以可能返回401）
            response = requests.get(f"{self.base_url}/api/v1/health/database", timeout=10)
            
            # 401表示端点存在但需要认证，这是正常的
            if response.status_code in [200, 401]:
                self.log_success("数据库健康检查端点可访问")
                return True
            else:
                self.log_warning(f"数据库健康检查端点返回: HTTP {response.status_code}")
                return True  # 不算严重错误
                
        except requests.exceptions.RequestException as e:
            self.log_error(f"数据库连接测试失败: {e}")
            return False
        except Exception as e:
            self.log_error(f"数据库连接测试失败: {e}")
            return False
    
    def test_api_endpoints(self) -> bool:
        """测试关键 API 端点"""
        print("\n🔍 测试关键 API 端点...")
        
        # 测试不需要认证的端点
        public_endpoints = [
            "/api/v1/health/",
            "/api/v1/health/liveness",
            "/docs",
            "/openapi.json"
        ]
        
        success_count = 0
        for endpoint in public_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    self.log_success(f"端点 {endpoint} 可访问")
                    success_count += 1
                else:
                    self.log_warning(f"端点 {endpoint} 返回: HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.log_warning(f"端点 {endpoint} 请求失败: {e}")
            except Exception as e:
                self.log_warning(f"端点 {endpoint} 测试失败: {e}")
        
        # 测试需要认证的端点（应该返回401）
        auth_endpoints = [
            "/api/v1/users/",
            "/api/v1/strategies/",
            "/api/v1/orders/"
        ]
        
        for endpoint in auth_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                
                if response.status_code == 401:
                    self.log_success(f"认证端点 {endpoint} 正确返回401")
                    success_count += 1
                elif response.status_code == 200:
                    self.log_warning(f"认证端点 {endpoint} 未要求认证")
                else:
                    self.log_warning(f"认证端点 {endpoint} 返回: HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.log_warning(f"认证端点 {endpoint} 请求失败: {e}")
            except Exception as e:
                self.log_warning(f"认证端点 {endpoint} 测试失败: {e}")
        
        return success_count >= len(public_endpoints) // 2  # 至少一半的端点可用
    
    def test_frontend_accessibility(self) -> bool:
        """测试前端可访问性"""
        print("\n🔍 测试前端可访问性...")
        
        try:
            response = requests.get(self.frontend_url, timeout=10)
            
            if response.status_code == 200:
                self.log_success("前端页面可访问")
                
                # 检查是否包含Vue.js应用的标识
                content = response.text
                if 'id="app"' in content or 'Vue' in content:
                    self.log_success("前端Vue.js应用正常")
                else:
                    self.log_warning("前端页面可能未正确加载Vue.js应用")
                
                return True
            else:
                self.log_error(f"前端页面不可访问: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_error(f"前端可访问性测试失败: {e}")
            return False
        except Exception as e:
            self.log_error(f"前端可访问性测试失败: {e}")
            return False
    
    def test_api_proxy(self) -> bool:
        """测试前端到后端的API代理"""
        print("\n🔍 测试API代理...")
        
        try:
            # 通过前端代理访问后端API
            response = requests.get(f"{self.frontend_url}/api/v1/health/", timeout=10)
            
            if response.status_code == 200:
                self.log_success("API代理工作正常")
                return True
            else:
                self.log_warning(f"API代理可能有问题: HTTP {response.status_code}")
                return True  # 不算严重错误，可能是配置问题
                
        except requests.exceptions.RequestException as e:
            self.log_warning(f"API代理测试失败: {e}")
            return True  # 不算严重错误
        except Exception as e:
            self.log_warning(f"API代理测试失败: {e}")
            return True
    
    def run_end_to_end_test(self) -> bool:
        """运行端到端测试"""
        print("\n🔍 运行端到端测试...")
        
        try:
            # 1. 测试健康检查链路
            health_response = requests.get(f"{self.base_url}/api/v1/health/", timeout=10)
            if health_response.status_code != 200:
                self.log_error("端到端测试失败: 健康检查不可用")
                return False
            
            # 2. 测试API文档可访问性
            docs_response = requests.get(f"{self.base_url}/docs", timeout=10)
            if docs_response.status_code != 200:
                self.log_warning("API文档不可访问")
            else:
                self.log_success("API文档可访问")
            
            # 3. 测试前端页面
            frontend_response = requests.get(self.frontend_url, timeout=10)
            if frontend_response.status_code != 200:
                self.log_error("端到端测试失败: 前端页面不可访问")
                return False
            
            self.log_success("端到端测试通过")
            return True
            
        except Exception as e:
            self.log_error(f"端到端测试失败: {e}")
            return False
    
    def run_validation(self) -> bool:
        """运行完整的启动验证"""
        print("🚀 开始启动验证...\n")
        
        # 1. 检查Docker Compose服务状态
        if not self.check_docker_compose_status():
            return False
        
        # 2. 等待关键服务启动
        print("\n🔍 等待服务启动...")
        for service_name, config in self.services.items():
            if not self.wait_for_service(service_name, config['port']):
                if service_name in ['backend', 'frontend']:
                    return False  # 关键服务必须启动
                else:
                    self.log_warning(f"服务 {service_name} 未启动，但继续测试")
        
        # 3. 测试后端健康检查
        if not self.test_backend_health():
            return False
        
        # 4. 测试数据库连接
        self.test_database_connectivity()
        
        # 5. 测试API端点
        if not self.test_api_endpoints():
            self.log_warning("部分API端点测试失败")
        
        # 6. 测试前端可访问性
        if not self.test_frontend_accessibility():
            self.log_warning("前端可访问性测试失败")
        
        # 7. 测试API代理
        self.test_api_proxy()
        
        # 8. 运行端到端测试
        if not self.run_end_to_end_test():
            self.log_warning("端到端测试失败")
        
        return len(self.errors) == 0
    
    def print_summary(self):
        """打印验证摘要"""
        print("\n" + "="*60)
        print("启动验证摘要")
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
            print("\n🎉 所有启动验证通过，系统运行正常")
        elif not self.errors:
            print(f"\n✅ 启动验证基本通过，但有 {len(self.warnings)} 个警告需要注意")
        else:
            print(f"\n❌ 启动验证失败，请修复 {len(self.errors)} 个错误")
        
        print("\n" + "="*60)


def main():
    """主函数"""
    validator = StartupValidator()
    
    success = validator.run_validation()
    validator.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())