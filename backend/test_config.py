#!/usr/bin/env python3
"""
配置测试脚本
测试配置是否能正确加载和使用
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_config_loading():
    """测试配置加载"""
    print("测试配置加载...")
    
    try:
        from app.core.config import settings
        print("✓ 配置模块导入成功")
        
        # 测试基本配置
        print(f"✓ 应用名称: {settings.APP_NAME}")
        print(f"✓ 应用版本: {settings.APP_VERSION}")
        print(f"✓ 调试模式: {settings.DEBUG}")
        print(f"✓ 日志级别: {settings.LOG_LEVEL}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return False


def test_database_config():
    """测试数据库配置"""
    print("\n测试数据库配置...")
    
    try:
        from app.core.config import settings
        
        db_config = settings.get_database_config()
        print(f"✓ 数据库URL: {db_config['url']}")
        print(f"✓ 连接池大小: {db_config['pool_size']}")
        print(f"✓ 最大溢出: {db_config['max_overflow']}")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据库配置测试失败: {e}")
        return False


def test_jwt_config():
    """测试JWT配置"""
    print("\n测试JWT配置...")
    
    try:
        from app.core.config import settings
        
        jwt_config = settings.get_jwt_config()
        print(f"✓ JWT算法: {jwt_config['algorithm']}")
        print(f"✓ 访问令牌过期时间: {jwt_config['access_token_expire_minutes']}分钟")
        print(f"✓ 刷新令牌过期时间: {jwt_config['refresh_token_expire_days']}天")
        print(f"✓ 密钥长度: {len(jwt_config['secret_key'])}字符")
        
        return True
        
    except Exception as e:
        print(f"✗ JWT配置测试失败: {e}")
        return False


def test_redis_config():
    """测试Redis配置"""
    print("\n测试Redis配置...")
    
    try:
        from app.core.config import settings
        
        redis_config = settings.get_redis_config()
        print(f"✓ Redis URL: {redis_config['url']}")
        print(f"✓ 最大连接数: {redis_config['max_connections']}")
        print(f"✓ 连接超时: {redis_config['connection_timeout']}秒")
        
        return True
        
    except Exception as e:
        print(f"✗ Redis配置测试失败: {e}")
        return False


def test_cors_config():
    """测试CORS配置"""
    print("\n测试CORS配置...")
    
    try:
        from app.core.config import settings
        
        cors_origins = settings.CORS_ORIGINS
        print(f"✓ CORS域名数量: {len(cors_origins)}")
        print(f"✓ CORS域名: {cors_origins}")
        
        return True
        
    except Exception as e:
        print(f"✗ CORS配置测试失败: {e}")
        return False


def test_production_warnings():
    """测试生产环境警告"""
    print("\n测试生产环境警告...")
    
    try:
        from app.core.config import settings
        
        warnings = settings.validate_production_config()
        
        if warnings:
            print(f"⚠️  发现 {len(warnings)} 个生产环境警告:")
            for i, warning in enumerate(warnings, 1):
                print(f"   {i}. {warning}")
        else:
            print("✓ 没有生产环境警告")
        
        return True
        
    except Exception as e:
        print(f"✗ 生产环境警告测试失败: {e}")
        return False


def test_environment_detection():
    """测试环境检测"""
    print("\n测试环境检测...")
    
    try:
        from app.core.config import settings
        
        print(f"✓ 调试模式: {settings.DEBUG}")
        print(f"✓ 环境类型: {'开发' if settings.DEBUG else '生产'}")
        
        # 测试不同环境的配置差异
        if settings.DEBUG:
            print("✓ 开发环境配置已加载")
        else:
            print("✓ 生产环境配置已加载")
        
        return True
        
    except Exception as e:
        print(f"✗ 环境检测测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始配置测试...")
    print("=" * 60)
    
    tests = [
        ("配置加载", test_config_loading),
        ("数据库配置", test_database_config),
        ("JWT配置", test_jwt_config),
        ("Redis配置", test_redis_config),
        ("CORS配置", test_cors_config),
        ("生产环境警告", test_production_warnings),
        ("环境检测", test_environment_detection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"  {test_name} 测试失败")
        except Exception as e:
            print(f"  {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"配置测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有配置测试通过！")
        return 0
    else:
        print("❌ 部分配置测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())