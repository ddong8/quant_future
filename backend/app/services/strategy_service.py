"""
策略管理服务
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime

from ..models.strategy import Strategy, StrategyVersion, StrategyTemplate, StrategyStatus, StrategyType
from ..models.user import User
from ..schemas.strategy import (
    StrategyCreate, StrategyUpdate, StrategySearchParams,
    StrategyVersionCreate, StrategyTemplateCreate, StrategyTemplateUpdate
)
from ..core.exceptions import BusinessLogicError, ValidationError
from ..websocket.publisher import publisher

logger = logging.getLogger(__name__)


class StrategyService:
    """策略管理服务"""
    
    def __init__(self):
        pass
    
    def create_strategy(self, db: Session, strategy_data: StrategyCreate, user_id: int) -> Strategy:
        """创建策略"""
        try:
            # 检查策略名称是否重复（同一用户下）
            existing_strategy = db.query(Strategy).filter(
                and_(
                    Strategy.user_id == user_id,
                    Strategy.name == strategy_data.name
                )
            ).first()
            
            if existing_strategy:
                raise BusinessLogicError(
                    error_code="STRATEGY_NAME_EXISTS",
                    message=f"策略名称 '{strategy_data.name}' 已存在"
                )
            
            # 创建策略
            strategy = Strategy(
                **strategy_data.dict(),
                user_id=user_id,
                status=StrategyStatus.DRAFT,
                version=1
            )
            
            db.add(strategy)
            db.commit()
            db.refresh(strategy)
            
            # 创建初始版本
            self._create_initial_version(db, strategy)
            
            # 发送WebSocket通知
            self._notify_strategy_update(strategy, "created")
            
            logger.info(f"用户 {user_id} 创建策略: {strategy.name} (ID: {strategy.id})")
            return strategy
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建策略失败: {e}")
            raise
    
    def get_strategy(self, db: Session, strategy_id: int, user_id: int) -> Optional[Strategy]:
        """获取策略详情"""
        strategy = db.query(Strategy).filter(
            and_(
                Strategy.id == strategy_id,
                or_(
                    Strategy.user_id == user_id,
                    Strategy.is_public == True
                )
            )
        ).first()
        
        if not strategy:
            raise BusinessLogicError(
                error_code="STRATEGY_NOT_FOUND",
                message="策略不存在或无权限访问"
            )
        
        return strategy
    
    def get_strategy_by_uuid(self, db: Session, strategy_uuid: str, user_id: int) -> Optional[Strategy]:
        """通过UUID获取策略"""
        strategy = db.query(Strategy).filter(
            and_(
                Strategy.uuid == strategy_uuid,
                or_(
                    Strategy.user_id == user_id,
                    Strategy.is_public == True
                )
            )
        ).first()
        
        if not strategy:
            raise BusinessLogicError(
                error_code="STRATEGY_NOT_FOUND",
                message="策略不存在或无权限访问"
            )
        
        return strategy
    
    def update_strategy(self, db: Session, strategy_id: int, strategy_data: StrategyUpdate, user_id: int) -> Strategy:
        """更新策略"""
        try:
            strategy = db.query(Strategy).filter(
                and_(
                    Strategy.id == strategy_id,
                    Strategy.user_id == user_id
                )
            ).first()
            
            if not strategy:
                raise BusinessLogicError(
                    error_code="STRATEGY_NOT_FOUND",
                    message="策略不存在或无权限修改"
                )
            
            # 检查策略是否正在运行
            if strategy.is_running and strategy_data.code is not None:
                raise BusinessLogicError(
                    error_code="STRATEGY_RUNNING",
                    message="策略正在运行，无法修改代码"
                )
            
            # 检查名称重复
            if strategy_data.name and strategy_data.name != strategy.name:
                existing_strategy = db.query(Strategy).filter(
                    and_(
                        Strategy.user_id == user_id,
                        Strategy.name == strategy_data.name,
                        Strategy.id != strategy_id
                    )
                ).first()
                
                if existing_strategy:
                    raise BusinessLogicError(
                        error_code="STRATEGY_NAME_EXISTS",
                        message=f"策略名称 '{strategy_data.name}' 已存在"
                    )
            
            # 更新策略
            update_data = strategy_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(strategy, field, value)
            
            # 如果代码有变更，创建新版本
            if strategy_data.code is not None:
                strategy.version += 1
                self._create_version(db, strategy, strategy_data.code, "代码更新")
            
            db.commit()
            db.refresh(strategy)
            
            # 发送WebSocket通知
            self._notify_strategy_update(strategy, "updated")
            
            logger.info(f"用户 {user_id} 更新策略: {strategy.name} (ID: {strategy.id})")
            return strategy
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新策略失败: {e}")
            raise
    
    def delete_strategy(self, db: Session, strategy_id: int, user_id: int) -> bool:
        """删除策略"""
        try:
            strategy = db.query(Strategy).filter(
                and_(
                    Strategy.id == strategy_id,
                    Strategy.user_id == user_id
                )
            ).first()
            
            if not strategy:
                raise BusinessLogicError(
                    error_code="STRATEGY_NOT_FOUND",
                    message="策略不存在或无权限删除"
                )
            
            # 检查策略是否正在运行
            if strategy.is_running:
                raise BusinessLogicError(
                    error_code="STRATEGY_RUNNING",
                    message="策略正在运行，无法删除"
                )
            
            strategy_name = strategy.name
            db.delete(strategy)
            db.commit()
            
            # 发送WebSocket通知
            self._notify_strategy_update(strategy, "deleted")
            
            logger.info(f"用户 {user_id} 删除策略: {strategy_name} (ID: {strategy_id})")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"删除策略失败: {e}")
            raise
    
    def search_strategies(self, db: Session, params: StrategySearchParams, user_id: int) -> Tuple[List[Strategy], int]:
        """搜索策略"""
        query = db.query(Strategy)
        
        # 权限过滤：只能看到自己的策略或公开的策略
        query = query.filter(
            or_(
                Strategy.user_id == user_id,
                Strategy.is_public == True
            )
        )
        
        # 关键词搜索
        if params.keyword:
            keyword = f"%{params.keyword}%"
            query = query.filter(
                or_(
                    Strategy.name.ilike(keyword),
                    Strategy.description.ilike(keyword)
                )
            )
        
        # 策略类型筛选
        if params.strategy_type:
            query = query.filter(Strategy.strategy_type == params.strategy_type)
        
        # 状态筛选
        if params.status:
            query = query.filter(Strategy.status == params.status)
        
        # 标签筛选
        if params.tags:
            for tag in params.tags:
                query = query.filter(Strategy.tags.contains([tag]))
        
        # 公开状态筛选
        if params.is_public is not None:
            query = query.filter(Strategy.is_public == params.is_public)
        
        # 模板状态筛选
        if params.is_template is not None:
            query = query.filter(Strategy.is_template == params.is_template)
        
        # 运行状态筛选
        if params.is_running is not None:
            query = query.filter(Strategy.is_running == params.is_running)
        
        # 时间范围筛选
        if params.created_after:
            query = query.filter(Strategy.created_at >= params.created_after)
        
        if params.created_before:
            query = query.filter(Strategy.created_at <= params.created_before)
        
        # 获取总数
        total = query.count()
        
        # 排序
        if params.sort_order == 'desc':
            query = query.order_by(desc(getattr(Strategy, params.sort_by)))
        else:
            query = query.order_by(asc(getattr(Strategy, params.sort_by)))
        
        # 分页
        offset = (params.page - 1) * params.page_size
        strategies = query.offset(offset).limit(params.page_size).all()
        
        return strategies, total
    
    def get_user_strategies(self, db: Session, user_id: int, status: Optional[StrategyStatus] = None) -> List[Strategy]:
        """获取用户的策略列表"""
        query = db.query(Strategy).filter(Strategy.user_id == user_id)
        
        if status:
            query = query.filter(Strategy.status == status)
        
        return query.order_by(desc(Strategy.updated_at)).all()
    
    def copy_strategy(self, db: Session, strategy_id: int, user_id: int, new_name: Optional[str] = None) -> Strategy:
        """复制策略"""
        try:
            # 获取原策略
            original_strategy = self.get_strategy(db, strategy_id, user_id)
            
            # 生成新名称
            if not new_name:
                new_name = f"{original_strategy.name} - 副本"
            
            # 检查名称重复
            counter = 1
            base_name = new_name
            while db.query(Strategy).filter(
                and_(
                    Strategy.user_id == user_id,
                    Strategy.name == new_name
                )
            ).first():
                new_name = f"{base_name} ({counter})"
                counter += 1
            
            # 创建新策略
            new_strategy = Strategy(
                name=new_name,
                description=f"复制自: {original_strategy.name}",
                strategy_type=original_strategy.strategy_type,
                code=original_strategy.code,
                entry_point=original_strategy.entry_point,
                language=original_strategy.language,
                parameters=original_strategy.parameters.copy() if original_strategy.parameters else {},
                symbols=original_strategy.symbols.copy() if original_strategy.symbols else [],
                timeframe=original_strategy.timeframe,
                max_position_size=original_strategy.max_position_size,
                max_drawdown=original_strategy.max_drawdown,
                stop_loss=original_strategy.stop_loss,
                take_profit=original_strategy.take_profit,
                tags=original_strategy.tags.copy() if original_strategy.tags else [],
                is_public=False,  # 复制的策略默认为私有
                user_id=user_id,
                status=StrategyStatus.DRAFT,
                version=1
            )
            
            db.add(new_strategy)
            db.commit()
            db.refresh(new_strategy)
            
            # 创建初始版本
            self._create_initial_version(db, new_strategy)
            
            # 发送WebSocket通知
            self._notify_strategy_update(new_strategy, "created")
            
            logger.info(f"用户 {user_id} 复制策略: {original_strategy.name} -> {new_name}")
            return new_strategy
            
        except Exception as e:
            db.rollback()
            logger.error(f"复制策略失败: {e}")
            raise
    
    def get_strategy_statistics(self, db: Session, user_id: int) -> Dict[str, Any]:
        """获取策略统计信息"""
        # 基础统计
        total_strategies = db.query(Strategy).filter(Strategy.user_id == user_id).count()
        active_strategies = db.query(Strategy).filter(
            and_(Strategy.user_id == user_id, Strategy.status == StrategyStatus.ACTIVE)
        ).count()
        running_strategies = db.query(Strategy).filter(
            and_(Strategy.user_id == user_id, Strategy.is_running == True)
        ).count()
        draft_strategies = db.query(Strategy).filter(
            and_(Strategy.user_id == user_id, Strategy.status == StrategyStatus.DRAFT)
        ).count()
        public_strategies = db.query(Strategy).filter(
            and_(Strategy.user_id == user_id, Strategy.is_public == True)
        ).count()
        template_strategies = db.query(Strategy).filter(
            and_(Strategy.user_id == user_id, Strategy.is_template == True)
        ).count()
        
        # 性能统计
        performance_stats = db.query(
            func.avg(Strategy.total_returns).label('avg_returns'),
            func.avg(Strategy.sharpe_ratio).label('avg_sharpe_ratio'),
            func.avg(Strategy.win_rate).label('avg_win_rate'),
            func.sum(Strategy.total_trades).label('total_trades')
        ).filter(Strategy.user_id == user_id).first()
        
        return {
            'total_strategies': total_strategies,
            'active_strategies': active_strategies,
            'running_strategies': running_strategies,
            'draft_strategies': draft_strategies,
            'public_strategies': public_strategies,
            'template_strategies': template_strategies,
            'avg_returns': float(performance_stats.avg_returns or 0),
            'avg_sharpe_ratio': float(performance_stats.avg_sharpe_ratio or 0),
            'avg_win_rate': float(performance_stats.avg_win_rate or 0),
            'total_trades': int(performance_stats.total_trades or 0)
        }
    
    def _create_initial_version(self, db: Session, strategy: Strategy):
        """创建初始版本"""
        version = StrategyVersion(
            version_number=1,
            version_name="初始版本",
            description="策略创建时的初始版本",
            code=strategy.code,
            entry_point=strategy.entry_point,
            parameters=strategy.parameters,
            change_log="策略创建",
            is_major_version=True,
            strategy_id=strategy.id,
            user_id=strategy.user_id
        )
        
        db.add(version)
        db.commit()
    
    def _create_version(self, db: Session, strategy: Strategy, code: str, change_log: str):
        """创建新版本"""
        version = StrategyVersion(
            version_number=strategy.version,
            version_name=f"版本 {strategy.version}",
            code=code,
            entry_point=strategy.entry_point,
            parameters=strategy.parameters,
            change_log=change_log,
            strategy_id=strategy.id,
            user_id=strategy.user_id
        )
        
        db.add(version)
        db.commit()
    
    def _notify_strategy_update(self, strategy: Strategy, action: str):
        """发送策略更新通知"""
        try:
            # 异步发送WebSocket通知
            import asyncio
            asyncio.create_task(
                publisher.publish_strategy_update(
                    strategy.user_id,
                    {
                        'action': action,
                        'strategy': strategy.to_dict()
                    }
                )
            )
        except Exception as e:
            logger.error(f"发送策略更新通知失败: {e}")


# 全局策略服务实例
strategy_service = StrategyService()