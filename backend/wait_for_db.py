#!/usr/bin/env python3
"""
等待数据库就绪脚本
用于容器启动时等待数据库服务可用
"""
import sys
import asyncio
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def wait_for_database(max_wait_time: int = 60, check_interval: int = 2, verbose: bool = True):
    """等待数据库就绪"""
    if verbose:
        print(f"等待数据库就绪...")
        print(f"最大等待时间: {max_wait_time}秒")
        print(f"检查间隔: {check_interval}秒")
        print("-" * 40)
    
    try:
        from app.services.health_check_service import health_checker
        
        # 等待数据库就绪
        is_ready = await health_checker.wait_for_database_ready(
            max_wait_time=max_wait_time,
            check_interval=check_interval
        )
        
        if is_ready:
            if verbose:
                print("✅ 数据库已就绪")
            
            # 额外检查初始化状态
            init_status = await health_checker.check_database_initialization_status()
            
            if verbose:
                print(f"📊 初始化状态: {init_status['status']}")
                print(f"📋 现有表: {len(init_status.get('existing_tables', []))}")
                print(f"❌ 缺失表: {len(init_status.get('missing_tables', []))}")
                print(f"👤 管理员用户: {init_status.get('admin_users_count', 0)}")
            
            return True
        else:
            if verbose:
                print(f"❌ 数据库在 {max_wait_time} 秒内未就绪")
            return False
            
    except ImportError as e:
        if verbose:
            print(f"❌ 导入模块失败: {e}")
            print("请确保已安装所有依赖包")
        return False
    except Exception as e:
        if verbose:
            print(f"❌ 等待过程中发生错误: {e}")
        return False


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="等待数据库就绪")
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=60,
        help="最大等待时间（秒），默认60秒"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=2,
        help="检查间隔（秒），默认2秒"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="静默模式，不输出详细信息"
    )
    parser.add_argument(
        "--check-init",
        action="store_true",
        help="同时检查数据库初始化状态"
    )
    
    args = parser.parse_args()
    
    # 等待数据库就绪
    is_ready = await wait_for_database(
        max_wait_time=args.timeout,
        check_interval=args.interval,
        verbose=not args.quiet
    )
    
    if not is_ready:
        return 1
    
    # 如果需要检查初始化状态
    if args.check_init:
        try:
            from app.services.health_check_service import health_checker
            
            init_status = await health_checker.check_database_initialization_status()
            
            if not args.quiet:
                print(f"🔍 检查初始化状态...")
                print(f"状态: {init_status['status']}")
                print(f"初始化完成: {init_status.get('initialization_complete', False)}")
            
            if init_status['status'] == 'critical':
                if not args.quiet:
                    print("❌ 数据库初始化状态检查失败")
                return 2
            elif init_status['status'] == 'warning':
                if not args.quiet:
                    print("⚠️  数据库初始化状态有警告")
                # 警告不影响退出码，继续执行
        
        except Exception as e:
            if not args.quiet:
                print(f"❌ 初始化状态检查失败: {e}")
            return 3
    
    if not args.quiet:
        print("🎉 数据库就绪检查完成")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)