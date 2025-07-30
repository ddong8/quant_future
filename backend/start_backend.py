#!/usr/bin/env python3
"""
后端服务启动脚本
提供完整的启动流程管理和预检查
"""
import sys
import os
import asyncio
import time
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class BackendStarter:
    """后端服务启动器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.log_file = Path("/var/log/trading/backend_startup.log")
        
        # 确保日志目录存在
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
    
    async def wait_for_initialization(self) -> bool:
        """等待数据库初始化完成"""
        self.log("等待数据库初始化完成...")
        
        try:
            # 使用现有的初始化状态检查脚本
            result = subprocess.run(
                [sys.executable, "check_init_status.py", "--wait", "--timeout", "300"],
                capture_output=True,
                text=True,
                timeout=320  # 比脚本超时时间多20秒
            )
            
            if result.returncode == 0:
                self.log("数据库初始化已完成")
                return True
            else:
                self.log(f"数据库初始化等待失败: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("等待数据库初始化超时", "ERROR")
            return False
        except Exception as e:
            self.log(f"等待数据库初始化时发生错误: {e}", "ERROR")
            return False
    
    async def perform_startup_health_check(self) -> bool:
        """执行启动前健康检查"""
        self.log("执行启动前健康检查...")
        
        try:
            # 使用现有的数据库状态检查脚本
            result = subprocess.run(
                [sys.executable, "check_db_status.py"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log("启动前健康检查通过")
                self.log(f"健康检查输出: {result.stdout}")
                return True
            else:
                self.log(f"启动前健康检查失败: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("启动前健康检查超时", "ERROR")
            return False
        except Exception as e:
            self.log(f"启动前健康检查时发生错误: {e}", "ERROR")
            return False
    
    def validate_environment(self) -> bool:
        """验证环境变量"""
        self.log("验证环境变量...")
        
        required_env_vars = [
            'DATABASE_URL',
            'REDIS_URL',
            'INFLUXDB_URL',
            'SECRET_KEY'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.log(f"缺少必需的环境变量: {missing_vars}", "ERROR")
            return False
        
        self.log("环境变量验证通过")
        return True
    
    def get_uvicorn_command(self) -> list:
        """获取 Uvicorn 启动命令"""
        # 从环境变量获取配置
        host = os.getenv('UVICORN_HOST', '0.0.0.0')
        port = int(os.getenv('UVICORN_PORT', '8000'))
        workers = int(os.getenv('WORKER_PROCESSES', '1'))
        reload = os.getenv('DEBUG', 'false').lower() == 'true'
        log_level = os.getenv('LOG_LEVEL', 'info').lower()
        
        # 构建命令
        cmd = [
            'uvicorn',
            'app.main:app',
            '--host', host,
            '--port', str(port),
            '--log-level', log_level
        ]
        
        # 开发环境启用热重载
        if reload:
            cmd.append('--reload')
            self.log(f"启动开发模式服务器: {host}:{port} (热重载已启用)")
        else:
            # 生产环境使用多个worker
            if workers > 1:
                cmd.extend(['--workers', str(workers)])
            self.log(f"启动生产模式服务器: {host}:{port} (workers: {workers})")
        
        return cmd
    
    def start_uvicorn_server(self) -> bool:
        """启动 Uvicorn 服务器"""
        self.log("启动 FastAPI 服务器...")
        
        try:
            cmd = self.get_uvicorn_command()
            self.log(f"执行命令: {' '.join(cmd)}")
            
            # 启动服务器（这会阻塞直到服务器停止）
            result = subprocess.run(cmd)
            
            if result.returncode == 0:
                self.log("服务器正常退出")
                return True
            else:
                self.log(f"服务器异常退出，退出码: {result.returncode}", "ERROR")
                return False
                
        except KeyboardInterrupt:
            self.log("服务器被用户中断", "WARNING")
            return True
        except Exception as e:
            self.log(f"启动服务器时发生错误: {e}", "ERROR")
            return False
    
    async def run_startup_sequence(self) -> bool:
        """运行完整的启动序列"""
        self.log("开始后端服务启动序列")
        
        # 步骤1: 验证环境变量
        if not self.validate_environment():
            return False
        
        # 步骤2: 等待数据库初始化完成
        if not await self.wait_for_initialization():
            return False
        
        # 步骤3: 执行启动前健康检查
        if not await self.perform_startup_health_check():
            return False
        
        elapsed_time = time.time() - self.start_time
        self.log(f"启动前检查完成，耗时: {elapsed_time:.2f}秒")
        
        # 步骤4: 启动服务器
        return self.start_uvicorn_server()


async def main():
    """主函数"""
    starter = BackendStarter()
    
    try:
        success = await starter.run_startup_sequence()
        
        if success:
            starter.log("🎉 后端服务启动序列成功完成")
            return 0
        else:
            starter.log("❌ 后端服务启动序列失败", "ERROR")
            return 1
            
    except KeyboardInterrupt:
        starter.log("启动序列被用户中断", "WARNING")
        return 130
    except Exception as e:
        starter.log(f"启动序列发生未预期错误: {e}", "ERROR")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)