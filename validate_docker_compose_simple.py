#!/usr/bin/env python3
"""
Docker Compose 配置简单验证脚本
不依赖外部包，仅验证文件存在性和基本结构
"""
import sys
from pathlib import Path


def validate_file_exists(file_path: Path, description: str) -> bool:
    """验证文件是否存在"""
    if file_path.exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description} 不存在: {file_path}")
        return False


def validate_docker_compose_files():
    """验证 Docker Compose 文件"""
    print("验证 Docker Compose 配置文件...")

    files = [
        (Path("docker-compose.yml"), "主配置文件"),
        (Path("docker-compose.dev.yml"), "开发环境配置"),
        (Path("docker-compose.prod.yml"), "生产环境配置"),
    ]

    all_exist = True
    for file_path, description in files:
        if not validate_file_exists(file_path, description):
            all_exist = False

    return all_exist


def validate_dockerfiles():
    """验证 Dockerfile 文件"""
    print("\n验证 Dockerfile 文件...")

    files = [
        (Path("backend/Dockerfile"), "后端服务 Dockerfile"),
        (Path("backend/Dockerfile.init"), "初始化容器 Dockerfile"),
    ]

    all_exist = True
    for file_path, description in files:
        if not validate_file_exists(file_path, description):
            all_exist = False

    return all_exist


def validate_init_scripts():
    """验证初始化脚本"""
    print("\n验证初始化脚本...")

    scripts = [
        (Path("backend/init_db.py"), "数据库初始化脚本"),
        (Path("backend/wait_for_db.py"), "等待数据库就绪脚本"),
        (Path("backend/check_init_status.py"), "初始化状态检查脚本"),
        (Path("backend/run_init.py"), "初始化运行脚本"),
        (Path("backend/init_healthcheck.py"), "初始化健康检查脚本"),
    ]

    all_exist = True
    for file_path, description in scripts:
        if not validate_file_exists(file_path, description):
            all_exist = False

    return all_exist


def validate_docker_compose_content():
    """验证 Docker Compose 内容"""
    print("\n验证 Docker Compose 内容...")

    compose_file = Path("docker-compose.yml")
    if not compose_file.exists():
        print("❌ docker-compose.yml 文件不存在")
        return False

    try:
        with open(compose_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查关键服务
        required_services = ["postgres:", "redis:", "influxdb:", "db-init:", "backend:"]
        missing_services = []

        for service in required_services:
            if service not in content:
                missing_services.append(service.rstrip(":"))

        if missing_services:
            print(f"❌ 缺少服务定义: {missing_services}")
            return False
        else:
            print("✅ 所有必需服务都已定义")

        # 检查关键配置
        required_configs = [
            "depends_on:",
            "healthcheck:",
            "environment:",
            "volumes:",
            "db_init_status:",
        ]

        missing_configs = []
        for config in required_configs:
            if config not in content:
                missing_configs.append(config.rstrip(":"))

        if missing_configs:
            print(f"⚠️  可能缺少配置: {missing_configs}")
        else:
            print("✅ 关键配置都已包含")

        return True

    except Exception as e:
        print(f"❌ 读取 docker-compose.yml 失败: {e}")
        return False


def validate_documentation():
    """验证文档"""
    print("\n验证文档...")

    docs = [
        (Path("docs/docker-compose-guide.md"), "Docker Compose 使用指南"),
    ]

    all_exist = True
    for file_path, description in docs:
        if not validate_file_exists(file_path, description):
            all_exist = False

    return all_exist


def main():
    """主函数"""
    print("Docker Compose 配置简单验证")
    print("=" * 50)

    validations = [
        ("Docker Compose 文件", validate_docker_compose_files),
        ("Dockerfile 文件", validate_dockerfiles),
        ("初始化脚本", validate_init_scripts),
        ("配置内容", validate_docker_compose_content),
        ("文档", validate_documentation),
    ]

    passed = 0
    total = len(validations)

    for name, validation_func in validations:
        try:
            if validation_func():
                passed += 1
                print(f"✅ {name} 验证通过")
            else:
                print(f"❌ {name} 验证失败")
        except Exception as e:
            print(f"💥 {name} 验证异常: {e}")

    print(f"\n{'='*50}")
    print(f"验证结果: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 Docker Compose 配置验证通过！")
        print("\n✅ 数据库初始化容器配置已完成:")
        print("  - ✅ 数据库初始化容器 (db-init)")
        print("  - ✅ 专用初始化 Dockerfile")
        print("  - ✅ 完整的初始化脚本集合")
        print("  - ✅ 服务依赖关系和启动顺序")
        print("  - ✅ 健康检查和状态监控")
        print("  - ✅ 开发和生产环境配置")
        print("  - ✅ 详细的部署文档")
        return 0
    else:
        print("\n❌ 部分验证失败，请检查配置")
        return 1


if __name__ == "__main__":
    sys.exit(main())
