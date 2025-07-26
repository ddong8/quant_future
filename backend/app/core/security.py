"""
安全相关工具类
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from .config import settings
from .exceptions import AuthenticationError

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityManager:
    """安全管理器"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """获取密码哈希"""
        return pwd_context.hash(password)
    
    @staticmethod
    def generate_random_token(length: int = 32) -> str:
        """生成随机令牌"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """哈希令牌"""
        return hashlib.sha256(token.encode()).hexdigest()


class JWTManager:
    """JWT管理器"""
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """验证令牌"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # 检查令牌类型
            if payload.get("type") != token_type:
                raise AuthenticationError("令牌类型不匹配")
            
            # 检查过期时间
            exp = payload.get("exp")
            if exp is None:
                raise AuthenticationError("令牌缺少过期时间")
            
            if datetime.utcnow() > datetime.fromtimestamp(exp):
                raise AuthenticationError("令牌已过期")
            
            return payload
            
        except JWTError as e:
            raise AuthenticationError(f"令牌验证失败: {str(e)}")
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """解码令牌（不验证）"""
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False}
            )
        except JWTError:
            raise AuthenticationError("令牌格式无效")
    
    @staticmethod
    def get_token_expiry(token: str) -> Optional[datetime]:
        """获取令牌过期时间"""
        try:
            payload = JWTManager.decode_token(token)
            exp = payload.get("exp")
            if exp:
                return datetime.fromtimestamp(exp)
            return None
        except:
            return None


class EmailManager:
    """邮件管理器"""
    
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False
    ) -> bool:
        """发送邮件"""
        if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_USER
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 添加邮件内容
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # 发送邮件
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(settings.SMTP_USER, to_email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"发送邮件失败: {e}")
            return False
    
    @staticmethod
    def send_verification_email(email: str, token: str) -> bool:
        """发送验证邮件"""
        subject = "验证您的邮箱地址"
        body = f"""
        <html>
        <body>
            <h2>邮箱验证</h2>
            <p>请点击以下链接验证您的邮箱地址：</p>
            <p><a href="http://localhost:3000/verify-email?token={token}">验证邮箱</a></p>
            <p>如果您没有注册账户，请忽略此邮件。</p>
            <p>此链接将在24小时后失效。</p>
        </body>
        </html>
        """
        
        return EmailManager.send_email(email, subject, body, is_html=True)
    
    @staticmethod
    def send_password_reset_email(email: str, token: str) -> bool:
        """发送密码重置邮件"""
        subject = "重置您的密码"
        body = f"""
        <html>
        <body>
            <h2>密码重置</h2>
            <p>请点击以下链接重置您的密码：</p>
            <p><a href="http://localhost:3000/reset-password?token={token}">重置密码</a></p>
            <p>如果您没有请求重置密码，请忽略此邮件。</p>
            <p>此链接将在1小时后失效。</p>
        </body>
        </html>
        """
        
        return EmailManager.send_email(email, subject, body, is_html=True)


class TokenBlacklist:
    """令牌黑名单管理"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.blacklist_prefix = "token_blacklist:"
    
    def add_token(self, token: str, expires_at: datetime) -> bool:
        """添加令牌到黑名单"""
        try:
            key = f"{self.blacklist_prefix}{SecurityManager.hash_token(token)}"
            ttl = int((expires_at - datetime.utcnow()).total_seconds())
            
            if ttl > 0:
                self.redis_client.setex(key, ttl, "blacklisted")
            
            return True
        except Exception:
            return False
    
    def is_blacklisted(self, token: str) -> bool:
        """检查令牌是否在黑名单中"""
        try:
            key = f"{self.blacklist_prefix}{SecurityManager.hash_token(token)}"
            return self.redis_client.exists(key)
        except Exception:
            return False
    
    def remove_token(self, token: str) -> bool:
        """从黑名单中移除令牌"""
        try:
            key = f"{self.blacklist_prefix}{SecurityManager.hash_token(token)}"
            self.redis_client.delete(key)
            return True
        except Exception:
            return False


# 创建全局实例
security_manager = SecurityManager()
jwt_manager = JWTManager()
email_manager = EmailManager()