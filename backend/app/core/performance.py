"""
性能优化工具
"""
import time
import asyncio
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
from contextlib import contextmanager
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import text, event
from sqlalchemy.engine import Engine

from app.core.logging import logger
from app.core.cache import cache_manager, query_cache


class QueryOptimizer:
    """查询优化器"""
    
    @staticmethod
    def optimize_user_queries(db: Session):
        """优化用户相关查询"""
        # 预加载用户策略
        return db.query(User).options(
            selectinload(User.strategies),
            selectinload(User.backtests)
        )
    
    @staticmethod
    def optimize_strategy_queries(db: Session):
        """优化策略相关查询"""
        # 预加载策略回测和用户信息
        return db.query(Strategy).options(
            joinedload(Strategy.user),
            selectinload(Strategy.backtests)
        )
    
    @staticmethod
    def optimize_backtest_queries(db: Session):
        """优化回测相关查询"""
        # 预加载回测策略和用户信息
        return db.query(Backtest).options(
            joinedload(Backtest.strategy).joinedload(Strategy.user),
            joinedload(Backtest.user)
        )
    
    @staticmethod
    def optimize_trading_queries(db: Session):
        """优化交易相关查询"""
        # 预加载订单用户和策略信息
        return db.query(Order).options(
            joinedload(Order.user),
            joinedload(Order.strategy)
        )


class DatabaseOptimizer:
    """数据库优化器"""
    
    def __init__(self):
        self.slow_query_threshold = 1.0  # 慢查询阈值（秒）
        self.query_stats = {}
    
    def setup_query_monitoring(self, engine: Engine):
        """设置查询监控"""
        
        @event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            
            # 记录慢查询
            if total > self.slow_query_threshold:
                logger.warning(f"慢查询检测: {total:.3f}s - {statement[:200]}...")
            
            # 统计查询性能
            query_hash = hash(statement)
            if query_hash not in self.query_stats:
                self.query_stats[query_hash] = {
                    'statement': statement[:200],
                    'count': 0,
                    'total_time': 0,
                    'avg_time': 0,
                    'max_time': 0
                }
            
            stats = self.query_stats[query_hash]
            stats['count'] += 1
            stats['total_time'] += total
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['max_time'] = max(stats['max_time'], total)
    
    def get_query_stats(self) -> Dict[str, Any]:
        """获取查询统计"""
        return dict(self.query_stats)
    
    def optimize_table_stats(self, db: Session):
        """优化表统计信息"""
        try:
            # PostgreSQL
            db.execute(text("ANALYZE;"))
            logger.info("表统计信息已更新")
        except Exception as e:
            logger.error(f"更新表统计信息失败: {e}")
    
    def vacuum_tables(self, db: Session):
        """清理表空间"""
        try:
            # PostgreSQL
            db.execute(text("VACUUM;"))
            logger.info("表空间清理完成")
        except Exception as e:
            logger.error(f"表空间清理失败: {e}")


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {}
        self.thresholds = {
            'response_time': 2.0,  # 响应时间阈值（秒）
            'memory_usage': 0.8,   # 内存使用率阈值
            'cpu_usage': 0.8       # CPU使用率阈值
        }
    
    @contextmanager
    def measure_time(self, operation: str):
        """测量操作时间"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_metric(f"{operation}_time", duration)
            
            if duration > self.thresholds['response_time']:
                logger.warning(f"性能警告: {operation} 耗时 {duration:.3f}s")
    
    def record_metric(self, name: str, value: float):
        """记录性能指标"""
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            'value': value,
            'timestamp': time.time()
        })
        
        # 保留最近1000个数据点
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-1000:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        result = {}
        for name, values in self.metrics.items():
            if values:
                recent_values = [v['value'] for v in values[-100:]]  # 最近100个值
                result[name] = {
                    'current': values[-1]['value'],
                    'average': sum(recent_values) / len(recent_values),
                    'max': max(recent_values),
                    'min': min(recent_values),
                    'count': len(values)
                }
        return result
    
    def check_performance_alerts(self) -> List[Dict[str, Any]]:
        """检查性能警报"""
        alerts = []
        metrics = self.get_metrics()
        
        for metric_name, metric_data in metrics.items():
            if 'time' in metric_name and metric_data['average'] > self.thresholds['response_time']:
                alerts.append({
                    'type': 'response_time',
                    'metric': metric_name,
                    'value': metric_data['average'],
                    'threshold': self.thresholds['response_time'],
                    'message': f"{metric_name} 平均响应时间过长: {metric_data['average']:.3f}s"
                })
        
        return alerts


def performance_monitor(operation: str):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            monitor = PerformanceMonitor()
            with monitor.measure_time(operation):
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            monitor = PerformanceMonitor()
            with monitor.measure_time(operation):
                return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


class BatchProcessor:
    """批处理器"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
    
    def process_in_batches(self, items: List[Any], 
                          processor: Callable[[List[Any]], Any]) -> List[Any]:
        """批量处理数据"""
        results = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_result = processor(batch)
            results.extend(batch_result if isinstance(batch_result, list) else [batch_result])
        
        return results
    
    def bulk_insert(self, db: Session, model_class: Any, data: List[Dict[str, Any]]):
        """批量插入数据"""
        try:
            db.bulk_insert_mappings(model_class, data)
            db.commit()
            logger.info(f"批量插入 {len(data)} 条记录到 {model_class.__name__}")
        except Exception as e:
            db.rollback()
            logger.error(f"批量插入失败: {e}")
            raise
    
    def bulk_update(self, db: Session, model_class: Any, data: List[Dict[str, Any]]):
        """批量更新数据"""
        try:
            db.bulk_update_mappings(model_class, data)
            db.commit()
            logger.info(f"批量更新 {len(data)} 条记录在 {model_class.__name__}")
        except Exception as e:
            db.rollback()
            logger.error(f"批量更新失败: {e}")
            raise


class ConnectionPoolOptimizer:
    """连接池优化器"""
    
    @staticmethod
    def get_optimal_pool_settings(max_connections: int = 20) -> Dict[str, Any]:
        """获取最优连接池设置"""
        return {
            'pool_size': max_connections // 2,
            'max_overflow': max_connections // 2,
            'pool_timeout': 30,
            'pool_recycle': 3600,  # 1小时回收连接
            'pool_pre_ping': True,  # 连接前ping检查
        }
    
    @staticmethod
    def monitor_connection_pool(engine: Engine) -> Dict[str, Any]:
        """监控连接池状态"""
        pool = engine.pool
        return {
            'size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'invalid': pool.invalid()
        }


class MemoryOptimizer:
    """内存优化器"""
    
    @staticmethod
    def optimize_query_result(query_result: Any) -> Any:
        """优化查询结果内存使用"""
        # 如果是大结果集，使用生成器
        if hasattr(query_result, '__iter__') and not isinstance(query_result, (str, bytes)):
            return (item for item in query_result)
        return query_result
    
    @staticmethod
    def clear_session_cache(db: Session):
        """清理会话缓存"""
        db.expunge_all()
        db.close()
    
    @staticmethod
    def optimize_large_dataset_processing(data: List[Any], 
                                        processor: Callable[[Any], Any]) -> List[Any]:
        """优化大数据集处理"""
        # 使用生成器表达式减少内存使用
        return [processor(item) for item in data]


# 全局实例
query_optimizer = QueryOptimizer()
db_optimizer = DatabaseOptimizer()
performance_monitor = PerformanceMonitor()
batch_processor = BatchProcessor()
memory_optimizer = MemoryOptimizer()


def get_query_optimizer() -> QueryOptimizer:
    """获取查询优化器"""
    return query_optimizer


def get_db_optimizer() -> DatabaseOptimizer:
    """获取数据库优化器"""
    return db_optimizer


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器"""
    return performance_monitor


def get_batch_processor() -> BatchProcessor:
    """获取批处理器"""
    return batch_processor


def get_memory_optimizer() -> MemoryOptimizer:
    """获取内存优化器"""
    return memory_optimizer