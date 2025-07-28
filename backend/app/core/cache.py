"""
缓存管理模块
"""
import json
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import redis
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=False  # 支持二进制数据
        )
        self.default_ttl = 3600  # 默认1小时过期
        
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            data = self.redis_client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"缓存获取失败: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            ttl = ttl or self.default_ttl
            data = pickle.dumps(value)
            return self.redis_client.setex(key, ttl, data)
        except Exception as e:
            logger.error(f"缓存设置失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"缓存删除失败: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"缓存检查失败: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"缓存模式清除失败: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            info = self.redis_client.info()
            return {
                'used_memory': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses'),
                'hit_rate': info.get('keyspace_hits', 0) / max(
                    info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1
                )
            }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {}


# 全局缓存管理器实例
cache_manager = CacheManager()


def cache_result(prefix: str, ttl: Optional[int] = None, 
                key_func: Optional[callable] = None):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager._generate_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            logger.debug(f"缓存设置: {cache_key}")
            
            return result
        return wrapper
    return decorator


class QueryCache:
    """数据库查询缓存"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.query_ttl = 300  # 查询缓存5分钟
    
    def cache_query(self, query_key: str, query_func: callable, 
                   ttl: Optional[int] = None) -> Any:
        """缓存数据库查询结果"""
        ttl = ttl or self.query_ttl
        
        # 检查缓存
        cached_result = self.cache.get(query_key)
        if cached_result is not None:
            return cached_result
        
        # 执行查询并缓存
        result = query_func()
        self.cache.set(query_key, result, ttl)
        
        return result
    
    def invalidate_user_cache(self, user_id: str):
        """清除用户相关缓存"""
        patterns = [
            f"user:{user_id}:*",
            f"strategies:user:{user_id}:*",
            f"backtests:user:{user_id}:*",
            f"orders:user:{user_id}:*",
            f"positions:user:{user_id}:*"
        ]
        
        for pattern in patterns:
            self.cache.clear_pattern(pattern)
    
    def invalidate_strategy_cache(self, strategy_id: str, user_id: str):
        """清除策略相关缓存"""
        patterns = [
            f"strategy:{strategy_id}:*",
            f"strategies:user:{user_id}:*",
            f"backtests:strategy:{strategy_id}:*"
        ]
        
        for pattern in patterns:
            self.cache.clear_pattern(pattern)
    
    def invalidate_market_cache(self, symbol: str):
        """清除市场数据缓存"""
        patterns = [
            f"market:{symbol}:*",
            f"quote:{symbol}:*",
            f"kline:{symbol}:*"
        ]
        
        for pattern in patterns:
            self.cache.clear_pattern(pattern)


# 全局查询缓存实例
query_cache = QueryCache(cache_manager)


class APIResponseCache:
    """API响应缓存"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.response_ttl = 60  # API响应缓存1分钟
    
    def cache_response(self, cache_key: str, response_data: Any, 
                      ttl: Optional[int] = None) -> bool:
        """缓存API响应"""
        ttl = ttl or self.response_ttl
        return self.cache.set(cache_key, response_data, ttl)
    
    def get_cached_response(self, cache_key: str) -> Optional[Any]:
        """获取缓存的API响应"""
        return self.cache.get(cache_key)
    
    def generate_api_key(self, endpoint: str, user_id: str, 
                        params: Dict[str, Any]) -> str:
        """生成API缓存键"""
        return self.cache._generate_key(f"api:{endpoint}:{user_id}", **params)


# 全局API响应缓存实例
api_cache = APIResponseCache(cache_manager)


class SessionCache:
    """会话缓存"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.session_ttl = 86400  # 会话缓存24小时
    
    def set_user_session(self, user_id: str, session_data: Dict[str, Any]) -> bool:
        """设置用户会话"""
        key = f"session:user:{user_id}"
        return self.cache.set(key, session_data, self.session_ttl)
    
    def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户会话"""
        key = f"session:user:{user_id}"
        return self.cache.get(key)
    
    def delete_user_session(self, user_id: str) -> bool:
        """删除用户会话"""
        key = f"session:user:{user_id}"
        return self.cache.delete(key)
    
    def set_strategy_session(self, strategy_id: str, session_data: Dict[str, Any]) -> bool:
        """设置策略会话"""
        key = f"session:strategy:{strategy_id}"
        return self.cache.set(key, session_data, self.session_ttl)
    
    def get_strategy_session(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """获取策略会话"""
        key = f"session:strategy:{strategy_id}"
        return self.cache.get(key)


# 全局会话缓存实例
session_cache = SessionCache(cache_manager)


class RateLimitCache:
    """限流缓存"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """检查限流"""
        try:
            current = self.cache.redis_client.get(key)
            if current is None:
                # 首次请求
                self.cache.redis_client.setex(key, window, 1)
                return True
            
            current_count = int(current)
            if current_count >= limit:
                return False
            
            # 增加计数
            self.cache.redis_client.incr(key)
            return True
            
        except Exception as e:
            logger.error(f"限流检查失败: {e}")
            return True  # 出错时允许通过
    
    def get_remaining_requests(self, key: str, limit: int) -> int:
        """获取剩余请求次数"""
        try:
            current = self.cache.redis_client.get(key)
            if current is None:
                return limit
            
            current_count = int(current)
            return max(0, limit - current_count)
            
        except Exception as e:
            logger.error(f"获取剩余请求次数失败: {e}")
            return limit


# 全局限流缓存实例
rate_limit_cache = RateLimitCache(cache_manager)


def get_cache_manager() -> CacheManager:
    """获取缓存管理器"""
    return cache_manager


def get_query_cache() -> QueryCache:
    """获取查询缓存"""
    return query_cache


def get_api_cache() -> APIResponseCache:
    """获取API缓存"""
    return api_cache


def get_session_cache() -> SessionCache:
    """获取会话缓存"""
    return session_cache


def get_rate_limit_cache() -> RateLimitCache:
    """获取限流缓存"""
    return rate_limit_cache