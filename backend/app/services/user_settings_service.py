"""
用户设置服务
"""
import logging
import secrets
import qrcode
import io
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from passlib.context import CryptContext
import pyotp
from ..models.user import User
from ..models.user_settings import UserSettings, SecuritySettings, NotificationSettings, LoginDevice, UserActivityLog
from ..core.database import get_db

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserSettingsService:
    """用户设置服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 用户个人资料管理 ====================
    
    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """获取用户个人资料"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'phone': user.phone,
                'avatar': user.avatar,
                'timezone': user.timezone or 'Asia/Shanghai',
                'language': user.language or 'zh-CN',
                'date_format': user.date_format or 'YYYY-MM-DD',
                'currency_display': user.currency_display or 'USD',
                'created_at': user.created_at,
                'updated_at': user.updated_at,
                'last_login_at': user.last_login_at
            }
            
        except Exception as e:
            logger.error(f"获取用户个人资料失败: {e}")
            raise
    
    def update_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户个人资料"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            # 更新允许的字段
            allowed_fields = [
                'full_name', 'phone', 'avatar', 'timezone', 
                'language', 'date_format', 'currency_display'
            ]
            
            for field in allowed_fields:
                if field in profile_data:
                    setattr(user, field, profile_data[field])
            
            user.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(user)
            
            # 记录活动日志
            self._log_user_activity(user_id, "profile_updated", "更新个人资料")
            
            logger.info(f"用户个人资料更新成功: {user_id}")
            return self.get_user_profile(user_id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新用户个人资料失败: {e}")
            raise
    
    # ==================== 用户设置管理 ====================
    
    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """获取用户设置"""
        try:
            settings = self.db.query(UserSettings).filter(
                UserSettings.user_id == user_id
            ).first()
            
            if not settings:
                # 创建默认设置
                settings = self._create_default_user_settings(user_id)
            
            return {
                'id': settings.id,
                'user_id': settings.user_id,
                'theme': settings.theme,
                'sidebar_collapsed': settings.sidebar_collapsed,
                'auto_refresh': settings.auto_refresh,
                'refresh_interval': settings.refresh_interval,
                'default_chart_period': settings.default_chart_period,
                'show_advanced_features': settings.show_advanced_features,
                'created_at': settings.created_at,
                'updated_at': settings.updated_at
            }
            
        except Exception as e:
            logger.error(f"获取用户设置失败: {e}")
            raise
    
    def update_user_settings(self, user_id: int, settings_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户设置"""
        try:
            settings = self.db.query(UserSettings).filter(
                UserSettings.user_id == user_id
            ).first()
            
            if not settings:
                settings = self._create_default_user_settings(user_id)
            
            # 更新设置
            allowed_fields = [
                'theme', 'sidebar_collapsed', 'auto_refresh', 'refresh_interval',
                'default_chart_period', 'show_advanced_features'
            ]
            
            for field in allowed_fields:
                if field in settings_data:
                    setattr(settings, field, settings_data[field])
            
            settings.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(settings)
            
            logger.info(f"用户设置更新成功: {user_id}")
            return self.get_user_settings(user_id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新用户设置失败: {e}")
            raise
    
    # ==================== 安全设置管理 ====================
    
    def get_security_settings(self, user_id: int) -> Dict[str, Any]:
        """获取安全设置"""
        try:
            settings = self.db.query(SecuritySettings).filter(
                SecuritySettings.user_id == user_id
            ).first()
            
            if not settings:
                settings = self._create_default_security_settings(user_id)
            
            return {
                'id': settings.id,
                'user_id': settings.user_id,
                'two_factor_enabled': settings.two_factor_enabled,
                'login_notifications': settings.login_notifications,
                'session_timeout': settings.session_timeout,
                'ip_whitelist': settings.ip_whitelist or [],
                'allowed_devices': settings.allowed_devices,
                'created_at': settings.created_at,
                'updated_at': settings.updated_at
            }
            
        except Exception as e:
            logger.error(f"获取安全设置失败: {e}")
            raise
    
    def update_security_settings(self, user_id: int, security_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新安全设置"""
        try:
            settings = self.db.query(SecuritySettings).filter(
                SecuritySettings.user_id == user_id
            ).first()
            
            if not settings:
                settings = self._create_default_security_settings(user_id)
            
            # 更新设置
            allowed_fields = [
                'login_notifications', 'session_timeout', 'ip_whitelist', 'allowed_devices'
            ]
            
            for field in allowed_fields:
                if field in security_data:
                    setattr(settings, field, security_data[field])
            
            settings.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(settings)
            
            # 记录活动日志
            self._log_user_activity(user_id, "security_settings_updated", "更新安全设置")
            
            logger.info(f"安全设置更新成功: {user_id}")
            return self.get_security_settings(user_id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新安全设置失败: {e}")
            raise
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """修改密码"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            # 验证当前密码
            if not pwd_context.verify(current_password, user.password_hash):
                return False
            
            # 更新密码
            user.password_hash = pwd_context.hash(new_password)
            user.updated_at = datetime.now()
            self.db.commit()
            
            # 记录活动日志
            self._log_user_activity(user_id, "password_changed", "修改密码")
            
            logger.info(f"用户密码修改成功: {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"修改密码失败: {e}")
            raise
    
    def toggle_two_factor_auth(self, user_id: int, enabled: bool) -> bool:
        """启用/关闭双因子认证"""
        try:
            settings = self.db.query(SecuritySettings).filter(
                SecuritySettings.user_id == user_id
            ).first()
            
            if not settings:
                settings = self._create_default_security_settings(user_id)
            
            if enabled and not settings.two_factor_secret:
                # 生成新的密钥
                settings.two_factor_secret = pyotp.random_base32()
                settings.backup_codes = self._generate_backup_codes()
            
            settings.two_factor_enabled = enabled
            settings.updated_at = datetime.now()
            self.db.commit()
            
            # 记录活动日志
            action = "启用" if enabled else "关闭"
            self._log_user_activity(user_id, "two_factor_toggled", f"{action}双因子认证")
            
            logger.info(f"双因子认证{action}成功: {user_id}")
            return enabled
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"切换双因子认证失败: {e}")
            raise
    
    def generate_two_factor_qr_code(self, user_id: int) -> Dict[str, Any]:
        """生成双因子认证二维码"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            settings = self.db.query(SecuritySettings).filter(
                SecuritySettings.user_id == user_id
            ).first()
            
            if not settings or not settings.two_factor_secret:
                raise ValueError("双因子认证未设置")
            
            # 生成TOTP URI
            totp = pyotp.TOTP(settings.two_factor_secret)
            provisioning_uri = totp.provisioning_uri(
                name=user.email or user.username,
                issuer_name="量化交易平台"
            )
            
            # 生成二维码
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 转换为base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_code_data = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                'qr_code_url': f"data:image/png;base64,{qr_code_data}",
                'secret_key': settings.two_factor_secret,
                'backup_codes': settings.backup_codes or []
            }
            
        except Exception as e:
            logger.error(f"生成双因子认证二维码失败: {e}")
            raise
    
    def verify_two_factor_code(self, user_id: int, code: str) -> bool:
        """验证双因子认证码"""
        try:
            settings = self.db.query(SecuritySettings).filter(
                SecuritySettings.user_id == user_id
            ).first()
            
            if not settings or not settings.two_factor_secret:
                return False
            
            # 验证TOTP码
            totp = pyotp.TOTP(settings.two_factor_secret)
            if totp.verify(code):
                return True
            
            # 验证备用码
            if settings.backup_codes and code in settings.backup_codes:
                # 使用后移除备用码
                settings.backup_codes.remove(code)
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"验证双因子认证码失败: {e}")
            return False
    
    # ==================== 通知设置管理 ====================
    
    def get_notification_settings(self, user_id: int) -> Dict[str, Any]:
        """获取通知设置"""
        try:
            settings = self.db.query(NotificationSettings).filter(
                NotificationSettings.user_id == user_id
            ).first()
            
            if not settings:
                settings = self._create_default_notification_settings(user_id)
            
            return {
                'id': settings.id,
                'user_id': settings.user_id,
                'email_enabled': settings.email_enabled,
                'sms_enabled': settings.sms_enabled,
                'push_enabled': settings.push_enabled,
                'trade_notifications': settings.trade_notifications or [],
                'risk_notifications': settings.risk_notifications or [],
                'system_notifications': settings.system_notifications or [],
                'notification_hours': settings.notification_hours or {},
                'created_at': settings.created_at,
                'updated_at': settings.updated_at
            }
            
        except Exception as e:
            logger.error(f"获取通知设置失败: {e}")
            raise
    
    def update_notification_settings(self, user_id: int, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新通知设置"""
        try:
            settings = self.db.query(NotificationSettings).filter(
                NotificationSettings.user_id == user_id
            ).first()
            
            if not settings:
                settings = self._create_default_notification_settings(user_id)
            
            # 更新设置
            allowed_fields = [
                'email_enabled', 'sms_enabled', 'push_enabled',
                'trade_notifications', 'risk_notifications', 'system_notifications',
                'notification_hours'
            ]
            
            for field in allowed_fields:
                if field in notification_data:
                    setattr(settings, field, notification_data[field])
            
            settings.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(settings)
            
            logger.info(f"通知设置更新成功: {user_id}")
            return self.get_notification_settings(user_id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新通知设置失败: {e}")
            raise
    
    # ==================== 登录设备管理 ====================
    
    def get_login_devices(self, user_id: int) -> List[Dict[str, Any]]:
        """获取登录设备列表"""
        try:
            devices = self.db.query(LoginDevice).filter(
                LoginDevice.user_id == user_id
            ).order_by(desc(LoginDevice.last_login_at)).all()
            
            return [
                {
                    'id': device.id,
                    'user_id': device.user_id,
                    'device_name': device.device_name,
                    'device_type': device.device_type,
                    'browser': device.browser,
                    'os': device.os,
                    'ip_address': device.ip_address,
                    'location': device.location,
                    'is_current': device.is_current,
                    'last_login_at': device.last_login_at,
                    'created_at': device.created_at
                }
                for device in devices
            ]
            
        except Exception as e:
            logger.error(f"获取登录设备列表失败: {e}")
            raise
    
    def remove_login_device(self, user_id: int, device_id: int) -> bool:
        """移除登录设备"""
        try:
            device = self.db.query(LoginDevice).filter(
                LoginDevice.id == device_id,
                LoginDevice.user_id == user_id,
                LoginDevice.is_current == False  # 不能移除当前设备
            ).first()
            
            if not device:
                return False
            
            self.db.delete(device)
            self.db.commit()
            
            # 记录活动日志
            self._log_user_activity(user_id, "device_removed", f"移除设备: {device.device_name}")
            
            logger.info(f"登录设备移除成功: {user_id}, {device_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"移除登录设备失败: {e}")
            raise
    
    def logout_all_devices(self, user_id: int) -> int:
        """登出所有设备"""
        try:
            devices = self.db.query(LoginDevice).filter(
                LoginDevice.user_id == user_id,
                LoginDevice.is_current == False
            ).all()
            
            count = len(devices)
            
            for device in devices:
                self.db.delete(device)
            
            self.db.commit()
            
            # 记录活动日志
            self._log_user_activity(user_id, "logout_all_devices", f"登出所有设备: {count}个")
            
            logger.info(f"登出所有设备成功: {user_id}, {count}个设备")
            return count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"登出所有设备失败: {e}")
            raise
    
    # ==================== 用户活动日志 ====================
    
    def get_user_activity_log(self, user_id: int, limit: int = 50, skip: int = 0) -> Dict[str, Any]:
        """获取用户活动日志"""
        try:
            query = self.db.query(UserActivityLog).filter(
                UserActivityLog.user_id == user_id
            ).order_by(desc(UserActivityLog.created_at))
            
            total_count = query.count()
            logs = query.offset(skip).limit(limit).all()
            
            return {
                'logs': [
                    {
                        'id': log.id,
                        'action': log.action,
                        'description': log.description,
                        'ip_address': log.ip_address,
                        'user_agent': log.user_agent,
                        'metadata': log.metadata or {},
                        'created_at': log.created_at
                    }
                    for log in logs
                ],
                'total_count': total_count,
                'page_info': {
                    'skip': skip,
                    'limit': limit,
                    'has_more': skip + len(logs) < total_count
                }
            }
            
        except Exception as e:
            logger.error(f"获取用户活动日志失败: {e}")
            raise
    
    def export_user_data(self, user_id: int, export_type: str = "all") -> Dict[str, Any]:
        """导出用户数据"""
        try:
            export_data = {}
            
            # 基本信息
            if export_type in ["all", "profile"]:
                export_data["profile"] = self.get_user_profile(user_id)
            
            # 设置信息
            if export_type in ["all", "settings"]:
                export_data["settings"] = {
                    "user_settings": self.get_user_settings(user_id),
                    "security_settings": self.get_security_settings(user_id),
                    "notification_settings": self.get_notification_settings(user_id)
                }
            
            # 活动日志
            if export_type in ["all", "activity"]:
                export_data["activity_log"] = self.get_user_activity_log(user_id, limit=1000)
            
            # 登录设备
            if export_type in ["all", "devices"]:
                export_data["login_devices"] = self.get_login_devices(user_id)
            
            # 生成导出文件
            import json
            export_content = json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
            
            return {
                'export_id': f"export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'status': 'completed',
                'content': export_content,
                'content_type': 'application/json',
                'file_size': len(export_content.encode('utf-8')),
                'created_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"导出用户数据失败: {e}")
            raise
    
    def delete_user_account(self, user_id: int, password: str) -> bool:
        """删除用户账户"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            # 验证密码
            if not pwd_context.verify(password, user.password_hash):
                return False
            
            # 记录删除日志
            self._log_user_activity(user_id, "account_deleted", "删除账户")
            
            # 软删除用户（标记为已删除，不实际删除数据）
            user.is_active = False
            user.deleted_at = datetime.now()
            user.updated_at = datetime.now()
            self.db.commit()
            
            logger.info(f"用户账户删除成功: {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除用户账户失败: {e}")
            raise
    
    # ==================== 私有辅助方法 ====================
    
    def _create_default_user_settings(self, user_id: int) -> 'UserSettings':
        """创建默认用户设置"""
        settings = UserSettings(
            user_id=user_id,
            theme='light',
            sidebar_collapsed=False,
            auto_refresh=True,
            refresh_interval=30,
            default_chart_period='1d',
            show_advanced_features=False
        )
        
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        
        return settings
    
    def _create_default_security_settings(self, user_id: int) -> 'SecuritySettings':
        """创建默认安全设置"""
        settings = SecuritySettings(
            user_id=user_id,
            two_factor_enabled=False,
            login_notifications=True,
            session_timeout=3600,
            ip_whitelist=[],
            allowed_devices=5
        )
        
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        
        return settings
    
    def _create_default_notification_settings(self, user_id: int) -> 'NotificationSettings':
        """创建默认通知设置"""
        settings = NotificationSettings(
            user_id=user_id,
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True,
            trade_notifications=['order_filled', 'position_closed'],
            risk_notifications=['margin_call', 'large_loss'],
            system_notifications=['maintenance', 'security_alert'],
            notification_hours={'start': '09:00', 'end': '21:00'}
        )
        
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        
        return settings
    
    def _generate_backup_codes(self) -> List[str]:
        """生成备用码"""
        return [secrets.token_hex(4).upper() for _ in range(10)]
    
    def _log_user_activity(self, user_id: int, action: str, description: str, 
                          ip_address: str = None, user_agent: str = None, 
                          metadata: Dict[str, Any] = None):
        """记录用户活动日志"""
        try:
            log = UserActivityLog(
                user_id=user_id,
                action=action,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {}
            )
            
            self.db.add(log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"记录用户活动日志失败: {e}")
            # 不抛出异常，避免影响主要功能