"""
通知服务
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """通知服务"""
    
    def __init__(self):
        self.email_config = {
            'smtp_server': settings.SMTP_HOST,
            'smtp_port': settings.SMTP_PORT,
            'username': settings.SMTP_USER,
            'password': settings.SMTP_PASSWORD,
            'use_tls': True  # 默认使用TLS
        }
    
    async def send_email(
        self,
        subject: str,
        content: str,
        recipients: Optional[List[str]] = None,
        email_type: str = "text"
    ) -> bool:
        """发送邮件通知"""
        try:
            if recipients is None:
                recipients = []
            
            if not recipients:
                logger.warning("没有指定邮件接收者")
                return False
            
            if not all(self.email_config.values()):
                logger.warning("邮件配置不完整，跳过邮件发送")
                return False
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.email_config['username']
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # 添加邮件内容
            if email_type == "html":
                msg.attach(MIMEText(content, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                if self.email_config['use_tls']:
                    server.starttls()
                
                server.login(self.email_config['username'], self.email_config['password'])
                server.send_message(msg)
            
            logger.info(f"邮件发送成功: {subject} -> {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False
    
    async def send_sms(
        self,
        content: str,
        recipients: Optional[List[str]] = None
    ) -> bool:
        """发送短信通知"""
        try:
            if recipients is None:
                recipients = []
            
            if not recipients:
                logger.warning("没有指定短信接收者")
                return False
            
            # 这里应该实现短信发送逻辑
            # 简化实现：只记录日志
            logger.info(f"短信发送: {content} -> {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"发送短信失败: {e}")
            return False
    
    async def send_webhook(
        self,
        content: str,
        webhook_url: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """发送Webhook通知"""
        try:
            if not webhook_url:
                logger.warning("没有指定Webhook URL")
                return False
            
            # 这里应该实现Webhook发送逻辑
            # 简化实现：只记录日志
            logger.info(f"Webhook发送: {content} -> {webhook_url}")
            return True
            
        except Exception as e:
            logger.error(f"发送Webhook失败: {e}")
            return False
    
    async def send_system_alert(
        self,
        title: str,
        message: str,
        level: str = "INFO",
        recipients: Optional[List[str]] = None
    ) -> bool:
        """发送系统告警"""
        try:
            subject = f"[{level}] {title}"
            content = f"""
系统告警通知

告警级别: {level}
告警时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
告警标题: {title}
告警内容: {message}

请及时处理相关问题。
            """.strip()
            
            # 发送邮件通知
            email_sent = await self.send_email(subject, content, recipients)
            
            # 记录告警日志
            if level == "CRITICAL":
                logger.critical(f"系统告警: {title} - {message}")
            elif level == "ERROR":
                logger.error(f"系统告警: {title} - {message}")
            elif level == "WARNING":
                logger.warning(f"系统告警: {title} - {message}")
            else:
                logger.info(f"系统告警: {title} - {message}")
            
            return email_sent
            
        except Exception as e:
            logger.error(f"发送系统告警失败: {e}")
            return False
    
    async def send_trade_notification(
        self,
        user_id: int,
        trade_info: Dict[str, Any],
        recipients: Optional[List[str]] = None
    ) -> bool:
        """发送交易通知"""
        try:
            subject = f"交易通知 - 用户{user_id}"
            content = f"""
交易通知

用户ID: {user_id}
交易时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
交易信息: {trade_info}

请注意查看交易详情。
            """.strip()
            
            return await self.send_email(subject, content, recipients)
            
        except Exception as e:
            logger.error(f"发送交易通知失败: {e}")
            return False
    
    async def send_risk_alert(
        self,
        user_id: int,
        risk_info: Dict[str, Any],
        recipients: Optional[List[str]] = None
    ) -> bool:
        """发送风险告警"""
        try:
            subject = f"风险告警 - 用户{user_id}"
            content = f"""
风险告警通知

用户ID: {user_id}
告警时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
风险信息: {risk_info}

请立即处理相关风险。
            """.strip()
            
            return await self.send_email(subject, content, recipients)
            
        except Exception as e:
            logger.error(f"发送风险告警失败: {e}")
            return False


# 全局通知服务实例
notification_service = NotificationService()