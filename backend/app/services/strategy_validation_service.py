"""
策略代码测试和验证服务
"""

import ast
import logging
import re
import sys
import traceback
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import subprocess
import tempfile
import os
import importlib.util
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidationLevel(str, Enum):
    """验证级别"""
    ERROR = "error"      # 错误
    WARNING = "warning"  # 警告
    INFO = "info"        # 信息


class ValidationCategory(str, Enum):
    """验证分类"""
    SYNTAX = "syntax"           # 语法检查
    SECURITY = "security"       # 安全检查
    PERFORMANCE = "performance" # 性能检查
    STYLE = "style"            # 代码风格
    DEPENDENCY = "dependency"   # 依赖检查
    LOGIC = "logic"            # 逻辑检查


@dataclass
class ValidationIssue:
    """验证问题"""
    level: ValidationLevel
    category: ValidationCategory
    message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    code: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    issues: List[ValidationIssue]
    execution_time: float
    code_metrics: Dict[str, Any]
    dependencies: List[str]
    entry_points: List[str]


class StrategyCodeValidator:
    """策略代码验证器"""
    
    def __init__(self):
        # 危险函数和模块列表
        self.dangerous_functions = {
            'exec', 'eval', 'compile', '__import__', 'open', 'file',
            'input', 'raw_input', 'reload', 'vars', 'globals', 'locals',
            'dir', 'getattr', 'setattr', 'delattr', 'hasattr'
        }
        
        self.dangerous_modules = {
            'os', 'sys', 'subprocess', 'shutil', 'tempfile', 'pickle',
            'marshal', 'shelve', 'dbm', 'sqlite3', 'socket', 'urllib',
            'http', 'ftplib', 'smtplib', 'poplib', 'imaplib', 'telnetlib'
        }
        
        # 允许的模块列表
        self.allowed_modules = {
            'numpy', 'pandas', 'matplotlib', 'seaborn', 'scipy',
            'sklearn', 'talib', 'math', 'datetime', 'time', 'json',
            'collections', 'itertools', 'functools', 'operator',
            'statistics', 'random', 'decimal', 'fractions'
        }
        
        # 必需的函数签名
        self.required_functions = {
            'initialize': ['context'],
            'handle_data': ['context', 'data'],
            'before_trading_start': ['context', 'data'],
            'after_trading_end': ['context', 'data']
        }
    
    def validate_code(self, code: str, strategy_name: str = "strategy") -> ValidationResult:
        """验证策略代码"""
        start_time = datetime.now()
        issues = []
        
        try:
            # 1. 语法检查
            syntax_issues = self._check_syntax(code)
            issues.extend(syntax_issues)
            
            # 如果有语法错误，直接返回
            if any(issue.level == ValidationLevel.ERROR for issue in syntax_issues):
                return ValidationResult(
                    is_valid=False,
                    issues=issues,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    code_metrics={},
                    dependencies=[],
                    entry_points=[]
                )
            
            # 2. 安全检查
            security_issues = self._check_security(code)
            issues.extend(security_issues)
            
            # 3. 依赖检查
            dependencies, dependency_issues = self._check_dependencies(code)
            issues.extend(dependency_issues)
            
            # 4. 代码结构检查
            structure_issues, entry_points = self._check_structure(code)
            issues.extend(structure_issues)
            
            # 5. 性能检查
            performance_issues = self._check_performance(code)
            issues.extend(performance_issues)
            
            # 6. 代码风格检查
            style_issues = self._check_style(code)
            issues.extend(style_issues)
            
            # 7. 逻辑检查
            logic_issues = self._check_logic(code)
            issues.extend(logic_issues)
            
            # 8. 计算代码指标
            code_metrics = self._calculate_metrics(code)
            
            # 判断是否有效
            has_errors = any(issue.level == ValidationLevel.ERROR for issue in issues)
            
            return ValidationResult(
                is_valid=not has_errors,
                issues=issues,
                execution_time=(datetime.now() - start_time).total_seconds(),
                code_metrics=code_metrics,
                dependencies=dependencies,
                entry_points=entry_points
            )
            
        except Exception as e:
            logger.error(f"代码验证失败: {str(e)}")
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category=ValidationCategory.SYNTAX,
                message=f"验证过程中发生错误: {str(e)}"
            ))
            
            return ValidationResult(
                is_valid=False,
                issues=issues,
                execution_time=(datetime.now() - start_time).total_seconds(),
                code_metrics={},
                dependencies=[],
                entry_points=[]
            )
    
    def _check_syntax(self, code: str) -> List[ValidationIssue]:
        """检查语法错误"""
        issues = []
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category=ValidationCategory.SYNTAX,
                message=f"语法错误: {e.msg}",
                line_number=e.lineno,
                column_number=e.offset,
                suggestion="请检查代码语法，确保符合Python语法规范"
            ))
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category=ValidationCategory.SYNTAX,
                message=f"代码解析错误: {str(e)}",
                suggestion="请检查代码是否为有效的Python代码"
            ))
        
        return issues
    
    def _check_security(self, code: str) -> List[ValidationIssue]:
        """检查安全问题"""
        issues = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # 检查危险函数调用
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        if func_name in self.dangerous_functions:
                            issues.append(ValidationIssue(
                                level=ValidationLevel.ERROR,
                                category=ValidationCategory.SECURITY,
                                message=f"禁止使用危险函数: {func_name}",
                                line_number=node.lineno,
                                suggestion=f"请移除对 {func_name} 函数的调用"
                            ))
                
                # 检查危险模块导入
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.dangerous_modules:
                            issues.append(ValidationIssue(
                                level=ValidationLevel.ERROR,
                                category=ValidationCategory.SECURITY,
                                message=f"禁止导入危险模块: {alias.name}",
                                line_number=node.lineno,
                                suggestion=f"请移除对 {alias.name} 模块的导入"
                            ))
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module in self.dangerous_modules:
                        issues.append(ValidationIssue(
                            level=ValidationLevel.ERROR,
                            category=ValidationCategory.SECURITY,
                            message=f"禁止从危险模块导入: {node.module}",
                            line_number=node.lineno,
                            suggestion=f"请移除从 {node.module} 模块的导入"
                        ))
        
        except Exception as e:
            logger.error(f"安全检查失败: {str(e)}")
        
        return issues
    
    def _check_dependencies(self, code: str) -> Tuple[List[str], List[ValidationIssue]]:
        """检查依赖"""
        dependencies = []
        issues = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]
                        if module_name not in dependencies:
                            dependencies.append(module_name)
                        
                        # 检查是否为允许的模块
                        if (module_name not in self.allowed_modules and 
                            module_name not in self.dangerous_modules):
                            issues.append(ValidationIssue(
                                level=ValidationLevel.WARNING,
                                category=ValidationCategory.DEPENDENCY,
                                message=f"未知模块: {module_name}",
                                line_number=node.lineno,
                                suggestion="请确认该模块在运行环境中可用"
                            ))
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split('.')[0]
                        if module_name not in dependencies:
                            dependencies.append(module_name)
                        
                        if (module_name not in self.allowed_modules and 
                            module_name not in self.dangerous_modules):
                            issues.append(ValidationIssue(
                                level=ValidationLevel.WARNING,
                                category=ValidationCategory.DEPENDENCY,
                                message=f"未知模块: {module_name}",
                                line_number=node.lineno,
                                suggestion="请确认该模块在运行环境中可用"
                            ))
        
        except Exception as e:
            logger.error(f"依赖检查失败: {str(e)}")
        
        return dependencies, issues
    
    def _check_structure(self, code: str) -> Tuple[List[ValidationIssue], List[str]]:
        """检查代码结构"""
        issues = []
        entry_points = []
        
        try:
            tree = ast.parse(code)
            
            # 查找函数定义
            functions = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions[node.name] = node
                    entry_points.append(node.name)
            
            # 检查必需函数
            for func_name, required_args in self.required_functions.items():
                if func_name in functions:
                    func_node = functions[func_name]
                    
                    # 检查参数
                    actual_args = [arg.arg for arg in func_node.args.args]
                    if actual_args != required_args:
                        issues.append(ValidationIssue(
                            level=ValidationLevel.WARNING,
                            category=ValidationCategory.LOGIC,
                            message=f"函数 {func_name} 参数不匹配，期望: {required_args}，实际: {actual_args}",
                            line_number=func_node.lineno,
                            suggestion=f"请将函数参数修改为: {', '.join(required_args)}"
                        ))
                else:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.INFO,
                        category=ValidationCategory.LOGIC,
                        message=f"建议添加函数: {func_name}({', '.join(required_args)})",
                        suggestion=f"添加 {func_name} 函数可以提供更好的策略控制"
                    ))
            
            # 检查是否有主要逻辑
            if not functions:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category=ValidationCategory.LOGIC,
                    message="代码中没有找到函数定义",
                    suggestion="策略代码应该包含至少一个函数"
                ))
        
        except Exception as e:
            logger.error(f"结构检查失败: {str(e)}")
        
        return issues, entry_points
    
    def _check_performance(self, code: str) -> List[ValidationIssue]:
        """检查性能问题"""
        issues = []
        
        try:
            # 检查潜在的性能问题
            lines = code.split('\n')
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                
                # 检查循环中的重复计算
                if 'for ' in line and ('range(' in line or 'in ' in line):
                    if any(perf_issue in line for perf_issue in ['len(', '.append(', '.extend(']):
                        issues.append(ValidationIssue(
                            level=ValidationLevel.WARNING,
                            category=ValidationCategory.PERFORMANCE,
                            message="循环中可能存在性能问题",
                            line_number=i,
                            suggestion="考虑将重复计算移到循环外部"
                        ))
                
                # 检查字符串拼接
                if '+=' in line and ("'" in line or '"' in line):
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category=ValidationCategory.PERFORMANCE,
                        message="字符串拼接可能影响性能",
                        line_number=i,
                        suggestion="考虑使用 join() 方法或 f-string"
                    ))
                
                # 检查全局变量访问
                if 'global ' in line:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category=ValidationCategory.PERFORMANCE,
                        message="使用全局变量可能影响性能",
                        line_number=i,
                        suggestion="考虑使用局部变量或参数传递"
                    ))
        
        except Exception as e:
            logger.error(f"性能检查失败: {str(e)}")
        
        return issues
    
    def _check_style(self, code: str) -> List[ValidationIssue]:
        """检查代码风格"""
        issues = []
        
        try:
            lines = code.split('\n')
            
            for i, line in enumerate(lines, 1):
                # 检查行长度
                if len(line) > 120:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category=ValidationCategory.STYLE,
                        message=f"行长度超过120字符 ({len(line)})",
                        line_number=i,
                        suggestion="建议将长行拆分为多行"
                    ))
                
                # 检查缩进
                if line.strip() and not line.startswith(' ' * (len(line) - len(line.lstrip()))):
                    if '\t' in line:
                        issues.append(ValidationIssue(
                            level=ValidationLevel.WARNING,
                            category=ValidationCategory.STYLE,
                            message="使用了制表符缩进",
                            line_number=i,
                            suggestion="建议使用4个空格进行缩进"
                        ))
                
                # 检查命名规范
                if 'def ' in line:
                    func_match = re.search(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                    if func_match:
                        func_name = func_match.group(1)
                        if not re.match(r'^[a-z_][a-z0-9_]*$', func_name):
                            issues.append(ValidationIssue(
                                level=ValidationLevel.INFO,
                                category=ValidationCategory.STYLE,
                                message=f"函数名 '{func_name}' 不符合命名规范",
                                line_number=i,
                                suggestion="函数名应使用小写字母和下划线"
                            ))
        
        except Exception as e:
            logger.error(f"风格检查失败: {str(e)}")
        
        return issues
    
    def _check_logic(self, code: str) -> List[ValidationIssue]:
        """检查逻辑问题"""
        issues = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # 检查除零错误
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                    if isinstance(node.right, ast.Constant) and node.right.value == 0:
                        issues.append(ValidationIssue(
                            level=ValidationLevel.ERROR,
                            category=ValidationCategory.LOGIC,
                            message="除零错误",
                            line_number=node.lineno,
                            suggestion="请检查除数不为零"
                        ))
                
                # 检查未使用的变量
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            # 简单检查：如果变量名以下划线开头，通常表示未使用
                            if var_name.startswith('_') and not var_name.startswith('__'):
                                issues.append(ValidationIssue(
                                    level=ValidationLevel.INFO,
                                    category=ValidationCategory.LOGIC,
                                    message=f"变量 '{var_name}' 可能未使用",
                                    line_number=node.lineno,
                                    suggestion="考虑移除未使用的变量"
                                ))
        
        except Exception as e:
            logger.error(f"逻辑检查失败: {str(e)}")
        
        return issues
    
    def _calculate_metrics(self, code: str) -> Dict[str, Any]:
        """计算代码指标"""
        metrics = {
            'lines_of_code': 0,
            'lines_of_comments': 0,
            'blank_lines': 0,
            'functions_count': 0,
            'classes_count': 0,
            'complexity_score': 0,
            'maintainability_index': 0
        }
        
        try:
            lines = code.split('\n')
            
            # 基本行数统计
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    metrics['blank_lines'] += 1
                elif stripped.startswith('#'):
                    metrics['lines_of_comments'] += 1
                else:
                    metrics['lines_of_code'] += 1
            
            # AST分析
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics['functions_count'] += 1
                elif isinstance(node, ast.ClassDef):
                    metrics['classes_count'] += 1
                elif isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                    metrics['complexity_score'] += 1
            
            # 计算可维护性指数（简化版本）
            total_lines = len(lines)
            if total_lines > 0:
                comment_ratio = metrics['lines_of_comments'] / total_lines
                complexity_ratio = metrics['complexity_score'] / max(metrics['functions_count'], 1)
                metrics['maintainability_index'] = max(0, 100 - complexity_ratio * 10 + comment_ratio * 20)
        
        except Exception as e:
            logger.error(f"指标计算失败: {str(e)}")
        
        return metrics


class StrategyTestFramework:
    """策略测试框架"""
    
    def __init__(self):
        self.test_cases = []
    
    def add_test_case(self, name: str, test_func: callable, description: str = ""):
        """添加测试用例"""
        self.test_cases.append({
            'name': name,
            'test_func': test_func,
            'description': description
        })
    
    def run_tests(self, strategy_code: str) -> Dict[str, Any]:
        """运行测试用例"""
        results = {
            'total_tests': len(self.test_cases),
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': []
        }
        
        for test_case in self.test_cases:
            try:
                # 在安全环境中执行测试
                test_result = self._run_single_test(strategy_code, test_case)
                results['test_results'].append(test_result)
                
                if test_result['passed']:
                    results['passed_tests'] += 1
                else:
                    results['failed_tests'] += 1
                    
            except Exception as e:
                results['test_results'].append({
                    'name': test_case['name'],
                    'passed': False,
                    'error': str(e),
                    'execution_time': 0
                })
                results['failed_tests'] += 1
        
        return results
    
    def _run_single_test(self, strategy_code: str, test_case: Dict) -> Dict[str, Any]:
        """运行单个测试用例"""
        start_time = datetime.now()
        
        try:
            # 创建临时文件执行测试
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(strategy_code)
                f.write('\n\n# Test code\n')
                f.write(f"test_result = {test_case['test_func'].__name__}()")
                temp_file = f.name
            
            # 执行测试（这里需要更安全的执行环境）
            result = subprocess.run([
                sys.executable, '-c', f"""
import sys
sys.path.insert(0, '{os.path.dirname(temp_file)}')
exec(open('{temp_file}').read())
print(test_result)
"""
            ], capture_output=True, text=True, timeout=30)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            if result.returncode == 0:
                return {
                    'name': test_case['name'],
                    'passed': True,
                    'output': result.stdout.strip(),
                    'execution_time': execution_time
                }
            else:
                return {
                    'name': test_case['name'],
                    'passed': False,
                    'error': result.stderr,
                    'execution_time': execution_time
                }
                
        except subprocess.TimeoutExpired:
            return {
                'name': test_case['name'],
                'passed': False,
                'error': '测试超时',
                'execution_time': 30.0
            }
        except Exception as e:
            return {
                'name': test_case['name'],
                'passed': False,
                'error': str(e),
                'execution_time': (datetime.now() - start_time).total_seconds()
            }
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file)
            except:
                pass


# 默认测试用例
def create_default_test_framework() -> StrategyTestFramework:
    """创建默认测试框架"""
    framework = StrategyTestFramework()
    
    # 基本语法测试
    def test_syntax():
        return "语法检查通过"
    
    framework.add_test_case(
        "syntax_test",
        test_syntax,
        "检查代码语法是否正确"
    )
    
    # 函数存在性测试
    def test_required_functions():
        required_funcs = ['initialize', 'handle_data']
        missing_funcs = []
        for func in required_funcs:
            if func not in globals():
                missing_funcs.append(func)
        
        if missing_funcs:
            return f"缺少必需函数: {', '.join(missing_funcs)}"
        return "必需函数检查通过"
    
    framework.add_test_case(
        "required_functions_test",
        test_required_functions,
        "检查是否包含必需的函数"
    )
    
    return framework