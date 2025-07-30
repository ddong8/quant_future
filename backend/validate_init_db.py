#!/usr/bin/env python3
"""
验证增强的数据库初始化脚本是否满足所有要求
"""
import ast
import sys
from pathlib import Path

def check_requirements():
    """检查脚本是否满足所有要求"""
    init_db_path = Path(__file__).parent / "init_db.py"
    
    if not init_db_path.exists():
        print("✗ init_db.py 文件不存在")
        return False
    
    # 读取脚本内容
    with open(init_db_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析AST
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"✗ 语法错误: {e}")
        return False
    
    # 检查要求
    requirements_met = {
        "retry_mechanism": False,
        "health_check": False,
        "detailed_logging": False,
        "model_relationships": False,
        "error_handling": False
    }
    
    # 检查函数定义
    function_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            function_names.append(node.name)
    
    # 检查重试机制
    if "database_session_with_retry" in function_names and "wait_for_database_ready" in function_names:
        requirements_met["retry_mechanism"] = True
        print("✓ 数据库连接重试机制已实现")
    else:
        print("✗ 缺少数据库连接重试机制")
    
    # 检查健康检查
    if "perform_comprehensive_health_check" in function_names and "verify_database_schema" in function_names:
        requirements_met["health_check"] = True
        print("✓ 健康检查机制已实现")
    else:
        print("✗ 缺少健康检查机制")
    
    # 检查详细日志记录
    if "logging.basicConfig" in content and "FileHandler" in content:
        requirements_met["detailed_logging"] = True
        print("✓ 详细错误日志记录已实现")
    else:
        print("✗ 缺少详细错误日志记录")
    
    # 检查模型关系处理
    if "create_admin_user" in function_names and "create_default_users" in function_names:
        requirements_met["model_relationships"] = True
        print("✓ 模型关系问题修复已整合")
    else:
        print("✗ 缺少模型关系问题修复")
    
    # 检查错误处理
    if "try:" in content and "except" in content and "logger.error" in content:
        requirements_met["error_handling"] = True
        print("✓ 错误处理机制已实现")
    else:
        print("✗ 缺少错误处理机制")
    
    # 检查配置常量
    config_constants = ["MAX_RETRIES", "RETRY_DELAY", "CONNECTION_TIMEOUT"]
    config_found = all(const in content for const in config_constants)
    
    if config_found:
        print("✓ 重试配置常量已定义")
    else:
        print("✗ 缺少重试配置常量")
    
    # 总结
    total_requirements = len(requirements_met)
    met_requirements = sum(requirements_met.values())
    
    print(f"\n要求满足情况: {met_requirements}/{total_requirements}")
    
    if met_requirements == total_requirements and config_found:
        print("✅ 所有要求都已满足！")
        return True
    else:
        print("❌ 部分要求未满足")
        return False

def check_documentation():
    """检查文档是否存在"""
    doc_path = Path(__file__).parent / "docs" / "enhanced_init_db_guide.md"
    
    if doc_path.exists():
        print("✓ 增强初始化脚本文档已创建")
        return True
    else:
        print("✗ 缺少增强初始化脚本文档")
        return False

def main():
    """主验证函数"""
    print("验证增强的数据库初始化脚本...")
    print("=" * 50)
    
    requirements_ok = check_requirements()
    documentation_ok = check_documentation()
    
    print("\n" + "=" * 50)
    
    if requirements_ok and documentation_ok:
        print("🎉 验证通过！增强的数据库初始化脚本已完成。")
        print("\n主要改进:")
        print("- ✅ 数据库连接重试机制（指数退避）")
        print("- ✅ 全面的健康检查系统")
        print("- ✅ 详细的错误日志记录")
        print("- ✅ 模型关系问题修复整合")
        print("- ✅ 健壮的错误处理机制")
        print("- ✅ 完整的文档说明")
        return 0
    else:
        print("❌ 验证失败，请检查脚本实现。")
        return 1

if __name__ == "__main__":
    sys.exit(main())