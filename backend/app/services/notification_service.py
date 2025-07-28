"""
通知服务
负责发送各种类型的通知（邮件、短信、微信等）
"""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import aiohttp

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class NotificationService:
    """通知服务"""
    
    def __init__(self):
        self.email_config = {
            'smtp_server': settings.SMTP_SERVER,
            'smtp_port': settings.SMTP_PORT,
            'username': settings.SMTP_USERNAME,
            'password': settings.SMTP_PASSWORD,
            'use_tls': settings.SMTP_USE_TLS
        }
        
        self.sms_config = {
            'api_url': settings.SMS_API_URL,
            'api_key': settings.SMS_API_KEY,
            'api_secret': settings.SMS_API_SECRET
        }
        
        self.wechat_config = {
            'webhook_url': settings.WECHAT_WEBHOOK_URL,
            'app_id': settings.WECHAT_APP_ID,
            'app_secret': settings.WECHAT_APP_SECRET
        }
    
    async def send_alert(
        self,
        title: str,
        message: str,
        level: str = 'info',
        channels: List[str] = None,
        recipients: List[str] = None
    ):
        """发送告警通知"""
        if channels is None:
            channels = ['email']  # 默认邮件通知
        
        tasks = []
        
        for channel in channels:
            if channel == 'email':
                tasks.append(self._send_email_alert(title, message, level, recipients))
            elif channel == 'sms':
                tasks.append(self._send_sms_alert(title, message, level, recipients))
            elif channel == 'wechat':
                tasks.append(self._send_wechat_alert(title, message, level, recipients))
            elif channel == 'webhook':
                tasks.append(self._send_webhook_alert(title, message, level, recipients))
        
        # 并行发送所有通知
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_email_alert(
        self,
        title: str,
        message: str,
        level: str,
        recipients: List[str] = None
    ):
        """发送邮件告警"""
        try:
            if not self.email_config['smtp_server']:
                logger.warning("邮件服务未配置")
                return
            
            if recipients is None:
                recipients = [settings.ADMIN_EMAIL] if settings.ADMIN_EMAIL else []
            
            if not recipients:
                logger.warning("没有邮件接收者")
                return
            
            # 创建邮件内容
            msg = MIMEMultipart()
            msg['From'] = self.email_config['username']
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"[{level.upper()}] {title}"
            
            # 邮件正文
            html_body = self._create_email_template(title, message, level)
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                if self.email_config['use_tls']:
                    server.starttls()
                
                server.login(self.email_config['username'], self.email_config['password'])
                server.send_message(msg)
            
            logger.info(f"邮件告警发送成功: {title}")
            
        except Exception as e:
            logger.error(f"发送邮件告警失败: {e}")
    
    def _create_email_template(self, title: str, message: str, level: str) -> str:
        """创建邮件模板"""
        level_colors = {
            'info': '#17a2b8',
            'warning': '#ffc107',
            'error': '#dc3545',
            'critical': '#dc3545'
        }
        
        color = level_colors.get(level, '#17a2b8')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background-color: {color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
                .message {{ background-color: #f8f9fa; padding: 15px; border-radius: 4px; margin: 15px 0; white-space: pre-line; }}
                .timestamp {{ color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                    <div class="timestamp">告警时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                <div class="content">
                    <div class="message">{message}</div>
                </div>
                <div class="footer">
                    量化交易平台 - 系统监控告警
                </div>
            </div>
        </body>
        </html>
        """
    
    async def _send_sms_alert(
        self,
        title: str,
        message: str,
        level: str,
        recipients: List[str] = None
    ):
        """发送短信告警"""
        try:
            if not self.sms_config['api_url']:
                logger.warning("短信服务未配置")
                return
            
            if recipients is None:
                recipients = [settings.ADMIN_PHONE] if settings.ADMIN_PHONE else []
            
            if not recipients:
                logger.warning("没有短信接收者")
                return
            
            # 短信内容（限制长度）
            sms_content = f"[{level.upper()}] {title}\n{message[:100]}..."
            
            # 发送短信API调用
            async with aiohttp.ClientSession() as session:
                for phone in recipients:
                    payload = {
                        'api_key': self.sms_config['api_key'],
                        'api_secret': self.sms_config['api_secret'],
                        'phone': phone,
                        'message': sms_content
                    }
                    
                    async with session.post(self.sms_config['api_url'], json=payload) as response:
                        if response.status == 200:
                            logger.info(f"短信告警发送成功: {phone}")
                        else:
                            logger.error(f"短信告警发送失败: {phone}, 状态码: {response.status}")
            
        except Exception as e:
            logger.error(f"发送短信告警失败: {e}")
    
    async def _send_wechat_alert(
        self,
        title: str,
        message: str,
        level: str,
        recipients: List[str] = None
    ):
        """发送微信告警"""
        try:
            if not self.wechat_config['webhook_url']:
                logger.warning("微信服务未配置")
                return
            
            # 微信消息格式
            level_colors = {
                'info': 'info',
                'warning': 'warning',
                'error': 'error',
                'critical': 'error'
            }
            
            color = level_colors.get(level, 'info')
            
            payload = {
                'msgtype': 'markdown',
                'markdown': {
                    'content': f"""## {title}
                    
**告警级别**: <font color="{color}">{level.upper()}</font>

**告警内容**:
{message}

**告警时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
量化交易平台监控系统"""
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.wechat_config['webhook_url'], json=payload) as response:
                    if response.status == 200:
                        logger.info("微信告警发送成功")
                    else:
                        logger.error(f"微信告警发送失败, 状态码: {response.status}")
            
        except Exception as e:
            logger.error(f"发送微信告警失败: {e}")
    
    async def _send_webhook_alert(
        self,
        title: str,
        message: str,
        level: str,
        recipients: List[str] = None
    ):
        """发送Webhook告警"""
        try:
            webhook_urls = recipients or [settings.WEBHOOK_URL] if settings.WEBHOOK_URL else []
            
            if not webhook_urls:
                logger.warning("没有配置Webhook URL")
                return
            
            payload = {
                'title': title,
                'message': message,
                'level': level,
                'timestamp': datetime.now().isoformat(),
                'source': 'quantitative_trading_platform'
            }
            
            async with aiohttp.ClientSession() as session:
                for url in webhook_urls:
                    try:
                        async with session.post(url, json=payload, timeout=10) as response:
                            if response.status == 200:
                                logger.info(f"Webhook告警发送成功: {url}")
                            else:
                                logger.error(f"Webhook告警发送失败: {url}, 状态码: {response.status}")
                    except asyncio.TimeoutError:
                        logger.error(f"Webhook告警超时: {url}")
                    except Exception as e:
                        logger.error(f"Webhook告警发送异常: {url}, 错误: {e}")
            
        except Exception as e:
            logger.error(f"发送Webhook告警失败: {e}")
    
    async def send_notification(
        self,
        title: str,
        message: str,
        channel: str = 'email',
        recipients: List[str] = None,
        template: str = None,
        data: Dict[str, Any] = None
    ):
        """发送通用通知"""
        try:
            if channel == 'email':
                await self._send_email_notification(title, message, recipients, template, data)
            elif channel == 'sms':
                await self._send_sms_notification(title, message, recipients)
            elif channel == 'wechat':
                await self._send_wechat_notification(title, message, recipients)
            else:
                logger.warning(f"不支持的通知渠道: {channel}")
                
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
    
    async def _send_email_notification(
        self,
        title: str,
        message: str,
        recipients: List[str] = None,
        template: str = None,
        data: Dict[str, Any] = None
    ):
        """发送邮件通知"""
        try:
            if not self.email_config['smtp_server']:
                logger.warning("邮件服务未配置")
                return
            
            if recipients is None:
                recipients = [settings.ADMIN_EMAIL] if settings.ADMIN_EMAIL else []
            
            if not recipients:
                logger.warning("没有邮件接收者")
                return
            
            # 创建邮件内容
            msg = MIMEMultipart()
            msg['From'] = self.email_config['username']
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = title
            
            # 使用模板或默认格式
            if template and data:
                html_body = self._render_email_template(template, data)
            else:
                html_body = self._create_simple_email_template(title, message)
            
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                if self.email_config['use_tls']:
                    server.starttls()
                
                server.login(self.email_config['username'], self.email_config['password'])
                server.send_message(msg)
            
            logger.info(f"邮件通知发送成功: {title}")
            
        except Exception as e:
            logger.error(f"发送邮件通知失败: {e}")
    
    def _create_simple_email_template(self, title: str, message: str) -> str:
        """创建简单邮件模板"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
                .message {{ line-height: 1.6; white-space: pre-line; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                </div>
                <div class="content">
                    <div class="message">{message}</div>
                </div>
                <div class="footer">
                    量化交易平台
                </div>
            </div>
        </body>
        </html>
        """
    
    def _render_email_template(self, template: str, data: Dict[str, Any]) -> str:
        """渲染邮件模板"""
        try:
            # 简单的模板渲染，实际项目中可以使用Jinja2等模板引擎
            rendered = template
            for key, value in data.items():
                rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
            return rendered
        except Exception as e:
            logger.error(f"渲染邮件模板失败: {e}")
            return self._create_simple_email_template("通知", str(data))
    
    async def _send_sms_notification(
        self,
        title: str,
        message: str,
        recipients: List[str] = None
    ):
        """发送短信通知"""
        await self._send_sms_alert(title, message, 'info', recipients)
    
    async def _send_wechat_notification(
        self,
        title: str,
        message: str,
        recipients: List[str] = None
    ):
        """发送微信通知"""
        await self._send_wechat_alert(title, message, 'info', recipients)
    
    async def send_batch_notification(
        self,
        notifications: List[Dict[str, Any]]
    ):
        """批量发送通知"""
        tasks = []
        
        for notification in notifications:
            task = self.send_notification(
                title=notification.get('title', ''),
                message=notification.get('message', ''),
                channel=notification.get('channel', 'email'),
                recipients=notification.get('recipients'),
                template=notification.get('template'),
                data=notification.get('data')
            )
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def test_configuration(self) -> Dict[str, bool]:
        """测试通知配置"""
        results = {}
        
        # 测试邮件配置
        try:
            if self.email_config['smtp_server']:
                with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                    if self.email_config['use_tls']:
                        server.starttls()
                    server.login(self.email_config['username'], self.email_config['password'])
                results['email'] = True
            else:
                results['email'] = False
        except Exception as e:
            logger.error(f"邮件配置测试失败: {e}")
            results['email'] = False
        
        # 测试短信配置
        results['sms'] = bool(self.sms_config['api_url'] and self.sms_config['api_key'])
        
        # 测试微信配置
        results['wechat'] = bool(self.wechat_config['webhook_url'])
        
        return results