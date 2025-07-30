#!/usr/bin/env python3
"""
数据库模型关系验证脚本
验证所有模型的外键约束和关系映射是否正确
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import importlib

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from sqlalchemy import inspect
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql.schema import ForeignKey
    from app.models import *
    from app.core.database import Base
    HAS_SQLALCHEMY = True
except ImportError as e:
    print(f"导入错误: {e}")
    HAS_SQLALCHEMY = False


class ModelRelationshipValidator:
    """模型关系验证器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.models = {}
        self.relationships = {}
        self.foreign_keys = {}
        
    def collect_models(self):
        """收集所有模型类"""
        if not HAS_SQLALCHEMY:
            self.errors.append("SQLAlchemy 未正确导入，无法验证模型关系")
            return False
            
        try:
            # 获取所有继承自 Base 的模型类
            for cls in Base.registry._class_registry.values():
                if hasattr(cls, '__tablename__'):
                    self.models[cls.__name__] = cls
                    print(f"发现模型: {cls.__name__} -> {cls.__tablename__}")
            
            return True
            
        except Exception as e:
            self.errors.append(f"收集模型时发生错误: {e}")
            return False
    
    def analyze_relationships(self):
        """分析模型关系"""
        for model_name, model_cls in self.models.items():
            self.relationships[model_name] = {}
            self.foreign_keys[model_name] = {}
            
            # 分析关系属性
            for attr_name in dir(model_cls):
                attr = getattr(model_cls, attr_name)
                if isinstance(attr.property, relationship) if hasattr(attr, 'property') else False:
                    rel_info = {
                        'target_model': attr.property.mapper.class_.__name__,
                        'back_populates': attr.property.back_populates,
                        'foreign_keys': [fk.target_fullname for fk in attr.property.local_columns] if attr.property.local_columns else [],
                        'cascade': attr.property.cascade,
                    }
                    self.relationships[model_name][attr_name] = rel_info
                    print(f"  关系: {model_name}.{attr_name} -> {rel_info['target_model']}")
            
            # 分析外键
            if hasattr(model_cls, '__table__'):
                for column in model_cls.__table__.columns:
                    if column.foreign_keys:
                        for fk in column.foreign_keys:
                            fk_info = {
                                'column': column.name,
                                'target_table': fk.column.table.name,
                                'target_column': fk.column.name,
                            }
                            self.foreign_keys[model_name][column.name] = fk_info
                            print(f"  外键: {model_name}.{column.name} -> {fk.column.table.name}.{fk.column.name}")
    
    def validate_relationship_consistency(self):
        """验证关系一致性"""
        print("\n🔍 验证关系一致性...")
        
        for model_name, relationships in self.relationships.items():
            for rel_name, rel_info in relationships.items():
                target_model = rel_info['target_model']
                back_populates = rel_info['back_populates']
                
                # 检查目标模型是否存在
                if target_model not in self.models:
                    self.errors.append(
                        f"{model_name}.{rel_name} 引用了不存在的模型: {target_model}"
                    )
                    continue
                
                # 检查 back_populates 关系
                if back_populates:
                    if target_model not in self.relationships:
                        self.warnings.append(
                            f"{model_name}.{rel_name} 的 back_populates '{back_populates}' "
                            f"在目标模型 {target_model} 中未找到关系定义"
                        )
                        continue
                    
                    target_relationships = self.relationships[target_model]
                    if back_populates not in target_relationships:
                        self.errors.append(
                            f"{model_name}.{rel_name} 的 back_populates '{back_populates}' "
                            f"在目标模型 {target_model} 中不存在"
                        )
                    else:
                        # 检查反向关系是否正确
                        reverse_rel = target_relationships[back_populates]
                        if reverse_rel['target_model'] != model_name:
                            self.errors.append(
                                f"关系不匹配: {model_name}.{rel_name} -> {target_model}.{back_populates} "
                                f"但 {target_model}.{back_populates} -> {reverse_rel['target_model']}"
                            )
                        
                        if reverse_rel['back_populates'] != rel_name:
                            self.errors.append(
                                f"back_populates 不匹配: {model_name}.{rel_name} 期望 '{rel_name}' "
                                f"但 {target_model}.{back_populates} 指向 '{reverse_rel['back_populates']}'"
                            )
    
    def validate_foreign_key_consistency(self):
        """验证外键一致性"""
        print("\n🔍 验证外键一致性...")
        
        for model_name, foreign_keys in self.foreign_keys.items():
            for fk_column, fk_info in foreign_keys.items():
                target_table = fk_info['target_table']
                target_column = fk_info['target_column']
                
                # 查找目标表对应的模型
                target_model = None
                for m_name, m_cls in self.models.items():
                    if hasattr(m_cls, '__tablename__') and m_cls.__tablename__ == target_table:
                        target_model = m_name
                        break
                
                if not target_model:
                    self.errors.append(
                        f"{model_name}.{fk_column} 引用了不存在的表: {target_table}"
                    )
                    continue
                
                # 检查目标列是否存在
                target_model_cls = self.models[target_model]
                if hasattr(target_model_cls, '__table__'):
                    target_columns = [col.name for col in target_model_cls.__table__.columns]
                    if target_column not in target_columns:
                        self.errors.append(
                            f"{model_name}.{fk_column} 引用了不存在的列: {target_table}.{target_column}"
                        )
    
    def validate_specific_issues(self):
        """验证特定的已知问题"""
        print("\n🔍 验证特定问题...")
        
        # 检查 AlertRule.creator 关系
        if 'AlertRule' in self.models:
            alert_rule_cls = self.models['AlertRule']
            
            # 检查是否有 created_by 外键
            has_created_by_fk = False
            if hasattr(alert_rule_cls, '__table__'):
                for column in alert_rule_cls.__table__.columns:
                    if column.name == 'created_by' and column.foreign_keys:
                        has_created_by_fk = True
                        break
            
            if not has_created_by_fk:
                self.errors.append("AlertRule 模型缺少 created_by 外键")
            
            # 检查 creator 关系是否正确配置
            if 'AlertRule' in self.relationships and 'creator' in self.relationships['AlertRule']:
                creator_rel = self.relationships['AlertRule']['creator']
                if creator_rel['target_model'] != 'User':
                    self.errors.append("AlertRule.creator 关系应该指向 User 模型")
            else:
                self.errors.append("AlertRule 模型缺少 creator 关系")
        
        # 检查 Strategy 模型是否有不应该存在的 orders 关系
        if 'Strategy' in self.relationships:
            strategy_rels = self.relationships['Strategy']
            if 'orders' in strategy_rels:
                self.errors.append("Strategy 模型不应该有 orders 关系")
        
        # 检查 User 模型的关系
        if 'User' in self.relationships:
            user_rels = self.relationships['User']
            expected_relations = [
                'strategies', 'backtests', 'risk_events', 'trading_account',
                'orders', 'positions', 'alert_rules'
            ]
            
            for expected_rel in expected_relations:
                if expected_rel not in user_rels:
                    self.warnings.append(f"User 模型缺少预期的关系: {expected_rel}")
    
    def check_cascade_settings(self):
        """检查级联设置"""
        print("\n🔍 检查级联设置...")
        
        # 检查一些重要的级联设置
        cascade_checks = [
            ('User', 'strategies', 'all, delete-orphan'),
            ('User', 'backtests', 'all, delete-orphan'),
            ('Strategy', 'backtests', 'all, delete-orphan'),
            ('AlertRule', 'history', 'all, delete-orphan'),
        ]
        
        for model_name, rel_name, expected_cascade in cascade_checks:
            if (model_name in self.relationships and 
                rel_name in self.relationships[model_name]):
                
                actual_cascade = self.relationships[model_name][rel_name]['cascade']
                if str(actual_cascade) != expected_cascade:
                    self.warnings.append(
                        f"{model_name}.{rel_name} 的级联设置可能不正确: "
                        f"期望 '{expected_cascade}', 实际 '{actual_cascade}'"
                    )
    
    def run_validation(self) -> bool:
        """运行完整验证"""
        print("🔍 开始验证数据库模型关系...")
        
        # 收集模型
        if not self.collect_models():
            return False
        
        print(f"\n📊 发现 {len(self.models)} 个模型")
        
        # 分析关系
        self.analyze_relationships()
        
        # 执行各项验证
        self.validate_relationship_consistency()
        self.validate_foreign_key_consistency()
        self.validate_specific_issues()
        self.check_cascade_settings()
        
        return len(self.errors) == 0
    
    def print_results(self):
        """打印验证结果"""
        print("\n" + "="*60)
        print("模型关系验证结果")
        print("="*60)
        
        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ 模型关系验证通过，未发现问题")
        elif not self.errors:
            print(f"\n✅ 模型关系基本正确，但有 {len(self.warnings)} 个警告需要注意")
        else:
            print(f"\n❌ 模型关系验证失败，请修复 {len(self.errors)} 个错误")
        
        print("\n" + "="*60)
    
    def generate_relationship_diagram(self):
        """生成关系图"""
        print("\n📊 模型关系图:")
        print("-" * 40)
        
        for model_name, relationships in self.relationships.items():
            if relationships:
                print(f"\n{model_name}:")
                for rel_name, rel_info in relationships.items():
                    arrow = "<->" if rel_info['back_populates'] else "->"
                    print(f"  {rel_name} {arrow} {rel_info['target_model']}")


def main():
    """主函数"""
    validator = ModelRelationshipValidator()
    
    success = validator.run_validation()
    validator.print_results()
    validator.generate_relationship_diagram()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())