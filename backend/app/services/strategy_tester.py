"""
策略测试服务
"""
import time
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from sqlalchemy.orm import Session

from ..models import Strategy
from ..schemas.strategy import (
    StrategyTestRequest,
    StrategyTestResponse,
    StrategyValidationRequest,
    StrategySandboxRequest,
)
from .strategy_validator import StrategyValidator
from .strategy_sandbox import StrategySandbox
from ..core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class StrategyTester:
    """策略测试器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.validator = StrategyValidator()
        self.sandbox = StrategySandbox()
    
    def test_strategy(self, request: StrategyTestRequest, user_id: int) -> StrategyTestResponse:
        """测试策略"""
        try:
            # 获取策略
            strategy = self.db.query(Strategy).filter(
                Strategy.id == request.strategy_id,
                Strategy.user_id == user_id
            ).first()
            
            if not strategy:
                raise NotFoundError("策略不存在")
            
            test_start_time = datetime.utcnow()
            
            # 1. 代码验证
            validation_result = self._validate_strategy_code(strategy.code)
            
            # 2. 沙盒执行测试
            execution_result = self._execute_strategy_test(
                strategy.code, 
                request.test_params or {},
                request.timeout
            )
            
            # 3. 性能评估
            performance_result = self._evaluate_strategy_performance(
                strategy, 
                execution_result
            )
            
            # 4. 生成建议
            recommendations = self._generate_test_recommendations(
                validation_result,
                execution_result,
                performance_result
            )
            
            # 确定整体测试结果
            overall_result = self._determine_overall_result(
                validation_result,
                execution_result,
                performance_result
            )
            
            return StrategyTestResponse(
                strategy_id=strategy.id,
                strategy_name=strategy.name,
                test_time=test_start_time.isoformat(),
                overall_result=overall_result,
                validation=validation_result,
                execution=execution_result,
                performance=performance_result,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"策略测试失败: {e}")
            return StrategyTestResponse(
                strategy_id=request.strategy_id,
                strategy_name="未知",
                test_time=datetime.utcnow().isoformat(),
                overall_result="ERROR",
                validation={},
                execution={},
                performance={},
                recommendations=[],
                error=str(e)
            )
    
    def _validate_strategy_code(self, code: str) -> Dict[str, Any]:
        """验证策略代码"""
        try:
            validation_request = StrategyValidationRequest(
                code=code,
                check_syntax=True,
                check_security=True,
                check_structure=True,
                check_dependencies=True
            )
            
            validation_result = self.validator.validate_strategy(validation_request)
            
            # 获取代码分析
            code_analysis = self.validator.analyze_code(code)
            
            # 获取依赖信息
            dependency_info = self.validator.get_dependency_info(code)
            
            # 获取安全报告
            security_report = self.validator.generate_security_report(code)
            
            return {
                'valid': validation_result.valid,
                'errors': validation_result.errors,
                'warnings': validation_result.warnings,
                'checks': validation_result.checks,
                'suggestions': validation_result.suggestions,
                'code_analysis': {
                    'lines_of_code': code_analysis.lines_of_code,
                    'complexity_score': code_analysis.complexity_score,
                    'functions_count': code_analysis.functions_count,
                    'imports_count': code_analysis.imports_count,
                    'security_score': code_analysis.security_score,
                    'maintainability_score': code_analysis.maintainability_score,
                    'suggestions': code_analysis.suggestions
                },
                'dependencies': [
                    {
                        'module_name': dep.module_name,
                        'is_available': dep.is_available,
                        'version': dep.version,
                        'description': dep.description,
                        'installation_command': dep.installation_command
                    }
                    for dep in dependency_info
                ],
                'security_report': {
                    'security_level': security_report.security_level,
                    'issues': security_report.issues,
                    'recommendations': security_report.recommendations,
                    'safe_to_execute': security_report.safe_to_execute
                }
            }
            
        except Exception as e:
            logger.error(f"代码验证失败: {e}")
            return {
                'valid': False,
                'errors': [f"验证失败: {str(e)}"],
                'warnings': [],
                'checks': {},
                'suggestions': []
            }
    
    def _execute_strategy_test(self, code: str, test_params: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """执行策略测试"""
        try:
            # 准备测试数据
            test_data = {
                'params': test_params,
                'symbol': test_params.get('symbol', 'SHFE.cu2401'),
                'initial_capital': test_params.get('initial_capital', 1000000),
            }
            
            # 创建沙盒请求
            sandbox_request = StrategySandboxRequest(
                code=code,
                test_data=test_data,
                timeout=timeout
            )
            
            # 执行测试
            sandbox_result = self.sandbox.execute(sandbox_request)
            
            return {
                'success': sandbox_result.success,
                'output': sandbox_result.output,
                'error': sandbox_result.error,
                'execution_time': sandbox_result.execution_time,
                'memory_usage': sandbox_result.memory_usage,
                'timeout': timeout,
                'test_params': test_params
            }
            
        except Exception as e:
            logger.error(f"策略执行测试失败: {e}")
            return {
                'success': False,
                'output': '',
                'error': f"执行测试失败: {str(e)}",
                'execution_time': 0.0,
                'memory_usage': 0.0,
                'timeout': timeout,
                'test_params': test_params
            }
    
    def _evaluate_strategy_performance(self, strategy: Strategy, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """评估策略性能"""
        try:
            performance_metrics = {
                'execution_efficiency': self._calculate_execution_efficiency(execution_result),
                'memory_efficiency': self._calculate_memory_efficiency(execution_result),
                'code_quality': self._calculate_code_quality(strategy.code),
                'robustness': self._calculate_robustness(execution_result),
                'maintainability': self._calculate_maintainability(strategy.code),
            }
            
            # 计算总体评分
            overall_score = sum(performance_metrics.values()) / len(performance_metrics)
            
            # 性能等级
            if overall_score >= 8.0:
                performance_grade = 'A'
            elif overall_score >= 6.0:
                performance_grade = 'B'
            elif overall_score >= 4.0:
                performance_grade = 'C'
            else:
                performance_grade = 'D'
            
            return {
                'overall_score': overall_score,
                'performance_grade': performance_grade,
                'metrics': performance_metrics,
                'details': {
                    'execution_time': execution_result.get('execution_time', 0.0),
                    'memory_usage': execution_result.get('memory_usage', 0.0),
                    'success_rate': 1.0 if execution_result.get('success', False) else 0.0,
                }
            }
            
        except Exception as e:
            logger.error(f"性能评估失败: {e}")
            return {
                'overall_score': 0.0,
                'performance_grade': 'F',
                'metrics': {},
                'details': {},
                'error': str(e)
            }
    
    def _calculate_execution_efficiency(self, execution_result: Dict[str, Any]) -> float:
        """计算执行效率"""
        execution_time = execution_result.get('execution_time', 0.0)
        
        if execution_time <= 1.0:
            return 10.0
        elif execution_time <= 5.0:
            return 8.0
        elif execution_time <= 10.0:
            return 6.0
        elif execution_time <= 30.0:
            return 4.0
        else:
            return 2.0
    
    def _calculate_memory_efficiency(self, execution_result: Dict[str, Any]) -> float:
        """计算内存效率"""
        memory_usage = execution_result.get('memory_usage', 0.0)
        
        if memory_usage <= 10.0:  # 10MB以下
            return 10.0
        elif memory_usage <= 50.0:  # 50MB以下
            return 8.0
        elif memory_usage <= 100.0:  # 100MB以下
            return 6.0
        elif memory_usage <= 200.0:  # 200MB以下
            return 4.0
        else:
            return 2.0
    
    def _calculate_code_quality(self, code: str) -> float:
        """计算代码质量"""
        try:
            code_analysis = self.validator.analyze_code(code)
            
            # 综合各项指标
            quality_score = (
                (10.0 - code_analysis.complexity_score) * 0.3 +  # 复杂度（越低越好）
                code_analysis.security_score * 0.3 +  # 安全性
                code_analysis.maintainability_score * 0.4  # 可维护性
            )
            
            return max(0.0, min(10.0, quality_score))
            
        except Exception:
            return 5.0  # 默认中等分数
    
    def _calculate_robustness(self, execution_result: Dict[str, Any]) -> float:
        """计算健壮性"""
        if not execution_result.get('success', False):
            return 2.0
        
        error_message = execution_result.get('error', '')
        if error_message:
            if 'timeout' in error_message.lower():
                return 4.0
            elif 'memory' in error_message.lower():
                return 3.0
            else:
                return 5.0
        
        return 8.0
    
    def _calculate_maintainability(self, code: str) -> float:
        """计算可维护性"""
        try:
            code_analysis = self.validator.analyze_code(code)
            return code_analysis.maintainability_score
        except Exception:
            return 5.0
    
    def _generate_test_recommendations(self, 
                                     validation_result: Dict[str, Any],
                                     execution_result: Dict[str, Any],
                                     performance_result: Dict[str, Any]) -> List[str]:
        """生成测试建议"""
        recommendations = []
        
        # 验证相关建议
        if not validation_result.get('valid', False):
            recommendations.append("修复代码验证错误后再进行测试")
        
        if validation_result.get('warnings'):
            recommendations.append("关注代码警告信息，提高代码质量")
        
        # 执行相关建议
        if not execution_result.get('success', False):
            recommendations.append("修复代码执行错误")
        
        execution_time = execution_result.get('execution_time', 0.0)
        if execution_time > 10.0:
            recommendations.append("优化代码执行效率，减少运行时间")
        
        memory_usage = execution_result.get('memory_usage', 0.0)
        if memory_usage > 100.0:
            recommendations.append("优化内存使用，减少内存占用")
        
        # 性能相关建议
        overall_score = performance_result.get('overall_score', 0.0)
        if overall_score < 6.0:
            recommendations.append("整体性能需要改进")
        
        performance_grade = performance_result.get('performance_grade', 'F')
        if performance_grade in ['C', 'D', 'F']:
            recommendations.append("建议重构代码以提高性能等级")
        
        # 安全相关建议
        security_report = validation_result.get('security_report', {})
        if not security_report.get('safe_to_execute', True):
            recommendations.append("修复安全问题后再部署到生产环境")
        
        # 代码质量建议
        code_analysis = validation_result.get('code_analysis', {})
        if code_analysis.get('complexity_score', 0.0) > 5.0:
            recommendations.append("降低代码复杂度，提高可读性")
        
        if code_analysis.get('maintainability_score', 0.0) < 6.0:
            recommendations.append("改进代码结构，提高可维护性")
        
        # 依赖相关建议
        dependencies = validation_result.get('dependencies', [])
        unavailable_deps = [dep for dep in dependencies if not dep.get('is_available', True)]
        if unavailable_deps:
            recommendations.append("安装缺失的依赖模块")
        
        # 如果没有具体建议，给出通用建议
        if not recommendations:
            if overall_score >= 8.0:
                recommendations.append("策略测试通过，可以考虑部署")
            else:
                recommendations.append("继续优化策略代码和逻辑")
        
        return recommendations
    
    def _determine_overall_result(self,
                                validation_result: Dict[str, Any],
                                execution_result: Dict[str, Any],
                                performance_result: Dict[str, Any]) -> str:
        """确定整体测试结果"""
        # 如果验证失败，直接返回FAIL
        if not validation_result.get('valid', False):
            return 'FAIL'
        
        # 如果执行失败，返回ERROR
        if not execution_result.get('success', False):
            return 'ERROR'
        
        # 如果安全检查不通过，返回FAIL
        security_report = validation_result.get('security_report', {})
        if not security_report.get('safe_to_execute', True):
            return 'FAIL'
        
        # 根据性能评分确定结果
        overall_score = performance_result.get('overall_score', 0.0)
        if overall_score >= 6.0:
            return 'PASS'
        else:
            return 'FAIL'
    
    def run_quick_test(self, code: str, test_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """运行快速测试"""
        try:
            # 基础验证
            validation_request = StrategyValidationRequest(
                code=code,
                check_syntax=True,
                check_security=True,
                check_structure=True,
                check_dependencies=False  # 快速测试跳过依赖检查
            )
            
            validation_result = self.validator.validate_strategy(validation_request)
            
            if not validation_result.valid:
                return {
                    'success': False,
                    'result': 'VALIDATION_FAILED',
                    'errors': validation_result.errors,
                    'warnings': validation_result.warnings
                }
            
            # 快速执行测试
            test_data = {
                'params': test_params or {},
                'symbol': 'SHFE.cu2401',
                'initial_capital': 1000000,
            }
            
            sandbox_request = StrategySandboxRequest(
                code=code,
                test_data=test_data,
                timeout=10  # 快速测试限制10秒
            )
            
            sandbox_result = self.sandbox.execute(sandbox_request)
            
            return {
                'success': sandbox_result.success,
                'result': 'PASS' if sandbox_result.success else 'FAIL',
                'output': sandbox_result.output,
                'error': sandbox_result.error,
                'execution_time': sandbox_result.execution_time,
                'memory_usage': sandbox_result.memory_usage,
                'warnings': validation_result.warnings
            }
            
        except Exception as e:
            logger.error(f"快速测试失败: {e}")
            return {
                'success': False,
                'result': 'ERROR',
                'error': str(e),
                'output': '',
                'execution_time': 0.0,
                'memory_usage': 0.0
            }