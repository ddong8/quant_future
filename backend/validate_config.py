#!/usr/bin/env python3
"""
配置验证脚本
验证环境变量配置的完整性和正确性
"""
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import re

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self, env_file_path: str = ".env"):
        self.env_file_path = Path(env_file_path)
        self.env_example_path = Path(".env.example")
        self.config_errors = []
        self.config_warnings = []
        
    def validate_env_file_exists(self) -> bool:
        """验证 .env 文件是否存在"""
        if not self.env_file_path.exists():
            self.config_errors.append(f".env file not found at {self.env_file_path}")
            return False
        return True
    
    def validate_env_example_exists(self) -> bool:
        """验证 .env.example 文件是否存在"""
        if not self.env_example_path.exists():
            self.config_warnings.append(f".env.example file not found at {self.env_example_path}")
            return False
        return True
    
    def load_env_variables(self, file_path: Path) -> Dict[str, str]:
        """加载环境变量文件"""
        env_vars = {}
        
        if not file_path.exists():
            return env_vars
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # 跳过注释和空行
                    if not line or line.startswith('#'):
                        continue
                    
                    # 解析环境变量
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
                    else:
                        self.config_warnings.append(
                            f"Invalid line format in {file_path.name}:{line_num}: {line}"
                        )
        
        except Exception as e:
            self.config_errors.append(f"Failed to read {file_path}: {e}")
        
        return env_vars
    
    def validate_required_variables(self, env_vars: Dict[str, str]) -> bool:
        """验证必需的环境变量"""
        required_vars = [
            'APP_NAME',
            'SECRET_KEY',
            'DATABASE_URL',
            'INFLUXDB_URL',
            'INFLUXDB_TOKEN',
            'REDIS_URL',
            'JWT_ALGORITHM',
        ]
        
        missing_vars = []
        for var in required_vars:
            if var not in env_vars or not env_vars[var]:
                missing_vars.append(var)
        
        if missing_vars:
            self.config_errors.append(f"Missing required environment variables: {missing_vars}")
            return False
        
        return True
    
    def validate_database_url(self, database_url: str) -> bool:
        """验证数据库 URL 格式"""
        if not database_url.startswith(('postgresql://', 'postgresql+psycopg2://')):
            self.config_errors.append("DATABASE_URL must be a PostgreSQL URL")
            return False
        
        # 检查是否包含必要的组件
        pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
        match = re.match(pattern, database_url)
        
        if not match:
            self.config_errors.append("DATABASE_URL format is invalid")
            return False
        
        username, password, host, port, database = match.groups()
        
        # 验证组件
        if not all([username, password, host, port, database]):
            self.config_errors.append("DATABASE_URL is missing required components")
            return False
        
        # 检查端口是否为数字
        try:
            port_num = int(port)
            if port_num <= 0 or port_num > 65535:
                self.config_errors.append(f"DATABASE_URL port {port} is invalid")
                return False
        except ValueError:
            self.config_errors.append(f"DATABASE_URL port {port} is not a number")
            return False
        
        return True
    
    def validate_secret_key(self, secret_key: str) -> bool:
        """验证密钥安全性"""
        if len(secret_key) < 32:
            self.config_errors.append("SECRET_KEY must be at least 32 characters long")
            return False
        
        if secret_key == "default-secret-key-change-in-production":
            self.config_warnings.append("SECRET_KEY is using default value, should be changed in production")
        
        if secret_key.startswith("your-"):
            self.config_errors.append("SECRET_KEY appears to be a placeholder value")
            return False
        
        return True
    
    def validate_urls(self, env_vars: Dict[str, str]) -> bool:
        """验证各种 URL 配置"""
        url_configs = {
            'INFLUXDB_URL': r'^https?://',
            'REDIS_URL': r'^redis://',
        }
        
        all_valid = True
        
        for var_name, pattern in url_configs.items():
            if var_name in env_vars:
                url = env_vars[var_name]
                if not re.match(pattern, url):
                    self.config_errors.append(f"{var_name} format is invalid: {url}")
                    all_valid = False
        
        return all_valid
    
    def validate_numeric_values(self, env_vars: Dict[str, str]) -> bool:
        """验证数值配置"""
        numeric_configs = {
            'JWT_ACCESS_TOKEN_EXPIRE_MINUTES': (1, 1440),  # 1分钟到24小时
            'JWT_REFRESH_TOKEN_EXPIRE_DAYS': (1, 365),     # 1天到1年
            'MAX_DAILY_LOSS_PERCENT': (0.1, 100.0),       # 0.1% 到 100%
            'MAX_POSITION_PERCENT': (0.1, 100.0),         # 0.1% 到 100%
            'MAX_ORDERS_PER_MINUTE': (1, 1000),           # 1到1000
            'BACKEND_PORT': (1000, 65535),                # 有效端口范围
            'FRONTEND_PORT': (1000, 65535),               # 有效端口范围
        }
        
        all_valid = True
        
        for var_name, (min_val, max_val) in numeric_configs.items():
            if var_name in env_vars:
                try:
                    value = float(env_vars[var_name])
                    if not (min_val <= value <= max_val):
                        self.config_errors.append(
                            f"{var_name} value {value} is out of range [{min_val}, {max_val}]"
                        )
                        all_valid = False
                except ValueError:
                    self.config_errors.append(f"{var_name} is not a valid number: {env_vars[var_name]}")
                    all_valid = False
        
        return all_valid
    
    def validate_docker_compatibility(self, env_vars: Dict[str, str]) -> bool:
        """验证 Docker 环境兼容性"""
        docker_incompatible_hosts = ['localhost', '127.0.0.1']
        
        url_vars = ['DATABASE_URL', 'INFLUXDB_URL', 'REDIS_URL']
        
        for var_name in url_vars:
            if var_name in env_vars:
                url = env_vars[var_name]
                for host in docker_incompatible_hosts:
                    if host in url:
                        self.config_warnings.append(
                            f"{var_name} contains {host}, may not work in Docker containers"
                        )
        
        return True
    
    def validate_security_settings(self, env_vars: Dict[str, str]) -> bool:
        """验证安全设置"""
        # 检查默认值
        default_values = {
            'INFLUXDB_TOKEN': ['my-super-secret-auth-token', 'admin-token'],
            'SECRET_KEY': ['default-secret-key-change-in-production'],
        }
        
        for var_name, defaults in default_values.items():
            if var_name in env_vars:
                value = env_vars[var_name]
                if value in defaults:
                    self.config_warnings.append(
                        f"{var_name} is using a default value, should be changed in production"
                    )
        
        # 检查调试模式
        if env_vars.get('DEBUG', '').lower() in ['true', '1', 'yes']:
            self.config_warnings.append("DEBUG mode is enabled, should be disabled in production")
        
        return True
    
    def compare_with_example(self) -> bool:
        """与示例文件比较，检查缺失的配置"""
        if not self.validate_env_example_exists():
            return True  # 如果没有示例文件，跳过比较
        
        env_vars = self.load_env_variables(self.env_file_path)
        example_vars = self.load_env_variables(self.env_example_path)
        
        # 找出示例文件中有但 .env 中没有的变量
        missing_in_env = set(example_vars.keys()) - set(env_vars.keys())
        
        if missing_in_env:
            self.config_warnings.append(
                f"Variables in .env.example but missing in .env: {sorted(missing_in_env)}"
            )
        
        return True
    
    def validate_all(self) -> bool:
        """执行所有验证"""
        print("开始配置验证...")
        print("=" * 60)
        
        # 检查文件存在性
        if not self.validate_env_file_exists():
            return False
        
        # 加载环境变量
        env_vars = self.load_env_variables(self.env_file_path)
        
        if not env_vars:
            self.config_errors.append("No environment variables found in .env file")
            return False
        
        print(f"✓ 加载了 {len(env_vars)} 个环境变量")
        
        # 执行各项验证
        validations = [
            ("必需变量", lambda: self.validate_required_variables(env_vars)),
            ("数据库URL", lambda: self.validate_database_url(env_vars.get('DATABASE_URL', ''))),
            ("密钥安全性", lambda: self.validate_secret_key(env_vars.get('SECRET_KEY', ''))),
            ("URL格式", lambda: self.validate_urls(env_vars)),
            ("数值配置", lambda: self.validate_numeric_values(env_vars)),
            ("Docker兼容性", lambda: self.validate_docker_compatibility(env_vars)),
            ("安全设置", lambda: self.validate_security_settings(env_vars)),
            ("示例文件比较", lambda: self.compare_with_example()),
        ]
        
        for name, validation_func in validations:
            try:
                if validation_func():
                    print(f"✓ {name}验证通过")
                else:
                    print(f"✗ {name}验证失败")
            except Exception as e:
                print(f"✗ {name}验证出错: {e}")
                self.config_errors.append(f"{name}验证异常: {e}")
        
        return len(self.config_errors) == 0
    
    def print_results(self):
        """打印验证结果"""
        print("\n" + "=" * 60)
        print("配置验证结果")
        print("=" * 60)
        
        if self.config_errors:
            print(f"\n❌ 发现 {len(self.config_errors)} 个错误:")
            for i, error in enumerate(self.config_errors, 1):
                print(f"  {i}. {error}")
        
        if self.config_warnings:
            print(f"\n⚠️  发现 {len(self.config_warnings)} 个警告:")
            for i, warning in enumerate(self.config_warnings, 1):
                print(f"  {i}. {warning}")
        
        if not self.config_errors and not self.config_warnings:
            print("\n🎉 配置验证完全通过！")
        elif not self.config_errors:
            print("\n✅ 配置验证通过，但有一些警告需要注意")
        else:
            print("\n❌ 配置验证失败，请修复错误后重试")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="验证环境变量配置")
    parser.add_argument(
        "--env-file", 
        default=".env", 
        help="环境变量文件路径 (默认: .env)"
    )
    parser.add_argument(
        "--strict", 
        action="store_true", 
        help="严格模式，警告也视为失败"
    )
    
    args = parser.parse_args()
    
    # 切换到脚本所在目录
    os.chdir(Path(__file__).parent)
    
    validator = ConfigValidator(args.env_file)
    
    try:
        success = validator.validate_all()
        validator.print_results()
        
        # 在严格模式下，警告也视为失败
        if args.strict and validator.config_warnings:
            success = False
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n💥 配置验证过程中发生异常: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())