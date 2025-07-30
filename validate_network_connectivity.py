#!/usr/bin/env python3
"""
容器间网络连通性验证脚本
验证所有服务间的网络连通性
"""
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple


class NetworkConnectivityValidator:
    """网络连通性验证器"""
    
    def __init__(self):
        self.services = {
            'postgres': {'port': 5432, 'description': 'PostgreSQL 数据库'},
            'redis': {'port': 6379, 'description': 'Redis 缓存'},
            'influxdb': {'port': 8086, 'description': 'InfluxDB 时序数据库'},
            'backend': {'port': 8000, 'description': 'FastAPI 后端服务'},
            'frontend': {'port': 3000, 'description': 'Vue.js 前端服务'},
        }
        
        self.network_tests = [
            # (源服务, 目标服务, 测试类型, 描述)
            ('backend', 'postgres', 'tcp', '后端到数据库连接'),
            ('backend', 'redis', 'tcp', '后端到Redis连接'),
            ('backend', 'influxdb', 'tcp', '后端到InfluxDB连接'),
            ('frontend', 'backend', 'http', '前端到后端API连接'),
            ('backend', 'backend', 'http', '后端健康检查'),
            ('frontend', 'frontend', 'http', '前端健康检查'),
        ]
    
    def check_docker_compose_running(self) -> bool:
        """检查 Docker Compose 是否运行"""
        print("检查 Docker Compose 服务状态...")
        
        try:
            result = subprocess.run(
                ['docker-compose', 'ps', '--services', '--filter', 'status=running'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                running_services = result.stdout.strip().split('\n')
                running_services = [s for s in running_services if s]
                
                print(f"✅ 发现 {len(running_services)} 个运行中的服务")
                for service in running_services:
                    print(f"  - {service}")
                
                return len(running_services) > 0
            else:
                print(f"❌ 无法获取服务状态: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ 检查服务状态超时")
            return False
        except FileNotFoundError:
            print("❌ 未找到 docker-compose 命令")
            return False
        except Exception as e:
            print(f"❌ 检查服务状态时发生错误: {e}")
            return False
    
    def test_tcp_connectivity(self, source: str, target: str, port: int) -> bool:
        """测试TCP连接"""
        try:
            # 使用 docker-compose exec 在源容器中测试到目标容器的连接
            cmd = [
                'docker-compose', 'exec', '-T', source,
                'sh', '-c', f'nc -z -w5 {target} {port}'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"  TCP测试异常: {e}")
            return False
    
    def test_http_connectivity(self, source: str, target: str, port: int) -> bool:
        """测试HTTP连接"""
        try:
            if target == 'backend':
                url = f'http://{target}:{port}/api/v1/health/'
            elif target == 'frontend':
                url = f'http://{target}:{port}/'
            else:
                url = f'http://{target}:{port}/'
            
            # 使用 docker-compose exec 在源容器中测试HTTP连接
            cmd = [
                'docker-compose', 'exec', '-T', source,
                'sh', '-c', f'wget --timeout=5 --tries=1 --spider {url} 2>/dev/null'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"  HTTP测试异常: {e}")
            return False
    
    def test_service_connectivity(self, source: str, target: str, test_type: str, description: str) -> bool:
        """测试服务连通性"""
        print(f"测试: {description}")
        
        if target not in self.services:
            print(f"  ❌ 未知目标服务: {target}")
            return False
        
        port = self.services[target]['port']
        
        if test_type == 'tcp':
            success = self.test_tcp_connectivity(source, target, port)
        elif test_type == 'http':
            success = self.test_http_connectivity(source, target, port)
        else:
            print(f"  ❌ 未知测试类型: {test_type}")
            return False
        
        if success:
            print(f"  ✅ {description} - 连接成功")
        else:
            print(f"  ❌ {description} - 连接失败")
        
        return success
    
    def validate_docker_network(self) -> bool:
        """验证Docker网络配置"""
        print("\n验证Docker网络配置...")
        
        try:
            # 检查网络是否存在
            result = subprocess.run(
                ['docker', 'network', 'ls', '--filter', 'name=trading_network'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and 'trading_network' in result.stdout:
                print("✅ trading_network 网络已创建")
            else:
                print("⚠️  trading_network 网络未找到，使用默认网络")
            
            # 检查容器网络连接
            result = subprocess.run(
                ['docker-compose', 'ps', '--format', 'table'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("✅ 容器网络状态正常")
                return True
            else:
                print(f"❌ 容器网络状态异常: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 验证Docker网络时发生错误: {e}")
            return False
    
    def validate_service_discovery(self) -> bool:
        """验证服务发现"""
        print("\n验证服务发现...")
        
        try:
            # 在后端容器中测试服务名解析
            services_to_test = ['postgres', 'redis', 'influxdb']
            
            for service in services_to_test:
                cmd = [
                    'docker-compose', 'exec', '-T', 'backend',
                    'sh', '-c', f'nslookup {service} || getent hosts {service}'
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    print(f"✅ 服务 {service} 可解析")
                else:
                    print(f"❌ 服务 {service} 无法解析")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ 验证服务发现时发生错误: {e}")
            return False
    
    def run_connectivity_tests(self) -> Tuple[int, int]:
        """运行所有连通性测试"""
        print("\n运行网络连通性测试...")
        print("-" * 50)
        
        passed = 0
        total = len(self.network_tests)
        
        for source, target, test_type, description in self.network_tests:
            try:
                if self.test_service_connectivity(source, target, test_type, description):
                    passed += 1
                time.sleep(1)  # 避免测试过于频繁
            except Exception as e:
                print(f"  💥 测试异常: {e}")
        
        return passed, total
    
    def validate_proxy_configuration(self) -> bool:
        """验证代理配置"""
        print("\n验证代理配置...")
        
        # 检查前端Vite配置
        vite_config = Path('frontend/vite.config.ts')
        if vite_config.exists():
            try:
                with open(vite_config, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'backend:8000' in content:
                    print("✅ Vite代理配置使用容器名称")
                else:
                    print("⚠️  Vite代理配置可能未使用容器名称")
                
                if 'proxy:' in content:
                    print("✅ Vite代理配置已启用")
                else:
                    print("❌ Vite代理配置未启用")
                    return False
                    
            except Exception as e:
                print(f"❌ 读取Vite配置失败: {e}")
                return False
        else:
            print("❌ Vite配置文件不存在")
            return False
        
        # 检查nginx配置
        nginx_config = Path('frontend/nginx.conf')
        if nginx_config.exists():
            try:
                with open(nginx_config, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'backend:8000' in content:
                    print("✅ Nginx代理配置使用容器名称")
                else:
                    print("⚠️  Nginx代理配置可能未使用容器名称")
                    
            except Exception as e:
                print(f"❌ 读取Nginx配置失败: {e}")
        
        return True
    
    def validate_all(self) -> bool:
        """执行所有验证"""
        print("容器间网络连通性验证")
        print("=" * 60)
        
        # 检查Docker Compose状态
        if not self.check_docker_compose_running():
            print("\n❌ Docker Compose服务未运行，请先启动服务")
            print("   运行: docker-compose up -d")
            return False
        
        # 验证Docker网络
        network_ok = self.validate_docker_network()
        
        # 验证服务发现
        discovery_ok = self.validate_service_discovery()
        
        # 验证代理配置
        proxy_ok = self.validate_proxy_configuration()
        
        # 运行连通性测试
        passed, total = self.run_connectivity_tests()
        
        # 总结结果
        print("\n" + "=" * 60)
        print("网络连通性验证结果")
        print("=" * 60)
        
        print(f"Docker网络: {'✅ 正常' if network_ok else '❌ 异常'}")
        print(f"服务发现: {'✅ 正常' if discovery_ok else '❌ 异常'}")
        print(f"代理配置: {'✅ 正常' if proxy_ok else '❌ 异常'}")
        print(f"连通性测试: {passed}/{total} 通过")
        
        all_ok = network_ok and discovery_ok and proxy_ok and (passed == total)
        
        if all_ok:
            print("\n🎉 所有网络连通性验证通过！")
        else:
            print("\n❌ 部分网络连通性验证失败")
        
        return all_ok


def main():
    """主函数"""
    validator = NetworkConnectivityValidator()
    
    try:
        success = validator.validate_all()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n验证被用户中断")
        return 130
    except Exception as e:
        print(f"\n💥 验证过程中发生异常: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())