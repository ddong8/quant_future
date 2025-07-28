"""
策略验证和测试综合服务
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from sqlalchemy.orm import Session

from ..models import Strategy
from ..schemas.strategy import (
    StrategyValidationRequest,
    StrategyValidationResponse,
    StrategyTestRequest,
    StrategyTestResponse,
    StrategySandboxRequest,
    StrategySandboxResponse,
)
from .strategy_validator import StrategyValidator
from .strategy_sandbox import StrategySandbox
from .strategy_tester import StrategyTester
from .strategy_unittest import run_strategy_unit_tests
from ..core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class StrategyValidationService:
    """策略验证和测试综合服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.validator = StrategyValidator()
        self.sandbox = StrategySandbox()
        self.tester = StrategyTester(db)
    
    def comprehensive_validation(self, strategy_id: int, user_id: int) -> Dict[str, Any]:
        """综合验证策略"""
        try:
            # 获取策略
            strategy = self.db.query(Strategy).filter(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id
            ).first()
            
            if not strategy:
                raise NotFoundError("策略不存在")
            
            validation_start_time = datetime.utcnow()
            
            # 1. 代码验证
            code_validation = self._validate_code(strategy.code)
            
            # 2. 安全检查
            security_check = self._security_check(strategy.code)
            
            # 3. 依赖检查
            dependency_check = self._dependency_check(strategy.code)
            
            # 4. 结构检查
            structure_check = self._structure_check(strategy.code)
            
            # 5. 单元测试
            unit_test_results = self._run_unit_tests(strategy.code)
            
            # 6. 沙盒测试
            sandbox_test = self._sandbox_test(strategy.code)
            
            # 7. 性能评估
            performance_assessment = self._performance_assessment(strategy.code)
            
            # 综合评分
            overall_score = self._calculate_overall_score({
                'code_validation': code_validation,
                'security_check': security_check,
                'dependency_check': dependency_check,
                'structure_check': structure_check,
                'unit_tests': unit_test_results,
                'sandbox_test': sandbox_test,
                'performance': performance_assessment
            })
            
            # 生成建议
            recommendations = self._generate_comprehensive_recommendations({
                'code_validation': code_validation,
                'security_check': security_check,
                'dependency_check': dependency_check,
                'structure_check': structure_check,
                'unit_tests': unit_test_results,
                'sandbox_test': sandbox_test,
                'performance': performance_assessment
            })
            
            # 确定验证结果
            validation_result = self._determine_validation_result(overall_score, {
                'code_validation': code_validation,
                'security_check': security_check,
                'unit_tests': unit_test_results,
                'sandbox_test': sandbox_test
            })
            
            validation_time = (datetime.utcnow() - validation_start_time).total_seconds()
            
            return {
                'strategy_id': strategy.id,
                'strategy_name': strategy.name,
                'validation_time': validation_start_time.isoformat(),
                'execution_time': validation_time,
                'overall_result': validation_result,
                'overall_score': overall_score,
                'details': {
                    'code_validation': code_validation,
                    'security_check': security_check,
                    'dependency_check': dependency_check,
                    'structure_check': structure_check,
                    'unit_tests': unit_test_results,
                    'sandbox_test': sandbox_test,
                    'performance': performance_assessment
                },
                'recommendations': recommendations,
                'ready_for_deployment': validation_result == 'PASS' and overall_score >= 7.0
            }
            
        except Exception as e:
            logger.error(f"综合验证失败: {e}")
            return {
                'strategy_id': strategy_id,
                'strategy_name': "未知",
                'validation_time': datetime.utcnow().isoformat(),
                'execution_time': 0.0,
                'overall_result': 'ERROR',
                'overall_score': 0.0,
                'error': str(e),
                'recommendations': ["修复验证过程中的错误"],
                'ready_for_deployment': False
            }
    
    def _validate_code(self, code: str) -> Dict[str, Any]:
        """代码验证"""
        try:
            validation_request = StrategyValidationRequest(
                code=code,
                check_syntax=True,
                check_security=True,
                check_structure=True,
                check_dependencies=True
            )
            
            validation_result = self.validator.validate_strategy(validation_request)
            code_analysis = self.validator.analyze_code(code)
            
            return {
                'valid': validation_result.valid,
                'errors': validation_result.errors,
                'warnings': validation_result.warnings,
                'checks': validation_result.checks,
                'suggestions': validation_result.suggestions,
                'code_quality_score': (
                    code_analysis.security_score * 0.3 +
                    code_analysis.maintainability_score * 0.4 +
                    (10.0 - code_analysis.complexity_score) * 0.3
                ),
                'lines_of_code': code_analysis.lines_of_code,
                'complexity_score': code_analysis.complexity_score,
                'functions_count': code_analysis.functions_count
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"代码验证失败: {str(e)}"],
                'warnings': [],
                'checks': {},
                'suggestions': [],
                'code_quality_score': 0.0
            }
    
    def _security_check(self, code: str) -> Dict[str, Any]:
        """安全检查"""
        try:
            security_report = self.validator.generate_security_report(code)
            
            return {
                'security_level': security_report.security_level,
                'safe_to_execute': security_report.safe_to_execute,
                'issues_count': len(security_report.issues),
                'high_risk_issues': len([issue for issue in security_report.issues if issue['severity'] == 'HIGH']),
                'medium_risk_issues': len([issue for issue in security_report.issues if issue['severity'] == 'MEDIUM']),
                'issues': security_report.issues,
                'recommendations': security_report.recommendations,
                'security_score': 10.0 if security_report.security_level == 'HIGH' else 
                                5.0 if security_report.security_level == 'MEDIUM' else 2.0
            }
            
        except Exception as e:
            return {
                'security_level': 'LOW',
                'safe_to_execute': False,
                'issues_count': 1,
                'high_risk_issues': 1,
                'medium_risk_issues': 0,
                'issues': [{'type': 'error', 'description': f"安全检查失败: {str(e)}", 'severity': 'HIGH'}],
                'recommendations': ["修复安全检查错误"],
                'security_score': 0.0
            }
    
    def _dependency_check(self, code: str) -> Dict[str, Any]:
        """依赖检查"""
        try:
            dependency_info = self.validator.get_dependency_info(code)
            
            total_dependencies = len(dependency_info)
            available_dependencies = len([dep for dep in dependency_info if dep.is_available])
            missing_dependencies = [dep for dep in dependency_info if not dep.is_available]
            
            return {
                'total_dependencies': total_dependencies,
                'available_dependencies': available_dependencies,
                'missing_dependencies': len(missing_dependencies),
                'missing_list': [dep.module_name for dep in missing_dependencies],
                'dependency_score': (available_dependencies / total_dependencies * 10.0) if total_dependencies > 0 else 10.0,
                'all_dependencies_available': len(missing_dependencies) == 0,
                'dependencies': [
                    {
                        'module_name': dep.module_name,
                        'is_available': dep.is_available,
                        'version': dep.version,
                        'description': dep.description
                    }
                    for dep in dependency_info
                ]
            }
            
        except Exception as e:
            return {
                'total_dependencies': 0,
                'available_dependencies': 0,
                'missing_dependencies': 0,
                'missing_list': [],
                'dependency_score': 0.0,
                'all_dependencies_available': False,
                'error': f"依赖检查失败: {str(e)}"
            }
    
    def _structure_check(self, code: str) -> Dict[str, Any]:
        """结构检查"""
        try:
            validation_request = StrategyValidationRequest(
                code=code,
                check_syntax=False,
                check_security=False,
                check_structure=True,
                check_dependencies=False
            )
            
            validation_result = self.validator.validate_strategy(validation_request)
            
            return {
                'structure_valid': validation_result.checks.get('structure', False),
                'errors': validation_result.errors,
                'warnings': validation_result.warnings,
                'structure_score': 10.0 if validation_result.checks.get('structure', False) else 0.0,
                'has_required_functions': validation_result.checks.get('structure', False)
            }
            
        except Exception as e:
            return {
                'structure_valid': False,
                'errors': [f"结构检查失败: {str(e)}"],
                'warnings': [],
                'structure_score': 0.0,
                'has_required_functions': False
            }
    
    def _run_unit_tests(self, code: str) -> Dict[str, Any]:
        """运行单元测试"""
        try:
            test_data = {
                'params': {'symbol': 'SHFE.cu2401', 'initial_capital': 1000000},
                'initial_capital': 1000000
            }
            
            unit_test_results = run_strategy_unit_tests(code, test_data)
            
            return {
                'overall_success': unit_test_results['overall_success'],
                'total_tests': unit_test_results['total_tests'],
                'passed_tests': unit_test_results['passed_tests'],
                'failed_tests': unit_test_results['failed_tests'],
                'test_score': (unit_test_results['passed_tests'] / unit_test_results['total_tests'] * 10.0) 
                             if unit_test_results['total_tests'] > 0 else 0.0,
                'basic_tests': unit_test_results['basic_tests'],
                'trading_tests': unit_test_results['trading_tests'],
                'summary': unit_test_results['summary']
            }
            
        except Exception as e:
            return {
                'overall_success': False,
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'test_score': 0.0,
                'error': f"单元测试失败: {str(e)}"
            }
    
    def _sandbox_test(self, code: str) -> Dict[str, Any]:
        """沙盒测试"""
        try:
            test_data = {
                'params': {'symbol': 'SHFE.cu2401', 'initial_capital': 1000000},
                'initial_capital': 1000000
            }
            
            sandbox_request = StrategySandboxRequest(
                code=code,
                test_data=test_data,
                timeout=30
            )
            
            sandbox_result = self.sandbox.execute(sandbox_request)
            
            # 计算沙盒测试评分
            sandbox_score = 0.0
            if sandbox_result.success:
                sandbox_score = 8.0
                # 根据执行时间和内存使用调整评分
                if sandbox_result.execution_time < 5.0:
                    sandbox_score += 1.0
                if sandbox_result.memory_usage < 50.0:
                    sandbox_score += 1.0
            
            return {
                'success': sandbox_result.success,
                'output': sandbox_result.output,
                'error': sandbox_result.error,
                'execution_time': sandbox_result.execution_time,
                'memory_usage': sandbox_result.memory_usage,
                'sandbox_score': sandbox_score,
                'performance_acceptable': sandbox_result.execution_time < 30.0 and sandbox_result.memory_usage < 100.0
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f"沙盒测试失败: {str(e)}",
                'execution_time': 0.0,
                'memory_usage': 0.0,
                'sandbox_score': 0.0,
                'performance_acceptable': False
            }
    
    def _performance_assessment(self, code: str) -> Dict[str, Any]:
        """性能评估"""
        try:
            code_analysis = self.validator.analyze_code(code)
            
            # 性能指标
            performance_metrics = {
                'code_complexity': code_analysis.complexity_score,
                'maintainability': code_analysis.maintainability_score,
                'security': code_analysis.security_score,
                'lines_of_code': code_analysis.lines_of_code,
                'functions_count': code_analysis.functions_count
            }
            
            # 计算性能评分
            performance_score = (
                (10.0 - code_analysis.complexity_score) * 0.3 +  # 复杂度越低越好
                code_analysis.maintainability_score * 0.4 +      # 可维护性
                code_analysis.security_score * 0.3               # 安全性
            )
            
            # 性能等级
            if performance_score >= 8.0:
                performance_grade = 'A'
            elif performance_score >= 6.0:
                performance_grade = 'B'
            elif performance_score >= 4.0:
                performance_grade = 'C'
            else:
                performance_grade = 'D'
            
            return {
                'performance_score': performance_score,
                'performance_grade': performance_grade,
                'metrics': performance_metrics,
                'suggestions': code_analysis.suggestions,
                'optimization_needed': performance_score < 6.0
            }
            
        except Exception as e:
            return {
                'performance_score': 0.0,
                'performance_grade': 'F',
                'metrics': {},
                'suggestions': [],
                'optimization_needed': True,
                'error': f"性能评估失败: {str(e)}"
            }
    
    def _calculate_overall_score(self, results: Dict[str, Any]) -> float:
        """计算总体评分"""
        try:
            weights = {
                'code_validation': 0.25,
                'security_check': 0.20,
                'dependency_check': 0.15,
                'structure_check': 0.15,
                'unit_tests': 0.15,
                'sandbox_test': 0.10
            }
            
            total_score = 0.0
            
            # 代码验证评分
            if results['code_validation'].get('valid', False):
                total_score += results['code_validation'].get('code_quality_score', 0.0) * weights['code_validation']
            
            # 安全检查评分
            total_score += results['security_check'].get('security_score', 0.0) * weights['security_check']
            
            # 依赖检查评分
            total_score += results['dependency_check'].get('dependency_score', 0.0) * weights['dependency_check']
            
            # 结构检查评分
            total_score += results['structure_check'].get('structure_score', 0.0) * weights['structure_check']
            
            # 单元测试评分
            total_score += results['unit_tests'].get('test_score', 0.0) * weights['unit_tests']
            
            # 沙盒测试评分
            total_score += results['sandbox_test'].get('sandbox_score', 0.0) * weights['sandbox_test']
            
            return min(total_score, 10.0)
            
        except Exception as e:
            logger.error(f"计算总体评分失败: {e}")
            return 0.0
    
    def _generate_comprehensive_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """生成综合建议"""
        recommendations = []
        
        # 代码验证建议
        if not results['code_validation'].get('valid', False):
            recommendations.append("修复代码验证错误")
        
        if results['code_validation'].get('code_quality_score', 0.0) < 6.0:
            recommendations.append("提高代码质量评分")
        
        # 安全建议
        if not results['security_check'].get('safe_to_execute', True):
            recommendations.append("修复安全问题后再部署")
        
        if results['security_check'].get('high_risk_issues', 0) > 0:
            recommendations.append("立即修复高风险安全问题")
        
        # 依赖建议
        if not results['dependency_check'].get('all_dependencies_available', True):
            missing = results['dependency_check'].get('missing_list', [])
            recommendations.append(f"安装缺失的依赖模块: {', '.join(missing)}")
        
        # 结构建议
        if not results['structure_check'].get('structure_valid', False):
            recommendations.append("修复策略结构问题")
        
        # 单元测试建议
        if not results['unit_tests'].get('overall_success', False):
            recommendations.append("修复单元测试失败的问题")
        
        if results['unit_tests'].get('test_score', 0.0) < 8.0:
            recommendations.append("改进代码以通过更多单元测试")
        
        # 沙盒测试建议
        if not results['sandbox_test'].get('success', False):
            recommendations.append("修复沙盒执行错误")
        
        if not results['sandbox_test'].get('performance_acceptable', True):
            recommendations.append("优化代码性能，减少执行时间和内存使用")
        
        # 性能建议
        if results.get('performance', {}).get('optimization_needed', False):
            recommendations.append("优化代码性能和结构")
        
        # 如果没有具体建议，给出通用建议
        if not recommendations:
            recommendations.append("策略验证通过，可以考虑部署到测试环境")
        
        return recommendations
    
    def _determine_validation_result(self, overall_score: float, key_results: Dict[str, Any]) -> str:
        """确定验证结果"""
        # 关键检查项
        if not key_results['code_validation'].get('valid', False):
            return 'FAIL'
        
        if not key_results['security_check'].get('safe_to_execute', True):
            return 'FAIL'
        
        if not key_results['structure_check'].get('structure_valid', False):
            return 'FAIL'
        
        if not key_results['sandbox_test'].get('success', False):
            return 'ERROR'
        
        # 根据总体评分确定结果
        if overall_score >= 7.0:
            return 'PASS'
        elif overall_score >= 5.0:
            return 'WARNING'
        else:
            return 'FAIL'
    
    def quick_validation(self, code: str) -> Dict[str, Any]:
        """快速验证"""
        try:
            # 基础验证
            validation_request = StrategyValidationRequest(
                code=code,
                check_syntax=True,
                check_security=True,
                check_structure=True,
                check_dependencies=False
            )
            
            validation_result = self.validator.validate_strategy(validation_request)
            
            # 快速沙盒测试
            sandbox_request = StrategySandboxRequest(
                code=code,
                test_data={'params': {}, 'initial_capital': 1000000},
                timeout=10
            )
            
            sandbox_result = self.sandbox.execute(sandbox_request)
            
            # 快速评分
            quick_score = 0.0
            if validation_result.valid:
                quick_score += 5.0
            if validation_result.checks.get('security', False):
                quick_score += 2.0
            if validation_result.checks.get('structure', False):
                quick_score += 2.0
            if sandbox_result.success:
                quick_score += 1.0
            
            return {
                'validation_result': 'PASS' if quick_score >= 7.0 else 'FAIL',
                'quick_score': quick_score,
                'code_valid': validation_result.valid,
                'security_ok': validation_result.checks.get('security', False),
                'structure_ok': validation_result.checks.get('structure', False),
                'execution_ok': sandbox_result.success,
                'errors': validation_result.errors,
                'warnings': validation_result.warnings,
                'execution_error': sandbox_result.error if not sandbox_result.success else None
            }
            
        except Exception as e:
            return {
                'validation_result': 'ERROR',
                'quick_score': 0.0,
                'error': str(e)
            }