"""
报告调度服务
负责定时报告生成任务的管理和执行
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from croniter import croniter
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database_manager import DatabaseManager
from app.core.logging import get_logger
from app.models.system import ScheduledTask
from app.services.report_service import report_service
from app.services.notification_service import NotificationService

logger = get_logger(__name__)


class ReportScheduler:
    """报告调度器"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.notification_service = NotificationService()
        self.is_running = False
        self.scheduled_tasks = {}
        
    async def start_scheduler(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("报告调度器已在运行")
            return
            
        self.is_running = True
        logger.info("启动报告调度器")
        
        # 加载调度任务
        await self._load_scheduled_tasks()
        
        # 启动调度循环
        await self._run_scheduler_loop()
    
    async def stop_scheduler(self):
        """停止调度器"""
        self.is_running = False
        logger.info("停止报告调度器")
    
    async def _load_scheduled_tasks(self):
        """加载调度任务"""
        try:
            with self.db_manager.get_session() as db:
                tasks = db.query(ScheduledTask).filter(
                    and_(
                        ScheduledTask.is_active == True,
                        ScheduledTask.task_type == 'report'
                    )
                ).all()
                
                for task in tasks:
                    await self._schedule_task(task)
                    
                logger.info(f"加载了 {len(tasks)} 个报告调度任务")
                
        except Exception as e:
            logger.error(f"加载调度任务失败: {e}")
    
    async def _schedule_task(self, task: ScheduledTask):
        """调度单个任务"""
        try:
            # 计算下次执行时间
            cron = croniter(task.cron_expression, datetime.utcnow())
            next_run = cron.get_next(datetime)
            
            # 更新数据库中的下次执行时间
            with self.db_manager.get_session() as db:
                db_task = db.query(ScheduledTask).filter(
                    ScheduledTask.id == task.id
                ).first()
                if db_task:
                    db_task.next_run_at = next_run
                    db.commit()
            
            # 添加到内存调度
            self.scheduled_tasks[task.id] = {
                'task': task,
                'next_run': next_run,
                'cron': cron
            }
            
            logger.info(f"调度任务: {task.name}, 下次执行: {next_run}")
            
        except Exception as e:
            logger.error(f"调度任务失败: {e}")
    
    async def _run_scheduler_loop(self):
        """运行调度循环"""
        while self.is_running:
            try:
                current_time = datetime.utcnow()
                
                # 检查需要执行的任务
                for task_id, task_info in list(self.scheduled_tasks.items()):
                    if current_time >= task_info['next_run']:
                        # 执行任务
                        await self._execute_task(task_info['task'])
                        
                        # 计算下次执行时间
                        next_run = task_info['cron'].get_next(datetime)
                        task_info['next_run'] = next_run
                        
                        # 更新数据库
                        await self._update_task_next_run(task_id, next_run)
                
                # 等待一分钟再检查
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"调度循环错误: {e}")
                await asyncio.sleep(60)
    
    async def _execute_task(self, task: ScheduledTask):
        """执行报告生成任务"""
        try:
            logger.info(f"开始执行报告任务: {task.name}")
            
            # 更新任务状态
            await self._update_task_status(task.id, 'running', datetime.utcnow())
            
            # 解析任务参数
            params = task.parameters or {}
            report_type = params.get('report_type', 'trading')
            user_id = params.get('user_id')
            template_name = params.get('template_name')
            recipients = params.get('recipients', [])
            
            # 计算报告时间范围
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=params.get('period_days', 1))
            
            # 生成报告
            if report_type == 'trading':
                html_content = await report_service.generate_trading_report(
                    user_id=user_id,
                    start_date=start_date,
                    end_date=end_date,
                    template_name=template_name
                )
            elif report_type == 'performance':
                html_content = await report_service.generate_performance_report(
                    user_id=user_id,
                    start_date=start_date,
                    end_date=end_date,
                    template_name=template_name
                )
            elif report_type == 'risk':
                html_content = await report_service.generate_risk_report(
                    user_id=user_id,
                    start_date=start_date,
                    end_date=end_date,
                    template_name=template_name
                )
            else:
                raise ValueError(f"不支持的报告类型: {report_type}")
            
            # 保存报告文件
            report_path = await self._save_report_file(
                task.name, html_content, params.get('format', 'html')
            )
            
            # 发送通知
            if recipients:
                await self._send_report_notification(
                    task.name, report_path, recipients, params
                )
            
            # 更新任务状态
            await self._update_task_status(
                task.id, 'success', datetime.utcnow(), None
            )
            
            # 更新统计
            await self._update_task_stats(task.id, True)
            
            logger.info(f"报告任务执行成功: {task.name}")
            
        except Exception as e:
            logger.error(f"执行报告任务失败: {task.name}, 错误: {e}")
            
            # 更新任务状态
            await self._update_task_status(
                task.id, 'failed', datetime.utcnow(), str(e)
            )
            
            # 更新统计
            await self._update_task_stats(task.id, False)
    
    async def _save_report_file(
        self,
        task_name: str,
        content: str,
        format: str = 'html'
    ) -> str:
        """保存报告文件"""
        try:
            from pathlib import Path
            
            # 创建报告目录
            reports_dir = Path("reports/scheduled")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{task_name}_{timestamp}.{format}"
            file_path = reports_dir / filename
            
            if format == 'html':
                # 保存HTML文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            elif format == 'pdf':
                # 转换为PDF并保存
                pdf_path = await report_service.export_report_to_pdf(
                    content, str(file_path.with_suffix('.pdf'))
                )
                file_path = Path(pdf_path)
            
            logger.info(f"报告文件保存成功: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"保存报告文件失败: {e}")
            raise
    
    async def _send_report_notification(
        self,
        task_name: str,
        report_path: str,
        recipients: List[str],
        params: Dict[str, Any]
    ):
        """发送报告通知"""
        try:
            # 准备邮件内容
            subject = f"定时报告: {task_name}"
            message = f"""
            您好，
            
            定时报告 "{task_name}" 已生成完成。
            
            报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            报告类型: {params.get('report_type', '未知')}
            
            请查看附件中的报告文件。
            
            此邮件由系统自动发送，请勿回复。
            """
            
            # 发送邮件通知
            await self.notification_service.send_notification(
                title=subject,
                message=message,
                channel='email',
                recipients=recipients,
                data={
                    'attachment_path': report_path,
                    'task_name': task_name
                }
            )
            
            logger.info(f"报告通知发送成功: {task_name}")
            
        except Exception as e:
            logger.error(f"发送报告通知失败: {e}")
    
    async def _update_task_status(
        self,
        task_id: int,
        status: str,
        run_time: datetime,
        error_message: str = None
    ):
        """更新任务状态"""
        try:
            with self.db_manager.get_session() as db:
                task = db.query(ScheduledTask).filter(
                    ScheduledTask.id == task_id
                ).first()
                
                if task:
                    task.last_run_at = run_time
                    task.last_status = status
                    task.last_error = error_message
                    db.commit()
                    
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
    
    async def _update_task_next_run(self, task_id: int, next_run: datetime):
        """更新任务下次执行时间"""
        try:
            with self.db_manager.get_session() as db:
                task = db.query(ScheduledTask).filter(
                    ScheduledTask.id == task_id
                ).first()
                
                if task:
                    task.next_run_at = next_run
                    db.commit()
                    
        except Exception as e:
            logger.error(f"更新任务下次执行时间失败: {e}")
    
    async def _update_task_stats(self, task_id: int, success: bool):
        """更新任务统计"""
        try:
            with self.db_manager.get_session() as db:
                task = db.query(ScheduledTask).filter(
                    ScheduledTask.id == task_id
                ).first()
                
                if task:
                    task.total_runs += 1
                    if success:
                        task.success_runs += 1
                    else:
                        task.failed_runs += 1
                    db.commit()
                    
        except Exception as e:
            logger.error(f"更新任务统计失败: {e}")
    
    async def add_scheduled_task(
        self,
        name: str,
        cron_expression: str,
        parameters: Dict[str, Any]
    ) -> int:
        """添加调度任务"""
        try:
            with self.db_manager.get_session() as db:
                task = ScheduledTask(
                    name=name,
                    description=f"定时报告: {name}",
                    task_type='report',
                    cron_expression=cron_expression,
                    parameters=parameters,
                    is_active=True
                )
                
                db.add(task)
                db.commit()
                db.refresh(task)
                
                # 添加到调度
                await self._schedule_task(task)
                
                logger.info(f"添加调度任务成功: {name}")
                return task.id
                
        except Exception as e:
            logger.error(f"添加调度任务失败: {e}")
            raise
    
    async def remove_scheduled_task(self, task_id: int) -> bool:
        """移除调度任务"""
        try:
            with self.db_manager.get_session() as db:
                task = db.query(ScheduledTask).filter(
                    ScheduledTask.id == task_id
                ).first()
                
                if task:
                    task.is_active = False
                    db.commit()
                    
                    # 从内存调度中移除
                    if task_id in self.scheduled_tasks:
                        del self.scheduled_tasks[task_id]
                    
                    logger.info(f"移除调度任务成功: {task.name}")
                    return True
                else:
                    return False
                    
        except Exception as e:
            logger.error(f"移除调度任务失败: {e}")
            return False
    
    async def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """获取调度任务列表"""
        try:
            with self.db_manager.get_session() as db:
                tasks = db.query(ScheduledTask).filter(
                    ScheduledTask.task_type == 'report'
                ).all()
                
                task_list = []
                for task in tasks:
                    task_info = {
                        'id': task.id,
                        'name': task.name,
                        'description': task.description,
                        'cron_expression': task.cron_expression,
                        'is_active': task.is_active,
                        'last_run_at': task.last_run_at,
                        'next_run_at': task.next_run_at,
                        'last_status': task.last_status,
                        'total_runs': task.total_runs,
                        'success_runs': task.success_runs,
                        'failed_runs': task.failed_runs,
                        'parameters': task.parameters
                    }
                    task_list.append(task_info)
                
                return task_list
                
        except Exception as e:
            logger.error(f"获取调度任务列表失败: {e}")
            return []
    
    async def execute_task_now(self, task_id: int) -> bool:
        """立即执行任务"""
        try:
            with self.db_manager.get_session() as db:
                task = db.query(ScheduledTask).filter(
                    ScheduledTask.id == task_id
                ).first()
                
                if task:
                    await self._execute_task(task)
                    return True
                else:
                    return False
                    
        except Exception as e:
            logger.error(f"立即执行任务失败: {e}")
            return False


# 全局报告调度器实例
report_scheduler = ReportScheduler()