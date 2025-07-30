#!/usr/bin/env python3
"""
完整部署流程验证脚本
验证从零开始的完整部署流程，确保所有功能正常工作
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class DeploymentValidator:
    """部署流程验证器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.project_root = Path.cwd()
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
    
    def log_step(self, step: str):
        """记录步骤"""
        print(f"\n🔄 {step}")
    
    def run_command(self, command: List[str], timeout: int = 60, cwd: Optional[Path] = None) -> tuple:
        """运行命令并返回结果"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd or self.project_root
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"命令超时 ({timeout}s)"
        except Exception as e:
            return -1, "", str(e)
    
    def wait_for_service(self, url: str, timeout: int = 120, interval: int = 5) -> bool:
        """等待服务启动"""
        if not HAS_REQUESTS:
            self.log_warning("requests 库未安装，跳过服务等待检查")
            return True
            
        self.log_info(f"等待服务 {url} 启动...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code in [200, 401]:  # 401表示需要认证，但服务正常
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(interval)
        
        return False
    
    def validate_prerequisites(self) -> bool:
        """验证部署前提条件"""
        self.log_step("验证部署前提条件")
        
        # 检查Docker
        returncode, stdout, stderr = self.run_command(['docker', '--version'])
        if returncode != 0:
            self.log_error("Docker 未安装或不可用")
            return False
        else:
            self.log_success(f"Docker 已安装: {stdout.strip()}")
        
        # 检查Docker Compose
        returncode, stdout, stderr = self.run_command(['docker-compose', '--version'])
        if returncode != 0:
            # 尝试新版本的命令
            returncode, stdout, stderr = self.run_command(['docker', 'compose', 'version'])
            if returncode != 0:
                self.log_error("Docker Compose 未安装或不可用")
                return False
        
        self.log_success(f"Docker Compose 已安装: {stdout.strip()}")
        
        # 检查必要文件
        required_files = [
            'docker-compose.yml',
            '.env.template',
            'start-trading-platform.sh',
            'backend/Dockerfile',
            'backend/Dockerfile.init',
            'frontend/Dockerfile'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.log_error(f"缺少必要文件: {', '.join(missing_files)}")
            return False
        else:
            self.log_success("所有必要文件都存在")
        
        return True
    
    def setup_environment(self) -> bool:
        """设置环境"""
        self.log_step("设置环境")
        
        # 创建.env文件
        env_file = self.project_root / '.env'
        env_template = self.project_root / '.env.template'
        
        if not env_file.exists() and env_template.exists():
            try:
                import shutil
                shutil.copy(env_template, env_file)
                self.log_success("从模板创建 .env 文件")
            except Exception as e:
                self.log_error(f"创建 .env 文件失败: {e}")
                return False
        elif env_file.exists():
            self.log_success(".env 文件已存在")
        else:
            self.log_error(".env 文件和模板都不存在")
            return False
        
        return True
    
    def clean_environment(self) -> bool:
        """清理环境"""
        self.log_step("清理现有环境")
        
        # 停止并删除容器
        returncode, stdout, stderr = self.run_command(['docker-compose', 'down', '-v'])
        if returncode != 0:
            self.log_warning(f"清理环境时出现警告: {stderr}")
        else:
            self.log_success("环境清理完成")
        
        # 清理Docker资源
        returncode, stdout, stderr = self.run_command(['docker', 'system', 'prune', '-f'])
        if returncode == 0:
            self.log_success("Docker 资源清理完成")
        
        return True
    
    def build_and_start_services(self) -> bool:
        """构建并启动服务"""
        self.log_step("构建并启动服务")
        
        # 构建镜像
        self.log_info("构建Docker镜像...")
        returncode, stdout, stderr = self.run_command(
            ['docker-compose', 'build', '--no-cache'], 
            timeout=600  # 10分钟超时
        )
        
        if returncode != 0:
            self.log_error(f"构建镜像失败: {stderr}")
            return False
        else:
            self.log_success("Docker镜像构建完成")
        
        # 启动服务
        self.log_info("启动服务...")
        returncode, stdout, stderr = self.run_command(
            ['docker-compose', 'up', '-d'],
            timeout=300  # 5分钟超时
        )
        
        if returncode != 0:
            self.log_error(f"启动服务失败: {stderr}")
            return False
        else:
            self.log_success("服务启动完成")
        
        return True
    
    def wait_for_all_services(self) -> bool:
        """等待所有服务启动"""
        self.log_step("等待服务启动")
        
        services = [
            (f"{self.base_url}/api/v1/health/", "后端API"),
            (f"{self.frontend_url}/", "前端应用")
        ]
        
        all_ready = True
        for url, name in services:
            if self.wait_for_service(url, timeout=180):
                self.log_success(f"{name} 已启动")
            else:
                self.log_error(f"{name} 启动超时")
                all_ready = False
        
        return all_ready
    
    def validate_database_initialization(self) -> bool:
        """验证数据库初始化"""
        self.log_step("验证数据库初始化")
        
        # 检查初始化容器日志
        returncode, stdout, stderr = self.run_command(['docker-compose', 'logs', 'db-init'])
        
        if "初始化完成" in stdout or "initialization complete" in stdout.lower():
            self.log_success("数据库初始化完成")
        else:
            self.log_warning("数据库初始化状态不明确")
        
        if not HAS_REQUESTS:
            self.log_warning("requests 库未安装，跳过数据库连接验证")
            return True
        
        # 检查数据库连接
        try:
            response = requests.get(f"{self.base_url}/api/v1/health/readiness", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('ready'):
                    self.log_success("数据库就绪检查通过")
                    return True
                else:
                    self.log_error("数据库未就绪")
                    return False
            else:
                self.log_error(f"就绪检查失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_error(f"数据库连接验证失败: {e}")
            return False
    
    def test_api_endpoints(self) -> bool:
        """测试API端点"""
        self.log_step("测试API端点")
        
        if not HAS_REQUESTS:
            self.log_warning("requests 库未安装，跳过API端点测试")
            return True
        
        # 测试公开端点
        public_endpoints = [
            ("/api/v1/health/", "基础健康检查"),
            ("/api/v1/health/liveness", "存活检查"),
            ("/api/v1/health/readiness", "就绪检查"),
            ("/docs", "API文档"),
            ("/openapi.json", "OpenAPI规范")
        ]
        
        success_count = 0
        for endpoint, name in public_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    self.log_success(f"{name} 可访问")
                    success_count += 1
                else:
                    self.log_warning(f"{name} 返回 HTTP {response.status_code}")
            except Exception as e:
                self.log_warning(f"{name} 请求失败: {e}")
        
        # 测试需要认证的端点（应该返回401）
        auth_endpoints = [
            ("/api/v1/users/", "用户管理"),
            ("/api/v1/strategies/", "策略管理"),
            ("/api/v1/health/detailed", "详细健康检查")
        ]
        
        for endpoint, name in auth_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 401:
                    self.log_success(f"{name} 正确要求认证")
                    success_count += 1
                elif response.status_code == 200:
                    self.log_warning(f"{name} 未要求认证")
                else:
                    self.log_warning(f"{name} 返回 HTTP {response.status_code}")
            except Exception as e:
                self.log_warning(f"{name} 请求失败: {e}")
        
        return success_count >= len(public_endpoints) // 2
    
    def test_frontend_functionality(self) -> bool:
        """测试前端功能"""
        self.log_step("测试前端功能")
        
        if not HAS_REQUESTS:
            self.log_warning("requests 库未安装，跳过前端功能测试")
            return True
        
        try:
            # 测试前端页面
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                self.log_success("前端页面可访问")
                
                # 检查页面内容
                content = response.text
                if 'id="app"' in content:
                    self.log_success("Vue.js应用容器存在")
                else:
                    self.log_warning("未找到Vue.js应用容器")
                
                # 测试API代理
                try:
                    proxy_response = requests.get(f"{self.frontend_url}/api/v1/health/", timeout=10)
                    if proxy_response.status_code == 200:
                        self.log_success("前端API代理工作正常")
                    else:
                        self.log_warning(f"前端API代理返回: HTTP {proxy_response.status_code}")
                except Exception as e:
                    self.log_warning(f"前端API代理测试失败: {e}")
                
                return True
            else:
                self.log_error(f"前端页面不可访问: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error(f"前端功能测试失败: {e}")
            return False
    
    def test_end_to_end_workflow(self) -> bool:
        """测试端到端工作流"""
        self.log_step("测试端到端工作流")
        
        if not HAS_REQUESTS:
            self.log_warning("requests 库未安装，跳过端到端工作流测试")
            return True
        
        try:
            # 1. 健康检查链路
            health_response = requests.get(f"{self.base_url}/api/v1/health/", timeout=10)
            if health_response.status_code != 200:
                self.log_error("健康检查链路失败")
                return False
            
            health_data = health_response.json()
            if health_data.get('status') not in ['healthy', 'warning']:
                self.log_error(f"系统健康状态异常: {health_data.get('status')}")
                return False
            
            self.log_success("健康检查链路正常")
            
            # 2. 前端到后端通信
            frontend_response = requests.get(self.frontend_url, timeout=10)
            if frontend_response.status_code != 200:
                self.log_error("前端页面不可访问")
                return False
            
            self.log_success("前端页面正常")
            
            # 3. 数据库连接
            readiness_response = requests.get(f"{self.base_url}/api/v1/health/readiness", timeout=10)
            if readiness_response.status_code == 200:
                readiness_data = readiness_response.json()
                if readiness_data.get('ready'):
                    self.log_success("数据库连接正常")
                else:
                    self.log_warning("数据库连接可能有问题")
            
            self.log_success("端到端工作流测试通过")
            return True
            
        except Exception as e:
            self.log_error(f"端到端工作流测试失败: {e}")
            return False
    
    def validate_documentation(self) -> bool:
        """验证文档完整性"""
        self.log_step("验证文档完整性")
        
        # 检查文档文件
        doc_files = [
            'README.md',
            'docs/docker-compose-setup.md',
            'docs/troubleshooting-guide.md'
        ]
        
        missing_docs = []
        for doc_file in doc_files:
            doc_path = self.project_root / doc_file
            if not doc_path.exists():
                missing_docs.append(doc_file)
            else:
                # 检查文档内容是否为空
                try:
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    if len(content) < 100:  # 文档太短可能不完整
                        self.log_warning(f"文档 {doc_file} 内容可能不完整")
                    else:
                        self.log_success(f"文档 {doc_file} 存在且内容充实")
                except Exception as e:
                    self.log_warning(f"读取文档 {doc_file} 失败: {e}")
        
        if missing_docs:
            self.log_error(f"缺少文档文件: {', '.join(missing_docs)}")
            return False
        
        return True
    
    def collect_deployment_info(self) -> Dict[str, Any]:
        """收集部署信息"""
        self.log_step("收集部署信息")
        
        info = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'services': {},
            'system': {}
        }
        
        # 收集服务状态
        returncode, stdout, stderr = self.run_command(['docker-compose', 'ps', '--format', 'json'])
        if returncode == 0:
            try:
                services = []
                for line in stdout.strip().split('\n'):
                    if line.strip():
                        services.append(json.loads(line))
                info['services'] = services
            except Exception as e:
                self.log_warning(f"解析服务状态失败: {e}")
        
        # 收集系统信息
        try:
            import platform
            info['system'] = {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'architecture': platform.architecture()[0]
            }
        except Exception as e:
            self.log_warning(f"收集系统信息失败: {e}")
        
        # 保存部署信息
        try:
            with open('deployment_info.json', 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2, ensure_ascii=False)
            self.log_success("部署信息已保存到 deployment_info.json")
        except Exception as e:
            self.log_warning(f"保存部署信息失败: {e}")
        
        return info
    
    def run_validation(self) -> bool:
        """运行完整的部署验证"""
        print("🚀 开始完整部署流程验证...\n")
        
        # 验证步骤
        steps = [
            ("验证前提条件", self.validate_prerequisites),
            ("设置环境", self.setup_environment),
            ("清理环境", self.clean_environment),
            ("构建并启动服务", self.build_and_start_services),
            ("等待服务启动", self.wait_for_all_services),
            ("验证数据库初始化", self.validate_database_initialization),
            ("测试API端点", self.test_api_endpoints),
            ("测试前端功能", self.test_frontend_functionality),
            ("测试端到端工作流", self.test_end_to_end_workflow),
            ("验证文档完整性", self.validate_documentation),
        ]
        
        results = []
        for step_name, step_func in steps:
            try:
                result = step_func()
                results.append(result)
                if not result:
                    self.log_error(f"步骤 '{step_name}' 失败")
            except Exception as e:
                self.log_error(f"步骤 '{step_name}' 执行时发生错误: {e}")
                results.append(False)
        
        # 收集部署信息
        self.collect_deployment_info()
        
        return all(results)
    
    def print_summary(self):
        """打印验证摘要"""
        print("\n" + "="*60)
        print("完整部署流程验证摘要")
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
            print("\n🎉 完整部署流程验证通过！")
            print("✨ 系统已成功部署并正常运行")
            print(f"🌐 前端地址: {self.frontend_url}")
            print(f"🔧 后端地址: {self.base_url}")
            print(f"📚 API文档: {self.base_url}/docs")
        elif not self.errors:
            print(f"\n✅ 部署基本成功，但有 {len(self.warnings)} 个警告需要注意")
        else:
            print(f"\n❌ 部署验证失败，请修复 {len(self.errors)} 个错误")
        
        print("\n" + "="*60)


def main():
    """主函数"""
    validator = DeploymentValidator()
    
    success = validator.run_validation()
    validator.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())