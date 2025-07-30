#!/usr/bin/env python3
"""
测试增强的数据库初始化脚本
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_import():
    """测试导入功能"""
    try:
        from init_db import (
            database_session_with_retry,
            wait_for_database_ready,
            verify_database_schema,
            create_admin_user,
            create_default_users,
            validate_user_creation,
            perform_comprehensive_health_check,
            log_initialization_summary
        )
        print("✓ 所有函数导入成功")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_configuration():
    """测试配置"""
    try:
        from init_db import MAX_RETRIES, RETRY_DELAY, CONNECTION_TIMEOUT
        print(f"✓ 配置加载成功:")
        print(f"  - 最大重试次数: {MAX_RETRIES}")
        print(f"  - 重试延迟: {RETRY_DELAY}秒")
        print(f"  - 连接超时: {CONNECTION_TIMEOUT}秒")
        return True
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        return False

def test_logging_setup():
    """测试日志设置"""
    try:
        from init_db import logger
        logger.info("测试日志记录")
        print("✓ 日志设置正常")
        return True
    except Exception as e:
        print(f"✗ 日志设置失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试增强的数据库初始化脚本...")
    print("=" * 50)
    
    tests = [
        ("导入测试", test_import),
        ("配置测试", test_configuration),
        ("日志测试", test_logging_setup)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n运行 {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"  {test_name} 失败")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过！增强的初始化脚本准备就绪。")
        return 0
    else:
        print("✗ 部分测试失败，请检查脚本。")
        return 1

if __name__ == "__main__":
    sys.exit(main())