"""
设置管理服务 - 支持分类管理、权限控制和版本控制
"""
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from ..models.user import User
from ..models.user_settings import (
    SettingsCategory, SettingsItem, UserSettingsValue, 
    SettingsHistory, SettingsTemplate
)
from ..core.permissions import check_user_permission

logger = logging.getLogger(__name__)

class SettingsManagementService:
    """设置管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 设置分类管理 ====================
    
    def get_settings_categories(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户可访问的设置分类"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            # 获取所有激活的分类
            categories = self.db.query(SettingsCategory).filter(
                SettingsCategory.is_active == True
            ).order_by(SettingsCategory.sort_order).all()
            
            # 过滤用户有权限访问的分类
            accessible_categories = []
            for category in categories:
                if self._check_category_permission(user, category):
                    accessible_categories.append({
                        'id': category.id,
                        'name': category.name,
                        'display_name': category.display_name,
                        'description': category.description,
                        'icon': category.icon,
                        'sort_order': category.sort_order
                    })
            
            return accessible_categories
            
        except Exception as e:
            logger.error(f"获取设置分类失败: {e}")
            raise
    
    def create_settings_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建设置分类"""
        try:
            category = SettingsCategory(
                name=category_data['name'],
                display_name=category_data['display_name'],
                description=category_data.get('description'),
                icon=category_data.get('icon'),
                sort_order=category_data.get('sort_order', 0),
                required_permissions=category_data.get('required_permissions', []),
                min_user_level=category_data.get('min_user_level', 0)
            )
            
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)
            
            logger.info(f"设置分类创建成功: {category.name}")
            return self._format_category(category)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建设置分类失败: {e}")
            raise
    
    # ==================== 设置项管理 ====================
    
    def get_settings_items(self, user_id: int, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取用户可访问的设置项"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            # 构建查询
            query = self.db.query(SettingsItem).join(SettingsCategory).filter(
                SettingsCategory.is_active == True,
                SettingsItem.is_visible == True
            )
            
            if category_id:
                query = query.filter(SettingsItem.category_id == category_id)
            
            items = query.order_by(
                SettingsCategory.sort_order,
                SettingsItem.sort_order
            ).all()
            
            # 过滤用户有权限访问的设置项
            accessible_items = []
            for item in items:
                if self._check_item_permission(user, item):
                    item_data = self._format_settings_item(item)
                    # 获取用户当前设置值
                    current_value = self.get_user_setting_value(user_id, item.id)
                    item_data['current_value'] = current_value
                    accessible_items.append(item_data)
            
            return accessible_items
            
        except Exception as e:
            logger.error(f"获取设置项失败: {e}")
            raise
    
    def create_settings_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建设置项"""
        try:
            item = SettingsItem(
                category_id=item_data['category_id'],
                key=item_data['key'],
                name=item_data['name'],
                description=item_data.get('description'),
                data_type=item_data['data_type'],
                default_value=item_data.get('default_value'),
                validation_rules=item_data.get('validation_rules', {}),
                options=item_data.get('options'),
                display_type=item_data.get('display_type', 'input'),
                is_visible=item_data.get('is_visible', True),
                is_editable=item_data.get('is_editable', True),
                sort_order=item_data.get('sort_order', 0),
                required_permissions=item_data.get('required_permissions', []),
                min_user_level=item_data.get('min_user_level', 0)
            )
            
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            
            logger.info(f"设置项创建成功: {item.key}")
            return self._format_settings_item(item)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建设置项失败: {e}")
            raise
    
    # ==================== 用户设置值管理 ====================
    
    def get_user_setting_value(self, user_id: int, settings_item_id: int) -> Any:
        """获取用户设置值"""
        try:
            # 获取当前版本的设置值
            value_record = self.db.query(UserSettingsValue).filter(
                UserSettingsValue.user_id == user_id,
                UserSettingsValue.settings_item_id == settings_item_id,
                UserSettingsValue.is_current == True
            ).first()
            
            if value_record:
                return value_record.value
            
            # 如果没有用户设置值，返回默认值
            settings_item = self.db.query(SettingsItem).filter(
                SettingsItem.id == settings_item_id
            ).first()
            
            return settings_item.default_value if settings_item else None
            
        except Exception as e:
            logger.error(f"获取用户设置值失败: {e}")
            return None
    
    def set_user_setting_value(self, user_id: int, settings_item_id: int, 
                              value: Any, reason: str = None, 
                              source: str = "user") -> Dict[str, Any]:
        """设置用户设置值（支持版本控制）"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            settings_item = self.db.query(SettingsItem).filter(
                SettingsItem.id == settings_item_id
            ).first()
            if not settings_item:
                raise ValueError("设置项不存在")
            
            # 检查权限
            if not self._check_item_permission(user, settings_item):
                raise ValueError("没有权限修改此设置")
            
            # 验证设置值
            if not self._validate_setting_value(settings_item, value):
                raise ValueError("设置值不符合验证规则")
            
            # 获取当前设置值
            current_record = self.db.query(UserSettingsValue).filter(
                UserSettingsValue.user_id == user_id,
                UserSettingsValue.settings_item_id == settings_item_id,
                UserSettingsValue.is_current == True
            ).first()
            
            old_value = current_record.value if current_record else settings_item.default_value
            
            # 如果值没有变化，直接返回
            if old_value == value:
                return {'message': '设置值未发生变化', 'value': value}
            
            # 将当前记录标记为非当前版本
            if current_record:
                current_record.is_current = False
                current_record.updated_at = datetime.now()
            
            # 创建新版本记录
            new_version = (current_record.version + 1) if current_record else 1
            new_record = UserSettingsValue(
                user_id=user_id,
                settings_item_id=settings_item_id,
                value=value,
                version=new_version,
                is_current=True,
                source=source,
                notes=reason
            )
            
            self.db.add(new_record)
            
            # 记录历史
            history = SettingsHistory(
                user_id=user_id,
                settings_item_id=settings_item_id,
                action='update',
                old_value=old_value,
                new_value=value,
                reason=reason,
                source=source
            )
            
            self.db.add(history)
            self.db.commit()
            
            logger.info(f"用户设置值更新成功: {user_id}, {settings_item.key}")
            return {
                'message': '设置更新成功',
                'value': value,
                'version': new_version,
                'previous_value': old_value
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"设置用户设置值失败: {e}")
            raise
    
    def get_user_settings_history(self, user_id: int, settings_item_id: Optional[int] = None,
                                 limit: int = 50, skip: int = 0) -> Dict[str, Any]:
        """获取用户设置历史记录"""
        try:
            query = self.db.query(SettingsHistory).filter(
                SettingsHistory.user_id == user_id
            )
            
            if settings_item_id:
                query = query.filter(SettingsHistory.settings_item_id == settings_item_id)
            
            query = query.order_by(desc(SettingsHistory.created_at))
            
            total_count = query.count()
            history_records = query.offset(skip).limit(limit).all()
            
            return {
                'history': [
                    {
                        'id': record.id,
                        'settings_item_id': record.settings_item_id,
                        'action': record.action,
                        'old_value': record.old_value,
                        'new_value': record.new_value,
                        'reason': record.reason,
                        'source': record.source,
                        'created_at': record.created_at
                    }
                    for record in history_records
                ],
                'total_count': total_count,
                'page_info': {
                    'skip': skip,
                    'limit': limit,
                    'has_more': skip + len(history_records) < total_count
                }
            }
            
        except Exception as e:
            logger.error(f"获取用户设置历史失败: {e}")
            raise
    
    def rollback_setting_value(self, user_id: int, settings_item_id: int, 
                              target_version: int, reason: str = None) -> Dict[str, Any]:
        """回滚设置值到指定版本"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            settings_item = self.db.query(SettingsItem).filter(
                SettingsItem.id == settings_item_id
            ).first()
            if not settings_item:
                raise ValueError("设置项不存在")
            
            # 检查权限
            if not self._check_item_permission(user, settings_item):
                raise ValueError("没有权限修改此设置")
            
            # 获取目标版本的设置值
            target_record = self.db.query(UserSettingsValue).filter(
                UserSettingsValue.user_id == user_id,
                UserSettingsValue.settings_item_id == settings_item_id,
                UserSettingsValue.version == target_version
            ).first()
            
            if not target_record:
                raise ValueError("目标版本不存在")
            
            # 获取当前设置值
            current_record = self.db.query(UserSettingsValue).filter(
                UserSettingsValue.user_id == user_id,
                UserSettingsValue.settings_item_id == settings_item_id,
                UserSettingsValue.is_current == True
            ).first()
            
            current_value = current_record.value if current_record else None
            
            # 执行回滚
            return self.set_user_setting_value(
                user_id, settings_item_id, target_record.value,
                reason or f"回滚到版本 {target_version}", "rollback"
            )
            
        except Exception as e:
            logger.error(f"回滚设置值失败: {e}")
            raise
    
    # ==================== 设置模板管理 ====================
    
    def get_settings_templates(self, user_id: int) -> List[Dict[str, Any]]:
        """获取可用的设置模板"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            templates = self.db.query(SettingsTemplate).filter(
                SettingsTemplate.is_active == True
            ).order_by(SettingsTemplate.is_default.desc(), SettingsTemplate.name).all()
            
            # 过滤适用的模板
            applicable_templates = []
            for template in templates:
                if self._check_template_applicability(user, template):
                    applicable_templates.append({
                        'id': template.id,
                        'name': template.name,
                        'description': template.description,
                        'is_default': template.is_default,
                        'usage_count': template.usage_count
                    })
            
            return applicable_templates
            
        except Exception as e:
            logger.error(f"获取设置模板失败: {e}")
            raise
    
    def apply_settings_template(self, user_id: int, template_id: int, 
                               reason: str = None) -> Dict[str, Any]:
        """应用设置模板"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            template = self.db.query(SettingsTemplate).filter(
                SettingsTemplate.id == template_id,
                SettingsTemplate.is_active == True
            ).first()
            if not template:
                raise ValueError("模板不存在或已禁用")
            
            # 检查模板适用性
            if not self._check_template_applicability(user, template):
                raise ValueError("模板不适用于当前用户")
            
            # 应用模板设置
            applied_count = 0
            failed_items = []
            
            for item_key, item_value in template.settings_data.items():
                try:
                    # 根据key查找设置项
                    settings_item = self.db.query(SettingsItem).filter(
                        SettingsItem.key == item_key
                    ).first()
                    
                    if settings_item and self._check_item_permission(user, settings_item):
                        self.set_user_setting_value(
                            user_id, settings_item.id, item_value,
                            reason or f"应用模板: {template.name}", "template"
                        )
                        applied_count += 1
                    else:
                        failed_items.append(item_key)
                        
                except Exception as e:
                    logger.warning(f"应用模板设置项失败: {item_key}, {e}")
                    failed_items.append(item_key)
            
            # 更新模板使用次数
            template.usage_count += 1
            self.db.commit()
            
            logger.info(f"设置模板应用成功: {user_id}, {template.name}")
            return {
                'message': '模板应用成功',
                'applied_count': applied_count,
                'failed_items': failed_items,
                'template_name': template.name
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"应用设置模板失败: {e}")
            raise
    
    # ==================== 批量操作 ====================
    
    def batch_update_settings(self, user_id: int, settings_data: Dict[str, Any],
                             reason: str = None) -> Dict[str, Any]:
        """批量更新用户设置"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            updated_count = 0
            failed_items = []
            
            for item_key, item_value in settings_data.items():
                try:
                    # 根据key查找设置项
                    settings_item = self.db.query(SettingsItem).filter(
                        SettingsItem.key == item_key
                    ).first()
                    
                    if settings_item:
                        self.set_user_setting_value(
                            user_id, settings_item.id, item_value,
                            reason or "批量更新", "batch"
                        )
                        updated_count += 1
                    else:
                        failed_items.append(item_key)
                        
                except Exception as e:
                    logger.warning(f"批量更新设置项失败: {item_key}, {e}")
                    failed_items.append(item_key)
            
            return {
                'message': '批量更新完成',
                'updated_count': updated_count,
                'failed_items': failed_items
            }
            
        except Exception as e:
            logger.error(f"批量更新设置失败: {e}")
            raise
    
    def export_user_settings(self, user_id: int) -> Dict[str, Any]:
        """导出用户设置"""
        try:
            # 获取用户所有设置项
            settings_items = self.get_settings_items(user_id)
            
            # 构建导出数据
            export_data = {}
            for item in settings_items:
                export_data[item['key']] = item['current_value']
            
            return {
                'user_id': user_id,
                'export_time': datetime.now().isoformat(),
                'settings_count': len(export_data),
                'settings_data': export_data
            }
            
        except Exception as e:
            logger.error(f"导出用户设置失败: {e}")
            raise
    
    def import_user_settings(self, user_id: int, settings_data: Dict[str, Any],
                            reason: str = None) -> Dict[str, Any]:
        """导入用户设置"""
        try:
            return self.batch_update_settings(
                user_id, settings_data, 
                reason or "导入设置"
            )
            
        except Exception as e:
            logger.error(f"导入用户设置失败: {e}")
            raise
    
    # ==================== 私有辅助方法 ====================
    
    def _check_category_permission(self, user: User, category: SettingsCategory) -> bool:
        """检查用户是否有权限访问分类"""
        # 检查用户等级
        if hasattr(user, 'level') and user.level < category.min_user_level:
            return False
        
        # 检查权限
        if category.required_permissions:
            for permission in category.required_permissions:
                if not check_user_permission(user, permission):
                    return False
        
        return True
    
    def _check_item_permission(self, user: User, item: SettingsItem) -> bool:
        """检查用户是否有权限访问设置项"""
        # 检查用户等级
        if hasattr(user, 'level') and user.level < item.min_user_level:
            return False
        
        # 检查权限
        if item.required_permissions:
            for permission in item.required_permissions:
                if not check_user_permission(user, permission):
                    return False
        
        return True
    
    def _check_template_applicability(self, user: User, template: SettingsTemplate) -> bool:
        """检查模板是否适用于用户"""
        # 检查用户类型
        if template.target_user_types:
            user_type = getattr(user, 'user_type', 'regular')
            if user_type not in template.target_user_types:
                return False
        
        # 检查用户等级
        if template.target_user_levels:
            user_level = getattr(user, 'level', 0)
            if user_level not in template.target_user_levels:
                return False
        
        return True
    
    def _validate_setting_value(self, settings_item: SettingsItem, value: Any) -> bool:
        """验证设置值"""
        try:
            # 基本数据类型检查
            if settings_item.data_type == 'string' and not isinstance(value, str):
                return False
            elif settings_item.data_type == 'integer' and not isinstance(value, int):
                return False
            elif settings_item.data_type == 'boolean' and not isinstance(value, bool):
                return False
            elif settings_item.data_type == 'array' and not isinstance(value, list):
                return False
            elif settings_item.data_type == 'object' and not isinstance(value, dict):
                return False
            
            # 验证规则检查
            if settings_item.validation_rules:
                rules = settings_item.validation_rules
                
                # 字符串长度检查
                if 'min_length' in rules and isinstance(value, str):
                    if len(value) < rules['min_length']:
                        return False
                
                if 'max_length' in rules and isinstance(value, str):
                    if len(value) > rules['max_length']:
                        return False
                
                # 数值范围检查
                if 'min_value' in rules and isinstance(value, (int, float)):
                    if value < rules['min_value']:
                        return False
                
                if 'max_value' in rules and isinstance(value, (int, float)):
                    if value > rules['max_value']:
                        return False
                
                # 选项检查
                if 'allowed_values' in rules:
                    if value not in rules['allowed_values']:
                        return False
            
            return True
            
        except Exception as e:
            logger.warning(f"验证设置值时出错: {e}")
            return False
    
    def _format_category(self, category: SettingsCategory) -> Dict[str, Any]:
        """格式化分类数据"""
        return {
            'id': category.id,
            'name': category.name,
            'display_name': category.display_name,
            'description': category.description,
            'icon': category.icon,
            'sort_order': category.sort_order,
            'is_active': category.is_active,
            'created_at': category.created_at,
            'updated_at': category.updated_at
        }
    
    def _format_settings_item(self, item: SettingsItem) -> Dict[str, Any]:
        """格式化设置项数据"""
        return {
            'id': item.id,
            'category_id': item.category_id,
            'key': item.key,
            'name': item.name,
            'description': item.description,
            'data_type': item.data_type,
            'default_value': item.default_value,
            'validation_rules': item.validation_rules or {},
            'options': item.options,
            'display_type': item.display_type,
            'is_visible': item.is_visible,
            'is_editable': item.is_editable,
            'sort_order': item.sort_order
        }