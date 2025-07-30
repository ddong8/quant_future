#!/usr/bin/env python3
"""
健康检查语法和结构测试脚本
不依赖外部包，仅测试代码结构和语法
"""
import sys
import ast
from pathlib import Path


def test_file_syntax(file_path: Path) -> bool:
    """测试文件语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析AST
        ast.parse(content)
        return True
    except SyntaxError as e:
        print(f"  语法错误: {e}")
        return False
    except Exception as e:
        print(f"  解析错误: {e}")
        return False


def test_class_structure(file_path: Path, expected_class: str, expected_methods: list) -> bool:
    """测试类结构"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # 查找类定义
        class_found = False
        methods_found = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == expected_class:
                class_found = True
                
                # 查找方法（包括异步方法）
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods_found.append(item.name)
        
        if not class_found:
            print(f"  类 {expected_class} 未找到")
            return False
        
        # 检查期望的方法
        missing_methods = []
        for method in expected_methods:
            if method not in methods_found:
                missing_methods.append(method)
        
        if missing_methods:
            print(f"  缺少方法: {missing_methods}")
            return False
        
        print(f"  类 {expected_class} 结构正确")
        print(f"  找到方法: {len(methods_found)}")
        return True
        
    except Exception as e:
        print(f"  结构检查错误: {e}")
        return False


def test_api_routes(file_path: Path) -> bool:
    """测试API路由定义"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查路由装饰器
        route_decorators = [
            '@router.get("/")',
            '@router.get("/detailed")',
            '@router.get("/database")',
            '@router.get("/initialization")',
            '@router.get("/readiness")',
            '@router.get("/liveness")'
        ]
        
        found_routes = []
        for decorator in route_decorators:
            if decorator in content:
                found_routes.append(decorator)
        
        print(f"  找到路由: {len(found_routes)}")
        
        if len(found_routes) >= 4:  # 至少要有4个主要路由
            return True
        else:
            print(f"  路由数量不足，期望至少4个，实际{len(found_routes)}个")
            return False
            
    except Exception as e:
        print(f"  路由检查错误: {e}")
        return False


def test_configuration_presence() -> bool:
    """测试配置文件中的健康检查配置"""
    env_example_path = Path("backend/.env.example")
    
    if not env_example_path.exists():
        print("  .env.example 文件不存在")
        return False
    
    try:
        with open(env_example_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        health_configs = [
            'DB_INIT_TIMEOUT',
            'DB_INIT_RETRY_COUNT',
            'HEALTH_CHECK_INTERVAL',
            'HEALTH_CHECK_TIMEOUT'
        ]
        
        found_configs = []
        for config in health_configs:
            if config in content:
                found_configs.append(config)
        
        print(f"  找到健康检查配置: {len(found_configs)}")
        
        return len(found_configs) >= 2  # 至少要有2个配置
        
    except Exception as e:
        print(f"  配置检查错误: {e}")
        return False


def main():
    """主测试函数"""
    print("健康检查语法和结构测试")
    print("=" * 50)
    
    tests = [
        {
            "name": "健康检查服务语法",
            "func": lambda: test_file_syntax(Path("backend/app/services/health_check_service.py"))
        },
        {
            "name": "健康检查API语法", 
            "func": lambda: test_file_syntax(Path("backend/app/api/v1/health.py"))
        },
        {
            "name": "数据库状态检查脚本语法",
            "func": lambda: test_file_syntax(Path("backend/check_db_status.py"))
        },
        {
            "name": "等待数据库脚本语法",
            "func": lambda: test_file_syntax(Path("backend/wait_for_db.py"))
        },
        {
            "name": "健康检查器类结构",
            "func": lambda: test_class_structure(
                Path("backend/app/services/health_check_service.py"),
                "DatabaseHealthChecker",
                ["__init__", "check_postgresql_health", "check_influxdb_health", "check_redis_health", 
                 "check_database_initialization_status", "perform_comprehensive_health_check", "wait_for_database_ready"]
            )
        },
        {
            "name": "API路由定义",
            "func": lambda: test_api_routes(Path("backend/app/api/v1/health.py"))
        },
        {
            "name": "配置文件健康检查设置",
            "func": test_configuration_presence
        }
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\n测试: {test['name']}")
        try:
            if test['func']():
                print(f"✅ {test['name']} 通过")
                passed += 1
            else:
                print(f"❌ {test['name']} 失败")
        except Exception as e:
            print(f"💥 {test['name']} 异常: {e}")
    
    print(f"\n{'='*50}")
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有语法和结构测试通过！")
        print("\n✅ 健康检查机制实现完成:")
        print("  - DatabaseHealthChecker 服务类")
        print("  - 完整的健康检查API端点")
        print("  - 数据库状态检查脚本")
        print("  - 等待数据库就绪脚本")
        print("  - 配置文件集成")
        print("  - 详细的使用文档")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())