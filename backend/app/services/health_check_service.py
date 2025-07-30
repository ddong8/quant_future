"""
数据库健康检查服务
提供全面的数据库连接和状态检查功能
"""
import time
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import logging

from ..core.database_manager import db_manager
from ..core.database import get_influx_client, get_redis_client
from ..core.config import settings

logger = logging.getLogger(__name__)


class DatabaseHealthChecker:
    """数据库健康检查器"""
    
    def __init__(self):
        self.check_timeout = 10  # 检查超时时间（秒）
        self.warning_threshold = 1000  # 响应时间警告阈值（毫秒）
        self.critical_threshold = 5000  # 响应时间严重阈值（毫秒）
    
    async def check_postgresql_health(self) -> Dict[str, Any]:
        """检查 PostgreSQL 数据库健康状态"""
        start_time = time.time()
        
        try:
            with db_manager.get_db_session() as db:
                # 执行简单查询测试连接
                result = db.execute(text("SELECT 1 as test")).scalar()
                
                if result != 1:
                    raise Exception("Database query returned unexpected result")
                
                # 检查数据库版本
                version_result = db.execute(text("SELECT version()")).scalar()
                
                # 检查连接数
                connection_count = db.execute(text("""
                    SELECT count(*) 
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                """)).scalar()
                
                # 检查数据库大小
                db_size_result = db.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """)).scalar()
                
                response_time = (time.time() - start_time) * 1000
                
                # 确定状态
                if response_time > self.critical_threshold:
                    status = "critical"
                elif response_time > self.warning_threshold:
                    status = "warning"
                else:
                    status = "healthy"
                
                return {
                    "service": "postgresql",
                    "status": status,
                    "response_time_ms": round(response_time, 2),
                    "connection_count": connection_count,
                    "database_size": db_size_result,
                    "version": version_result.split()[1] if version_result else "unknown",
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"PostgreSQL 响应时间: {response_time:.2f}ms"
                }
                
        except OperationalError as e:
            return {
                "service": "postgresql",
                "status": "critical",
                "response_time_ms": (time.time() - start_time) * 1000,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"PostgreSQL 连接失败: {str(e)}"
            }
        except Exception as e:
            return {
                "service": "postgresql",
                "status": "critical",
                "response_time_ms": (time.time() - start_time) * 1000,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"PostgreSQL 检查失败: {str(e)}"
            }
    
    async def check_influxdb_health(self) -> Dict[str, Any]:
        """检查 InfluxDB 健康状态"""
        start_time = time.time()
        
        try:
            client = get_influx_client()
            
            # 测试连接
            health = client.health()
            
            # 检查组织和存储桶
            orgs_api = client.organizations_api()
            org = orgs_api.find_organizations(org=settings.INFLUXDB_ORG)
            
            buckets_api = client.buckets_api()
            bucket = buckets_api.find_bucket_by_name(settings.INFLUXDB_BUCKET)
            
            response_time = (time.time() - start_time) * 1000
            
            # 确定状态
            if health.status != "pass":
                status = "critical"
            elif response_time > self.critical_threshold:
                status = "critical"
            elif response_time > self.warning_threshold:
                status = "warning"
            else:
                status = "healthy"
            
            return {
                "service": "influxdb",
                "status": status,
                "response_time_ms": round(response_time, 2),
                "health_status": health.status,
                "organization": settings.INFLUXDB_ORG,
                "bucket": settings.INFLUXDB_BUCKET,
                "org_exists": len(org) > 0,
                "bucket_exists": bucket is not None,
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"InfluxDB 响应时间: {response_time:.2f}ms, 状态: {health.status}"
            }
            
        except Exception as e:
            return {
                "service": "influxdb",
                "status": "critical",
                "response_time_ms": (time.time() - start_time) * 1000,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"InfluxDB 检查失败: {str(e)}"
            }
    
    async def check_redis_health(self) -> Dict[str, Any]:
        """检查 Redis 健康状态"""
        start_time = time.time()
        
        try:
            redis_client = get_redis_client()
            
            # 测试连接
            pong = redis_client.ping()
            
            if not pong:
                raise Exception("Redis ping failed")
            
            # 获取 Redis 信息
            info = redis_client.info()
            
            # 测试读写操作
            test_key = "health_check_test"
            redis_client.set(test_key, "test_value", ex=60)
            test_value = redis_client.get(test_key)
            redis_client.delete(test_key)
            
            if test_value != "test_value":
                raise Exception("Redis read/write test failed")
            
            response_time = (time.time() - start_time) * 1000
            
            # 确定状态
            if response_time > self.critical_threshold:
                status = "critical"
            elif response_time > self.warning_threshold:
                status = "warning"
            else:
                status = "healthy"
            
            return {
                "service": "redis",
                "status": status,
                "response_time_ms": round(response_time, 2),
                "version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Redis 响应时间: {response_time:.2f}ms"
            }
            
        except Exception as e:
            return {
                "service": "redis",
                "status": "critical",
                "response_time_ms": (time.time() - start_time) * 1000,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Redis 检查失败: {str(e)}"
            }
    
    async def check_database_initialization_status(self) -> Dict[str, Any]:
        """检查数据库初始化状态"""
        start_time = time.time()
        
        try:
            with db_manager.get_db_session() as db:
                # 检查关键表是否存在
                required_tables = [
                    'users', 'strategies', 'orders', 'positions', 
                    'backtests', 'risk_rules', 'system_logs'
                ]
                
                existing_tables = []
                missing_tables = []
                
                for table in required_tables:
                    try:
                        result = db.execute(text(f"""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_name = '{table}'
                            )
                        """)).scalar()
                        
                        if result:
                            existing_tables.append(table)
                        else:
                            missing_tables.append(table)
                    except Exception as e:
                        logger.warning(f"检查表 {table} 时出错: {e}")
                        missing_tables.append(table)
                
                # 检查是否有管理员用户
                admin_count = 0
                try:
                    admin_count = db.execute(text("""
                        SELECT COUNT(*) FROM users WHERE role = 'ADMIN'
                    """)).scalar()
                except Exception:
                    pass
                
                response_time = (time.time() - start_time) * 1000
                
                # 确定状态
                if missing_tables:
                    status = "critical"
                elif admin_count == 0:
                    status = "warning"
                else:
                    status = "healthy"
                
                return {
                    "service": "database_initialization",
                    "status": status,
                    "response_time_ms": round(response_time, 2),
                    "existing_tables": existing_tables,
                    "missing_tables": missing_tables,
                    "admin_users_count": admin_count,
                    "initialization_complete": len(missing_tables) == 0 and admin_count > 0,
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"数据库初始化状态: {'完成' if len(missing_tables) == 0 else '未完成'}"
                }
                
        except Exception as e:
            return {
                "service": "database_initialization",
                "status": "critical",
                "response_time_ms": (time.time() - start_time) * 1000,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"数据库初始化状态检查失败: {str(e)}"
            }
    
    async def perform_comprehensive_health_check(self) -> Dict[str, Any]:
        """执行全面的健康检查"""
        start_time = time.time()
        
        # 并行执行所有检查
        checks = await asyncio.gather(
            self.check_postgresql_health(),
            self.check_influxdb_health(),
            self.check_redis_health(),
            self.check_database_initialization_status(),
            return_exceptions=True
        )
        
        # 处理检查结果
        results = {}
        overall_status = "healthy"
        
        for check in checks:
            if isinstance(check, Exception):
                logger.error(f"健康检查异常: {check}")
                continue
            
            service_name = check["service"]
            results[service_name] = check
            
            # 更新整体状态
            if check["status"] == "critical":
                overall_status = "critical"
            elif check["status"] == "warning" and overall_status == "healthy":
                overall_status = "warning"
        
        total_time = (time.time() - start_time) * 1000
        
        return {
            "overall_status": overall_status,
            "total_response_time_ms": round(total_time, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results,
            "summary": {
                "total_checks": len(results),
                "healthy": sum(1 for r in results.values() if r["status"] == "healthy"),
                "warning": sum(1 for r in results.values() if r["status"] == "warning"),
                "critical": sum(1 for r in results.values() if r["status"] == "critical")
            }
        }
    
    async def wait_for_database_ready(self, max_wait_time: int = 60, check_interval: int = 2) -> bool:
        """等待数据库就绪"""
        logger.info(f"等待数据库就绪，最大等待时间: {max_wait_time}秒")
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # 检查 PostgreSQL
                pg_check = await self.check_postgresql_health()
                if pg_check["status"] in ["healthy", "warning"]:
                    logger.info("PostgreSQL 数据库已就绪")
                    return True
                
                logger.debug(f"PostgreSQL 状态: {pg_check['status']}, 等待中...")
                
            except Exception as e:
                logger.debug(f"数据库连接测试失败: {e}")
            
            await asyncio.sleep(check_interval)
        
        logger.error(f"数据库在 {max_wait_time} 秒内未就绪")
        return False
    
    def get_health_check_summary(self, time_window_minutes: int = 5) -> Dict[str, Any]:
        """获取健康检查摘要"""
        try:
            with db_manager.get_db_session() as db:
                # 获取指定时间窗口内的健康检查记录
                since_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
                
                # 这里需要根据实际的健康检查记录表结构来实现
                # 暂时返回基本信息
                return {
                    "time_window_minutes": time_window_minutes,
                    "summary": "健康检查摘要功能需要配合数据库记录表实现",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"获取健康检查摘要失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# 创建全局健康检查器实例
health_checker = DatabaseHealthChecker()