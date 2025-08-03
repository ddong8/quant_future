"""
回测管理服务
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime, timedelta
import uuid

from ..models.backtest import Backtest, BacktestTemplate, BacktestComparison
from ..models.enums import BacktestStatus
from ..models.strategy import Strategy, StrategyVersion
from ..schemas.backtest import (
    BacktestCreate, BacktestUpdate, BacktestSearchRequest,
    BacktestComparisonRequest
)
from ..core.exceptions import ValidationError, NotFoundError, PermissionError
from ..core.dependencies import get_current_user

logger = logging.getLogger(__name__)


class BacktestService:
    """回测管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_backtest(self, backtest_data: BacktestCreate, user_id: int) -> Backtest:
        """创建回测"""
        try:
            # 验证策略是否存在且用户有权限
            strategy = self.db.query(Strategy).filter(
                Strategy.id == backtest_data.strategy_id,
                Strategy.user_id == user_id
            ).first()
            
            if not strategy:
                raise NotFoundError("策略不存在或无权限访问")
            
            # 验证策略版本（如果指定）
            if backtest_data.strategy_version_id:
                strategy_version = self.db.query(StrategyVersion).filter(
                    StrategyVersion.id == backtest_data.strategy_version_id,
                    StrategyVersion.strategy_id == backtest_data.strategy_id
                ).first()
                
                if not strategy_version:
                    raise NotFoundError("策略版本不存在")
            
            # 创建回测记录
            backtest = Backtest(
                uuid=str(uuid.uuid4()),
                name=backtest_data.name,
                description=backtest_data.description,
                backtest_type=backtest_data.backtest_type,
                status=BacktestStatus.PENDING,
                strategy_id=backtest_data.strategy_id,
                strategy_version_id=backtest_data.strategy_version_id,
                start_date=backtest_data.start_date,
                end_date=backtest_data.end_date,
                initial_capital=backtest_data.initial_capital,
                benchmark=backtest_data.benchmark,
                commission_rate=backtest_data.commission_rate,
                slippage_rate=backtest_data.slippage_rate,
                min_commission=backtest_data.min_commission,
                max_position_size=backtest_data.max_position_size,
                stop_loss=backtest_data.stop_loss,
                take_profit=backtest_data.take_profit,
                data_source=backtest_data.data_source,
                symbols=backtest_data.symbols,
                frequency=backtest_data.frequency,
                tags=backtest_data.tags,
                is_public=backtest_data.is_public,
                user_id=user_id,
                config_snapshot=backtest_data.dict()  # 保存配置快照
            )
            
            self.db.add(backtest)
            self.db.commit()
            self.db.refresh(backtest)
            
            logger.info(f"创建回测成功: {backtest.id} - {backtest.name}")
            return backtest
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建回测失败: {str(e)}")
            raise
    
    def get_backtest(self, backtest_id: int, user_id: int) -> Optional[Backtest]:
        """获取回测详情"""
        backtest = self.db.query(Backtest).filter(
            Backtest.id == backtest_id,
            or_(
                Backtest.user_id == user_id,
                Backtest.is_public == True
            )
        ).first()
        
        if not backtest:
            raise NotFoundError("回测不存在或无权限访问")
        
        return backtest
    
    def search_backtests(self, params: BacktestSearchRequest, user_id: int) -> Tuple[List[Backtest], int]:
        """搜索回测"""
        query = self.db.query(Backtest)
        
        # 权限过滤
        query = query.filter(
            or_(
                Backtest.user_id == user_id,
                Backtest.is_public == True
            )
        )
        
        # 关键词搜索
        if params.keyword:
            query = query.filter(
                or_(
                    Backtest.name.ilike(f"%{params.keyword}%"),
                    Backtest.description.ilike(f"%{params.keyword}%")
                )
            )
        
        # 策略筛选
        if params.strategy_id:
            query = query.filter(Backtest.strategy_id == params.strategy_id)
        
        # 获取总数
        total = query.count()
        
        # 排序
        sort_field = getattr(Backtest, params.sort_by)
        if params.sort_order == 'desc':
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(asc(sort_field))
        
        # 分页
        offset = (params.page - 1) * params.page_size
        backtests = query.offset(offset).limit(params.page_size).all()
        
        return backtests, total
    
    def get_backtest_stats(self, user_id: int) -> Dict[str, Any]:
        """获取回测统计信息"""
        # 基础统计
        total_backtests = self.db.query(Backtest).filter(
            Backtest.user_id == user_id
        ).count()
        
        completed_backtests = self.db.query(Backtest).filter(
            Backtest.user_id == user_id,
            Backtest.status == BacktestStatus.COMPLETED
        ).count()
        
        return {
            'total_backtests': total_backtests,
            'completed_backtests': completed_backtests,
        }