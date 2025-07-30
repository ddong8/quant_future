#!/usr/bin/env python3
"""
初始化状态检查脚本
检查数据库是否已经初始化完成
"""
import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def check_initialization_status():
    """检查初始化状态"""
    print("检查数据库初始化状态...")
    
    # 检查初始化标记文件
    init_marker = Path("/var/lib/db-init/initialized")
    if init_marker.exists():
        print("✅ 发现初始化标记文件")
        return True
    
    # 检查数据库初始化状态
    try:
        from app.services.health_check_service import health_checker
        
        init_status = await health_checker.check_database_initialization_status()
        
        print(f"📊 数据库初始化状态: {init_status['status']}")
        print(f"📋 现有表数量: {len(init_status.get('existing_tables', []))}")
        print(f"❌ 缺失表数量: {len(init_status.get('missing_tables', []))}")
        print(f"👤 管理员用户数: {init_status.get('admin_users_count', 0)}")
        
        if init_status.get('initialization_complete', False):
            print("✅ 数据库初始化已完成")
            return True
        else:
            print("❌ 数据库初始化未完成")
            if init_status.get('missing_tables'):
                print(f"   缺失表: {init_status['missing_tables']}")
            return False
            
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 检查过程中发生错误: {e}")
        return False


async def wait_for_initialization(max_wait_time: int = 300, check_interval: int = 5):
    """等待初始化完成"""
    print(f"等待数据库初始化完成...")
    print(f"最大等待时间: {max_wait_time}秒")
    print(f"检查间隔: {check_interval}秒")
    print("-" * 40)
    
    import time
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        if await check_initialization_status():
            elapsed = time.time() - start_time
            print(f"🎉 初始化完成，耗时: {elapsed:.2f}秒")
            return True
        
        print(f"⏳ 初始化未完成，{check_interval}秒后重试...")
        await asyncio.sleep(check_interval)
    
    print(f"❌ 初始化在 {max_wait_time} 秒内未完成")
    return False


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="检查数据库初始化状态")
    parser.add_argument(
        "--wait", "-w",
        action="store_true",
        help="等待初始化完成"
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=300,
        help="最大等待时间（秒），默认300秒"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=5,
        help="检查间隔（秒），默认5秒"
    )
    
    args = parser.parse_args()
    
    if args.wait:
        success = await wait_for_initialization(args.timeout, args.interval)
    else:
        success = await check_initialization_status()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)