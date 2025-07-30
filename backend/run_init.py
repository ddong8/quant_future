#!/usr/bin/env python3
"""
数据库初始化运行脚本
提供完整的初始化流程管理和错误处理
"""
import sys
import os
import asyncio
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class InitializationRunner:
    """初始化运行器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.init_marker = Path("/var/lib/db-init/initialized")
        self.log_file = Path("/var/log/trading/init.log")
        
        # 确保目录存在
        self.init_marker.parent.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        
        print(log_message)
        
        # 写入日志文件
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_message + "\n")
        except Exception as e:
            print(f"写入日志文件失败: {e}")
    
    def check_already_initialized(self) -> bool:
        """检查是否已经初始化"""
        if self.init_marker.exists():
            self.log("发现初始化标记文件，跳过初始化")
            return True
        return False
    
    async def wait_for_databases(self) -> bool:
        """等待数据库就绪"""
        self.log("等待数据库服务就绪...")
        
        try:
            from app.services.health_check_service import health_checker
            
            # 等待数据库就绪
            db_ready = await health_checker.wait_for_database_ready(
                max_wait_time=60,
                check_interval=2
            )
            
            if not db_ready:
                self.log("数据库未在指定时间内就绪", "ERROR")
                return False
            
            self.log("数据库已就绪")
            return True
            
        except Exception as e:
            self.log(f"等待数据库就绪时发生错误: {e}", "ERROR")
            return False
    
    async def perform_health_check(self) -> bool:
        """执行健康检查"""
        self.log("执行全面健康检查...")
        
        try:
            from app.services.health_check_service import health_checker
            
            health_result = await health_checker.perform_comprehensive_health_check()
            
            self.log(f"整体健康状态: {health_result['overall_status']}")
            
            # 记录各服务状态
            for service, result in health_result['checks'].items():
                self.log(f"  {service}: {result['status']} ({result['response_time_ms']:.2f}ms)")
            
            if health_result['overall_status'] == 'critical':
                self.log("关键服务健康检查失败", "ERROR")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"健康检查时发生错误: {e}", "ERROR")
            return False
    
    def run_database_initialization(self) -> bool:
        """运行数据库初始化"""
        self.log("开始数据库初始化...")
        
        try:
            # 导入并运行初始化脚本
            import subprocess
            
            result = subprocess.run(
                [sys.executable, "init_db.py"],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                self.log("数据库初始化脚本执行成功")
                self.log(f"输出: {result.stdout}")
                return True
            else:
                self.log(f"数据库初始化脚本执行失败: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("数据库初始化脚本执行超时", "ERROR")
            return False
        except Exception as e:
            self.log(f"运行数据库初始化时发生错误: {e}", "ERROR")
            return False
    
    async def verify_initialization(self) -> bool:
        """验证初始化结果"""
        self.log("验证初始化结果...")
        
        try:
            from app.services.health_check_service import health_checker
            
            init_status = await health_checker.check_database_initialization_status()
            
            self.log(f"初始化状态: {init_status['status']}")
            self.log(f"现有表: {len(init_status.get('existing_tables', []))}")
            self.log(f"缺失表: {len(init_status.get('missing_tables', []))}")
            self.log(f"管理员用户: {init_status.get('admin_users_count', 0)}")
            
            if init_status.get('initialization_complete', False):
                self.log("初始化验证通过")
                return True
            else:
                self.log("初始化验证失败", "ERROR")
                if init_status.get('missing_tables'):
                    self.log(f"缺失表: {init_status['missing_tables']}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"验证初始化时发生错误: {e}", "ERROR")
            return False
    
    def create_init_marker(self):
        """创建初始化标记"""
        try:
            with open(self.init_marker, "w") as f:
                f.write(f"initialized_at={time.time()}\n")
                f.write(f"initialized_by=run_init.py\n")
            self.log("创建初始化标记文件")
        except Exception as e:
            self.log(f"创建初始化标记失败: {e}", "ERROR")
    
    async def run_full_initialization(self) -> bool:
        """运行完整的初始化流程"""
        self.log("开始完整的数据库初始化流程")
        
        # 检查是否已经初始化
        if self.check_already_initialized():
            return True
        
        # 步骤1: 等待数据库就绪
        if not await self.wait_for_databases():
            return False
        
        # 步骤2: 执行健康检查
        if not await self.perform_health_check():
            return False
        
        # 步骤3: 运行数据库初始化
        if not self.run_database_initialization():
            return False
        
        # 步骤4: 验证初始化结果
        if not await self.verify_initialization():
            return False
        
        # 步骤5: 创建初始化标记
        self.create_init_marker()
        
        elapsed_time = time.time() - self.start_time
        self.log(f"数据库初始化完成，总耗时: {elapsed_time:.2f}秒")
        
        return True


async def main():
    """主函数"""
    runner = InitializationRunner()
    
    try:
        success = await runner.run_full_initialization()
        
        if success:
            runner.log("🎉 数据库初始化流程成功完成")
            return 0
        else:
            runner.log("❌ 数据库初始化流程失败", "ERROR")
            return 1
            
    except KeyboardInterrupt:
        runner.log("初始化流程被用户中断", "WARNING")
        return 130
    except Exception as e:
        runner.log(f"初始化流程发生未预期错误: {e}", "ERROR")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)