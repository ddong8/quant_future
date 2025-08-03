"""
数据库查询优化服务
"""
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import text, func, and_, or_
from sqlalchemy.orm import Session, Query, joinedload, selectinload
from sqlalchemy.sql import Select
from datetime import datetime, timedelta
import logging
from contextlib import contextmanager
import time

from app.core.database import get_db
from app.models.order import Order
from app.models.position import Position
from app.models.transaction import Transaction
from app.models.market_data import MarketData
from app.models.backtest import Backtest
from app.models.strategy import Strategy

logger = logging.getLogger(__name__)

class QueryOptimizationService:
    """数据库查询优化服务"""
    
    def __init__(self):
        self.query_cache = {}
        self.slow_query_threshold = 1.0  # 1秒
        self.cache_ttl = 300  # 5分钟
    
    @contextmanager
    def query_timer(self, query_name: str):
        """查询计时器上下文管理器"""
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            if execution_time > self.slow_query_threshold:
                logger.warning(f"Slow query detected: {query_name} took {execution_time:.2f}s")
            else:
                logger.debug(f"Query {query_name} executed in {execution_time:.2f}s")
    
    def get_optimized_orders_query(
        self, 
        db: Session, 
        user_id: int,
        status: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Query:
        """获取优化的订单查询"""
        
        with self.query_timer("get_optimized_orders"):
            query = db.query(Order).filter(Order.user_id == user_id)
            
            # 使用索引优化的过滤条件
            if status:
                query = query.filter(Order.status == status)
            
            if symbol:
                query = query.filter(Order.symbol == symbol)
            
            if start_date:
                query = query.filter(Order.created_at >= start_date)
            
            if end_date:
                query = query.filter(Order.created_at <= end_date)
            
            # 使用索引排序
            query = query.order_by(Order.created_at.desc())
            
            # 分页
            query = query.offset(offset).limit(limit)
            
            return query
    
    def get_optimized_positions_query(
        self,
        db: Session,
        user_id: int,
        status: Optional[str] = None,
        symbol: Optional[str] = None,
        include_closed: bool = False
    ) -> Query:
        """获取优化的持仓查询"""
        
        with self.query_timer("get_optimized_positions"):
            query = db.query(Position).filter(Position.user_id == user_id)
            
            if not include_closed:
                query = query.filter(Position.status != 'closed')
            
            if status:
                query = query.filter(Position.status == status)
            
            if symbol:
                query = query.filter(Position.symbol == symbol)
            
            # 使用索引排序
            query = query.order_by(Position.updated_at.desc())
            
            return query
    
    def get_optimized_transactions_query(
        self,
        db: Session,
        user_id: int,
        transaction_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Query:
        """获取优化的交易记录查询"""
        
        with self.query_timer("get_optimized_transactions"):
            query = db.query(Transaction).filter(Transaction.user_id == user_id)
            
            if transaction_type:
                query = query.filter(Transaction.type == transaction_type)
            
            if start_date:
                query = query.filter(Transaction.created_at >= start_date)
            
            if end_date:
                query = query.filter(Transaction.created_at <= end_date)
            
            # 使用索引排序
            query = query.order_by(Transaction.created_at.desc())
            
            # 分页
            query = query.offset(offset).limit(limit)
            
            return query
    
    def get_optimized_market_data_query(
        self,
        db: Session,
        symbol: str,
        data_type: str = 'kline',
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> Query:
        """获取优化的市场数据查询"""
        
        with self.query_timer("get_optimized_market_data"):
            query = db.query(MarketData).filter(
                and_(
                    MarketData.symbol == symbol,
                    MarketData.data_type == data_type
                )
            )
            
            if start_time:
                query = query.filter(MarketData.timestamp >= start_time)
            
            if end_time:
                query = query.filter(MarketData.timestamp <= end_time)
            
            # 使用索引排序
            query = query.order_by(MarketData.timestamp.desc())
            
            # 限制结果数量
            query = query.limit(limit)
            
            return query
    
    def get_user_dashboard_data(self, db: Session, user_id: int) -> Dict[str, Any]:
        """获取用户仪表板数据（优化版本）"""
        
        with self.query_timer("get_user_dashboard_data"):
            # 使用单个查询获取多个统计数据
            result = db.execute(text("""
                SELECT 
                    (SELECT COUNT(*) FROM orders WHERE user_id = :user_id AND status = 'active') as active_orders,
                    (SELECT COUNT(*) FROM positions WHERE user_id = :user_id AND status = 'open') as open_positions,
                    (SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = :user_id AND type = 'deposit') as total_deposits,
                    (SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = :user_id AND type = 'withdrawal') as total_withdrawals,
                    (SELECT COUNT(*) FROM backtests WHERE user_id = :user_id AND status = 'completed') as completed_backtests
            """), {"user_id": user_id}).fetchone()
            
            return {
                "active_orders": result.active_orders,
                "open_positions": result.open_positions,
                "total_deposits": float(result.total_deposits),
                "total_withdrawals": float(result.total_withdrawals),
                "completed_backtests": result.completed_backtests,
                "net_deposits": float(result.total_deposits) - float(result.total_withdrawals)
            }
    
    def get_portfolio_summary(self, db: Session, user_id: int) -> Dict[str, Any]:
        """获取投资组合摘要（优化版本）"""
        
        with self.query_timer("get_portfolio_summary"):
            # 使用聚合查询获取投资组合数据
            result = db.execute(text("""
                SELECT 
                    symbol,
                    SUM(quantity) as total_quantity,
                    AVG(entry_price) as avg_entry_price,
                    SUM(unrealized_pnl) as total_unrealized_pnl,
                    SUM(realized_pnl) as total_realized_pnl
                FROM positions 
                WHERE user_id = :user_id AND status = 'open'
                GROUP BY symbol
                ORDER BY total_unrealized_pnl DESC
            """), {"user_id": user_id}).fetchall()
            
            portfolio_data = []
            total_unrealized_pnl = 0
            total_realized_pnl = 0
            
            for row in result:
                position_data = {
                    "symbol": row.symbol,
                    "quantity": float(row.total_quantity),
                    "avg_entry_price": float(row.avg_entry_price),
                    "unrealized_pnl": float(row.total_unrealized_pnl),
                    "realized_pnl": float(row.total_realized_pnl)
                }
                portfolio_data.append(position_data)
                total_unrealized_pnl += position_data["unrealized_pnl"]
                total_realized_pnl += position_data["realized_pnl"]
            
            return {
                "positions": portfolio_data,
                "total_unrealized_pnl": total_unrealized_pnl,
                "total_realized_pnl": total_realized_pnl,
                "total_pnl": total_unrealized_pnl + total_realized_pnl
            }
    
    def get_recent_activities(
        self, 
        db: Session, 
        user_id: int, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取最近活动（优化版本）"""
        
        with self.query_timer("get_recent_activities"):
            # 使用UNION查询合并多个表的数据
            result = db.execute(text("""
                (
                    SELECT 'order' as type, id, symbol, created_at, status, 
                           CAST(quantity as TEXT) as details
                    FROM orders 
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                )
                UNION ALL
                (
                    SELECT 'transaction' as type, id, 'N/A' as symbol, created_at, status,
                           CONCAT(type, ': ', amount) as details
                    FROM transactions 
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                )
                UNION ALL
                (
                    SELECT 'backtest' as type, id, 'N/A' as symbol, created_at, status,
                           name as details
                    FROM backtests 
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                )
                ORDER BY created_at DESC
                LIMIT :limit
            """), {"user_id": user_id, "limit": limit}).fetchall()
            
            activities = []
            for row in result:
                activities.append({
                    "type": row.type,
                    "id": row.id,
                    "symbol": row.symbol,
                    "created_at": row.created_at,
                    "status": row.status,
                    "details": row.details
                })
            
            return activities
    
    def optimize_query_with_eager_loading(
        self, 
        query: Query, 
        relationships: List[str]
    ) -> Query:
        """使用预加载优化查询"""
        
        for relationship in relationships:
            if '.' in relationship:
                # 嵌套关系使用 selectinload
                query = query.options(selectinload(relationship))
            else:
                # 简单关系使用 joinedload
                query = query.options(joinedload(relationship))
        
        return query
    
    def get_query_execution_plan(self, db: Session, query: str) -> List[Dict[str, Any]]:
        """获取查询执行计划"""
        
        try:
            result = db.execute(text(f"EXPLAIN ANALYZE {query}")).fetchall()
            return [{"plan": str(row[0])} for row in result]
        except Exception as e:
            logger.error(f"Failed to get query execution plan: {e}")
            return []
    
    def analyze_slow_queries(self, db: Session) -> List[Dict[str, Any]]:
        """分析慢查询"""
        
        try:
            # PostgreSQL 慢查询分析
            result = db.execute(text("""
                SELECT query, calls, total_time, mean_time, rows
                FROM pg_stat_statements 
                WHERE mean_time > :threshold
                ORDER BY mean_time DESC
                LIMIT 10
            """), {"threshold": self.slow_query_threshold * 1000}).fetchall()
            
            slow_queries = []
            for row in result:
                slow_queries.append({
                    "query": row.query,
                    "calls": row.calls,
                    "total_time": row.total_time,
                    "mean_time": row.mean_time,
                    "rows": row.rows
                })
            
            return slow_queries
        except Exception as e:
            logger.error(f"Failed to analyze slow queries: {e}")
            return []
    
    def get_database_statistics(self, db: Session) -> Dict[str, Any]:
        """获取数据库统计信息"""
        
        try:
            # 获取表大小统计
            table_stats = db.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats 
                WHERE schemaname = 'public'
                ORDER BY tablename, attname
            """)).fetchall()
            
            # 获取索引使用统计
            index_stats = db.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                ORDER BY idx_tup_read DESC
            """)).fetchall()
            
            return {
                "table_statistics": [
                    {
                        "schema": row.schemaname,
                        "table": row.tablename,
                        "column": row.attname,
                        "distinct_values": row.n_distinct,
                        "correlation": row.correlation
                    }
                    for row in table_stats
                ],
                "index_statistics": [
                    {
                        "schema": row.schemaname,
                        "table": row.tablename,
                        "index": row.indexname,
                        "reads": row.idx_tup_read,
                        "fetches": row.idx_tup_fetch
                    }
                    for row in index_stats
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            return {"table_statistics": [], "index_statistics": []}
    
    def suggest_query_optimizations(
        self, 
        db: Session, 
        query: str
    ) -> List[str]:
        """建议查询优化方案"""
        
        suggestions = []
        
        # 检查是否使用了索引
        if "WHERE" in query.upper() and "INDEX" not in query.upper():
            suggestions.append("考虑为WHERE子句中的列添加索引")
        
        # 检查是否使用了ORDER BY
        if "ORDER BY" in query.upper() and "INDEX" not in query.upper():
            suggestions.append("考虑为ORDER BY子句中的列添加索引")
        
        # 检查是否使用了LIMIT
        if "SELECT" in query.upper() and "LIMIT" not in query.upper():
            suggestions.append("考虑添加LIMIT子句限制结果数量")
        
        # 检查是否使用了JOIN
        if "JOIN" in query.upper():
            suggestions.append("确保JOIN条件使用了索引列")
        
        # 检查是否使用了子查询
        if query.count("SELECT") > 1:
            suggestions.append("考虑将子查询重写为JOIN以提高性能")
        
        return suggestions

# 创建全局实例
query_optimization_service = QueryOptimizationService()