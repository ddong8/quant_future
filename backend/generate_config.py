#!/usr/bin/env python3
"""
配置生成脚本
帮助用户生成安全的环境变量配置
"""
import sys
import os
import secrets
import string
from pathlib import Path
from typing import Dict, Any
import argparse


class ConfigGenerator:
    """配置生成器"""
    
    def __init__(self):
        self.env_example_path = Path(".env.example")
        self.env_path = Path(".env")
    
    def generate_secret_key(self, length: int = 64) -> str:
        """生成安全的密钥"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def generate_token(self, length: int = 32) -> str:
        """生成令牌"""
        return secrets.token_urlsafe(length)
    
    def get_default_values(self, environment: str = "development") -> Dict[str, str]:
        """获取默认配置值"""
        base_config = {
            'APP_NAME': '量化交易平台',
            'APP_VERSION': '0.1.0',
            'SECRET_KEY': self.generate_secret_key(),
            'JWT_ALGORITHM': 'HS256',
            'JWT_ACCESS_TOKEN_EXPIRE_MINUTES': '30',
            'JWT_REFRESH_TOKEN_EXPIRE_DAYS': '7',
            'INFLUXDB_TOKEN': self.generate_token(),
            'INFLUXDB_ORG': 'trading-org',
            'INFLUXDB_BUCKET': 'market-data',
            'LOG_LEVEL': 'INFO',
            'LOG_FILE': 'logs/app.log',
            'MAX_DAILY_LOSS_PERCENT': '5.0',
            'MAX_POSITION_PERCENT': '20.0',
            'MAX_ORDERS_PER_MINUTE': '10',
            'DB_INIT_RETRY_COUNT': '5',
            'DB_INIT_RETRY_DELAY': '2',
            'DB_INIT_TIMEOUT': '30',
            'HEALTH_CHECK_INTERVAL': '30s',
            'HEALTH_CHECK_TIMEOUT': '10s',
            'HEALTH_CHECK_RETRIES': '3',
            'BACKEND_PORT': '8000',
            'FRONTEND_PORT': '3000',
            'POSTGRES_PORT': '5432',
            'INFLUXDB_PORT': '8086',
            'REDIS_PORT': '6379',
            'DB_POOL_SIZE': '10',
            'DB_MAX_OVERFLOW': '20',
            'DB_POOL_RECYCLE': '300',
            'DB_POOL_PRE_PING': 'true',
            'REDIS_MAX_CONNECTIONS': '50',
            'REDIS_CONNECTION_TIMEOUT': '5',
            'WORKER_PROCESSES': '4',
            'WORKER_CONNECTIONS': '1000',
            'KEEPALIVE_TIMEOUT': '65',
        }
        
        if environment == "development":
            base_config.update({
                'DEBUG': 'true',
                'DATABASE_URL': 'postgresql://postgres:postgres123@localhost:5432/trading_db',
                'INFLUXDB_URL': 'http://localhost:8086',
                'REDIS_URL': 'redis://localhost:6379/0',
                'DEV_CORS_ORIGINS': '["http://localhost:3000", "http://127.0.0.1:3000"]',
                'PROMETHEUS_ENABLED': 'false',
                'GRAFANA_ENABLED': 'false',
            })
        elif environment == "docker":
            base_config.update({
                'DEBUG': 'false',
                'DATABASE_URL': 'postgresql://postgres:postgres123@db:5432/trading_db',
                'INFLUXDB_URL': 'http://influxdb:8086',
                'REDIS_URL': 'redis://redis:6379/0',
                'PROD_CORS_ORIGINS': '["http://localhost:3000"]',
                'PROMETHEUS_ENABLED': 'false',
                'GRAFANA_ENABLED': 'false',
            })
        elif environment == "production":
            base_config.update({
                'DEBUG': 'false',
                'DATABASE_URL': 'postgresql://postgres:CHANGE_ME@db:5432/trading_db',
                'INFLUXDB_URL': 'http://influxdb:8086',
                'REDIS_URL': 'redis://redis:6379/0',
                'PROD_CORS_ORIGINS': '["https://yourdomain.com"]',
                'PROD_SECURE_COOKIES': 'true',
                'PROD_HTTPS_ONLY': 'true',
                'PROMETHEUS_ENABLED': 'true',
                'GRAFANA_ENABLED': 'true',
                'SMTP_HOST': 'smtp.gmail.com',
                'SMTP_PORT': '587',
                'SMTP_USER': 'your-email@gmail.com',
                'SMTP_PASSWORD': 'your-app-password',
            })
        
        return base_config
    
    def load_existing_config(self) -> Dict[str, str]:
        """加载现有配置"""
        config = {}
        
        if self.env_path.exists():
            try:
                with open(self.env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
            except Exception as e:
                print(f"警告: 无法读取现有配置文件: {e}")
        
        return config
    
    def merge_configs(self, existing: Dict[str, str], defaults: Dict[str, str], 
                     preserve_existing: bool = True) -> Dict[str, str]:
        """合并配置"""
        if preserve_existing:
            # 保留现有值，只添加缺失的配置
            merged = defaults.copy()
            merged.update(existing)
        else:
            # 使用新的默认值，但保留用户自定义的值
            merged = defaults.copy()
            # 保留一些用户可能自定义的值
            preserve_keys = [
                'DATABASE_URL', 'TQSDK_AUTH', 'TQSDK_ACCOUNT', 
                'SMTP_HOST', 'SMTP_USER', 'SMTP_PASSWORD',
                'APP_NAME', 'PROD_CORS_ORIGINS'
            ]
            for key in preserve_keys:
                if key in existing and not existing[key].startswith('your-'):
                    merged[key] = existing[key]
        
        return merged
    
    def write_config_file(self, config: Dict[str, str], output_path: Path):
        """写入配置文件"""
        # 配置分组
        sections = {
            '应用基础配置': [
                'APP_NAME', 'APP_VERSION', 'DEBUG', 'SECRET_KEY'
            ],
            '数据库配置': [
                'DATABASE_URL', 'INFLUXDB_URL', 'INFLUXDB_TOKEN', 'INFLUXDB_ORG', 
                'INFLUXDB_BUCKET', 'REDIS_URL', 'DB_POOL_SIZE', 'DB_MAX_OVERFLOW',
                'DB_POOL_RECYCLE', 'DB_POOL_PRE_PING'
            ],
            'JWT 认证配置': [
                'JWT_ALGORITHM', 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 'JWT_REFRESH_TOKEN_EXPIRE_DAYS'
            ],
            '交易接口配置': [
                'TQSDK_AUTH', 'TQSDK_ACCOUNT'
            ],
            '邮件服务配置': [
                'SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD'
            ],
            '日志配置': [
                'LOG_LEVEL', 'LOG_FILE'
            ],
            '风险管理配置': [
                'MAX_DAILY_LOSS_PERCENT', 'MAX_POSITION_PERCENT', 'MAX_ORDERS_PER_MINUTE'
            ],
            'Docker 和部署配置': [
                'DB_INIT_RETRY_COUNT', 'DB_INIT_RETRY_DELAY', 'DB_INIT_TIMEOUT',
                'HEALTH_CHECK_INTERVAL', 'HEALTH_CHECK_TIMEOUT', 'HEALTH_CHECK_RETRIES',
                'BACKEND_PORT', 'FRONTEND_PORT', 'POSTGRES_PORT', 'INFLUXDB_PORT', 'REDIS_PORT'
            ],
            'CORS 和安全配置': [
                'DEV_CORS_ORIGINS', 'PROD_CORS_ORIGINS', 'PROD_SECURE_COOKIES', 'PROD_HTTPS_ONLY'
            ],
            '监控配置': [
                'PROMETHEUS_ENABLED', 'PROMETHEUS_PORT', 'GRAFANA_ENABLED', 'GRAFANA_PORT'
            ],
            '性能配置': [
                'WORKER_PROCESSES', 'WORKER_CONNECTIONS', 'KEEPALIVE_TIMEOUT',
                'REDIS_MAX_CONNECTIONS', 'REDIS_CONNECTION_TIMEOUT'
            ]
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# ============================================================================\n")
                f.write("# 量化交易平台环境变量配置文件\n")
                f.write("# \n")
                f.write("# 此文件由 generate_config.py 自动生成\n")
                f.write(f"# 生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("# \n")
                f.write("# 注意事项:\n")
                f.write("# 1. 请根据实际环境修改相关配置值\n")
                f.write("# 2. 生产环境中请务必修改所有密钥和密码\n")
                f.write("# 3. 数据库连接信息需要与实际部署环境匹配\n")
                f.write("# ============================================================================\n\n")
                
                for section_name, keys in sections.items():
                    f.write(f"# ============================================================================\n")
                    f.write(f"# {section_name}\n")
                    f.write(f"# ============================================================================\n")
                    
                    for key in keys:
                        if key in config:
                            f.write(f"{key}={config[key]}\n")
                    
                    f.write("\n")
                
                # 写入其他未分类的配置
                written_keys = set()
                for keys in sections.values():
                    written_keys.update(keys)
                
                other_keys = set(config.keys()) - written_keys
                if other_keys:
                    f.write("# ============================================================================\n")
                    f.write("# 其他配置\n")
                    f.write("# ============================================================================\n")
                    for key in sorted(other_keys):
                        f.write(f"{key}={config[key]}\n")
                    f.write("\n")
            
            print(f"✓ 配置文件已生成: {output_path}")
            
        except Exception as e:
            print(f"✗ 写入配置文件失败: {e}")
            return False
        
        return True
    
    def interactive_setup(self, environment: str) -> Dict[str, str]:
        """交互式配置设置"""
        print(f"\n开始 {environment} 环境的交互式配置...")
        print("=" * 60)
        
        config = self.get_default_values(environment)
        
        # 关键配置项的交互式设置
        interactive_keys = {
            'APP_NAME': '应用名称',
            'DATABASE_URL': '数据库连接URL',
            'TQSDK_AUTH': 'TQSDK认证令牌 (可选)',
            'TQSDK_ACCOUNT': 'TQSDK交易账户 (可选)',
            'SMTP_HOST': 'SMTP服务器 (可选)',
            'SMTP_USER': 'SMTP用户名 (可选)',
        }
        
        for key, description in interactive_keys.items():
            current_value = config.get(key, '')
            
            if key in ['TQSDK_AUTH', 'TQSDK_ACCOUNT', 'SMTP_HOST', 'SMTP_USER']:
                prompt = f"{description} [当前: {current_value or '未设置'}] (回车跳过): "
            else:
                prompt = f"{description} [当前: {current_value}]: "
            
            user_input = input(prompt).strip()
            
            if user_input:
                config[key] = user_input
            elif key in ['TQSDK_AUTH', 'TQSDK_ACCOUNT', 'SMTP_HOST', 'SMTP_USER']:
                # 可选配置，如果用户跳过则删除
                config.pop(key, None)
        
        return config
    
    def generate_config(self, environment: str = "development", 
                       interactive: bool = False, 
                       preserve_existing: bool = True,
                       output_file: str = None) -> bool:
        """生成配置文件"""
        print(f"生成 {environment} 环境配置...")
        
        # 获取默认配置
        default_config = self.get_default_values(environment)
        
        # 加载现有配置
        existing_config = self.load_existing_config()
        
        # 合并配置
        if existing_config and preserve_existing:
            config = self.merge_configs(existing_config, default_config, preserve_existing)
            print(f"✓ 合并了 {len(existing_config)} 个现有配置项")
        else:
            config = default_config
        
        # 交互式设置
        if interactive:
            config = self.interactive_setup(environment)
        
        # 确定输出文件
        output_path = Path(output_file) if output_file else self.env_path
        
        # 写入配置文件
        success = self.write_config_file(config, output_path)
        
        if success:
            print(f"\n🎉 配置生成成功!")
            print(f"   文件位置: {output_path.absolute()}")
            print(f"   配置项数: {len(config)}")
            print(f"   环境类型: {environment}")
            
            # 安全提醒
            if environment == "production":
                print("\n⚠️  生产环境安全提醒:")
                print("   1. 请修改所有包含 'CHANGE_ME' 的配置项")
                print("   2. 确保 SECRET_KEY 和 INFLUXDB_TOKEN 足够安全")
                print("   3. 配置正确的 CORS 域名")
                print("   4. 设置邮件服务器信息")
            
            print(f"\n下一步: 运行 'python validate_config.py' 验证配置")
        
        return success


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="生成环境变量配置文件")
    parser.add_argument(
        "--environment", "-e",
        choices=["development", "docker", "production"],
        default="development",
        help="目标环境 (默认: development)"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="交互式配置"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="强制覆盖现有配置"
    )
    parser.add_argument(
        "--output", "-o",
        help="输出文件路径 (默认: .env)"
    )
    
    args = parser.parse_args()
    
    # 切换到脚本所在目录
    os.chdir(Path(__file__).parent)
    
    generator = ConfigGenerator()
    
    # 检查现有文件
    if generator.env_path.exists() and not args.force:
        response = input(f"\n.env 文件已存在，是否要合并配置? (y/N): ").strip().lower()
        preserve_existing = response in ['y', 'yes']
        
        if not preserve_existing:
            response = input("是否要备份现有文件? (Y/n): ").strip().lower()
            if response not in ['n', 'no']:
                backup_path = generator.env_path.with_suffix('.env.backup')
                generator.env_path.rename(backup_path)
                print(f"✓ 现有文件已备份为: {backup_path}")
    else:
        preserve_existing = not args.force
    
    try:
        success = generator.generate_config(
            environment=args.environment,
            interactive=args.interactive,
            preserve_existing=preserve_existing,
            output_file=args.output
        )
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        return 1
    except Exception as e:
        print(f"\n💥 配置生成过程中发生异常: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())