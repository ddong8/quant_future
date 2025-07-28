"""
策略管理服务
"""
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import logging
import json
import uuid

from ..models import Strategy, StrategyVersion, User, StrategyStatus
from ..core.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    AuthorizationError,
)
from ..core.dependencies import PaginationParams, SortParams
from ..schemas.strategy import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyListResponse,
    StrategySearchRequest,
    StrategyStatusUpdate,
    StrategyVersionCreate,
    StrategyVersionResponse,
    StrategyStatsResponse,
    StrategyCloneRequest,
    BatchStrategyOperation,
    StrategyTemplate,
    StrategyPerformanceMetrics,
)

logger = logging.getLogger(__name__)


class StrategyService:
    """策略管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_strategy(
        self,
        strategy_data: StrategyCreate,
        user_id: int
    ) -> StrategyResponse:
        """创建策略"""
        try:
            # 检查策略名称是否已存在（同一用户下）
            existing_strategy = self.db.query(Strategy).filter(
                and_(
                    Strategy.name == strategy_data.name,
                    Strategy.user_id == user_id
                )
            ).first()
            
            if existing_strategy:
                raise ConflictError("策略名称已存在")
            
            # 创建新策略
            new_strategy = Strategy(
                name=strategy_data.name,
                description=strategy_data.description,
                code=strategy_data.code,
                language=strategy_data.language,
                version="1.0.0",
                user_id=user_id,
                status=StrategyStatus.DRAFT,
                parameters=strategy_data.parameters or {},
                tags=strategy_data.tags or [],
                total_return=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                win_rate=0.0,
            )
            
            self.db.add(new_strategy)
            self.db.commit()
            self.db.refresh(new_strategy)
            
            # 创建初始版本
            initial_version = StrategyVersion(
                strategy_id=new_strategy.id,
                version="1.0.0",
                code=strategy_data.code,
                description="初始版本",
                parameters=strategy_data.parameters or {},
            )
            
            self.db.add(initial_version)
            self.db.commit()
            
            logger.info(f"策略创建成功: {new_strategy.name}, 用户: {user_id}")
            
            return StrategyResponse.from_orm(new_strategy)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建策略失败: {e}")
            raise
    
    def get_strategy_by_id(
        self,
        strategy_id: int,
        user_id: Optional[int] = None
    ) -> StrategyResponse:
        """根据ID获取策略"""
        query = self.db.query(Strategy).filter(Strategy.id == strategy_id)
        
        # 如果指定了用户ID，则只能查看自己的策略
        if user_id:
            query = query.filter(Strategy.user_id == user_id)
        
        strategy = query.first()
        if not strategy:
            raise NotFoundError("策略不存在")
        
        return StrategyResponse.from_orm(strategy)
    
    def update_strategy(
        self,
        strategy_id: int,
        strategy_data: StrategyUpdate,
        user_id: int
    ) -> StrategyResponse:
        """更新策略"""
        try:
            strategy = self.db.query(Strategy).filter(
                and_(
                    Strategy.id == strategy_id,
                    Strategy.user_id == user_id
                )
            ).first()
            
            if not strategy:
                raise NotFoundError("策略不存在")
            
            # 检查策略状态是否允许修改
            if strategy.status == StrategyStatus.ACTIVE:
                raise ValidationError("运行中的策略不能修改")
            
            # 检查名称冲突
            if strategy_data.name and strategy_data.name != strategy.name:
                existing_strategy = self.db.query(Strategy).filter(
                    and_(
                        Strategy.name == strategy_data.name,
                        Strategy.user_id == user_id,
                        Strategy.id != strategy_id
                    )
                ).first()
                
                if existing_strategy:
                    raise ConflictError("策略名称已存在")
            
            # 更新策略信息
            update_data = strategy_data.dict(exclude_unset=True)
            
            # 如果代码有更新，创建新版本
            if 'code' in update_data and update_data['code'] != strategy.code:
                new_version = self._increment_version(strategy.version)
                
                # 创建新版本记录
                version_record = StrategyVersion(
                    strategy_id=strategy.id,
                    version=new_version,
                    code=update_data['code'],
                    description=f"版本 {new_version}",
                    parameters=update_data.get('parameters', strategy.parameters),
                )
                
                self.db.add(version_record)
                update_data['version'] = new_version
            
            # 应用更新
            for field, value in update_data.items():
                setattr(strategy, field, value)
            
            strategy.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(strategy)
            
            logger.info(f"策略更新成功: {strategy.name}")
            
            return StrategyResponse.from_orm(strategy)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新策略失败: {e}")
            raise
    
    def delete_strategy(
        self,
        strategy_id: int,
        user_id: int
    ) -> bool:
        """删除策略"""
        try:
            strategy = self.db.query(Strategy).filter(
                and_(
                    Strategy.id == strategy_id,
                    Strategy.user_id == user_id
                )
            ).first()
            
            if not strategy:
                raise NotFoundError("策略不存在")
            
            # 检查策略状态
            if strategy.status == StrategyStatus.ACTIVE:
                raise ValidationError("运行中的策略不能删除")
            
            # 删除策略版本
            self.db.query(StrategyVersion).filter(
                StrategyVersion.strategy_id == strategy_id
            ).delete()
            
            # 删除策略
            self.db.delete(strategy)
            self.db.commit()
            
            logger.info(f"策略删除成功: {strategy.name}")
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除策略失败: {e}")
            raise
    
    def get_strategies_list(
        self,
        user_id: Optional[int] = None,
        search_params: Optional[StrategySearchRequest] = None,
        pagination: Optional[PaginationParams] = None,
        sort_params: Optional[SortParams] = None
    ) -> Tuple[List[StrategyListResponse], int]:
        """获取策略列表"""
        query = self.db.query(Strategy)
        
        # 用户过滤
        if user_id:
            query = query.filter(Strategy.user_id == user_id)
        
        # 应用搜索条件
        if search_params:
            if search_params.keyword:
                keyword = f"%{search_params.keyword}%"
                query = query.filter(
                    or_(
                        Strategy.name.ilike(keyword),
                        Strategy.description.ilike(keyword)
                    )
                )
            
            if search_params.status:
                query = query.filter(Strategy.status == search_params.status)
            
            if search_params.tags:
                # 使用JSON查询匹配标签
                for tag in search_params.tags:
                    query = query.filter(Strategy.tags.contains([tag]))
            
            if search_params.user_id:
                query = query.filter(Strategy.user_id == search_params.user_id)
            
            if search_params.created_after:
                query = query.filter(Strategy.created_at >= search_params.created_after)
            
            if search_params.created_before:
                query = query.filter(Strategy.created_at <= search_params.created_before)
            
            if search_params.min_return is not None:
                query = query.filter(Strategy.total_return >= search_params.min_return)
            
            if search_params.max_drawdown is not None:
                query = query.filter(Strategy.max_drawdown <= search_params.max_drawdown)
        
        # 获取总数
        total = query.count()
        
        # 应用排序
        if sort_params:
            if hasattr(Strategy, sort_params.sort_by):
                sort_column = getattr(Strategy, sort_params.sort_by)
                if sort_params.sort_order == "asc":
                    query = query.order_by(sort_column)
                else:
                    query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(desc(Strategy.updated_at))
        
        # 应用分页
        if pagination:
            query = query.offset(pagination.offset).limit(pagination.page_size)
        
        strategies = query.all()
        strategy_list = [StrategyListResponse.from_orm(strategy) for strategy in strategies]
        
        return strategy_list, total
    
    def update_strategy_status(
        self,
        strategy_id: int,
        status_update: StrategyStatusUpdate,
        user_id: int
    ) -> StrategyResponse:
        """更新策略状态"""
        try:
            strategy = self.db.query(Strategy).filter(
                and_(
                    Strategy.id == strategy_id,
                    Strategy.user_id == user_id
                )
            ).first()
            
            if not strategy:
                raise NotFoundError("策略不存在")
            
            # 验证状态转换
            self._validate_status_transition(strategy.status, status_update.status)
            
            old_status = strategy.status
            strategy.status = status_update.status
            strategy.updated_at = datetime.utcnow()
            
            # 如果是激活状态，记录运行时间
            if status_update.status == StrategyStatus.ACTIVE:
                strategy.last_run_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(strategy)
            
            logger.info(f"策略状态更新: {strategy.name}, {old_status} -> {status_update.status}")
            
            return StrategyResponse.from_orm(strategy)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新策略状态失败: {e}")
            raise
    
    def create_strategy_version(
        self,
        strategy_id: int,
        version_data: StrategyVersionCreate,
        user_id: int
    ) -> StrategyVersionResponse:
        """创建策略版本"""
        try:
            strategy = self.db.query(Strategy).filter(
                and_(
                    Strategy.id == strategy_id,
                    Strategy.user_id == user_id
                )
            ).first()
            
            if not strategy:
                raise NotFoundError("策略不存在")
            
            # 检查版本号是否已存在
            existing_version = self.db.query(StrategyVersion).filter(
                and_(
                    StrategyVersion.strategy_id == strategy_id,
                    StrategyVersion.version == version_data.version
                )
            ).first()
            
            if existing_version:
                raise ConflictError("版本号已存在")
            
            # 创建新版本
            new_version = StrategyVersion(
                strategy_id=strategy_id,
                version=version_data.version,
                code=version_data.code,
                description=version_data.description,
                parameters=version_data.parameters or {},
            )
            
            self.db.add(new_version)
            
            # 更新策略的当前版本和代码
            strategy.version = version_data.version
            strategy.code = version_data.code
            strategy.parameters = version_data.parameters or strategy.parameters
            strategy.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(new_version)
            
            logger.info(f"策略版本创建成功: {strategy.name} v{version_data.version}")
            
            return StrategyVersionResponse.from_orm(new_version)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建策略版本失败: {e}")
            raise
    
    def get_strategy_versions(
        self,
        strategy_id: int,
        user_id: int
    ) -> List[StrategyVersionResponse]:
        """获取策略版本列表"""
        # 验证策略所有权
        strategy = self.db.query(Strategy).filter(
            and_(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id
            )
        ).first()
        
        if not strategy:
            raise NotFoundError("策略不存在")
        
        versions = self.db.query(StrategyVersion).filter(
            StrategyVersion.strategy_id == strategy_id
        ).order_by(desc(StrategyVersion.created_at)).all()
        
        return [StrategyVersionResponse.from_orm(version) for version in versions]
    
    def clone_strategy(
        self,
        strategy_id: int,
        clone_data: StrategyCloneRequest,
        user_id: int
    ) -> StrategyResponse:
        """克隆策略"""
        try:
            # 获取原策略
            original_strategy = self.db.query(Strategy).filter(
                Strategy.id == strategy_id
            ).first()
            
            if not original_strategy:
                raise NotFoundError("原策略不存在")
            
            # 检查新名称是否冲突
            existing_strategy = self.db.query(Strategy).filter(
                and_(
                    Strategy.name == clone_data.name,
                    Strategy.user_id == user_id
                )
            ).first()
            
            if existing_strategy:
                raise ConflictError("策略名称已存在")
            
            # 创建克隆策略
            cloned_strategy = Strategy(
                name=clone_data.name,
                description=clone_data.description or f"克隆自: {original_strategy.name}",
                code=original_strategy.code,
                language=original_strategy.language,
                version="1.0.0",
                user_id=user_id,
                status=StrategyStatus.DRAFT,
                parameters=original_strategy.parameters,
                tags=original_strategy.tags,
                total_return=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                win_rate=0.0,
            )
            
            self.db.add(cloned_strategy)
            self.db.commit()
            self.db.refresh(cloned_strategy)
            
            # 创建初始版本
            initial_version = StrategyVersion(
                strategy_id=cloned_strategy.id,
                version="1.0.0",
                code=original_strategy.code,
                description="克隆版本",
                parameters=original_strategy.parameters,
            )
            
            self.db.add(initial_version)
            self.db.commit()
            
            logger.info(f"策略克隆成功: {original_strategy.name} -> {clone_data.name}")
            
            return StrategyResponse.from_orm(cloned_strategy)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"克隆策略失败: {e}")
            raise
    
    def get_strategy_stats(self, user_id: Optional[int] = None) -> StrategyStatsResponse:
        """获取策略统计信息"""
        query = self.db.query(Strategy)
        
        if user_id:
            query = query.filter(Strategy.user_id == user_id)
        
        # 基础统计
        total_strategies = query.count()
        active_strategies = query.filter(Strategy.status == StrategyStatus.ACTIVE).count()
        draft_strategies = query.filter(Strategy.status == StrategyStatus.DRAFT).count()
        testing_strategies = query.filter(Strategy.status == StrategyStatus.TESTING).count()
        paused_strategies = query.filter(Strategy.status == StrategyStatus.PAUSED).count()
        stopped_strategies = query.filter(Strategy.status == StrategyStatus.STOPPED).count()
        
        # 性能统计
        avg_return = query.with_entities(func.avg(Strategy.total_return)).scalar() or 0.0
        avg_sharpe_ratio = query.with_entities(func.avg(Strategy.sharpe_ratio)).scalar() or 0.0
        
        # 获取表现最好的策略
        top_performers_query = query.filter(
            Strategy.total_return > 0
        ).order_by(desc(Strategy.total_return)).limit(5)
        
        top_performers = [
            StrategyListResponse.from_orm(strategy) 
            for strategy in top_performers_query.all()
        ]
        
        return StrategyStatsResponse(
            total_strategies=total_strategies,
            active_strategies=active_strategies,
            draft_strategies=draft_strategies,
            testing_strategies=testing_strategies,
            paused_strategies=paused_strategies,
            stopped_strategies=stopped_strategies,
            avg_return=avg_return,
            avg_sharpe_ratio=avg_sharpe_ratio,
            top_performers=top_performers,
        )
    
    def batch_strategy_operation(
        self,
        operation_data: BatchStrategyOperation,
        user_id: int
    ) -> Dict[str, Any]:
        """批量策略操作"""
        try:
            strategies = self.db.query(Strategy).filter(
                and_(
                    Strategy.id.in_(operation_data.strategy_ids),
                    Strategy.user_id == user_id
                )
            ).all()
            
            if len(strategies) != len(operation_data.strategy_ids):
                found_ids = [s.id for s in strategies]
                missing_ids = [sid for sid in operation_data.strategy_ids if sid not in found_ids]
                raise NotFoundError(f"以下策略不存在: {missing_ids}")
            
            success_count = 0
            failed_count = 0
            errors = []
            
            for strategy in strategies:
                try:
                    if operation_data.operation == 'activate':
                        if strategy.status in [StrategyStatus.DRAFT, StrategyStatus.PAUSED, StrategyStatus.STOPPED]:
                            strategy.status = StrategyStatus.ACTIVE
                            strategy.last_run_at = datetime.utcnow()
                        else:
                            errors.append(f"策略{strategy.name}状态不允许激活")
                            failed_count += 1
                            continue
                    
                    elif operation_data.operation == 'pause':
                        if strategy.status == StrategyStatus.ACTIVE:
                            strategy.status = StrategyStatus.PAUSED
                        else:
                            errors.append(f"策略{strategy.name}不是运行状态")
                            failed_count += 1
                            continue
                    
                    elif operation_data.operation == 'stop':
                        if strategy.status in [StrategyStatus.ACTIVE, StrategyStatus.PAUSED]:
                            strategy.status = StrategyStatus.STOPPED
                        else:
                            errors.append(f"策略{strategy.name}状态不允许停止")
                            failed_count += 1
                            continue
                    
                    elif operation_data.operation == 'delete':
                        if strategy.status != StrategyStatus.ACTIVE:
                            # 删除版本记录
                            self.db.query(StrategyVersion).filter(
                                StrategyVersion.strategy_id == strategy.id
                            ).delete()
                            # 删除策略
                            self.db.delete(strategy)
                        else:
                            errors.append(f"运行中的策略{strategy.name}不能删除")
                            failed_count += 1
                            continue
                    
                    strategy.updated_at = datetime.utcnow()
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"策略{strategy.name}: {str(e)}")
                    failed_count += 1
            
            self.db.commit()
            
            logger.info(f"批量策略操作完成: {operation_data.operation}, 成功: {success_count}, 失败: {failed_count}")
            
            return {
                "success_count": success_count,
                "failed_count": failed_count,
                "errors": errors,
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"批量策略操作失败: {e}")
            raise
    
    def get_strategy_templates(self) -> List[StrategyTemplate]:
        """获取策略模板"""
        # 这里返回一些预定义的策略模板
        templates = [
            StrategyTemplate(
                name="简单移动平均策略",
                description="基于双移动平均线的趋势跟踪策略",
                code=self._get_ma_strategy_template(),
                language="python",
                parameters={
                    "short_period": 5,
                    "long_period": 20,
                    "symbol": "SHFE.cu2401"
                },
                tags=["移动平均", "趋势跟踪"],
                category="trend_following"
            ),
            StrategyTemplate(
                name="均值回归策略",
                description="基于价格偏离均值的反转策略",
                code=self._get_mean_reversion_template(),
                language="python",
                parameters={
                    "period": 20,
                    "threshold": 2.0,
                    "symbol": "SHFE.cu2401"
                },
                tags=["均值回归", "反转"],
                category="mean_reversion"
            ),
        ]
        
        return templates
    
    def _validate_status_transition(self, current_status: str, new_status: StrategyStatus):
        """验证状态转换是否合法"""
        valid_transitions = {
            StrategyStatus.DRAFT: [StrategyStatus.TESTING, StrategyStatus.ACTIVE],
            StrategyStatus.TESTING: [StrategyStatus.DRAFT, StrategyStatus.ACTIVE, StrategyStatus.STOPPED],
            StrategyStatus.ACTIVE: [StrategyStatus.PAUSED, StrategyStatus.STOPPED],
            StrategyStatus.PAUSED: [StrategyStatus.ACTIVE, StrategyStatus.STOPPED],
            StrategyStatus.STOPPED: [StrategyStatus.DRAFT, StrategyStatus.TESTING],
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise ValidationError(f"不能从{current_status}状态转换到{new_status}状态")
    
    def _increment_version(self, current_version: str) -> str:
        """递增版本号"""
        try:
            parts = current_version.split('.')
            if len(parts) == 3:
                major, minor, patch = map(int, parts)
                return f"{major}.{minor}.{patch + 1}"
            else:
                return "1.0.1"
        except:
            return "1.0.1"
    
    def _get_ma_strategy_template(self) -> str:
        """获取移动平均策略模板代码"""
        return '''
# 双移动平均策略模板
from tqsdk import TqApi, TqSim

def initialize(context):
    """策略初始化"""
    context.symbol = context.params.get("symbol", "SHFE.cu2401")
    context.short_period = context.params.get("short_period", 5)
    context.long_period = context.params.get("long_period", 20)
    
def handle_bar(context, bar_dict):
    """处理K线数据"""
    # 获取K线数据
    klines = context.get_klines(context.symbol, context.long_period + 1)
    
    if len(klines) < context.long_period:
        return
    
    # 计算移动平均
    short_ma = sum(klines[-context.short_period:]) / context.short_period
    long_ma = sum(klines[-context.long_period:]) / context.long_period
    
    # 交易逻辑
    if short_ma > long_ma:
        # 金叉，买入
        context.order_target_percent(context.symbol, 1.0)
    elif short_ma < long_ma:
        # 死叉，卖出
        context.order_target_percent(context.symbol, 0.0)
'''
    
    def _get_mean_reversion_template(self) -> str:
        """获取均值回归策略模板代码"""
        return '''
# 均值回归策略模板
import numpy as np

def initialize(context):
    """策略初始化"""
    context.symbol = context.params.get("symbol", "SHFE.cu2401")
    context.period = context.params.get("period", 20)
    context.threshold = context.params.get("threshold", 2.0)
    
def handle_bar(context, bar_dict):
    """处理K线数据"""
    # 获取K线数据
    klines = context.get_klines(context.symbol, context.period + 1)
    
    if len(klines) < context.period:
        return
    
    # 计算均值和标准差
    prices = [k.close for k in klines[-context.period:]]
    mean_price = np.mean(prices)
    std_price = np.std(prices)
    
    current_price = klines[-1].close
    
    # 计算Z-score
    z_score = (current_price - mean_price) / std_price
    
    # 交易逻辑
    if z_score > context.threshold:
        # 价格过高，卖出
        context.order_target_percent(context.symbol, -0.5)
    elif z_score < -context.threshold:
        # 价格过低，买入
        context.order_target_percent(context.symbol, 0.5)
    elif abs(z_score) < 0.5:
        # 价格回归，平仓
        context.order_target_percent(context.symbol, 0.0)
'''