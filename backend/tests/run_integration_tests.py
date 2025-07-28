#!/usr/bin/env python3
"""
集成测试运行脚本
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def setup_test_environment():
    """设置测试环境"""
    print("🔧 设置测试环境...")
    
    # 设置环境变量
    os.environ["TESTING"] = "1"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    
    # 安装测试依赖
    success, stdout, stderr = run_command("pip install pytest pytest-asyncio httpx")
    if not success:
        print(f"❌ 安装测试依赖失败: {stderr}")
        return False
    
    print("✅ 测试环境设置完成")
    return True


def run_integration_tests(test_pattern=None, verbose=False, coverage=False):
    """运行集成测试"""
    print("🧪 开始运行集成测试...")
    
    # 构建pytest命令
    cmd_parts = ["python", "-m", "pytest"]
    
    # 添加测试目录
    test_dir = "tests/integration"
    if test_pattern:
        test_dir = f"{test_dir}/{test_pattern}"
    cmd_parts.append(test_dir)
    
    # 添加选项
    cmd_parts.extend([
        "-v" if verbose else "-q",
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    # 添加覆盖率选项
    if coverage:
        cmd_parts.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    # 运行测试
    command = " ".join(cmd_parts)
    print(f"执行命令: {command}")
    
    success, stdout, stderr = run_command(command)
    
    if success:
        print("✅ 集成测试通过")
        print(stdout)
        return True
    else:
        print("❌ 集成测试失败")
        print(f"标准输出: {stdout}")
        print(f"错误输出: {stderr}")
        return False


def run_specific_test_suite(suite_name):
    """运行特定测试套件"""
    test_suites = {
        "auth": "test_auth_api.py",
        "strategy": "test_strategy_api.py",
        "backtest": "test_backtest_api.py",
        "trading": "test_trading_api.py",
        "websocket": "test_websocket.py",
        "tqsdk": "test_tqsdk_integration.py",
        "database": "test_database_operations.py"
    }
    
    if suite_name not in test_suites:
        print(f"❌ 未知的测试套件: {suite_name}")
        print(f"可用的测试套件: {', '.join(test_suites.keys())}")
        return False
    
    test_file = test_suites[suite_name]
    print(f"🧪 运行测试套件: {suite_name} ({test_file})")
    
    return run_integration_tests(test_file, verbose=True)


def generate_test_report():
    """生成测试报告"""
    print("📊 生成测试报告...")
    
    # 运行测试并生成HTML报告
    cmd = [
        "python", "-m", "pytest",
        "tests/integration",
        "--html=reports/integration_test_report.html",
        "--self-contained-html",
        "--cov=app",
        "--cov-report=html:reports/coverage",
        "--junitxml=reports/junit.xml"
    ]
    
    # 创建报告目录
    os.makedirs("reports", exist_ok=True)
    
    success, stdout, stderr = run_command(" ".join(cmd))
    
    if success:
        print("✅ 测试报告生成完成")
        print("📄 HTML报告: reports/integration_test_report.html")
        print("📊 覆盖率报告: reports/coverage/index.html")
        print("📋 JUnit报告: reports/junit.xml")
        return True
    else:
        print("❌ 测试报告生成失败")
        print(f"错误: {stderr}")
        return False


def check_test_dependencies():
    """检查测试依赖"""
    print("🔍 检查测试依赖...")
    
    required_packages = [
        "pytest",
        "pytest-asyncio",
        "httpx",
        "sqlalchemy",
        "fastapi"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ 所有测试依赖已安装")
    return True


def cleanup_test_data():
    """清理测试数据"""
    print("🧹 清理测试数据...")
    
    # 删除测试数据库
    test_db_files = ["test.db", "test.db-shm", "test.db-wal"]
    for db_file in test_db_files:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"删除测试数据库文件: {db_file}")
    
    # 清理缓存
    cache_dirs = ["__pycache__", ".pytest_cache"]
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            import shutil
            shutil.rmtree(cache_dir)
            print(f"删除缓存目录: {cache_dir}")
    
    print("✅ 测试数据清理完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="量化交易平台集成测试运行器")
    
    parser.add_argument(
        "--suite",
        choices=["auth", "strategy", "backtest", "trading", "websocket", "tqsdk", "database"],
        help="运行特定测试套件"
    )
    
    parser.add_argument(
        "--pattern",
        help="测试文件模式匹配"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="生成覆盖率报告"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="生成HTML测试报告"
    )
    
    parser.add_argument(
        "--setup",
        action="store_true",
        help="设置测试环境"
    )
    
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="清理测试数据"
    )
    
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="检查测试依赖"
    )
    
    args = parser.parse_args()
    
    # 切换到backend目录
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    success = True
    
    # 检查依赖
    if args.check_deps or args.setup:
        success = check_test_dependencies()
        if not success:
            sys.exit(1)
    
    # 设置测试环境
    if args.setup:
        success = setup_test_environment()
        if not success:
            sys.exit(1)
    
    # 清理测试数据
    if args.cleanup:
        cleanup_test_data()
        return
    
    # 运行特定测试套件
    if args.suite:
        success = run_specific_test_suite(args.suite)
    # 生成测试报告
    elif args.report:
        success = generate_test_report()
    # 运行所有集成测试
    else:
        success = run_integration_tests(
            test_pattern=args.pattern,
            verbose=args.verbose,
            coverage=args.coverage
        )
    
    if not success:
        sys.exit(1)
    
    print("🎉 集成测试完成!")


if __name__ == "__main__":
    main()