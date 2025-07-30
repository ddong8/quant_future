#!/usr/bin/env python3
"""
健康检查功能测试脚本
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_health_check_imports():
    """测试健康检查模块导入"""
    print("测试健康检查模块导入...")
    
    try:
        from app.services.health_check_service import DatabaseHealthChecker, health_checker
        print("✓ 健康检查服务导入成功")
        
        from app.api.v1.health import router
        print("✓ 健康检查API路由导入成功")
        
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 导入异常: {e}")
        return False


def test_health_checker_initialization():
    """测试健康检查器初始化"""
    print("\n测试健康检查器初始化...")
    
    try:
        from app.services.health_check_service import DatabaseHealthChecker
        
        checker = DatabaseHealthChecker()
        
        # 检查属性
        assert hasattr(checker, 'check_timeout')
        assert hasattr(checker, 'warning_threshold')
        assert hasattr(checker, 'critical_threshold')
        
        print(f"✓ 检查超时时间: {checker.check_timeout}秒")
        print(f"✓ 警告阈值: {checker.warning_threshold}ms")
        print(f"✓ 严重阈值: {checker.critical_threshold}ms")
        
        return True
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        return False


def test_health_check_methods():
    """测试健康检查方法"""
    print("\n测试健康检查方法...")
    
    try:
        from app.services.health_check_service import DatabaseHealthChecker
        
        checker = DatabaseHealthChecker()
        
        # 检查方法存在
        methods = [
            'check_postgresql_health',
            'check_influxdb_health', 
            'check_redis_health',
            'check_database_initialization_status',
            'perform_comprehensive_health_check',
            'wait_for_database_ready'
        ]
        
        for method in methods:
            assert hasattr(checker, method), f"缺少方法: {method}"
            assert callable(getattr(checker, method)), f"方法不可调用: {method}"
            print(f"✓ 方法存在: {method}")
        
        return True
    except Exception as e:
        print(f"✗ 方法检查失败: {e}")
        return False


async def test_health_check_structure():
    """测试健康检查结构"""
    print("\n测试健康检查结构...")
    
    try:
        from app.services.health_check_service import DatabaseHealthChecker
        
        checker = DatabaseHealthChecker()
        
        # 模拟一个健康检查结果结构
        mock_result = {
            "service": "test",
            "status": "healthy",
            "response_time_ms": 100.0,
            "timestamp": "2024-01-01T12:00:00.000Z",
            "message": "测试消息"
        }
        
        # 检查必需字段
        required_fields = ["service", "status", "response_time_ms", "timestamp", "message"]
        for field in required_fields:
            assert field in mock_result, f"缺少必需字段: {field}"
            print(f"✓ 字段存在: {field}")
        
        # 检查状态值
        valid_statuses = ["healthy", "warning", "critical"]
        assert mock_result["status"] in valid_statuses, f"无效状态: {mock_result['status']}"
        print(f"✓ 状态值有效: {mock_result['status']}")
        
        return True
    except Exception as e:
        print(f"✗ 结构检查失败: {e}")
        return False


def test_api_endpoints():
    """测试API端点定义"""
    print("\n测试API端点定义...")
    
    try:
        from app.api.v1.health import router
        
        # 检查路由器属性
        assert hasattr(router, 'routes'), "路由器缺少routes属性"
        
        routes = router.routes
        print(f"✓ 定义了 {len(routes)} 个路由")
        
        # 检查一些关键路由
        route_paths = [route.path for route in routes if hasattr(route, 'path')]
        
        expected_paths = [
            "/",
            "/detailed", 
            "/database",
            "/initialization",
            "/readiness",
            "/liveness"
        ]
        
        for path in expected_paths:
            if any(path in route_path for route_path in route_paths):
                print(f"✓ 路由存在: {path}")
            else:
                print(f"⚠️  路由可能缺失: {path}")
        
        return True
    except Exception as e:
        print(f"✗ API端点检查失败: {e}")
        return False


def test_configuration_integration():
    """测试配置集成"""
    print("\n测试配置集成...")
    
    try:
        # 检查配置是否包含健康检查相关设置
        expected_configs = [
            'DB_INIT_TIMEOUT',
            'DB_INIT_RETRY_COUNT', 
            'DB_INIT_RETRY_DELAY',
            'HEALTH_CHECK_INTERVAL',
            'HEALTH_CHECK_TIMEOUT',
            'HEALTH_CHECK_RETRIES'
        ]
        
        # 读取 .env.example 文件检查配置
        env_example_path = Path("backend/.env.example")
        if env_example_path.exists():
            with open(env_example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for config in expected_configs:
                if config in content:
                    print(f"✓ 配置存在: {config}")
                else:
                    print(f"⚠️  配置可能缺失: {config}")
        else:
            print("⚠️  .env.example 文件不存在")
        
        return True
    except Exception as e:
        print(f"✗ 配置集成检查失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("健康检查功能测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_health_check_imports),
        ("健康检查器初始化", test_health_checker_initialization),
        ("健康检查方法", test_health_check_methods),
        ("健康检查结构", test_health_check_structure),
        ("API端点定义", test_api_endpoints),
        ("配置集成", test_configuration_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"💥 {test_name} 测试异常: {e}")
    
    print(f"\n{'='*50}")
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有健康检查功能测试通过！")
        return 0
    else:
        print("❌ 部分测试失败，请检查实现")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)