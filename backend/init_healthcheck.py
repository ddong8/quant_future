#!/usr/bin/env python3
"""
初始化容器健康检查脚本
用于检查初始化容器的状态
"""
import sys
from pathlib import Path


def check_init_container_health():
    """检查初始化容器健康状态"""
    init_marker = Path("/var/lib/db-init/initialized")
    log_file = Path("/var/log/trading/init.log")
    
    # 检查初始化标记文件
    if init_marker.exists():
        print("✅ 初始化已完成")
        return 0
    
    # 检查日志文件是否存在且有内容
    if log_file.exists() and log_file.stat().st_size > 0:
        # 读取最后几行日志
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    print(f"📝 最新日志: {last_line}")
                    
                    # 检查是否有错误
                    if "[ERROR]" in last_line:
                        print("❌ 发现错误日志")
                        return 1
                    
                    print("⏳ 初始化进行中...")
                    return 0
        except Exception as e:
            print(f"❌ 读取日志文件失败: {e}")
            return 1
    
    print("⏳ 初始化尚未开始或日志文件不存在")
    return 0


if __name__ == "__main__":
    sys.exit(check_init_container_health())