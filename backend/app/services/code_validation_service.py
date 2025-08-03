"""
代码验证服务
提供策略代码的语法检查、安全验证和质量分析功能
"""

import ast
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """验证错误"""
    line: int
    column: int
    message: str
    severity: str  # 'error', 'warning', 'info'
    rule: str


@dataclass
class CodeMetrics:
    """代码指标"""
    lines_of_code: int
    functions_count: int
    classes_count: int
    imports_count: int
    complexity: int
    maintainability_index: float


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    metrics: CodeMetrics
    suggestions: List[str]


class CodeValidationService:
    """代码验证服务"""
    
    # 危险的内置函数和模块
    DANGEROUS_BUILTINS = {
        'eval', 'exec', 'compile', '__import__', 'open', 'file',
        'input', 'raw_input', 'reload', 'vars', 'locals', 'globals',
        'dir', 'hasattr', 'getattr', 'setattr', 'delattr'
    }
    
    # 危险的模块
    DANGEROUS_MODULES = {
        'os', 'sys', 'subprocess', 'shutil', 'tempfile', 'pickle',
        'marshal', 'shelve', 'dbm', 'sqlite3', 'socket', 'urllib',
        'http', 'ftplib', 'smtplib', 'poplib', 'imaplib', 'telnetlib',
        'webbrowser', 'cgitb', 'pdb', 'profile', 'pstats', 'timeit'
    }
    
    # 允许的量化交易相关模块
    ALLOWED_MODULES = {
        'pandas', 'numpy', 'matplotlib', 'seaborn', 'plotly',
        'scipy', 'sklearn', 'statsmodels', 'ta', 'talib',
        'datetime', 'time', 'calendar', 'math', 'statistics',
        'random', 'decimal', 'fractions', 'collections',
        'itertools', 'functools', 'operator', 'json', 'csv',
        're', 'string', 'unicodedata', 'warnings', 'logging'
    }
    
    def __init__(self):
        pass
    
    def validate_python_code(self, code: str, entry_point: str = "main") -> ValidationResult:
        """
        验证Python代码
        
        Args:
            code: 策略代码
            entry_point: 入口函数名
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # 1. 语法检查
            syntax_errors = self._check_syntax(code)
            errors.extend(syntax_errors)
            
            # 2. 安全检查
            security_issues = self._check_security(code)
            errors.extend(security_issues)
            
            # 3. 代码质量检查
            quality_warnings = self._check_code_quality(code)
            warnings.extend(quality_warnings)
            
            # 4. 入口函数检查
            entry_point_issues = self._check_entry_point(code, entry_point)
            errors.extend(entry_point_issues)
            
            # 5. 导入检查
            import_issues = self._check_imports(code)
            errors.extend(import_issues)
            
            # 6. 计算代码指标
            metrics = self._calculate_metrics(code)
            
            # 7. 生成建议
            suggestions = self._generate_suggestions(code, errors, warnings)
            
            is_valid = len(errors) == 0
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                metrics=metrics,
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"代码验证失败: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(
                    line=1,
                    column=1,
                    message=f"验证过程出错: {str(e)}",
                    severity="error",
                    rule="validation_error"
                )],
                warnings=[],
                metrics=CodeMetrics(0, 0, 0, 0, 0, 0.0),
                suggestions=[]
            )
    
    def _check_syntax(self, code: str) -> List[ValidationError]:
        """检查语法错误"""
        errors = []
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(ValidationError(
                line=e.lineno or 1,
                column=e.offset or 1,
                message=f"语法错误: {e.msg}",
                severity="error",
                rule="syntax_error"
            ))
        except Exception as e:
            errors.append(ValidationError(
                line=1,
                column=1,
                message=f"解析错误: {str(e)}",
                severity="error",
                rule="parse_error"
            ))
        
        return errors
    
    def _check_security(self, code: str) -> List[ValidationError]:
        """检查安全问题"""
        errors = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # 检查危险的内置函数
            for dangerous_func in self.DANGEROUS_BUILTINS:
                if re.search(rf'\b{dangerous_func}\s*\(', line):
                    errors.append(ValidationError(
                        line=line_num,
                        column=1,
                        message=f"使用了危险的内置函数: {dangerous_func}",
                        severity="error",
                        rule="dangerous_builtin"
                    ))
            
            # 检查危险的模块导入
            import_match = re.match(r'^\s*(import|from)\s+(\w+)', line)
            if import_match:
                module_name = import_match.group(2)
                if module_name in self.DANGEROUS_MODULES:
                    errors.append(ValidationError(
                        line=line_num,
                        column=1,
                        message=f"导入了危险的模块: {module_name}",
                        severity="error",
                        rule="dangerous_import"
                    ))
                elif module_name not in self.ALLOWED_MODULES:
                    errors.append(ValidationError(
                        line=line_num,
                        column=1,
                        message=f"导入了未授权的模块: {module_name}",
                        severity="error",
                        rule="unauthorized_import"
                    ))
        
        return errors
    
    def _check_code_quality(self, code: str) -> List[ValidationError]:
        """检查代码质量"""
        warnings = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # 检查行长度
            if len(line) > 120:
                warnings.append(ValidationError(
                    line=line_num,
                    column=1,
                    message="行长度超过120个字符",
                    severity="warning",
                    rule="line_too_long"
                ))
            
            # 检查TODO注释
            if 'TODO' in line.upper():
                warnings.append(ValidationError(
                    line=line_num,
                    column=1,
                    message="存在TODO注释，建议完善代码",
                    severity="info",
                    rule="todo_comment"
                ))
        
        # 检查函数复杂度
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_cyclomatic_complexity(node)
                    if complexity > 10:
                        warnings.append(ValidationError(
                            line=node.lineno,
                            column=node.col_offset,
                            message=f"函数 {node.name} 复杂度过高 ({complexity})",
                            severity="warning",
                            rule="high_complexity"
                        ))
        except:
            pass
        
        return warnings
    
    def _check_entry_point(self, code: str, entry_point: str) -> List[ValidationError]:
        """检查入口函数"""
        errors = []
        
        try:
            tree = ast.parse(code)
            
            # 查找入口函数
            entry_function = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == entry_point:
                    entry_function = node
                    break
            
            if not entry_function:
                errors.append(ValidationError(
                    line=1,
                    column=1,
                    message=f"未找到入口函数: {entry_point}",
                    severity="error",
                    rule="missing_entry_point"
                ))
            else:
                # 检查入口函数参数
                if len(entry_function.args.args) == 0:
                    errors.append(ValidationError(
                        line=entry_function.lineno,
                        column=entry_function.col_offset,
                        message=f"入口函数 {entry_point} 应该至少有一个参数 (context)",
                        severity="warning",
                        rule="entry_point_no_context"
                    ))
        
        except:
            pass
        
        return errors
    
    def _check_imports(self, code: str) -> List[ValidationError]:
        """检查导入语句"""
        errors = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in self.ALLOWED_MODULES and alias.name not in self.DANGEROUS_MODULES:
                            # 这是一个未知模块，给出警告
                            pass
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module not in self.ALLOWED_MODULES and node.module not in self.DANGEROUS_MODULES:
                        # 这是一个未知模块，给出警告
                        pass
        
        except:
            pass
        
        return errors
    
    def _calculate_metrics(self, code: str) -> CodeMetrics:
        """计算代码指标"""
        lines = code.split('\n')
        lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        
        functions_count = 0
        classes_count = 0
        imports_count = 0
        complexity = 0
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions_count += 1
                    complexity += self._calculate_cyclomatic_complexity(node)
                elif isinstance(node, ast.ClassDef):
                    classes_count += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports_count += 1
        
        except:
            pass
        
        # 简单的可维护性指数计算
        maintainability_index = max(0, 171 - 5.2 * complexity - 0.23 * functions_count - 16.2 * (lines_of_code / 100))
        
        return CodeMetrics(
            lines_of_code=lines_of_code,
            functions_count=functions_count,
            classes_count=classes_count,
            imports_count=imports_count,
            complexity=complexity,
            maintainability_index=maintainability_index
        )
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """计算圈复杂度"""
        complexity = 1  # 基础复杂度
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _generate_suggestions(self, code: str, errors: List[ValidationError], warnings: List[ValidationError]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 基于错误和警告生成建议
        if any(error.rule == "missing_entry_point" for error in errors):
            suggestions.append("建议添加入口函数，通常命名为 'main' 或 'strategy'")
        
        if any(warning.rule == "high_complexity" for warning in warnings):
            suggestions.append("建议将复杂的函数拆分为更小的函数")
        
        if any(warning.rule == "line_too_long" for warning in warnings):
            suggestions.append("建议将过长的代码行进行换行处理")
        
        # 检查是否有文档字符串
        try:
            tree = ast.parse(code)
            has_docstring = False
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if (node.body and isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, ast.Str)):
                        has_docstring = True
                        break
            
            if not has_docstring:
                suggestions.append("建议为函数添加文档字符串，说明函数的功能和参数")
        
        except:
            pass
        
        # 检查是否有异常处理
        if 'try:' not in code:
            suggestions.append("建议添加异常处理，提高代码的健壮性")
        
        return suggestions
    
    def format_code(self, code: str, language: str = "python") -> Tuple[bool, str, str]:
        """
        格式化代码
        
        Args:
            code: 原始代码
            language: 编程语言
            
        Returns:
            Tuple[bool, str, str]: (是否成功, 格式化后的代码, 错误信息)
        """
        if language.lower() != "python":
            return False, code, "暂不支持该语言的代码格式化"
        
        try:
            # 使用black格式化Python代码
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # 尝试使用black格式化
                result = subprocess.run(
                    ['black', '--line-length', '88', '--quiet', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    with open(temp_file, 'r') as f:
                        formatted_code = f.read()
                    return True, formatted_code, ""
                else:
                    return False, code, "代码格式化失败"
            
            finally:
                os.unlink(temp_file)
        
        except subprocess.TimeoutExpired:
            return False, code, "代码格式化超时"
        except FileNotFoundError:
            # black未安装，使用简单的格式化
            return self._simple_format_python(code)
        except Exception as e:
            return False, code, f"格式化出错: {str(e)}"
    
    def _simple_format_python(self, code: str) -> Tuple[bool, str, str]:
        """简单的Python代码格式化"""
        try:
            # 解析AST并重新生成代码
            tree = ast.parse(code)
            
            # 这里可以实现简单的格式化逻辑
            # 暂时返回原代码
            return True, code, ""
        
        except Exception as e:
            return False, code, f"简单格式化失败: {str(e)}"


# 全局代码验证服务实例
code_validation_service = CodeValidationService()