"""
策略验证相关的Pydantic模式
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from enum import Enum


class ValidationLevel(str, Enum):
    """验证级别"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationCategory(str, Enum):
    """验证分类"""
    SYNTAX = "syntax"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    DEPENDENCY = "dependency"
    LOGIC = "logic"


class ValidationIssueResponse(BaseModel):
    """验证问题响应"""
    level: ValidationLevel
    category: ValidationCategory
    message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    code: Optional[str] = None
    suggestion: Optional[str] = None

    class Config:
        from_attributes = True


class CodeMetricsResponse(BaseModel):
    """代码指标响应"""
    lines_of_code: int = 0
    lines_of_comments: int = 0
    blank_lines: int = 0
    functions_count: int = 0
    classes_count: int = 0
    complexity_score: int = 0
    maintainability_index: float = 0.0

    class Config:
        from_attributes = True


class ValidationResultResponse(BaseModel):
    """验证结果响应"""
    is_valid: bool
    execution_time: float
    issues: List[ValidationIssueResponse]
    code_metrics: CodeMetricsResponse
    dependencies: List[str]
    entry_points: List[str]

    class Config:
        from_attributes = True


class CodeValidationRequest(BaseModel):
    """代码验证请求"""
    code: str = Field(..., min_length=1, description="策略代码")
    name: Optional[str] = Field(None, description="策略名称")
    entry_point: Optional[str] = Field("main", description="入口函数")
    validation_level: Optional[str] = Field("all", description="验证级别")

    @validator('validation_level')
    def validate_validation_level(cls, v):
        allowed_levels = ['syntax', 'security', 'performance', 'style', 'dependency', 'logic', 'all']
        if v not in allowed_levels:
            raise ValueError(f'验证级别必须是: {", ".join(allowed_levels)}')
        return v


class TestCaseRequest(BaseModel):
    """测试用例请求"""
    name: str = Field(..., description="测试用例名称")
    description: Optional[str] = Field(None, description="测试用例描述")
    test_code: str = Field(..., description="测试代码")
    expected_result: Optional[Any] = Field(None, description="期望结果")
    timeout: Optional[int] = Field(30, ge=1, le=300, description="超时时间（秒）")


class TestSuiteRequest(BaseModel):
    """测试套件请求"""
    code: str = Field(..., description="策略代码")
    test_type: Optional[str] = Field("default", description="测试类型")
    custom_tests: Optional[List[TestCaseRequest]] = Field(None, description="自定义测试用例")
    timeout: Optional[int] = Field(60, ge=1, le=600, description="总超时时间（秒）")

    @validator('test_type')
    def validate_test_type(cls, v):
        allowed_types = ['default', 'custom', 'unit', 'integration', 'performance']
        if v not in allowed_types:
            raise ValueError(f'测试类型必须是: {", ".join(allowed_types)}')
        return v


class TestResultResponse(BaseModel):
    """测试结果响应"""
    name: str
    passed: bool
    execution_time: float
    output: Optional[str] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True


class TestSuiteResultResponse(BaseModel):
    """测试套件结果响应"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    test_results: List[TestResultResponse]
    total_execution_time: float

    class Config:
        from_attributes = True


class QualityAnalysisRequest(BaseModel):
    """质量分析请求"""
    code: str = Field(..., description="策略代码")
    analysis_type: Optional[str] = Field("comprehensive", description="分析类型")
    include_suggestions: Optional[bool] = Field(True, description="是否包含改进建议")

    @validator('analysis_type')
    def validate_analysis_type(cls, v):
        allowed_types = ['basic', 'comprehensive', 'security', 'performance']
        if v not in allowed_types:
            raise ValueError(f'分析类型必须是: {", ".join(allowed_types)}')
        return v


class QualityAnalysisResponse(BaseModel):
    """质量分析响应"""
    quality_score: float = Field(..., ge=0, le=100, description="质量评分")
    grade: str = Field(..., description="质量等级")
    error_count: int = Field(..., ge=0, description="错误数量")
    warning_count: int = Field(..., ge=0, description="警告数量")
    code_metrics: CodeMetricsResponse
    suggestions: List[str]
    detailed_issues: List[ValidationIssueResponse]

    class Config:
        from_attributes = True


class DependencyCheckRequest(BaseModel):
    """依赖检查请求"""
    code: str = Field(..., description="策略代码")
    check_availability: Optional[bool] = Field(True, description="是否检查依赖可用性")
    include_versions: Optional[bool] = Field(False, description="是否包含版本信息")


class DependencyStatus(BaseModel):
    """依赖状态"""
    available: bool
    version: Optional[str] = None
    status: str  # installed, missing, outdated
    location: Optional[str] = None

    class Config:
        from_attributes = True


class DependencyCheckResponse(BaseModel):
    """依赖检查响应"""
    total_dependencies: int
    available_dependencies: int
    missing_dependencies: int
    dependency_status: Dict[str, DependencyStatus]
    dependency_issues: List[ValidationIssueResponse]
    recommendations: List[str]

    class Config:
        from_attributes = True


class SecurityScanRequest(BaseModel):
    """安全扫描请求"""
    code: str = Field(..., description="策略代码")
    scan_level: Optional[str] = Field("standard", description="扫描级别")
    include_recommendations: Optional[bool] = Field(True, description="是否包含安全建议")

    @validator('scan_level')
    def validate_scan_level(cls, v):
        allowed_levels = ['basic', 'standard', 'strict']
        if v not in allowed_levels:
            raise ValueError(f'扫描级别必须是: {", ".join(allowed_levels)}')
        return v


class SecurityScanResponse(BaseModel):
    """安全扫描响应"""
    security_score: float = Field(..., ge=0, le=100, description="安全评分")
    risk_level: str = Field(..., description="风险级别")
    critical_issues: int = Field(..., ge=0, description="严重问题数量")
    warning_issues: int = Field(..., ge=0, description="警告问题数量")
    security_issues: List[ValidationIssueResponse]
    recommendations: List[str]

    class Config:
        from_attributes = True


class PerformanceAnalysisRequest(BaseModel):
    """性能分析请求"""
    code: str = Field(..., description="策略代码")
    analysis_depth: Optional[str] = Field("standard", description="分析深度")
    include_profiling: Optional[bool] = Field(False, description="是否包含性能分析")

    @validator('analysis_depth')
    def validate_analysis_depth(cls, v):
        allowed_depths = ['basic', 'standard', 'deep']
        if v not in allowed_depths:
            raise ValueError(f'分析深度必须是: {", ".join(allowed_depths)}')
        return v


class PerformanceMetrics(BaseModel):
    """性能指标"""
    execution_time: float = Field(..., description="执行时间（秒）")
    memory_usage: float = Field(..., description="内存使用（MB）")
    cpu_usage: float = Field(..., description="CPU使用率（%）")
    function_calls: int = Field(..., description="函数调用次数")
    complexity_score: int = Field(..., description="复杂度评分")

    class Config:
        from_attributes = True


class PerformanceAnalysisResponse(BaseModel):
    """性能分析响应"""
    performance_score: float = Field(..., ge=0, le=100, description="性能评分")
    performance_grade: str = Field(..., description="性能等级")
    metrics: PerformanceMetrics
    bottlenecks: List[str]
    optimization_suggestions: List[str]
    performance_issues: List[ValidationIssueResponse]

    class Config:
        from_attributes = True


class ComprehensiveAnalysisRequest(BaseModel):
    """综合分析请求"""
    code: str = Field(..., description="策略代码")
    include_validation: Optional[bool] = Field(True, description="是否包含验证")
    include_testing: Optional[bool] = Field(True, description="是否包含测试")
    include_quality: Optional[bool] = Field(True, description="是否包含质量分析")
    include_security: Optional[bool] = Field(True, description="是否包含安全扫描")
    include_performance: Optional[bool] = Field(True, description="是否包含性能分析")
    include_dependencies: Optional[bool] = Field(True, description="是否包含依赖检查")


class ComprehensiveAnalysisResponse(BaseModel):
    """综合分析响应"""
    overall_score: float = Field(..., ge=0, le=100, description="综合评分")
    overall_grade: str = Field(..., description="综合等级")
    validation_result: Optional[ValidationResultResponse] = None
    test_result: Optional[TestSuiteResultResponse] = None
    quality_analysis: Optional[QualityAnalysisResponse] = None
    security_scan: Optional[SecurityScanResponse] = None
    performance_analysis: Optional[PerformanceAnalysisResponse] = None
    dependency_check: Optional[DependencyCheckResponse] = None
    summary: Dict[str, Any]
    recommendations: List[str]

    class Config:
        from_attributes = True