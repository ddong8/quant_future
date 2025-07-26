"""
用户活动日志服务
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging

from ..models import SystemLog, User
from ..core.dependencies import PaginationParams

logger = logging.getLogger(__name__)


class ActivityService:
    """用户活动日志服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_user_activity(
        self,
        user_id: int,
        action: str,
        description: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        extra_data: Optional[dict] = None
    ) -> bool:
        """记录用户活动日志"""
        try:
            log_entry = SystemLog(
                level="INFO",
                module="user_activity",
                function=action,
                message=description,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                extra_data=extra_data or {},
            )
            
            self.db.add(log_entry)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"记录用户活动日志失败: {e}")
            return False
    
    def get_user_activities(
        self,
        user_id: int,
        days: int = 30,
        pagination: Optional[PaginationParams] = None
    ) -> tuple[List[dict], int]:
        """获取用户活动日志"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(SystemLog).filter(
            SystemLog.user_id == user_id,
            SystemLog.module == "user_activity",
            SystemLog.created_at >= start_date
        ).order_by(desc(SystemLog.created_at))
        
        total = query.count()
        
        if pagination:
            query = query.offset(pagination.offset).limit(pagination.page_size)
        
        logs = query.all()
        
        activities = []
        for log in logs:
            activities.append({
                "id": log.id,
                "action": log.function,
                "description": log.message,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "extra_data": log.extra_data,
                "created_at": log.created_at,
            })
        
        return activities, total
    
    def get_system_activities(
        self,
        days: int = 7,
        pagination: Optional[PaginationParams] = None
    ) -> tuple[List[dict], int]:
        """获取系统活动日志（管理员用）"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(SystemLog, User).outerjoin(
            User, SystemLog.user_id == User.id
        ).filter(
            SystemLog.module == "user_activity",
            SystemLog.created_at >= start_date
        ).order_by(desc(SystemLog.created_at))
        
        total = query.count()
        
        if pagination:
            query = query.offset(pagination.offset).limit(pagination.page_size)
        
        results = query.all()
        
        activities = []
        for log, user in results:
            activities.append({
                "id": log.id,
                "user_id": log.user_id,
                "username": user.username if user else "未知用户",
                "action": log.function,
                "description": log.message,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "extra_data": log.extra_data,
                "created_at": log.created_at,
            })
        
        return activities, total