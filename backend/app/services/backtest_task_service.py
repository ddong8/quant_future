"""
回测任务管理和监控服务
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import uuid
from enum import Enum
from dataclasses import dataclass, asdict
import threading
import queue
import time

from ..models.backtest import Backtest, BacktestStatus
from ..models.user import User
from ..core.backtest_engine import BacktestEngine, BacktestTaskManager
from ..core.exceptions import NotFoundError, ValidationError, PermissionError
from ..core.websocket import websocket_manager

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class TaskAction(Enum):
    """任务操作"""
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    RESTART = "restart"


@dataclass
class BacktestTask:
    """回测任务"""
    id: str
    backtest_id: int
    user_id: int
    priority: TaskPriority
    status: BacktestStatus
    progress: float
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    estimated_duration: Optional[int] = None  # 预估执行时间（秒）
    actual_duration: Optional[int] = None     # 实际执行时间（秒）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'backtest_id': self.backtest_id,
            'user_id': self.user_id,
            'priority': self.priority.value,
            'status': self.status.value,
            'progress': self.progress,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'estimated_duration': self.estimated_duration,
            'actual_duration': self.actual_duration
        }


class BacktestTaskQueue:
    """回测任务队列"""
    
    def __init__(self, max_concurrent_tasks: int = 3):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.pending_queue = queue.PriorityQueue()
        self.running_tasks: Dict[str, BacktestTask] = {}
        self.completed_tasks: Dict[str, BacktestTask] = {}
        self.failed_tasks: Dict[str, BacktestTask] = {}
        self.paused_tasks: Dict[str, BacktestTask] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker_thread = None
        self._task_callbacks: Dict[str, List[Callable]] = {}
    
    def start(self):
        """启动任务队列"""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._stop_event.clear()
            self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker_thread.start()
            logger.info("回测任务队列已启动")
    
    def stop(self):
        """停止任务队列"""
        self._stop_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)
        logger.info("回测任务队列已停止")
    
    def add_task(self, task: BacktestTask) -> bool:
        """添加任务到队列"""
        try:
            with self._lock:
                # 检查是否已存在相同的任务
                if self._task_exists(task.backtest_id):
                    logger.warning(f"回测任务已存在: {task.backtest_id}")
                    return False
                
                # 按优先级排序（优先级高的先执行）
                priority_value = -task.priority.value  # 负数使高优先级排在前面
                self.pending_queue.put((priority_value, task.created_at, task))
                
                logger.info(f"添加回测任务到队列: {task.id}, 优先级: {task.priority}")
                return True
                
        except Exception as e:
            logger.error(f"添加任务失败: {str(e)}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[BacktestTask]:
        """获取任务状态"""
        with self._lock:
            # 检查运行中的任务
            if task_id in self.running_tasks:
                return self.running_tasks[task_id]
            
            # 检查已完成的任务
            if task_id in self.completed_tasks:
                return self.completed_tasks[task_id]
            
            # 检查失败的任务
            if task_id in self.failed_tasks:
                return self.failed_tasks[task_id]
            
            # 检查暂停的任务
            if task_id in self.paused_tasks:
                return self.paused_tasks[task_id]
            
            # 检查待执行队列
            temp_queue = queue.PriorityQueue()
            found_task = None
            
            while not self.pending_queue.empty():
                item = self.pending_queue.get()
                if item[2].id == task_id:
                    found_task = item[2]
                temp_queue.put(item)
            
            # 恢复队列
            self.pending_queue = temp_queue
            
            return found_task
    
    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        with self._lock:
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                task.status = BacktestStatus.PAUSED
                self.paused_tasks[task_id] = task
                del self.running_tasks[task_id]
                logger.info(f"任务已暂停: {task_id}")
                return True
            return False
    
    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        with self._lock:
            if task_id in self.paused_tasks:
                task = self.paused_tasks[task_id]
                task.status = BacktestStatus.PENDING
                priority_value = -task.priority.value
                self.pending_queue.put((priority_value, task.created_at, task))
                del self.paused_tasks[task_id]
                logger.info(f"任务已恢复: {task_id}")
                return True
            return False
    
    def stop_task(self, task_id: str) -> bool:
        """停止任务"""
        with self._lock:
            # 从运行中的任务移除
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                task.status = BacktestStatus.CANCELLED
                task.completed_at = datetime.now()
                self.failed_tasks[task_id] = task
                del self.running_tasks[task_id]
                logger.info(f"运行中任务已停止: {task_id}")
                return True
            
            # 从暂停的任务移除
            if task_id in self.paused_tasks:
                task = self.paused_tasks[task_id]
                task.status = BacktestStatus.CANCELLED
                task.completed_at = datetime.now()
                self.failed_tasks[task_id] = task
                del self.paused_tasks[task_id]
                logger.info(f"暂停任务已停止: {task_id}")
                return True
            
            # 从待执行队列移除
            temp_queue = queue.PriorityQueue()
            found = False
            
            while not self.pending_queue.empty():
                item = self.pending_queue.get()
                if item[2].id == task_id:
                    task = item[2]
                    task.status = BacktestStatus.CANCELLED
                    task.completed_at = datetime.now()
                    self.failed_tasks[task_id] = task
                    found = True
                    logger.info(f"待执行任务已停止: {task_id}")
                else:
                    temp_queue.put(item)
            
            self.pending_queue = temp_queue
            return found
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        with self._lock:
            return {
                'pending_count': self.pending_queue.qsize(),
                'running_count': len(self.running_tasks),
                'completed_count': len(self.completed_tasks),
                'failed_count': len(self.failed_tasks),
                'paused_count': len(self.paused_tasks),
                'max_concurrent': self.max_concurrent_tasks,
                'running_tasks': [task.to_dict() for task in self.running_tasks.values()],
                'queue_health': 'healthy' if len(self.running_tasks) < self.max_concurrent_tasks else 'busy'
            }
    
    def add_task_callback(self, task_id: str, callback: Callable):
        """添加任务回调"""
        if task_id not in self._task_callbacks:
            self._task_callbacks[task_id] = []
        self._task_callbacks[task_id].append(callback)
    
    def _worker_loop(self):
        """工作线程循环"""
        logger.info("回测任务工作线程已启动")
        
        while not self._stop_event.is_set():
            try:
                # 检查是否可以启动新任务
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    time.sleep(1)
                    continue
                
                # 获取下一个任务
                try:
                    priority, created_at, task = self.pending_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # 启动任务
                with self._lock:
                    task.status = BacktestStatus.RUNNING
                    task.started_at = datetime.now()
                    self.running_tasks[task.id] = task
                
                # 异步执行任务
                threading.Thread(
                    target=self._execute_task,
                    args=(task,),
                    daemon=True
                ).start()
                
            except Exception as e:
                logger.error(f"工作线程异常: {str(e)}")
                time.sleep(1)
        
        logger.info("回测任务工作线程已停止")
    
    def _execute_task(self, task: BacktestTask):
        """执行单个任务"""
        try:
            logger.info(f"开始执行回测任务: {task.id}")
            
            # 这里应该调用实际的回测执行逻辑
            # 模拟任务执行
            start_time = time.time()
            
            # 模拟进度更新
            for progress in range(0, 101, 10):
                if self._stop_event.is_set():
                    break
                
                task.progress = progress
                self._notify_progress(task)
                time.sleep(0.5)  # 模拟执行时间
            
            # 任务完成
            end_time = time.time()
            task.actual_duration = int(end_time - start_time)
            task.progress = 100.0
            task.status = BacktestStatus.COMPLETED
            task.completed_at = datetime.now()
            
            with self._lock:
                if task.id in self.running_tasks:
                    del self.running_tasks[task.id]
                self.completed_tasks[task.id] = task
            
            self._notify_completion(task)
            logger.info(f"回测任务完成: {task.id}")
            
        except Exception as e:
            logger.error(f"执行回测任务失败: {task.id}, 错误: {str(e)}")
            
            task.error_message = str(e)
            task.status = BacktestStatus.FAILED
            task.completed_at = datetime.now()
            task.retry_count += 1
            
            with self._lock:
                if task.id in self.running_tasks:
                    del self.running_tasks[task.id]
                
                # 检查是否需要重试
                if task.retry_count < task.max_retries:
                    task.status = BacktestStatus.PENDING
                    priority_value = -task.priority.value
                    self.pending_queue.put((priority_value, task.created_at, task))
                    logger.info(f"任务将重试: {task.id}, 重试次数: {task.retry_count}")
                else:
                    self.failed_tasks[task.id] = task
                    logger.error(f"任务重试次数已达上限: {task.id}")
            
            self._notify_failure(task)
    
    def _task_exists(self, backtest_id: int) -> bool:
        """检查任务是否已存在"""
        # 检查运行中的任务
        for task in self.running_tasks.values():
            if task.backtest_id == backtest_id:
                return True
        
        # 检查暂停的任务
        for task in self.paused_tasks.values():
            if task.backtest_id == backtest_id:
                return True
        
        # 检查待执行队列
        temp_queue = queue.PriorityQueue()
        exists = False
        
        while not self.pending_queue.empty():
            item = self.pending_queue.get()
            if item[2].backtest_id == backtest_id:
                exists = True
            temp_queue.put(item)
        
        self.pending_queue = temp_queue
        return exists
    
    def _notify_progress(self, task: BacktestTask):
        """通知进度更新"""
        try:
            # 发送WebSocket通知
            websocket_manager.send_to_user(
                task.user_id,
                {
                    'type': 'backtest_progress',
                    'task_id': task.id,
                    'backtest_id': task.backtest_id,
                    'progress': task.progress,
                    'status': task.status.value,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # 调用回调函数
            if task.id in self._task_callbacks:
                for callback in self._task_callbacks[task.id]:
                    try:
                        callback(task)
                    except Exception as e:
                        logger.error(f"回调函数执行失败: {str(e)}")
                        
        except Exception as e:
            logger.error(f"通知进度更新失败: {str(e)}")
    
    def _notify_completion(self, task: BacktestTask):
        """通知任务完成"""
        try:
            websocket_manager.send_to_user(
                task.user_id,
                {
                    'type': 'backtest_completed',
                    'task_id': task.id,
                    'backtest_id': task.backtest_id,
                    'status': task.status.value,
                    'actual_duration': task.actual_duration,
                    'timestamp': datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"通知任务完成失败: {str(e)}")
    
    def _notify_failure(self, task: BacktestTask):
        """通知任务失败"""
        try:
            websocket_manager.send_to_user(
                task.user_id,
                {
                    'type': 'backtest_failed',
                    'task_id': task.id,
                    'backtest_id': task.backtest_id,
                    'status': task.status.value,
                    'error_message': task.error_message,
                    'retry_count': task.retry_count,
                    'timestamp': datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"通知任务失败失败: {str(e)}")


class BacktestTaskService:
    """回测任务管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.task_queue = BacktestTaskQueue()
        self.task_queue.start()
    
    def create_task(self, backtest_id: int, user_id: int, 
                   priority: TaskPriority = TaskPriority.NORMAL) -> BacktestTask:
        """创建回测任务"""
        try:
            # 验证回测是否存在
            backtest = self.db.query(Backtest).filter(
                Backtest.id == backtest_id,
                Backtest.user_id == user_id
            ).first()
            
            if not backtest:
                raise NotFoundError("回测不存在或无权限访问")
            
            if backtest.status != BacktestStatus.PENDING:
                raise ValidationError("只能对待执行状态的回测创建任务")
            
            # 创建任务
            task = BacktestTask(
                id=str(uuid.uuid4()),
                backtest_id=backtest_id,
                user_id=user_id,
                priority=priority,
                status=BacktestStatus.PENDING,
                progress=0.0,
                created_at=datetime.now(),
                estimated_duration=self._estimate_duration(backtest)
            )
            
            # 添加到队列
            if self.task_queue.add_task(task):
                logger.info(f"回测任务创建成功: {task.id}")
                return task
            else:
                raise ValidationError("任务添加到队列失败")
                
        except Exception as e:
            logger.error(f"创建回测任务失败: {str(e)}")
            raise
    
    def get_task_status(self, task_id: str, user_id: int) -> Optional[BacktestTask]:
        """获取任务状态"""
        task = self.task_queue.get_task_status(task_id)
        if task and task.user_id == user_id:
            return task
        return None
    
    def control_task(self, task_id: str, action: TaskAction, user_id: int) -> bool:
        """控制任务执行"""
        try:
            # 验证权限
            task = self.get_task_status(task_id, user_id)
            if not task:
                raise NotFoundError("任务不存在或无权限访问")
            
            # 执行操作
            if action == TaskAction.PAUSE:
                return self.task_queue.pause_task(task_id)
            elif action == TaskAction.RESUME:
                return self.task_queue.resume_task(task_id)
            elif action == TaskAction.STOP:
                return self.task_queue.stop_task(task_id)
            elif action == TaskAction.RESTART:
                # 停止当前任务并创建新任务
                self.task_queue.stop_task(task_id)
                new_task = self.create_task(task.backtest_id, user_id, task.priority)
                return new_task is not None
            else:
                raise ValidationError(f"不支持的操作: {action}")
                
        except Exception as e:
            logger.error(f"控制任务失败: {str(e)}")
            raise
    
    def get_user_tasks(self, user_id: int, status: Optional[BacktestStatus] = None,
                      limit: int = 50) -> List[BacktestTask]:
        """获取用户的任务列表"""
        try:
            all_tasks = []
            
            # 获取队列中的所有任务
            queue_status = self.task_queue.get_queue_status()
            
            # 添加运行中的任务
            all_tasks.extend(self.task_queue.running_tasks.values())
            
            # 添加已完成的任务
            all_tasks.extend(self.task_queue.completed_tasks.values())
            
            # 添加失败的任务
            all_tasks.extend(self.task_queue.failed_tasks.values())
            
            # 添加暂停的任务
            all_tasks.extend(self.task_queue.paused_tasks.values())
            
            # 过滤用户任务
            user_tasks = [task for task in all_tasks if task.user_id == user_id]
            
            # 状态过滤
            if status:
                user_tasks = [task for task in user_tasks if task.status == status]
            
            # 按创建时间排序
            user_tasks.sort(key=lambda x: x.created_at, reverse=True)
            
            return user_tasks[:limit]
            
        except Exception as e:
            logger.error(f"获取用户任务失败: {str(e)}")
            return []
    
    def get_queue_statistics(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        try:
            queue_status = self.task_queue.get_queue_status()
            
            # 计算平均执行时间
            completed_tasks = list(self.task_queue.completed_tasks.values())
            avg_duration = 0
            if completed_tasks:
                durations = [task.actual_duration for task in completed_tasks if task.actual_duration]
                avg_duration = sum(durations) / len(durations) if durations else 0
            
            # 计算成功率
            total_finished = len(completed_tasks) + len(self.task_queue.failed_tasks)
            success_rate = len(completed_tasks) / total_finished if total_finished > 0 else 0
            
            return {
                **queue_status,
                'avg_execution_time': avg_duration,
                'success_rate': success_rate,
                'total_processed': total_finished,
                'system_load': len(self.task_queue.running_tasks) / self.task_queue.max_concurrent_tasks
            }
            
        except Exception as e:
            logger.error(f"获取队列统计失败: {str(e)}")
            return {}
    
    def get_task_history(self, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """获取任务历史记录"""
        try:
            # 获取指定天数内的任务
            cutoff_date = datetime.now() - timedelta(days=days)
            
            all_tasks = []
            all_tasks.extend(self.task_queue.completed_tasks.values())
            all_tasks.extend(self.task_queue.failed_tasks.values())
            
            # 过滤用户任务和时间范围
            history_tasks = [
                task for task in all_tasks 
                if task.user_id == user_id and task.created_at >= cutoff_date
            ]
            
            # 按日期分组统计
            daily_stats = {}
            for task in history_tasks:
                date_key = task.created_at.date().isoformat()
                if date_key not in daily_stats:
                    daily_stats[date_key] = {
                        'date': date_key,
                        'total': 0,
                        'completed': 0,
                        'failed': 0,
                        'avg_duration': 0,
                        'tasks': []
                    }
                
                daily_stats[date_key]['total'] += 1
                daily_stats[date_key]['tasks'].append(task.to_dict())
                
                if task.status == BacktestStatus.COMPLETED:
                    daily_stats[date_key]['completed'] += 1
                elif task.status == BacktestStatus.FAILED:
                    daily_stats[date_key]['failed'] += 1
            
            # 计算每日平均执行时间
            for stats in daily_stats.values():
                durations = [
                    task['actual_duration'] 
                    for task in stats['tasks'] 
                    if task['actual_duration']
                ]
                stats['avg_duration'] = sum(durations) / len(durations) if durations else 0
            
            return list(daily_stats.values())
            
        except Exception as e:
            logger.error(f"获取任务历史失败: {str(e)}")
            return []
    
    def compare_backtest_results(self, backtest_ids: List[int], user_id: int) -> Dict[str, Any]:
        """比较回测结果"""
        try:
            # 验证回测权限
            backtests = self.db.query(Backtest).filter(
                Backtest.id.in_(backtest_ids),
                or_(
                    Backtest.user_id == user_id,
                    Backtest.is_public == True
                )
            ).all()
            
            if len(backtests) != len(backtest_ids):
                raise ValidationError("部分回测不存在或无权限访问")
            
            # 只比较已完成的回测
            completed_backtests = [bt for bt in backtests if bt.status == BacktestStatus.COMPLETED]
            
            if len(completed_backtests) < 2:
                raise ValidationError("至少需要2个已完成的回测进行比较")
            
            # 生成比较数据
            comparison_data = {
                'backtests': [],
                'metrics_comparison': {},
                'performance_ranking': [],
                'summary': {}
            }
            
            # 收集回测数据
            for backtest in completed_backtests:
                comparison_data['backtests'].append({
                    'id': backtest.id,
                    'name': backtest.name,
                    'total_return': backtest.total_return,
                    'annual_return': backtest.annual_return,
                    'max_drawdown': backtest.max_drawdown,
                    'sharpe_ratio': backtest.sharpe_ratio,
                    'win_rate': backtest.win_rate,
                    'total_trades': backtest.total_trades,
                    'start_date': backtest.start_date,
                    'end_date': backtest.end_date
                })
            
            # 指标比较
            metrics = ['total_return', 'annual_return', 'max_drawdown', 'sharpe_ratio', 'win_rate']
            for metric in metrics:
                values = [getattr(bt, metric) for bt in completed_backtests if getattr(bt, metric) is not None]
                if values:
                    comparison_data['metrics_comparison'][metric] = {
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values),
                        'best_backtest': max(completed_backtests, key=lambda x: getattr(x, metric) or 0).name
                    }
            
            # 性能排名（基于夏普比率）
            ranked_backtests = sorted(
                completed_backtests, 
                key=lambda x: x.sharpe_ratio or 0, 
                reverse=True
            )
            
            comparison_data['performance_ranking'] = [
                {
                    'rank': i + 1,
                    'backtest_id': bt.id,
                    'name': bt.name,
                    'sharpe_ratio': bt.sharpe_ratio,
                    'total_return': bt.total_return
                }
                for i, bt in enumerate(ranked_backtests)
            ]
            
            # 生成总结
            best_backtest = ranked_backtests[0]
            comparison_data['summary'] = {
                'best_performer': best_backtest.name,
                'best_return': max(bt.total_return or 0 for bt in completed_backtests),
                'lowest_drawdown': min(abs(bt.max_drawdown or 0) for bt in completed_backtests),
                'highest_sharpe': max(bt.sharpe_ratio or 0 for bt in completed_backtests),
                'comparison_date': datetime.now().isoformat()
            }
            
            return comparison_data
            
        except Exception as e:
            logger.error(f"比较回测结果失败: {str(e)}")
            raise
    
    def _estimate_duration(self, backtest: Backtest) -> int:
        """估算回测执行时间"""
        try:
            # 基于历史数据估算执行时间
            start_date = datetime.fromisoformat(backtest.start_date)
            end_date = datetime.fromisoformat(backtest.end_date)
            days = (end_date - start_date).days
            
            # 基础时间：每天1秒
            base_time = days
            
            # 根据标的数量调整
            symbols_count = len(backtest.symbols) if backtest.symbols else 1
            time_multiplier = 1 + (symbols_count - 1) * 0.2
            
            # 根据数据频率调整
            frequency_multipliers = {
                '1m': 10,
                '5m': 5,
                '15m': 3,
                '30m': 2,
                '1h': 1.5,
                '4h': 1.2,
                '1d': 1,
                '1w': 0.5,
                '1M': 0.2
            }
            
            freq_multiplier = frequency_multipliers.get(backtest.frequency, 1)
            
            estimated_time = int(base_time * time_multiplier * freq_multiplier)
            
            # 最小30秒，最大3600秒（1小时）
            return max(30, min(estimated_time, 3600))
            
        except Exception as e:
            logger.error(f"估算执行时间失败: {str(e)}")
            return 300  # 默认5分钟
    
    def cleanup_old_tasks(self, days: int = 30):
        """清理旧任务"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 清理已完成的任务
            old_completed = [
                task_id for task_id, task in self.task_queue.completed_tasks.items()
                if task.completed_at and task.completed_at < cutoff_date
            ]
            
            for task_id in old_completed:
                del self.task_queue.completed_tasks[task_id]
            
            # 清理失败的任务
            old_failed = [
                task_id for task_id, task in self.task_queue.failed_tasks.items()
                if task.completed_at and task.completed_at < cutoff_date
            ]
            
            for task_id in old_failed:
                del self.task_queue.failed_tasks[task_id]
            
            logger.info(f"清理了 {len(old_completed) + len(old_failed)} 个旧任务")
            
        except Exception as e:
            logger.error(f"清理旧任务失败: {str(e)}")


# 全局任务服务实例
_task_service_instance = None

def get_task_service(db: Session) -> BacktestTaskService:
    """获取任务服务实例"""
    global _task_service_instance
    if _task_service_instance is None:
        _task_service_instance = BacktestTaskService(db)
    return _task_service_instance