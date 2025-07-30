#!/usr/bin/env python3
"""
环境变量语法验证脚本
不依赖外部包，仅验证 .env 文件的语法和基本格式
"""
import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


def validate_env_file_syntax(file_path: Path) -> Tuple[bool, List[str], List[str]]:
    """验证 .env 文件语法"""
    errors = []
    warnings = []
    
    if not file_path.exists():
        errors.append(f"文件不存在: {file_path}")
        return False, errors, warnings
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        errors.append(f"无法读取文件: {e}")
        return False, errors, warnings
    
    env_vars = {}
    
    for line_num, line in enumerate(lines, 1):
        original_line = line
        line = line.strip()
        
        # 跳过空行和注释
        if not line or line.startswith('#'):
            continue
        
        # 检查是否包含等号
        if '=' not in line:
            errors.append(f"第{line_num}行: 缺少等号 - {original_line.strip()}")
            continue
        
        # 分割键值对
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        # 验证键名格式
        if not re.match(r'^[A-Z][A-Z0-9_]*$', key):
            warnings.append(f"第{line_num}行: 键名格式不规范 '{key}' (建议使用大写字母和下划线)")
        
        # 检查重复键
        if key in env_vars:
            warnings.append(f"第{line_num}行: 重复的键 '{key}'")
        
        env_vars[key] = value
        
        # 检查值的格式
        if key.endswith('_URL') and value:
            if not re.match(r'^https?://|^redis://|^postgresql://', value):
                warnings.append(f"第{line_num}行: URL格式可能不正确 '{key}={value}'")
        
        if key.endswith('_PORT') and value:
            try:
                port = int(value)
                if port <= 0 or port > 65535:
                    errors.append(f"第{line_num}行: 端口号超出范围 '{key}={value}'")
            except ValueError:
                errors.append(f"第{line_num}行: 端口号不是数字 '{key}={value}'")
        
        # 检查敏感信息
        if 'PASSWORD' in key or 'SECRET' in key or 'TOKEN' in key:
            if value.startswith('your-') or value in ['password', 'secret', 'token']:
                warnings.append(f"第{line_num}行: 敏感信息使用默认值 '{key}'")
    
    return len(errors) == 0, errors, warnings


def check_required_variables(env_vars: Dict[str, str]) -> List[str]:
    """检查必需的环境变量"""
    required_vars = [
        'APP_NAME',
        'SECRET_KEY',
        'DATABASE_URL',
        'INFLUXDB_URL',
        'INFLUXDB_TOKEN',
        'REDIS_URL',
        'JWT_ALGORITHM',
    ]
    
    missing = []
    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            missing.append(var)
    
    return missing


def load_env_variables(file_path: Path) -> Dict[str, str]:
    """加载环境变量"""
    env_vars = {}
    
    if not file_path.exists():
        return env_vars
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception:
        pass
    
    return env_vars


def main():
    """主函数"""
    print("环境变量语法验证")
    print("=" * 50)
    
    env_file = Path(".env")
    env_example_file = Path(".env.example")
    
    # 验证 .env 文件
    print(f"\n检查 {env_file}...")
    success, errors, warnings = validate_env_file_syntax(env_file)
    
    if success:
        print("✓ 语法验证通过")
    else:
        print("✗ 语法验证失败")
        for error in errors:
            print(f"  错误: {error}")
    
    if warnings:
        print("⚠️  警告:")
        for warning in warnings:
            print(f"  {warning}")
    
    # 检查必需变量
    if success:
        env_vars = load_env_variables(env_file)
        missing_vars = check_required_variables(env_vars)
        
        if missing_vars:
            print(f"\n✗ 缺少必需的环境变量: {missing_vars}")
            success = False
        else:
            print("\n✓ 所有必需的环境变量都已设置")
    
    # 验证 .env.example 文件
    if env_example_file.exists():
        print(f"\n检查 {env_example_file}...")
        example_success, example_errors, example_warnings = validate_env_file_syntax(env_example_file)
        
        if example_success:
            print("✓ 示例文件语法验证通过")
        else:
            print("✗ 示例文件语法验证失败")
            for error in example_errors:
                print(f"  错误: {error}")
    
    # 总结
    print("\n" + "=" * 50)
    if success:
        print("🎉 环境变量配置验证通过！")
        return 0
    else:
        print("❌ 环境变量配置验证失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())