"""
通知管理服务
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func
from jinja2 import Template
import json
import re

from ..models.notification import (
    Notification, NotificationTemplate, NotificationPreference,
    NotificationRule, NotificationQueue, NotificationLog,
    NotificationDigest, NotificationType, NotificationChannel,
    NotificationPriority, NotificationStatus
)
from ..models.user import User
from ..schemas.notification import (
    NotificationCreate, NotificationBatchCreate,
    NotificationPreferenceUpdate, NotificationRuleCreate
)

logger = logging.getLogger(__name__)

class NotificationService:
    """通知管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 通知模板管理 ====================
    
    def get_templates(self, type_filter: Optional[NotificationType] = None) -> List[Dict[str, Any]]:
        """获取通知模板列表"""
        try:
            query = self.db.query(NotificationTemplate).filter(
                NotificationTemplate.is_active == True
            )
            
            if type_filter:
                query = query.filter(NotificationTemplate.type == type_filter)
            
            templates = query.order_by(NotificationTemplate.name).all()
            
            return [
                {
                    'id': template.id,
                    'name': template.name,
                    'code': template.code,
                    'type': template.type.value,
                    'title_template': template.title_template,
                    'content_template': template.content_template,
                    'channels': [ch.value for ch in template.channels],
                    'variables': template.variables or {},
                    'default_priority': template.default_priority.value,
                    'created_at': template.created_at,
                    'updated_at': template.updated_at
                }
                for template in templates
            ]
            
        except Exception as e:
            logger.error(f"获取通知模板失败: {e}")
            raise
    
    def get_template_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """根据代码获取通知模板"""
        try:
            template = self.db.query(NotificationTemplate).filter(
                NotificationTemplate.code == code,
                NotificationTemplate.is_active == True
            ).first()
            
            if not template:
                return None
            
            return {
                'id': template.id,
                'name': template.name,
                'code': template.code,
                'type': template.type.value,
                'title_template': template.title_template,
                'content_template': template.content_template,
                'channels': [ch.value for ch in template.channels],
                'variables': template.variables or {},
                'default_priority': template.default_priority.value
            }
            
        except Exception as e:
            logger.error(f"获取通知模板失败: {e}")
            return None
    
    def render_template(self, template_code: str, variables: Dict[str, Any]) -> Tuple[str, str]:
        """渲染通知模板"""
        try:
            template = self.get_template_by_code(template_code)
            if not template:
                raise ValueError(f"模板不存在: {template_code}")
            
            # 渲染标题
            title_template = Template(template['title_template'])
            title = title_template.render(**variables)
            
            # 渲染内容
            content_template = Template(template['content_template'])
            content = content_template.render(**variables)
            
            return title, content
            
        except Exception as e:
            logger.error(f"渲染模板失败: {e}")
            raise
    
    # ==================== 通知消息管理 ====================
    
    def create_notification(self, notification_data: NotificationCreate) -> Dict[str, Any]:
        """创建通知消息"""
        try:
            # 渲染模板（如果使用模板）
            if notification_data.template_id:
                template = self.db.query(NotificationTemplate).filter(
                    NotificationTemplate.id == notification_data.template_id
                ).first()
                
                if template:
                    title, content = self.render_template(
                        template.code, 
                        notification_data.variables or {}
                    )
                    notification_data.title = title
                    notification_data.content = content
            
            # 创建通知记录
            notification = Notification(
                user_id=notification_data.user_id,
                template_id=notification_data.template_id,
                type=notification_data.type,
                title=notification_data.title,
                content=notification_data.content,
                channel=notification_data.channel,
                priority=notification_data.priority,
                recipient=notification_data.recipient,
                metadata=notification_data.metadata,
                variables=notification_data.variables,
                expires_at=notification_data.expires_at,
                status=NotificationStatus.PENDING
            )
            
            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)
            
            # 添加到发送队列
            self._add_to_queue(notification)
            
            logger.info(f"通知创建成功: {notification.id}")
            return self._format_notification(notification)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建通知失败: {e}")
            raise
    
    def batch_create_notifications(self, batch_data: NotificationBatchCreate) -> Dict[str, Any]:
        """批量创建通知"""
        try:
            template = self.get_template_by_code(batch_data.template_code)
            if not template:
                raise ValueError(f"模板不存在: {batch_data.template_code}")
            
            notifications = []
            success_count = 0
            failed_count = 0
            notification_ids = []
            
            for user_id in batch_data.user_ids:
                try:
                    # 渲染模板
                    title, content = self.render_template(
                        batch_data.template_code,
                        batch_data.variables or {}
                    )
                    
                    # 为每个渠道创建通知
                    for channel in batch_data.channels:
                        notification = Notification(
                            user_id=user_id,
                            template_id=template['id'],
                            type=NotificationType(template['type']),
                            title=title,
                            content=content,
                            channel=channel,
                            priority=batch_data.priority,
                            metadata={'batch_id': f"batch_{datetime.now().timestamp()}"},
                            variables=batch_data.variables,
                            status=NotificationStatus.PENDING
                        )
                        
                        notifications.append(notification)
                        notification_ids.append(notification.id)
                        success_count += 1
                        
                except Exception as e:
                    logger.warning(f"创建用户通知失败 {user_id}: {e}")
                    failed_count += 1
            
            # 批量插入
            if notifications:
                self.db.add_all(notifications)
                self.db.commit()
                
                # 添加到队列
                for notification in notifications:
                    self._add_to_queue(notification, batch_data.scheduled_at)
            
            logger.info(f"批量通知创建完成: 成功{success_count}, 失败{failed_count}")
            return {
                'total_count': len(batch_data.user_ids) * len(batch_data.channels),
                'success_count': success_count,
                'failed_count': failed_count,
                'notification_ids': notification_ids
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"批量创建通知失败: {e}")
            raise
    
    def get_user_notifications(self, user_id: int, limit: int = 50, 
                              skip: int = 0, unread_only: bool = False) -> Dict[str, Any]:
        """获取用户通知列表"""
        try:
            query = self.db.query(Notification).filter(
                Notification.user_id == user_id
            )
            
            if unread_only:
                query = query.filter(Notification.read_at.is_(None))
            
            # 过滤未过期的通知
            query = query.filter(
                or_(
                    Notification.expires_at.is_(None),
                    Notification.expires_at > datetime.now()
                )
            )
            
            total_count = query.count()
            notifications = query.order_by(
                desc(Notification.created_at)
            ).offset(skip).limit(limit).all()
            
            return {
                'notifications': [self._format_notification(n) for n in notifications],
                'total_count': total_count,
                'unread_count': self._get_unread_count(user_id),
                'page_info': {
                    'skip': skip,
                    'limit': limit,
                    'has_more': skip + len(notifications) < total_count
                }
            }
            
        except Exception as e:
            logger.error(f"获取用户通知失败: {e}")
            raise
    
    def mark_notifications_read(self, user_id: int, notification_ids: List[int]) -> int:
        """标记通知为已读"""
        try:
            updated_count = self.db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.id.in_(notification_ids),
                Notification.read_at.is_(None)
            ).update(
                {'read_at': datetime.now(), 'status': NotificationStatus.READ},
                synchronize_session=False
            )
            
            self.db.commit()
            
            logger.info(f"标记通知已读: 用户{user_id}, 数量{updated_count}")
            return updated_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"标记通知已读失败: {e}")
            raise
    
    def delete_notifications(self, user_id: int, notification_ids: List[int], 
                           hard_delete: bool = False) -> int:
        """删除通知"""
        try:
            if hard_delete:
                # 硬删除
                deleted_count = self.db.query(Notification).filter(
                    Notification.user_id == user_id,
                    Notification.id.in_(notification_ids)
                ).delete(synchronize_session=False)
            else:
                # 软删除（标记为已取消）
                deleted_count = self.db.query(Notification).filter(
                    Notification.user_id == user_id,
                    Notification.id.in_(notification_ids)
                ).update(
                    {'status': NotificationStatus.CANCELLED},
                    synchronize_session=False
                )
            
            self.db.commit()
            
            logger.info(f"删除通知: 用户{user_id}, 数量{deleted_count}")
            return deleted_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除通知失败: {e}")
            raise
    
    # ==================== 通知偏好管理 ====================
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """获取用户通知偏好"""
        try:
            preference = self.db.query(NotificationPreference).filter(
                NotificationPreference.user_id == user_id
            ).first()
            
            if not preference:
                # 创建默认偏好
                preference = self._create_default_preference(user_id)
            
            return {
                'id': preference.id,
                'user_id': preference.user_id,
                'enabled': preference.enabled,
                'quiet_hours_enabled': preference.quiet_hours_enabled,
                'quiet_hours_start': preference.quiet_hours_start,
                'quiet_hours_end': preference.quiet_hours_end,
                'email_enabled': preference.email_enabled,
                'sms_enabled': preference.sms_enabled,
                'push_enabled': preference.push_enabled,
                'in_app_enabled': preference.in_app_enabled,
                'trade_notifications': preference.trade_notifications or {},
                'risk_notifications': preference.risk_notifications or {},
                'system_notifications': preference.system_notifications or {},
                'market_notifications': preference.market_notifications or {},
                'account_notifications': preference.account_notifications or {},
                'security_notifications': preference.security_notifications or {},
                'max_notifications_per_hour': preference.max_notifications_per_hour,
                'digest_enabled': preference.digest_enabled,
                'digest_frequency': preference.digest_frequency,
                'digest_time': preference.digest_time,
                'created_at': preference.created_at,
                'updated_at': preference.updated_at
            }
            
        except Exception as e:
            logger.error(f"获取通知偏好失败: {e}")
            raise
    
    def update_user_preferences(self, user_id: int, 
                               preference_data: NotificationPreferenceUpdate) -> Dict[str, Any]:
        """更新用户通知偏好"""
        try:
            preference = self.db.query(NotificationPreference).filter(
                NotificationPreference.user_id == user_id
            ).first()
            
            if not preference:
                preference = self._create_default_preference(user_id)
            
            # 更新字段
            update_data = preference_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(preference, field, value)
            
            preference.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(preference)
            
            logger.info(f"通知偏好更新成功: {user_id}")
            return self.get_user_preferences(user_id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新通知偏好失败: {e}")
            raise
    
    # ==================== 通知规则管理 ====================
    
    def create_notification_rule(self, user_id: int, 
                                rule_data: NotificationRuleCreate) -> Dict[str, Any]:
        """创建通知规则"""
        try:
            rule = NotificationRule(
                user_id=user_id,
                name=rule_data.name,
                description=rule_data.description,
                event_type=rule_data.event_type,
                conditions=rule_data.conditions,
                template_code=rule_data.template_code,
                channels=rule_data.channels,
                priority=rule_data.priority,
                rate_limit=rule_data.rate_limit,
                max_per_day=rule_data.max_per_day,
                is_active=rule_data.is_active
            )
            
            self.db.add(rule)
            self.db.commit()
            self.db.refresh(rule)
            
            logger.info(f"通知规则创建成功: {rule.id}")
            return self._format_notification_rule(rule)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建通知规则失败: {e}")
            raise
    
    def get_user_notification_rules(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户通知规则"""
        try:
            rules = self.db.query(NotificationRule).filter(
                NotificationRule.user_id == user_id
            ).order_by(desc(NotificationRule.created_at)).all()
            
            return [self._format_notification_rule(rule) for rule in rules]
            
        except Exception as e:
            logger.error(f"获取通知规则失败: {e}")
            raise
    
    # ==================== 通知统计 ====================
    
    def get_notification_stats(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """获取通知统计"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # 基础统计
            total_query = self.db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.created_at >= start_date
            )
            
            total_notifications = total_query.count()
            unread_notifications = total_query.filter(
                Notification.read_at.is_(None)
            ).count()
            
            # 按类型统计
            type_stats = self.db.query(
                Notification.type,
                func.count(Notification.id).label('count')
            ).filter(
                Notification.user_id == user_id,
                Notification.created_at >= start_date
            ).group_by(Notification.type).all()
            
            # 按渠道统计
            channel_stats = self.db.query(
                Notification.channel,
                func.count(Notification.id).label('count')
            ).filter(
                Notification.user_id == user_id,
                Notification.created_at >= start_date
            ).group_by(Notification.channel).all()
            
            # 按状态统计
            status_stats = self.db.query(
                Notification.status,
                func.count(Notification.id).label('count')
            ).filter(
                Notification.user_id == user_id,
                Notification.created_at >= start_date
            ).group_by(Notification.status).all()
            
            # 最近通知
            recent_notifications = total_query.order_by(
                desc(Notification.created_at)
            ).limit(10).all()
            
            return {
                'total_notifications': total_notifications,
                'unread_notifications': unread_notifications,
                'notifications_by_type': {stat.type.value: stat.count for stat in type_stats},
                'notifications_by_channel': {stat.channel.value: stat.count for stat in channel_stats},
                'notifications_by_status': {stat.status.value: stat.count for stat in status_stats},
                'recent_notifications': [self._format_notification(n) for n in recent_notifications]
            }
            
        except Exception as e:
            logger.error(f"获取通知统计失败: {e}")
            raise
    
    # ==================== 通知发送 ====================
    
    async def send_notification(self, notification_id: int) -> bool:
        """发送通知"""
        try:
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id
            ).first()
            
            if not notification:
                logger.warning(f"通知不存在: {notification_id}")
                return False
            
            # 检查用户偏好
            if not self._check_user_preference(notification):
                logger.info(f"用户偏好不允许发送通知: {notification_id}")
                notification.status = NotificationStatus.CANCELLED
                self.db.commit()
                return False
            
            # 根据渠道发送
            success = False
            if notification.channel == NotificationChannel.EMAIL:
                success = await self._send_email(notification)
            elif notification.channel == NotificationChannel.SMS:
                success = await self._send_sms(notification)
            elif notification.channel == NotificationChannel.PUSH:
                success = await self._send_push(notification)
            elif notification.channel == NotificationChannel.IN_APP:
                success = await self._send_in_app(notification)
            
            # 更新状态
            if success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.now()
            else:
                notification.status = NotificationStatus.FAILED
                notification.retry_count += 1
            
            self.db.commit()
            
            # 记录日志
            self._log_notification_action(
                notification, 
                'send', 
                'success' if success else 'failed'
            )
            
            return success
            
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            return False
    
    # ==================== 私有辅助方法 ====================
    
    def _format_notification(self, notification: Notification) -> Dict[str, Any]:
        """格式化通知数据"""
        return {
            'id': notification.id,
            'user_id': notification.user_id,
            'template_id': notification.template_id,
            'type': notification.type.value,
            'title': notification.title,
            'content': notification.content,
            'channel': notification.channel.value,
            'priority': notification.priority.value,
            'status': notification.status.value,
            'recipient': notification.recipient,
            'sent_at': notification.sent_at,
            'delivered_at': notification.delivered_at,
            'read_at': notification.read_at,
            'error_message': notification.error_message,
            'retry_count': notification.retry_count,
            'metadata': notification.metadata or {},
            'expires_at': notification.expires_at,
            'created_at': notification.created_at,
            'updated_at': notification.updated_at
        }
    
    def _format_notification_rule(self, rule: NotificationRule) -> Dict[str, Any]:
        """格式化通知规则数据"""
        return {
            'id': rule.id,
            'user_id': rule.user_id,
            'name': rule.name,
            'description': rule.description,
            'event_type': rule.event_type,
            'conditions': rule.conditions,
            'template_code': rule.template_code,
            'channels': [ch.value for ch in rule.channels],
            'priority': rule.priority.value,
            'rate_limit': rule.rate_limit,
            'max_per_day': rule.max_per_day,
            'is_active': rule.is_active,
            'trigger_count': rule.trigger_count,
            'last_triggered_at': rule.last_triggered_at,
            'created_at': rule.created_at,
            'updated_at': rule.updated_at
        }
    
    def _create_default_preference(self, user_id: int) -> NotificationPreference:
        """创建默认通知偏好"""
        preference = NotificationPreference(
            user_id=user_id,
            enabled=True,
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True,
            in_app_enabled=True,
            trade_notifications={
                'order_filled': True,
                'position_closed': True,
                'stop_loss_triggered': True
            },
            risk_notifications={
                'margin_call': True,
                'large_loss': True
            },
            system_notifications={
                'maintenance': True,
                'security_alert': True
            }
        )
        
        self.db.add(preference)
        self.db.commit()
        self.db.refresh(preference)
        
        return preference
    
    def _add_to_queue(self, notification: Notification, 
                     scheduled_at: Optional[datetime] = None):
        """添加通知到发送队列"""
        queue_item = NotificationQueue(
            notification_id=notification.id,
            queue_name=f"queue_{notification.channel.value}",
            scheduled_at=scheduled_at or datetime.now(),
            priority=self._get_queue_priority(notification.priority)
        )
        
        self.db.add(queue_item)
        self.db.commit()
    
    def _get_queue_priority(self, priority: NotificationPriority) -> int:
        """获取队列优先级"""
        priority_map = {
            NotificationPriority.URGENT: 1,
            NotificationPriority.HIGH: 2,
            NotificationPriority.NORMAL: 3,
            NotificationPriority.LOW: 4
        }
        return priority_map.get(priority, 3)
    
    def _get_unread_count(self, user_id: int) -> int:
        """获取未读通知数量"""
        return self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
            Notification.status != NotificationStatus.CANCELLED
        ).count()
    
    def _check_user_preference(self, notification: Notification) -> bool:
        """检查用户通知偏好"""
        try:
            preference = self.db.query(NotificationPreference).filter(
                NotificationPreference.user_id == notification.user_id
            ).first()
            
            if not preference or not preference.enabled:
                return False
            
            # 检查渠道偏好
            channel_enabled = {
                NotificationChannel.EMAIL: preference.email_enabled,
                NotificationChannel.SMS: preference.sms_enabled,
                NotificationChannel.PUSH: preference.push_enabled,
                NotificationChannel.IN_APP: preference.in_app_enabled
            }
            
            if not channel_enabled.get(notification.channel, False):
                return False
            
            # 检查免打扰时间
            if preference.quiet_hours_enabled:
                current_time = datetime.now().time()
                start_time = datetime.strptime(preference.quiet_hours_start, '%H:%M').time()
                end_time = datetime.strptime(preference.quiet_hours_end, '%H:%M').time()
                
                if start_time <= end_time:
                    if start_time <= current_time <= end_time:
                        return False
                else:
                    if current_time >= start_time or current_time <= end_time:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"检查用户偏好失败: {e}")
            return True  # 默认允许发送
    
    def _log_notification_action(self, notification: Notification, 
                                action: str, status: str, message: str = None):
        """记录通知操作日志"""
        try:
            log = NotificationLog(
                notification_id=notification.id,
                user_id=notification.user_id,
                action=action,
                status=status,
                message=message,
                channel=notification.channel.value
            )
            
            self.db.add(log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"记录通知日志失败: {e}")
    
    # 发送方法（需要具体实现）
    async def _send_email(self, notification: Notification) -> bool:
        """发送邮件通知"""
        # TODO: 实现邮件发送逻辑
        logger.info(f"发送邮件通知: {notification.id}")
        return True
    
    async def _send_sms(self, notification: Notification) -> bool:
        """发送短信通知"""
        # TODO: 实现短信发送逻辑
        logger.info(f"发送短信通知: {notification.id}")
        return True
    
    async def _send_push(self, notification: Notification) -> bool:
        """发送推送通知"""
        # TODO: 实现推送通知逻辑
        logger.info(f"发送推送通知: {notification.id}")
        return True
    
    async def _send_in_app(self, notification: Notification) -> bool:
        """发送站内信"""
        # 站内信直接标记为已发送
        logger.info(f"发送站内信: {notification.id}")
        return True