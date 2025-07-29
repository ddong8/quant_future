"""
回测服务
"""
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import logging

from ..models import Backtest, Strategy, User
from ..models.enums import BacktestStatus
from ..core.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    AuthorizationError,
)
from ..core.dependencies import PaginationParams, SortParams
from .backtest_engine import BacktestEngine
from .history_service import HistoryService
from .backtest_analyzer import BacktestAnalyzer
from .backtest_report_generator import BacktestReportGenerator
from .backtest_chart_service import BacktestChartService

logger = logging.getLogger(__name__)


class BacktestService:
    """回测服务类"""
    
    def __init__(self, db: Session, history_service: HistoryService):
        self.db = db
        self.history_service = history_service
        self.backtest_engine = BacktestEngine(db, history_service)
        self.analyzer = BacktestAnalyzer()
        self.report_generator = BacktestReportGenerator()
        self.chart_service = BacktestChartService()
        self.running_backtests = {}  # 存储正在运行的回测任务
    
    def create_backtest(self, backtest_data: Dict[str, Any], user_id: int) -> Backtest:
        """创建回测"""
        try:
            # 验证策略存在且属于用户
            strategy = self.db.query(Strategy).filter(
                and_(
                    Strategy.id == backtest_data['strategy_id'],
                    Strategy.user_id == user_id
                )
            ).first()
            
            if not strategy:
                raise NotFoundError("策略不存在或无权限访问")
            
            # 验证日期范围
            start_date = backtest_data['start_date']
            end_date = backtest_data['end_date']
            
            if start_date >= end_date:
                raise ValidationError("开始日期必须早于结束日期")
            
            if end_date > datetime.utcnow():
                raise ValidationError("结束日期不能超过当前时间")
            
            # 验证初始资金
            initial_capital = backtest_data['initial_capital']
            if initial_capital <= 0:
                raise ValidationError("初始资金必须大于0")
            
            # 验证交易品种
            symbols = backtest_data.get('symbols', [])
            if not symbols:
                raise ValidationError("必须指定至少一个交易品种")
            
            # 检查是否有重复的回测名称
            existing_backtest = self.db.query(Backtest).filter(
                and_(
                    Backtest.name == backtest_data['name'],
                    Backtest.user_id == user_id
                )
            ).first()
            
            if existing_backtest:
                raise ConflictError("回测名称已存在")
            
            # 创建回测记录
            new_backtest = Backtest(
                name=backtest_data['name'],
                description=backtest_data.get('description', ''),
                strategy_id=backtest_data['strategy_id'],
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                symbols=symbols,
                parameters=backtest_data.get('parameters', {}),
                status=BacktestStatus.PENDING
            )
            
            self.db.add(new_backtest)
            self.db.commit()
            self.db.refresh(new_backtest)
            
            logger.info(f"回测创建成功: {new_backtest.name}, 用户: {user_id}")
            
            return new_backtest
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建回测失败: {e}")
            raise
    
    def get_backtest_by_id(self, backtest_id: int, user_id: Optional[int] = None) -> Backtest:
        """根据ID获取回测"""
        query = self.db.query(Backtest).filter(Backtest.id == backtest_id)
        
        if user_id:
            query = query.filter(Backtest.user_id == user_id)
        
        backtest = query.first()
        if not backtest:
            raise NotFoundError("回测不存在")
        
        return backtest
    
    def get_backtests_list(self,
                          user_id: Optional[int] = None,
                          strategy_id: Optional[int] = None,
                          status: Optional[BacktestStatus] = None,
                          keyword: Optional[str] = None,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          pagination: Optional[PaginationParams] = None,
                          sort_params: Optional[SortParams] = None) -> Tuple[List[Backtest], int]:
        """获取回测列表"""
        query = self.db.query(Backtest)
        
        # 用户过滤
        if user_id:
            query = query.filter(Backtest.user_id == user_id)
        
        # 策略过滤
        if strategy_id:
            query = query.filter(Backtest.strategy_id == strategy_id)
        
        # 状态过滤
        if status:
            query = query.filter(Backtest.status == status)
        
        # 关键词搜索
        if keyword:
            keyword_pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    Backtest.name.ilike(keyword_pattern),
                    Backtest.description.ilike(keyword_pattern)
                )
            )
        
        # 日期范围过滤
        if start_date:
            query = query.filter(Backtest.created_at >= start_date)
        
        if end_date:
            query = query.filter(Backtest.created_at <= end_date)
        
        # 获取总数
        total = query.count()
        
        # 应用排序
        if sort_params:
            if hasattr(Backtest, sort_params.sort_by):
                sort_column = getattr(Backtest, sort_params.sort_by)
                if sort_params.sort_order == "asc":
                    query = query.order_by(sort_column)
                else:
                    query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(desc(Backtest.created_at))
        
        # 应用分页
        if pagination:
            query = query.offset(pagination.offset).limit(pagination.page_size)
        
        backtests = query.all()
        
        return backtests, total
    
    def update_backtest(self, backtest_id: int, update_data: Dict[str, Any], user_id: int) -> Backtest:
        """更新回测"""
        try:
            backtest = self.db.query(Backtest).filter(
                and_(
                    Backtest.id == backtest_id,
                    Backtest.user_id == user_id
                )
            ).first()
            
            if not backtest:
                raise NotFoundError("回测不存在")
            
            # 检查回测状态是否允许修改
            if backtest.status in [BacktestStatus.RUNNING, BacktestStatus.COMPLETED]:
                raise ValidationError("运行中或已完成的回测不能修改")
            
            # 更新允许的字段
            allowed_fields = ['name', 'description', 'start_date', 'end_date', 
                            'initial_capital', 'symbols', 'parameters']
            
            for field, value in update_data.items():
                if field in allowed_fields and hasattr(backtest, field):
                    setattr(backtest, field, value)
            
            backtest.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(backtest)
            
            logger.info(f"回测更新成功: {backtest.name}")
            
            return backtest
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新回测失败: {e}")
            raise
    
    def delete_backtest(self, backtest_id: int, user_id: int) -> bool:
        """删除回测"""
        try:
            backtest = self.db.query(Backtest).filter(
                and_(
                    Backtest.id == backtest_id,
                    Backtest.user_id == user_id
                )
            ).first()
            
            if not backtest:
                raise NotFoundError("回测不存在")
            
            # 检查回测状态
            if backtest.status == BacktestStatus.RUNNING:
                raise ValidationError("运行中的回测不能删除")
            
            self.db.delete(backtest)
            self.db.commit()
            
            logger.info(f"回测删除成功: {backtest.name}")
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除回测失败: {e}")
            raise
    
    async def start_backtest(self, backtest_id: int, user_id: int) -> Dict[str, Any]:
        """启动回测"""
        try:
            backtest = self.db.query(Backtest).filter(
                and_(
                    Backtest.id == backtest_id,
                    Backtest.user_id == user_id
                )
            ).first()
            
            if not backtest:
                raise NotFoundError("回测不存在")
            
            # 检查回测状态
            if backtest.status not in [BacktestStatus.PENDING, BacktestStatus.FAILED]:
                raise ValidationError("只能启动待运行或失败的回测")
            
            # 检查是否已经在运行
            if backtest_id in self.running_backtests:
                raise ValidationError("回测已在运行中")
            
            # 重置回测状态
            backtest.status = BacktestStatus.PENDING
            backtest.progress = 0.0
            backtest.error_message = None
            backtest.started_at = None
            backtest.completed_at = None
            
            # 清空之前的结果
            backtest.final_capital = 0.0
            backtest.total_return = 0.0
            backtest.annual_return = 0.0
            backtest.max_drawdown = 0.0
            backtest.sharpe_ratio = 0.0
            backtest.sortino_ratio = 0.0
            backtest.total_trades = 0
            backtest.winning_trades = 0
            backtest.losing_trades = 0
            backtest.win_rate = 0.0
            backtest.avg_win = 0.0
            backtest.avg_loss = 0.0
            backtest.profit_factor = 0.0
            backtest.equity_curve = None
            backtest.trade_records = None
            backtest.daily_returns = None
            
            self.db.commit()
            
            # 异步启动回测
            task = asyncio.create_task(self._run_backtest_async(backtest_id))
            self.running_backtests[backtest_id] = task
            
            logger.info(f"回测启动: {backtest.name}")
            
            return {
                'backtest_id': backtest_id,
                'status': 'started',
                'message': '回测已启动'
            }
            
        except Exception as e:
            logger.error(f"启动回测失败: {e}")
            raise
    
    async def _run_backtest_async(self, backtest_id: int):
        """异步运行回测"""
        try:
            result = await self.backtest_engine.run_backtest(backtest_id)
            logger.info(f"回测 {backtest_id} 完成")
        except Exception as e:
            logger.error(f"回测 {backtest_id} 执行失败: {e}")
        finally:
            # 从运行列表中移除
            if backtest_id in self.running_backtests:
                del self.running_backtests[backtest_id]
    
    def stop_backtest(self, backtest_id: int, user_id: int) -> Dict[str, Any]:
        """停止回测"""
        try:
            backtest = self.db.query(Backtest).filter(
                and_(
                    Backtest.id == backtest_id,
                    Backtest.user_id == user_id
                )
            ).first()
            
            if not backtest:
                raise NotFoundError("回测不存在")
            
            # 检查回测是否在运行
            if backtest.status != BacktestStatus.RUNNING:
                raise ValidationError("回测未在运行中")
            
            # 取消异步任务
            if backtest_id in self.running_backtests:
                task = self.running_backtests[backtest_id]
                task.cancel()
                del self.running_backtests[backtest_id]
            
            # 更新状态
            backtest.status = BacktestStatus.CANCELLED
            backtest.completed_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"回测停止: {backtest.name}")
            
            return {
                'backtest_id': backtest_id,
                'status': 'stopped',
                'message': '回测已停止'
            }
            
        except Exception as e:
            logger.error(f"停止回测失败: {e}")
            raise
    
    def get_backtest_progress(self, backtest_id: int, user_id: int) -> Dict[str, Any]:
        """获取回测进度"""
        backtest = self.db.query(Backtest).filter(
            and_(
                Backtest.id == backtest_id,
                Backtest.user_id == user_id
            )
        ).first()
        
        if not backtest:
            raise NotFoundError("回测不存在")
        
        # 计算预估完成时间
        eta = None
        if backtest.status == BacktestStatus.RUNNING and backtest.started_at:
            elapsed_time = datetime.utcnow() - backtest.started_at
            if backtest.progress > 0:
                total_time = elapsed_time.total_seconds() / (backtest.progress / 100)
                remaining_time = total_time - elapsed_time.total_seconds()
                eta = datetime.utcnow() + timedelta(seconds=remaining_time)
        
        return {
            'backtest_id': backtest_id,
            'status': backtest.status,
            'progress': backtest.progress,
            'started_at': backtest.started_at.isoformat() if backtest.started_at else None,
            'eta': eta.isoformat() if eta else None,
            'error_message': backtest.error_message
        }
    
    def get_backtest_results(self, backtest_id: int, user_id: int) -> Dict[str, Any]:
        """获取回测结果"""
        backtest = self.db.query(Backtest).filter(
            and_(
                Backtest.id == backtest_id,
                Backtest.user_id == user_id
            )
        ).first()
        
        if not backtest:
            raise NotFoundError("回测不存在")
        
        if backtest.status != BacktestStatus.COMPLETED:
            raise ValidationError("回测尚未完成")
        
        return {
            'backtest_id': backtest_id,
            'name': backtest.name,
            'strategy_id': backtest.strategy_id,
            'start_date': backtest.start_date.isoformat(),
            'end_date': backtest.end_date.isoformat(),
            'initial_capital': backtest.initial_capital,
            'symbols': backtest.symbols,
            'parameters': backtest.parameters,
            
            # 基础指标
            'final_capital': backtest.final_capital,
            'total_return': backtest.total_return,
            'annual_return': backtest.annual_return,
            'max_drawdown': backtest.max_drawdown,
            'sharpe_ratio': backtest.sharpe_ratio,
            'sortino_ratio': backtest.sortino_ratio,
            
            # 交易统计
            'total_trades': backtest.total_trades,
            'winning_trades': backtest.winning_trades,
            'losing_trades': backtest.losing_trades,
            'win_rate': backtest.win_rate,
            'avg_win': backtest.avg_win,
            'avg_loss': backtest.avg_loss,
            'profit_factor': backtest.profit_factor,
            
            # 详细数据
            'equity_curve': backtest.equity_curve,
            'trade_records': backtest.trade_records,
            'daily_returns': backtest.daily_returns,
            
            # 时间信息
            'created_at': backtest.created_at.isoformat(),
            'started_at': backtest.started_at.isoformat() if backtest.started_at else None,
            'completed_at': backtest.completed_at.isoformat() if backtest.completed_at else None,
        }
    
    def get_backtest_statistics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """获取回测统计信息"""
        query = self.db.query(Backtest)
        
        if user_id:
            query = query.filter(Backtest.user_id == user_id)
        
        # 基础统计
        total_backtests = query.count()
        completed_backtests = query.filter(Backtest.status == BacktestStatus.COMPLETED).count()
        running_backtests = query.filter(Backtest.status == BacktestStatus.RUNNING).count()
        failed_backtests = query.filter(Backtest.status == BacktestStatus.FAILED).count()
        
        # 性能统计
        completed_query = query.filter(Backtest.status == BacktestStatus.COMPLETED)
        
        avg_return = completed_query.with_entities(func.avg(Backtest.total_return)).scalar() or 0.0
        avg_sharpe = completed_query.with_entities(func.avg(Backtest.sharpe_ratio)).scalar() or 0.0
        avg_max_drawdown = completed_query.with_entities(func.avg(Backtest.max_drawdown)).scalar() or 0.0
        
        # 最佳表现回测
        best_return_backtest = completed_query.order_by(desc(Backtest.total_return)).first()
        best_sharpe_backtest = completed_query.order_by(desc(Backtest.sharpe_ratio)).first()
        
        return {
            'total_backtests': total_backtests,
            'completed_backtests': completed_backtests,
            'running_backtests': running_backtests,
            'failed_backtests': failed_backtests,
            'success_rate': completed_backtests / total_backtests if total_backtests > 0 else 0,
            
            'avg_return': avg_return,
            'avg_sharpe_ratio': avg_sharpe,
            'avg_max_drawdown': avg_max_drawdown,
            
            'best_return_backtest': {
                'id': best_return_backtest.id,
                'name': best_return_backtest.name,
                'total_return': best_return_backtest.total_return
            } if best_return_backtest else None,
            
            'best_sharpe_backtest': {
                'id': best_sharpe_backtest.id,
                'name': best_sharpe_backtest.name,
                'sharpe_ratio': best_sharpe_backtest.sharpe_ratio
            } if best_sharpe_backtest else None,
        }
    
    def compare_backtests(self, backtest_ids: List[int], user_id: int) -> Dict[str, Any]:
        """比较多个回测结果"""
        if len(backtest_ids) < 2:
            raise ValidationError("至少需要选择2个回测进行比较")
        
        if len(backtest_ids) > 10:
            raise ValidationError("最多只能比较10个回测")
        
        backtests = self.db.query(Backtest).filter(
            and_(
                Backtest.id.in_(backtest_ids),
                Backtest.user_id == user_id,
                Backtest.status == BacktestStatus.COMPLETED
            )
        ).all()
        
        if len(backtests) != len(backtest_ids):
            raise ValidationError("部分回测不存在或未完成")
        
        # 构建比较数据
        comparison_data = {
            'backtests': [],
            'metrics_comparison': {},
            'ranking': {}
        }
        
        # 收集所有回测的基础信息和指标
        for backtest in backtests:
            comparison_data['backtests'].append({
                'id': backtest.id,
                'name': backtest.name,
                'strategy_id': backtest.strategy_id,
                'start_date': backtest.start_date.isoformat(),
                'end_date': backtest.end_date.isoformat(),
                'initial_capital': backtest.initial_capital,
                'final_capital': backtest.final_capital,
                'total_return': backtest.total_return,
                'annual_return': backtest.annual_return,
                'max_drawdown': backtest.max_drawdown,
                'sharpe_ratio': backtest.sharpe_ratio,
                'sortino_ratio': backtest.sortino_ratio,
                'win_rate': backtest.win_rate,
                'profit_factor': backtest.profit_factor,
                'total_trades': backtest.total_trades,
            })
        
        # 计算指标排名
        metrics = ['total_return', 'annual_return', 'sharpe_ratio', 'sortino_ratio', 
                  'win_rate', 'profit_factor']
        
        for metric in metrics:
            sorted_backtests = sorted(backtests, 
                                    key=lambda x: getattr(x, metric), 
                                    reverse=True)
            comparison_data['ranking'][metric] = [bt.id for bt in sorted_backtests]
        
        # 最大回撤排名（越小越好）
        sorted_backtests = sorted(backtests, key=lambda x: x.max_drawdown)
        comparison_data['ranking']['max_drawdown'] = [bt.id for bt in sorted_backtests]
        
        return comparison_data
    
    def clone_backtest(self, backtest_id: int, new_name: str, user_id: int) -> Backtest:
        """克隆回测"""
        try:
            original_backtest = self.db.query(Backtest).filter(
                and_(
                    Backtest.id == backtest_id,
                    Backtest.user_id == user_id
                )
            ).first()
            
            if not original_backtest:
                raise NotFoundError("原回测不存在")
            
            # 检查新名称是否冲突
            existing_backtest = self.db.query(Backtest).filter(
                and_(
                    Backtest.name == new_name,
                    Backtest.user_id == user_id
                )
            ).first()
            
            if existing_backtest:
                raise ConflictError("回测名称已存在")
            
            # 创建克隆回测
            cloned_backtest = Backtest(
                name=new_name,
                description=f"克隆自: {original_backtest.name}",
                strategy_id=original_backtest.strategy_id,
                user_id=user_id,
                start_date=original_backtest.start_date,
                end_date=original_backtest.end_date,
                initial_capital=original_backtest.initial_capital,
                symbols=original_backtest.symbols,
                parameters=original_backtest.parameters,
                status=BacktestStatus.PENDING
            )
            
            self.db.add(cloned_backtest)
            self.db.commit()
            self.db.refresh(cloned_backtest)
            
            logger.info(f"回测克隆成功: {original_backtest.name} -> {new_name}")
            
            return cloned_backtest
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"克隆回测失败: {e}")
            raise  
    
    def analyze_backtest_results(self, backtest_id: int, user_id: int) -> Dict[str, Any]:
        """分析回测结果"""
        try:
            backtest = self.db.query(Backtest).filter(
                and_(
                    Backtest.id == backtest_id,
                    Backtest.user_id == user_id
                )
            ).first()
            
            if not backtest:
                raise NotFoundError("回测不存在")
            
            if backtest.status != BacktestStatus.COMPLETED:
                raise ValidationError("回测尚未完成")
            
            # 分析回测结果
            metrics = self.analyzer.analyze_backtest_results(
                equity_curve=backtest.equity_curve or [],
                trade_records=backtest.trade_records or [],
                daily_returns=backtest.daily_returns or [],
                initial_capital=backtest.initial_capital,
                start_date=backtest.start_date,
                end_date=backtest.end_date
            )
            
            # 生成性能摘要
            performance_summary = self.analyzer.generate_performance_summary(metrics)
            
            # 生成风险报告
            risk_report = self.analyzer.generate_risk_report(metrics)
            
            return {
                "backtest_id": backtest_id,
                "metrics": {
                    "total_return": metrics.total_return,
                    "annual_return": metrics.annual_return,
                    "max_drawdown": metrics.max_drawdown,
                    "sharpe_ratio": metrics.sharpe_ratio,
                    "sortino_ratio": metrics.sortino_ratio,
                    "calmar_ratio": metrics.calmar_ratio,
                    "volatility": metrics.volatility,
                    "win_rate": metrics.win_rate,
                    "profit_factor": metrics.profit_factor,
                    "total_trades": metrics.total_trades,
                    "var_95": metrics.var_95,
                    "cvar_95": metrics.cvar_95,
                    "skewness": metrics.skewness,
                    "kurtosis": metrics.kurtosis,
                    "best_day": metrics.best_day,
                    "worst_day": metrics.worst_day,
                    "max_drawdown_duration": metrics.max_drawdown_duration,
                },
                "performance_summary": performance_summary,
                "risk_report": risk_report,
                "analysis_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"分析回测结果失败: {e}")
            raise
    
    def generate_backtest_report(self, backtest_id: int, user_id: int, 
                               report_type: str = "detailed", 
                               format: str = "html",
                               include_charts: bool = True) -> Dict[str, Any]:
        """生成回测报告"""
        try:
            backtest = self.db.query(Backtest).filter(
                and_(
                    Backtest.id == backtest_id,
                    Backtest.user_id == user_id
                )
            ).first()
            
            if not backtest:
                raise NotFoundError("回测不存在")
            
            if backtest.status != BacktestStatus.COMPLETED:
                raise ValidationError("回测尚未完成")
            
            # 分析回测结果
            metrics = self.analyzer.analyze_backtest_results(
                equity_curve=backtest.equity_curve or [],
                trade_records=backtest.trade_records or [],
                daily_returns=backtest.daily_returns or [],
                initial_capital=backtest.initial_capital,
                start_date=backtest.start_date,
                end_date=backtest.end_date
            )
            
            # 生成报告
            if report_type == "summary":
                report_data = self.report_generator.generate_summary_report(backtest, metrics)
            elif report_type == "detailed":
                report_data = self.report_generator.generate_detailed_report(backtest, metrics)
            else:
                raise ValidationError("不支持的报告类型")
            
            # 生成文件（如果需要）
            file_path = None
            if format == "html":
                file_path = self.report_generator.generate_html_report(backtest, metrics, include_charts)
            
            # 保存报告记录
            report_record = BacktestReport(
                backtest_id=backtest_id,
                report_type=report_type,
                content=report_data,
                file_path=file_path,
                file_format=format
            )
            
            self.db.add(report_record)
            self.db.commit()
            self.db.refresh(report_record)
            
            return {
                "report_id": report_record.id,
                "backtest_id": backtest_id,
                "report_type": report_type,
                "format": format,
                "file_path": file_path,
                "content": report_data,
                "created_at": report_record.created_at.isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"生成回测报告失败: {e}")
            raise
    
    def get_chart_data(self, backtest_id: int, user_id: int, chart_type: str) -> Dict[str, Any]:
        """获取图表数据"""
        try:
            backtest = self.db.query(Backtest).filter(
                and_(
                    Backtest.id == backtest_id,
                    Backtest.user_id == user_id
                )
            ).first()
            
            if not backtest:
                raise NotFoundError("回测不存在")
            
            if backtest.status != BacktestStatus.COMPLETED:
                raise ValidationError("回测尚未完成")
            
            # 根据图表类型返回相应数据
            if chart_type == "equity_curve":
                return self.chart_service.format_equity_curve_data(backtest.equity_curve or [])
            
            elif chart_type == "drawdown":
                return self.chart_service.format_drawdown_data(backtest.equity_curve or [])
            
            elif chart_type == "returns_distribution":
                return self.chart_service.format_returns_distribution_data(backtest.daily_returns or [])
            
            elif chart_type == "monthly_returns":
                return self.chart_service.format_monthly_returns_data(backtest.daily_returns or [])
            
            elif chart_type == "rolling_metrics":
                return self.chart_service.format_rolling_metrics_data(backtest.daily_returns or [])
            
            elif chart_type == "trade_analysis":
                return self.chart_service.format_trade_analysis_data(backtest.trade_records or [])
            
            elif chart_type == "risk_metrics":
                return self.chart_service.format_risk_metrics_data(
                    backtest.daily_returns or [], 
                    backtest.equity_curve or []
                )
            
            else:
                raise ValidationError("不支持的图表类型")
            
        except Exception as e:
            logger.error(f"获取图表数据失败: {e}")
            raise
    
    def get_performance_attribution(self, backtest_id: int, user_id: int) -> Dict[str, Any]:
        """获取业绩归因分析"""
        try:
            backtest = self.db.query(Backtest).filter(
                and_(
                    Backtest.id == backtest_id,
                    Backtest.user_id == user_id
                )
            ).first()
            
            if not backtest:
                raise NotFoundError("回测不存在")
            
            if backtest.status != BacktestStatus.COMPLETED:
                raise ValidationError("回测尚未完成")
            
            # 业绩归因分析
            attribution_data = self.chart_service.format_performance_attribution_data(
                backtest.trade_records or []
            )
            
            return {
                "backtest_id": backtest_id,
                "attribution": attribution_data,
                "analysis_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取业绩归因失败: {e}")
            raise
    
    def compare_backtests_detailed(self, backtest_ids: List[int], user_id: int) -> Dict[str, Any]:
        """详细比较多个回测结果"""
        try:
            if len(backtest_ids) < 2:
                raise ValidationError("至少需要选择2个回测进行比较")
            
            if len(backtest_ids) > 10:
                raise ValidationError("最多只能比较10个回测")
            
            backtests = self.db.query(Backtest).filter(
                and_(
                    Backtest.id.in_(backtest_ids),
                    Backtest.user_id == user_id,
                    Backtest.status == BacktestStatus.COMPLETED
                )
            ).all()
            
            if len(backtests) != len(backtest_ids):
                raise ValidationError("部分回测不存在或未完成")
            
            # 分析每个回测
            metrics_list = []
            for backtest in backtests:
                metrics = self.analyzer.analyze_backtest_results(
                    equity_curve=backtest.equity_curve or [],
                    trade_records=backtest.trade_records or [],
                    daily_returns=backtest.daily_returns or [],
                    initial_capital=backtest.initial_capital,
                    start_date=backtest.start_date,
                    end_date=backtest.end_date
                )
                metrics_list.append(metrics)
            
            # 生成比较报告
            comparison_report = self.report_generator.generate_comparison_report(backtests, metrics_list)
            
            # 格式化比较数据
            comparison_data = []
            for backtest, metrics in zip(backtests, metrics_list):
                comparison_data.append({
                    "id": backtest.id,
                    "name": backtest.name,
                    "total_return": metrics.total_return,
                    "annual_return": metrics.annual_return,
                    "max_drawdown": metrics.max_drawdown,
                    "sharpe_ratio": metrics.sharpe_ratio,
                    "sortino_ratio": metrics.sortino_ratio,
                    "win_rate": metrics.win_rate,
                    "profit_factor": metrics.profit_factor,
                    "volatility": metrics.volatility,
                })
            
            chart_data = self.chart_service.format_comparison_data(comparison_data)
            
            return {
                "comparison_report": comparison_report,
                "chart_data": chart_data,
                "backtests_count": len(backtests),
                "analysis_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"详细比较回测失败: {e}")
            raise
    
    def get_rolling_performance(self, backtest_id: int, user_id: int, window: int = 252) -> Dict[str, Any]:
        """获取滚动性能指标"""
        try:
            backtest = self.db.query(Backtest).filter(
                and_(
                    Backtest.id == backtest_id,
                    Backtest.user_id == user_id
                )
            ).first()
            
            if not backtest:
                raise NotFoundError("回测不存在")
            
            if backtest.status != BacktestStatus.COMPLETED:
                raise ValidationError("回测尚未完成")
            
            if not backtest.daily_returns:
                raise ValidationError("缺少日收益率数据")
            
            # 计算滚动指标
            df = pd.DataFrame(backtest.daily_returns)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            rolling_metrics = self.analyzer.calculate_rolling_metrics(df, window)
            
            if not rolling_metrics:
                return {"message": "数据不足以计算滚动指标", "window": window}
            
            # 格式化数据
            formatted_data = self.chart_service.format_rolling_metrics_data(backtest.daily_returns, window)
            
            return {
                "backtest_id": backtest_id,
                "window": window,
                "rolling_data": formatted_data,
                "analysis_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取滚动性能失败: {e}")
            raise