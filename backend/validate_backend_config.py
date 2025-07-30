#!/usr/bin/env python3
"""
后端服务配置验证脚本
验证后端服务的配置是否正确
"""
import sys
import os
from pathlib import Path
from typing import Dict, List, Any


class BackendConfigValidator:
    """后端配置验证器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_environment_variables(self) -> bool:
        """验证环境变量"""
        print("验证环境变量...")
        
        # 必需的环境变量
        required_vars = {
            'DATABASE_URL': '数据库连接URL',
            'REDIS_URL': 'Redis连接URL',
            'INFLUXDB_URL': 'InfluxDB连接URL',
            'SECRET_KEY': '应用密钥',
        }
        
        # 推荐的环境变量
        recommended_vars = {
            'LOG_LEVEL': '日志级别',
            'DEBUG': '调试模式',
            'JWT_ALGORITHM': 'JWT算法',
            'DB_POOL_SIZE': '数据库连接池大小',
            'WORKER_PROCESSES': 'Worker进程数',
        }
        
        # 检查必需变量
        for var, description in required_vars.items():
            value = os.getenv(var)
            if not value:
                self.errors.append(f"缺少必需环境变量: {var} ({description})")
            else:
                print(f"✓ {var}: {description}")
        
        # 检查推荐变量
        for var, description in recommended_vars.items():
            value = os.getenv(var)
            if not value:
                self.warnings.append(f"建议设置环境变量: {var} ({description})")
            else:
                print(f"✓ {var}: {description}")
        
        return len(self.errors) == 0
    
    def validate_database_urls(self) -> bool:
        """验证数据库URL格式"""
        print("\n验证数据库URL格式...")
        
        url_configs = {
            'DATABASE_URL': ('postgresql://', 'PostgreSQL URL'),
            'REDIS_URL': ('redis://', 'Redis URL'),
            'INFLUXDB_URL': ('http', 'InfluxDB URL'),
        }
        
        all_valid = True
        
        for var, (prefix, description) in url_configs.items():
            url = os.getenv(var, '')
            if url:
                if not url.startswith(prefix):
                    self.errors.append(f"{var} 格式不正确，应以 '{prefix}' 开头")
                    all_valid = False
                else:
                    print(f"✓ {var}: {description} 格式正确")
            else:
                print(f"⚠ {var}: 未设置")
        
        return all_valid
    
    def validate_numeric_configs(self) -> bool:
        """验证数值配置"""
        print("\n验证数值配置...")
        
        numeric_configs = {
            'WORKER_PROCESSES': (1, 16, '工作进程数'),
            'DB_POOL_SIZE': (1, 100, '数据库连接池大小'),
            'DB_MAX_OVERFLOW': (0, 200, '数据库连接池最大溢出'),
            'JWT_ACCESS_TOKEN_EXPIRE_MINUTES': (1, 1440, 'JWT访问令牌过期时间'),
            'REDIS_MAX_CONNECTIONS': (1, 1000, 'Redis最大连接数'),
        }
        
        all_valid = True
        
        for var, (min_val, max_val, description) in numeric_configs.items():
            value_str = os.getenv(var)
            if value_str:
                try:
                    value = int(value_str)
                    if min_val <= value <= max_val:
                        print(f"✓ {var}: {description} = {value}")
                    else:
                        self.warnings.append(
                            f"{var} 值 {value} 超出推荐范围 [{min_val}, {max_val}]"
                        )
                except ValueError:
                    self.errors.append(f"{var} 不是有效数字: {value_str}")
                    all_valid = False
        
        return all_valid
    
    def validate_file_permissions(self) -> bool:
        """验证文件权限"""
        print("\n验证文件权限...")
        
        files_to_check = [
            ('init_db.py', '数据库初始化脚本'),
            ('start_backend.py', '后端启动脚本'),
            ('check_db_status.py', '数据库状态检查脚本'),
            ('wait_for_db.py', '等待数据库脚本'),
        ]
        
        all_valid = True
        
        for filename, description in files_to_check:
            file_path = Path(filename)
            if file_path.exists():
                if os.access(file_path, os.X_OK):
                    print(f"✓ {filename}: {description} 可执行")
                else:
                    self.warnings.append(f"{filename} 没有执行权限")
            else:
                self.errors.append(f"缺少文件: {filename} ({description})")
                all_valid = False
        
        return all_valid
    
    def validate_log_directory(self) -> bool:
        """验证日志目录"""
        print("\n验证日志目录...")
        
        log_dir = Path("/var/log/trading")
        
        if log_dir.exists():
            if os.access(log_dir, os.W_OK):
                print(f"✓ 日志目录可写: {log_dir}")
                return True
            else:
                self.errors.append(f"日志目录不可写: {log_dir}")
                return False
        else:
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
                print(f"✓ 创建日志目录: {log_dir}")
                return True
            except Exception as e:
                self.errors.append(f"无法创建日志目录 {log_dir}: {e}")
                return False
    
    def validate_security_settings(self) -> bool:
        """验证安全设置"""
        print("\n验证安全设置...")
        
        # 检查密钥强度
        secret_key = os.getenv('SECRET_KEY', '')
        if secret_key:
            if len(secret_key) < 32:
                self.errors.append("SECRET_KEY 长度应至少32字符")
            elif secret_key == 'your-super-secret-key-change-this-in-production':
                self.warnings.append("SECRET_KEY 使用默认值，生产环境应修改")
            else:
                print("✓ SECRET_KEY 长度符合要求")
        
        # 检查调试模式
        debug = os.getenv('DEBUG', 'false').lower()
        if debug == 'true':
            self.warnings.append("DEBUG 模式已启用，生产环境应禁用")
        else:
            print("✓ DEBUG 模式已禁用")
        
        return True
    
    def validate_all(self) -> bool:
        """执行所有验证"""
        validations = [
            self.validate_environment_variables,
            self.validate_database_urls,
            self.validate_numeric_configs,
            self.validate_file_permissions,
            self.validate_log_directory,
            self.validate_security_settings,
        ]
        
        all_valid = True
        for validation in validations:
            if not validation():
                all_valid = False
        
        return all_valid
    
    def print_results(self):
        """打印验证结果"""
        print("\n" + "=" * 60)
        print("后端服务配置验证结果")
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


def main():
    """主函数"""
    print("后端服务配置验证")
    print("=" * 50)
    
    validator = BackendConfigValidator()
    
    try:
        success = validator.validate_all()
        validator.print_results()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n💥 验证过程中发生异常: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())