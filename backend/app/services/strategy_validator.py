"""
策略代码验证服务
"""
import ast
import sys
import re
import subprocess
import tempfile
import os
import importlib.util
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import logging

from ..schemas.strategy import (
    StrategyValidationRequest,
    StrategyValidationResponse,
    StrategyCodeAnalysis,
    StrategyDependencyInfo,
    StrategySecurityReport,
)

logger = logging.getLogger(__name__)


class StrategyValidator:
    """策略代码验证器"""
    
    # 危险的内置函数和模块
    DANGEROUS_BUILTINS = {
        'eval', 'exec', 'compile', '__import__', 'open', 'file',
        'input', 'raw_input', 'reload', 'vars', 'globals', 'locals',
        'dir', 'getattr', 'setattr', 'delattr', 'hasattr'
    }
    
    # 危险的模块
    DANGEROUS_MODULES = {
        'os', 'sys', 'subprocess', 'shutil', 'tempfile', 'pickle',
        'marshal', 'imp', 'importlib', 'ctypes', 'multiprocessing',
        'threading', 'socket', 'urllib', 'requests', 'ftplib',
        'smtplib', 'telnetlib', 'webbrowser'
    }
    
    # 允许的模块
    ALLOWED_MODULES = {
        'math', 'random', 'datetime', 'time', 'json', 'collections',
        'itertools', 'functools', 'operator', 'copy', 'decimal',
        'fractions', 'statistics', 'uuid', 're', 'string',
        'numpy', 'pandas', 'scipy', 'matplotlib', 'seaborn',
        'sklearn', 'tqsdk', 'talib', 'backtrader'
    }
    
    # 必需的策略函数
    REQUIRED_FUNCTIONS = ['initialize', 'handle_bar']
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.suggestions = []
    
    def validate_strategy(self, request: StrategyValidationRequest) -> StrategyValidationResponse:
        """验证策略代码"""
        self.errors = []
        self.warnings = []
        self.suggestions = []
        
        checks = {
            'syntax': False,
            'security': False,
            'structure': False,
            'dependencies': False
        }
        
        try:
            # 语法检查
            if request.check_syntax:
                checks['syntax'] = self._check_syntax(request.code)
            
            # 安全检查
            if request.check_security:
                checks['security'] = self._check_security(request.code)
            
            # 结构检查
            if request.check_structure:
                checks['structure'] = self._check_structure(request.code)
            
            # 依赖检查
            if request.check_dependencies:
                checks['dependencies'] = self._check_dependencies(request.code)
            
            # 整体验证结果
            valid = all(checks.values()) and len(self.errors) == 0
            
            return StrategyValidationResponse(
                valid=valid,
                errors=self.errors,
                warnings=self.warnings,
                checks=checks,
                suggestions=self.suggestions
            )
            
        except Exception as e:
            logger.error(f"策略验证失败: {e}")
            self.errors.append(f"验证过程出错: {str(e)}")
            
            return StrategyValidationResponse(
                valid=False,
                errors=self.errors,
                warnings=self.warnings,
                checks=checks,
                suggestions=self.suggestions
            )
    
    def _check_syntax(self, code: str) -> bool:
        """检查Python语法"""
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            self.errors.append(f"语法错误 (行 {e.lineno}): {e.msg}")
            return False
        except Exception as e:
            self.errors.append(f"语法检查失败: {str(e)}")
            return False
    
    def _check_security(self, code: str) -> bool:
        """检查代码安全性"""
        try:
            tree = ast.parse(code)
            security_issues = []
            
            for node in ast.walk(tree):
                # 检查危险的内置函数调用
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in self.DANGEROUS_BUILTINS:
                            security_issues.append(f"使用了危险函数: {node.func.id}")
                
                # 检查危险的模块导入
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.DANGEROUS_MODULES:
                            security_issues.append(f"导入了危险模块: {alias.name}")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module in self.DANGEROUS_MODULES:
                        security_issues.append(f"从危险模块导入: {node.module}")
                
                # 检查文件操作
                elif isinstance(node, ast.With):
                    if isinstance(node.items[0].context_expr, ast.Call):
                        if isinstance(node.items[0].context_expr.func, ast.Name):
                            if node.items[0].context_expr.func.id == 'open':
                                security_issues.append("使用了文件操作")
            
            if security_issues:
                self.errors.extend(security_issues)
                return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"安全检查失败: {str(e)}")
            return False
    
    def _check_structure(self, code: str) -> bool:
        """检查策略结构"""
        try:
            tree = ast.parse(code)
            found_functions = set()
            
            # 查找函数定义
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    found_functions.add(node.name)
            
            # 检查必需函数
            missing_functions = []
            for required_func in self.REQUIRED_FUNCTIONS:
                if required_func not in found_functions:
                    missing_functions.append(required_func)
            
            if missing_functions:
                self.errors.append(f"缺少必需函数: {', '.join(missing_functions)}")
                return False
            
            # 检查函数参数
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name == 'initialize':
                        if len(node.args.args) != 1 or node.args.args[0].arg != 'context':
                            self.errors.append("initialize函数必须有且仅有一个参数: context")
                            return False
                    
                    elif node.name == 'handle_bar':
                        if len(node.args.args) != 2 or node.args.args[0].arg != 'context' or node.args.args[1].arg != 'bar_dict':
                            self.errors.append("handle_bar函数必须有两个参数: context, bar_dict")
                            return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"结构检查失败: {str(e)}")
            return False
    
    def _check_dependencies(self, code: str) -> bool:
        """检查依赖模块"""
        try:
            tree = ast.parse(code)
            imported_modules = set()
            
            # 收集导入的模块
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_modules.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported_modules.add(node.module.split('.')[0])
            
            # 检查模块可用性
            unavailable_modules = []
            for module in imported_modules:
                if module not in self.ALLOWED_MODULES:
                    if module not in self.DANGEROUS_MODULES:
                        self.warnings.append(f"未知模块: {module}")
                    continue
                
                try:
                    importlib.util.find_spec(module)
                except ImportError:
                    unavailable_modules.append(module)
            
            if unavailable_modules:
                self.errors.append(f"以下模块不可用: {', '.join(unavailable_modules)}")
                return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"依赖检查失败: {str(e)}")
            return False
    
    def analyze_code(self, code: str) -> StrategyCodeAnalysis:
        """分析策略代码"""
        try:
            tree = ast.parse(code)
            
            # 统计代码行数
            lines_of_code = len([line for line in code.split('\n') if line.strip() and not line.strip().startswith('#')])
            
            # 计算复杂度
            complexity_score = self._calculate_complexity(tree)
            
            # 统计函数数量
            functions_count = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
            
            # 统计导入数量
            imports_count = len([node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))])
            
            # 安全评分
            security_score = self._calculate_security_score(tree)
            
            # 可维护性评分
            maintainability_score = self._calculate_maintainability_score(tree, lines_of_code)
            
            # 生成建议
            suggestions = self._generate_suggestions(tree, lines_of_code, complexity_score)
            
            return StrategyCodeAnalysis(
                lines_of_code=lines_of_code,
                complexity_score=complexity_score,
                functions_count=functions_count,
                imports_count=imports_count,
                security_score=security_score,
                maintainability_score=maintainability_score,
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"代码分析失败: {e}")
            return StrategyCodeAnalysis(
                lines_of_code=0,
                complexity_score=0.0,
                functions_count=0,
                imports_count=0,
                security_score=0.0,
                maintainability_score=0.0,
                suggestions=[f"代码分析失败: {str(e)}"]
            )
    
    def get_dependency_info(self, code: str) -> List[StrategyDependencyInfo]:
        """获取依赖信息"""
        try:
            tree = ast.parse(code)
            imported_modules = set()
            
            # 收集导入的模块
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_modules.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported_modules.add(node.module.split('.')[0])
            
            dependency_info = []
            
            for module in imported_modules:
                try:
                    spec = importlib.util.find_spec(module)
                    is_available = spec is not None
                    
                    # 尝试获取版本信息
                    version = None
                    if is_available:
                        try:
                            mod = importlib.import_module(module)
                            version = getattr(mod, '__version__', None)
                        except:
                            pass
                    
                    # 模块描述和安装命令
                    description = self._get_module_description(module)
                    installation_command = f"pip install {module}" if not is_available else None
                    
                    dependency_info.append(StrategyDependencyInfo(
                        module_name=module,
                        is_available=is_available,
                        version=version,
                        description=description,
                        installation_command=installation_command
                    ))
                    
                except Exception as e:
                    dependency_info.append(StrategyDependencyInfo(
                        module_name=module,
                        is_available=False,
                        description=f"检查失败: {str(e)}",
                        installation_command=f"pip install {module}"
                    ))
            
            return dependency_info
            
        except Exception as e:
            logger.error(f"获取依赖信息失败: {e}")
            return []
    
    def generate_security_report(self, code: str) -> StrategySecurityReport:
        """生成安全报告"""
        try:
            tree = ast.parse(code)
            issues = []
            recommendations = []
            
            # 检查各种安全问题
            for node in ast.walk(tree):
                # 危险函数调用
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in self.DANGEROUS_BUILTINS:
                            issues.append({
                                'type': 'dangerous_function',
                                'description': f"使用了危险函数: {node.func.id}",
                                'severity': 'HIGH'
                            })
                
                # 危险模块导入
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.DANGEROUS_MODULES:
                            issues.append({
                                'type': 'dangerous_import',
                                'description': f"导入了危险模块: {alias.name}",
                                'severity': 'HIGH'
                            })
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module in self.DANGEROUS_MODULES:
                        issues.append({
                            'type': 'dangerous_import',
                            'description': f"从危险模块导入: {node.module}",
                            'severity': 'HIGH'
                        })
            
            # 生成安全级别
            high_issues = [issue for issue in issues if issue['severity'] == 'HIGH']
            medium_issues = [issue for issue in issues if issue['severity'] == 'MEDIUM']
            
            if high_issues:
                security_level = 'LOW'
                safe_to_execute = False
            elif medium_issues:
                security_level = 'MEDIUM'
                safe_to_execute = True
            else:
                security_level = 'HIGH'
                safe_to_execute = True
            
            # 生成建议
            if high_issues:
                recommendations.append("移除所有危险函数和模块的使用")
            if medium_issues:
                recommendations.append("谨慎使用标记为中等风险的功能")
            
            recommendations.extend([
                "只使用允许的模块列表中的模块",
                "避免直接操作文件系统",
                "不要使用网络相关功能",
                "确保所有输入都经过验证"
            ])
            
            return StrategySecurityReport(
                security_level=security_level,
                issues=issues,
                recommendations=recommendations,
                safe_to_execute=safe_to_execute
            )
            
        except Exception as e:
            logger.error(f"生成安全报告失败: {e}")
            return StrategySecurityReport(
                security_level='LOW',
                issues=[{'type': 'error', 'description': f"安全检查失败: {str(e)}", 'severity': 'HIGH'}],
                recommendations=["代码存在语法错误，无法进行安全检查"],
                safe_to_execute=False
            )
    
    def _calculate_complexity(self, tree: ast.AST) -> float:
        """计算代码复杂度"""
        complexity = 1  # 基础复杂度
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return min(complexity / 10.0, 10.0)  # 归一化到0-10
    
    def _calculate_security_score(self, tree: ast.AST) -> float:
        """计算安全评分"""
        score = 10.0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.DANGEROUS_BUILTINS:
                        score -= 3.0
            
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.DANGEROUS_MODULES:
                            score -= 2.0
                elif node.module in self.DANGEROUS_MODULES:
                    score -= 2.0
        
        return max(score, 0.0)
    
    def _calculate_maintainability_score(self, tree: ast.AST, lines_of_code: int) -> float:
        """计算可维护性评分"""
        score = 10.0
        
        # 代码长度惩罚
        if lines_of_code > 200:
            score -= 2.0
        elif lines_of_code > 100:
            score -= 1.0
        
        # 函数数量
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        if len(functions) > 10:
            score -= 1.0
        
        # 嵌套深度
        max_depth = self._calculate_max_depth(tree)
        if max_depth > 4:
            score -= 1.0
        
        return max(score, 0.0)
    
    def _calculate_max_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """计算最大嵌套深度"""
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With, ast.FunctionDef)):
                child_depth = self._calculate_max_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def _generate_suggestions(self, tree: ast.AST, lines_of_code: int, complexity: float) -> List[str]:
        """生成代码改进建议"""
        suggestions = []
        
        if lines_of_code > 200:
            suggestions.append("代码过长，建议拆分为多个函数")
        
        if complexity > 5.0:
            suggestions.append("代码复杂度较高，建议简化逻辑")
        
        # 检查是否有文档字符串
        has_docstring = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if (node.body and isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Str)):
                    has_docstring = True
                    break
        
        if not has_docstring:
            suggestions.append("建议为函数添加文档字符串")
        
        # 检查异常处理
        has_exception_handling = any(isinstance(node, ast.Try) for node in ast.walk(tree))
        if not has_exception_handling:
            suggestions.append("建议添加异常处理机制")
        
        return suggestions
    
    def _get_module_description(self, module_name: str) -> str:
        """获取模块描述"""
        descriptions = {
            'numpy': '数值计算库',
            'pandas': '数据分析库',
            'matplotlib': '绘图库',
            'scipy': '科学计算库',
            'sklearn': '机器学习库',
            'tqsdk': '天勤量化SDK',
            'talib': '技术分析库',
            'backtrader': '回测框架',
            'math': 'Python数学库',
            'datetime': 'Python日期时间库',
            'json': 'JSON处理库',
            'random': 'Python随机数库',
            'time': 'Python时间库',
            'collections': 'Python集合库',
            'itertools': 'Python迭代工具库',
            'functools': 'Python函数工具库',
            'operator': 'Python操作符库',
            'copy': 'Python复制库',
            'decimal': 'Python十进制库',
            'fractions': 'Python分数库',
            'statistics': 'Python统计库',
            'uuid': 'Python UUID库',
            're': 'Python正则表达式库',
            'string': 'Python字符串库',
        }
        
        return descriptions.get(module_name, '第三方库')