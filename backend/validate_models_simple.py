#!/usr/bin/env python3
"""
简化的数据库模型关系验证脚本
直接分析模型文件，不依赖完整的应用配置
"""

import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple


class SimpleModelValidator:
    """简化的模型验证器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.models = {}
        self.relationships = {}
        self.foreign_keys = {}
        
    def parse_model_file(self, file_path: Path) -> Dict:
        """解析模型文件"""
        model_info = {
            'classes': {},
            'relationships': {},
            'foreign_keys': {}
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找类定义
            class_pattern = r'class\s+(\w+)\(Base\):'
            classes = re.findall(class_pattern, content)
            
            for class_name in classes:
                model_info['classes'][class_name] = {
                    'file': file_path.name,
                    'tablename': self._extract_tablename(content, class_name)
                }
                
                # 查找关系定义
                relationships = self._extract_relationships(content, class_name)
                if relationships:
                    model_info['relationships'][class_name] = relationships
                
                # 查找外键定义
                foreign_keys = self._extract_foreign_keys(content, class_name)
                if foreign_keys:
                    model_info['foreign_keys'][class_name] = foreign_keys
            
            return model_info
            
        except Exception as e:
            self.errors.append(f"解析文件 {file_path} 时发生错误: {e}")
            return model_info
    
    def _extract_tablename(self, content: str, class_name: str) -> str:
        """提取表名"""
        pattern = rf'class\s+{class_name}\(Base\):.*?__tablename__\s*=\s*["\']([^"\']+)["\']'
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1) if match else ""
    
    def _extract_relationships(self, content: str, class_name: str) -> Dict:
        """提取关系定义"""
        relationships = {}
        
        # 查找类定义的开始和结束
        class_pattern = rf'class\s+{class_name}\(Base\):(.*?)(?=class\s+\w+|$)'
        class_match = re.search(class_pattern, content, re.DOTALL)
        
        if not class_match:
            return relationships
        
        class_content = class_match.group(1)
        
        # 查找 relationship 定义
        rel_pattern = r'(\w+)\s*=\s*relationship\(["\'](\w+)["\'](?:,\s*back_populates=["\'](\w+)["\'])?(?:,\s*foreign_keys=["\']?([^"\']+)["\']?)?[^)]*\)'
        
        for match in re.finditer(rel_pattern, class_content):
            rel_name = match.group(1)
            target_model = match.group(2)
            back_populates = match.group(3)
            foreign_keys = match.group(4)
            
            relationships[rel_name] = {
                'target_model': target_model,
                'back_populates': back_populates,
                'foreign_keys': foreign_keys
            }
        
        return relationships
    
    def _extract_foreign_keys(self, content: str, class_name: str) -> Dict:
        """提取外键定义"""
        foreign_keys = {}
        
        # 查找类定义的开始和结束
        class_pattern = rf'class\s+{class_name}\(Base\):(.*?)(?=class\s+\w+|$)'
        class_match = re.search(class_pattern, content, re.DOTALL)
        
        if not class_match:
            return foreign_keys
        
        class_content = class_match.group(1)
        
        # 查找 ForeignKey 定义
        fk_pattern = r'(\w+)\s*=\s*Column\([^,]*,\s*ForeignKey\(["\']([^"\']+)["\'][^)]*\)'
        
        for match in re.finditer(fk_pattern, class_content):
            column_name = match.group(1)
            target_ref = match.group(2)
            
            # 解析目标表和列
            if '.' in target_ref:
                target_table, target_column = target_ref.split('.', 1)
            else:
                target_table = target_ref
                target_column = 'id'  # 默认主键
            
            foreign_keys[column_name] = {
                'target_table': target_table,
                'target_column': target_column
            }
        
        return foreign_keys
    
    def load_all_models(self):
        """加载所有模型文件"""
        models_dir = Path(__file__).parent / 'app' / 'models'
        
        if not models_dir.exists():
            self.errors.append(f"模型目录不存在: {models_dir}")
            return False
        
        model_files = list(models_dir.glob('*.py'))
        model_files = [f for f in model_files if f.name != '__init__.py']
        
        print(f"发现 {len(model_files)} 个模型文件")
        
        for model_file in model_files:
            print(f"解析文件: {model_file.name}")
            model_info = self.parse_model_file(model_file)
            
            # 合并模型信息
            self.models.update(model_info['classes'])
            self.relationships.update(model_info['relationships'])
            self.foreign_keys.update(model_info['foreign_keys'])
        
        print(f"发现 {len(self.models)} 个模型类")
        return True
    
    def validate_relationships(self):
        """验证关系定义"""
        print("\n🔍 验证关系定义...")
        
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
    
    def validate_foreign_keys(self):
        """验证外键定义"""
        print("\n🔍 验证外键定义...")
        
        # 创建表名到模型名的映射
        table_to_model = {}
        for model_name, model_info in self.models.items():
            if model_info['tablename']:
                table_to_model[model_info['tablename']] = model_name
        
        for model_name, foreign_keys in self.foreign_keys.items():
            for fk_column, fk_info in foreign_keys.items():
                target_table = fk_info['target_table']
                target_column = fk_info['target_column']
                
                # 检查目标表是否存在
                if target_table not in table_to_model:
                    self.errors.append(
                        f"{model_name}.{fk_column} 引用了不存在的表: {target_table}"
                    )
    
    def validate_specific_issues(self):
        """验证特定问题"""
        print("\n🔍 验证特定问题...")
        
        # 检查 AlertRule.creator 关系
        if 'AlertRule' in self.models:
            # 检查是否有 created_by 外键
            if 'AlertRule' in self.foreign_keys:
                alert_fks = self.foreign_keys['AlertRule']
                if 'created_by' not in alert_fks:
                    self.errors.append("AlertRule 模型缺少 created_by 外键")
                else:
                    # 检查外键是否指向 users 表
                    created_by_fk = alert_fks['created_by']
                    if created_by_fk['target_table'] != 'users':
                        self.errors.append(
                            f"AlertRule.created_by 外键应该指向 users 表，"
                            f"但实际指向 {created_by_fk['target_table']}"
                        )
            else:
                self.errors.append("AlertRule 模型没有外键定义")
            
            # 检查 creator 关系
            if 'AlertRule' in self.relationships:
                alert_rels = self.relationships['AlertRule']
                if 'creator' not in alert_rels:
                    self.errors.append("AlertRule 模型缺少 creator 关系")
                else:
                    creator_rel = alert_rels['creator']
                    if creator_rel['target_model'] != 'User':
                        self.errors.append(
                            f"AlertRule.creator 关系应该指向 User 模型，"
                            f"但实际指向 {creator_rel['target_model']}"
                        )
                    if creator_rel['back_populates'] != 'alert_rules':
                        self.errors.append(
                            f"AlertRule.creator 关系的 back_populates 应该是 'alert_rules'，"
                            f"但实际是 '{creator_rel['back_populates']}'"
                        )
        
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
    
    def run_validation(self) -> bool:
        """运行完整验证"""
        print("🔍 开始验证数据库模型关系...")
        
        # 加载所有模型
        if not self.load_all_models():
            return False
        
        # 执行各项验证
        self.validate_relationships()
        self.validate_foreign_keys()
        self.validate_specific_issues()
        
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
    
    def print_model_summary(self):
        """打印模型摘要"""
        print("\n📊 模型摘要:")
        print("-" * 40)
        
        for model_name, model_info in self.models.items():
            print(f"\n{model_name} -> {model_info['tablename']}")
            
            # 显示关系
            if model_name in self.relationships:
                relationships = self.relationships[model_name]
                for rel_name, rel_info in relationships.items():
                    back_pop = f" (back_populates: {rel_info['back_populates']})" if rel_info['back_populates'] else ""
                    print(f"  关系: {rel_name} -> {rel_info['target_model']}{back_pop}")
            
            # 显示外键
            if model_name in self.foreign_keys:
                foreign_keys = self.foreign_keys[model_name]
                for fk_name, fk_info in foreign_keys.items():
                    print(f"  外键: {fk_name} -> {fk_info['target_table']}.{fk_info['target_column']}")


def main():
    """主函数"""
    validator = SimpleModelValidator()
    
    success = validator.run_validation()
    validator.print_results()
    validator.print_model_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())