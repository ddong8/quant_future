"""
用户设置数据模型
"""
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class UserSettings(Base):
    """用户设置模型"""
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # 界面设置
    theme = Column(String(20), default="light", comment="主题")
    sidebar_collapsed = Column(Boolean, default=False, comment="侧边栏折叠")
    auto_refresh = Column(Boolean, default=True, comment="自动刷新")
    refresh_interval = Column(Integer, default=30, comment="刷新间隔(秒)")
    default_chart_period = Column(String(10), default="1d", comment="默认图表周期")
    show_advanced_features = Column(Boolean, default=False, comment="显示高级功能")
    
    # 个性化设置
    dashboard_layout = Column(JSON, comment="仪表板布局")
    favorite_symbols = Column(JSON, comment="收藏标的")
    watchlists = Column(JSON, comment="自选列表")
    quick_actions = Column(JSON, comment="快捷操作")
    chart_settings = Column(JSON, comment="图表设置")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User", back_populates="settings")

class SecuritySettings(Base):
    """安全设置模型"""
    __tablename__ = "security_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # 双因子认证
    two_factor_enabled = Column(Boolean, default=False, comment="双因子认证启用")
    two_factor_secret = Column(String(32), comment="双因子认证密钥")
    backup_codes = Column(JSON, comment="备用码")
    
    # 登录安全
    login_notifications = Column(Boolean, default=True, comment="登录通知")
    session_timeout = Column(Integer, default=3600, comment="会话超时(秒)")
    max_failed_attempts = Column(Integer, default=5, comment="最大失败尝试次数")
    lockout_duration = Column(Integer, default=900, comment="锁定时长(秒)")
    
    # 访问控制
    ip_whitelist = Column(JSON, comment="IP白名单")
    allowed_devices = Column(Integer, default=5, comment="允许设备数量")
    require_approval_new_device = Column(Boolean, default=True, comment="新设备需要审批")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User", back_populates="security_settings")

class NotificationSettings(Base):
    """通知设置模型"""
    __tablename__ = "notification_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # 通知渠道
    email_enabled = Column(Boolean, default=True, comment="邮件通知启用")
    sms_enabled = Column(Boolean, default=False, comment="短信通知启用")
    push_enabled = Column(Boolean, default=True, comment="推送通知启用")
    
    # 通知类型
    trade_notifications = Column(JSON, comment="交易通知类型")
    risk_notifications = Column(JSON, comment="风险通知类型")
    system_notifications = Column(JSON, comment="系统通知类型")
    market_notifications = Column(JSON, comment="市场通知类型")
    
    # 通知时间
    notification_hours = Column(JSON, comment="通知时间段")
    quiet_hours = Column(JSON, comment="免打扰时间段")
    
    # 通知频率
    digest_frequency = Column(String(20), default="daily", comment="摘要频率")
    max_notifications_per_hour = Column(Integer, default=10, comment="每小时最大通知数")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User", back_populates="notification_settings")

class LoginDevice(Base):
    """登录设备模型"""
    __tablename__ = "login_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 设备信息
    device_name = Column(String(100), nullable=False, comment="设备名称")
    device_type = Column(String(50), nullable=False, comment="设备类型")
    device_id = Column(String(100), comment="设备唯一标识")
    browser = Column(String(50), comment="浏览器")
    os = Column(String(50), comment="操作系统")
    
    # 网络信息
    ip_address = Column(String(45), nullable=False, comment="IP地址")
    location = Column(String(100), comment="位置")
    user_agent = Column(Text, comment="用户代理")
    
    # 状态信息
    is_current = Column(Boolean, default=False, comment="是否当前设备")
    is_trusted = Column(Boolean, default=False, comment="是否受信任设备")
    is_active = Column(Boolean, default=True, comment="是否活跃")
    
    # 时间信息
    first_login_at = Column(DateTime, server_default=func.now(), comment="首次登录时间")
    last_login_at = Column(DateTime, server_default=func.now(), comment="最后登录时间")
    last_activity_at = Column(DateTime, server_default=func.now(), comment="最后活动时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关系
    user = relationship("User", back_populates="login_devices")

class UserActivityLog(Base):
    """用户活动日志模型"""
    __tablename__ = "user_activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 活动信息
    action = Column(String(50), nullable=False, comment="操作类型")
    description = Column(String(200), nullable=False, comment="操作描述")
    category = Column(String(50), comment="操作分类")
    
    # 请求信息
    ip_address = Column(String(45), comment="IP地址")
    user_agent = Column(Text, comment="用户代理")
    request_id = Column(String(50), comment="请求ID")
    
    # 结果信息
    status = Column(String(20), default="success", comment="操作状态")
    error_message = Column(Text, comment="错误信息")
    
    # 元数据
    model_metadata = Column(JSON, comment="元数据")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关系
    user = relationship("User", back_populates="activity_logs")

class APIKey(Base):
    """API密钥模型"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 密钥信息
    name = Column(String(100), nullable=False, comment="密钥名称")
    key_id = Column(String(32), nullable=False, unique=True, comment="密钥ID")
    key_secret_hash = Column(String(128), nullable=False, comment="密钥哈希")
    
    # 权限设置
    permissions = Column(JSON, nullable=False, comment="权限列表")
    ip_whitelist = Column(JSON, comment="IP白名单")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否激活")
    expires_at = Column(DateTime, comment="过期时间")
    
    # 使用统计
    last_used_at = Column(DateTime, comment="最后使用时间")
    usage_count = Column(Integer, default=0, comment="使用次数")
    rate_limit = Column(Integer, default=1000, comment="速率限制(每小时)")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User", back_populates="api_keys")

class UserPreferences(Base):
    """用户偏好设置模型"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # 交易偏好
    default_order_type = Column(String(20), default="MARKET", comment="默认订单类型")
    default_time_in_force = Column(String(20), default="DAY", comment="默认有效期")
    confirm_orders = Column(Boolean, default=True, comment="订单确认")
    auto_cancel_orders = Column(Boolean, default=False, comment="自动取消订单")
    
    # 风险偏好
    risk_tolerance = Column(String(20), default="MEDIUM", comment="风险承受能力")
    max_position_size = Column(Integer, comment="最大持仓数量")
    max_daily_loss = Column(Integer, comment="最大日亏损")
    stop_loss_percentage = Column(Integer, comment="止损百分比")
    
    # 显示偏好
    currency_display = Column(String(10), default="USD", comment="显示货币")
    number_format = Column(String(20), default="en-US", comment="数字格式")
    date_format = Column(String(20), default="YYYY-MM-DD", comment="日期格式")
    time_format = Column(String(10), default="24h", comment="时间格式")
    
    # 其他偏好
    auto_logout_minutes = Column(Integer, default=60, comment="自动登出时间(分钟)")
    sound_notifications = Column(Boolean, default=True, comment="声音通知")
    animation_enabled = Column(Boolean, default=True, comment="动画效果")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User", back_populates="preferences")

class SettingsCategory(Base):
    """设置分类模型"""
    __tablename__ = "settings_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, comment="分类名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, comment="分类描述")
    icon = Column(String(50), comment="图标")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 权限控制
    required_permissions = Column(JSON, comment="所需权限")
    min_user_level = Column(Integer, default=0, comment="最低用户等级")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    settings_items = relationship("SettingsItem", back_populates="category")

class SettingsItem(Base):
    """设置项模型"""
    __tablename__ = "settings_items"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("settings_categories.id"), nullable=False)
    
    # 基本信息
    key = Column(String(100), nullable=False, comment="设置键")
    name = Column(String(100), nullable=False, comment="设置名称")
    description = Column(Text, comment="设置描述")
    data_type = Column(String(20), nullable=False, comment="数据类型")
    
    # 默认值和约束
    default_value = Column(JSON, comment="默认值")
    validation_rules = Column(JSON, comment="验证规则")
    options = Column(JSON, comment="选项列表")
    
    # 显示控制
    display_type = Column(String(20), default="input", comment="显示类型")
    is_visible = Column(Boolean, default=True, comment="是否可见")
    is_editable = Column(Boolean, default=True, comment="是否可编辑")
    sort_order = Column(Integer, default=0, comment="排序")
    
    # 权限控制
    required_permissions = Column(JSON, comment="所需权限")
    min_user_level = Column(Integer, default=0, comment="最低用户等级")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    category = relationship("SettingsCategory", back_populates="settings_items")
    user_values = relationship("UserSettingsValue", back_populates="settings_item")

class UserSettingsValue(Base):
    """用户设置值模型"""
    __tablename__ = "user_settings_values"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    settings_item_id = Column(Integer, ForeignKey("settings_items.id"), nullable=False)
    
    # 设置值
    value = Column(JSON, nullable=False, comment="设置值")
    
    # 版本控制
    version = Column(Integer, default=1, comment="版本号")
    is_current = Column(Boolean, default=True, comment="是否当前版本")
    
    # 元数据
    source = Column(String(50), default="user", comment="来源")
    notes = Column(Text, comment="备注")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User")
    settings_item = relationship("SettingsItem", back_populates="user_values")
    
    # 唯一约束
    __table_args__ = (
        sa.UniqueConstraint('user_id', 'settings_item_id', 'version', name='uq_user_settings_version'),
        sa.Index('ix_user_settings_current', 'user_id', 'settings_item_id', 'is_current'),
    )

class SettingsHistory(Base):
    """设置历史记录模型"""
    __tablename__ = "settings_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    settings_item_id = Column(Integer, ForeignKey("settings_items.id"), nullable=False)
    
    # 变更信息
    action = Column(String(20), nullable=False, comment="操作类型")
    old_value = Column(JSON, comment="旧值")
    new_value = Column(JSON, comment="新值")
    
    # 变更原因
    reason = Column(String(200), comment="变更原因")
    source = Column(String(50), default="user", comment="变更来源")
    
    # 元数据
    ip_address = Column(String(45), comment="IP地址")
    user_agent = Column(Text, comment="用户代理")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关系
    user = relationship("User")
    settings_item = relationship("SettingsItem")

class SettingsTemplate(Base):
    """设置模板模型"""
    __tablename__ = "settings_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(Text, comment="模板描述")
    
    # 模板内容
    settings_data = Column(JSON, nullable=False, comment="设置数据")
    
    # 适用范围
    target_user_types = Column(JSON, comment="适用用户类型")
    target_user_levels = Column(JSON, comment="适用用户等级")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_default = Column(Boolean, default=False, comment="是否默认模板")
    
    # 统计
    usage_count = Column(Integer, default=0, comment="使用次数")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建者")
    
    # 关系
    creator = relationship("User")