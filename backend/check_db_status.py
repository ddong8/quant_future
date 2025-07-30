#!/usr/bin/env python3
"""
数据库状态检查脚本
用于验证数据库初始化状态和健康状况
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def main():
    """主函数"""
    print("数据库状态检查")
    print("=" * 50)
    
    try:
        from app.services.health_check_service import health_checker
        
        # 执行全面健康检查
        print("执行全面健康检查...")
        health_result = await health_checker.perform_comprehensive_health_check()
        
        # 显示结果
        print(f"\n整体状态: {health_result['overall_status']}")
        print(f"检查耗时: {health_result['total_response_time_ms']:.2f}ms")
        print(f"检查时间: {health_result['timestamp']}")
        
        print(f"\n检查摘要:")
        summary = health_result['summary']
        print(f"  总检查项: {summary['total_checks']}")
        print(f"  健康: {summary['healthy']}")
        print(f"  警告: {summary['warning']}")
        print(f"  严重: {summary['critical']}")
        
        print(f"\n详细检查结果:")
        for service, result in health_result['checks'].items():
            status_icon = {
                'healthy': '✅',
                'warning': '⚠️',
                'critical': '❌'
            }.get(result['status'], '❓')
            
            print(f"  {status_icon} {service}: {result['status']}")
            print(f"     响应时间: {result['response_time_ms']:.2f}ms")
            print(f"     消息: {result['message']}")
            
            if 'error' in result:
                print(f"     错误: {result['error']}")
            
            print()
        
        # 返回适当的退出码
        if health_result['overall_status'] == 'critical':
            print("❌ 数据库状态检查失败")
            return 1
        elif health_result['overall_status'] == 'warning':
            print("⚠️  数据库状态检查通过，但有警告")
            return 0
        else:
            print("✅ 数据库状态检查完全通过")
            return 0
            
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("请确保已安装所有依赖包")
        return 2
    except Exception as e:
        print(f"❌ 检查过程中发生错误: {e}")
        return 3


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)