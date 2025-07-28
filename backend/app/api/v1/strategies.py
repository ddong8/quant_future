"""
策略管理API路由
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ...core.dependencies import (
    get_database,
    get_current_user,
    require_trader_or_admin,
    get_pagination_params,
    get_sort_params,
    PaginationParams,
    SortParams,
)
from ...core.response import (
    success_response,
    created_response,
    paginated_response,
    deleted_response,
)
from ...services.strategy_service import StrategyService
from ...schemas.strategy import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyListResponse,
    StrategySearchRequest,
    StrategyStatusUpdate,
    StrategyVersionCreate,
    StrategyVersionResponse,
    StrategyStatsResponse,
    StrategyCloneRequest,
    BatchStrategyOperation,
    StrategyTemplate,
    StrategyValidationRequest,
    StrategyValidationResponse,
    StrategyTestRequest,
    StrategyTestResponse,
    StrategySandboxRequest,
    StrategySandboxResponse,
)
from ...models import User, StrategyStatus

router = APIRouter()


@router.post("/", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    strategy_data: StrategyCreate,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """创建策略"""
    strategy_service = StrategyService(db)
    strategy_response = strategy_service.create_strategy(strategy_data, current_user.id)
    
    return created_response(
        data=strategy_response.dict(),
        message="策略创建成功"
    )


@router.get("/", response_model=List[StrategyListResponse])
async def get_strategies_list(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[StrategyStatus] = Query(None, description="策略状态"),
    tags: Optional[List[str]] = Query(None, description="标签列表"),
    min_return: Optional[float] = Query(None, description="最小收益率"),
    max_drawdown: Optional[float] = Query(None, description="最大回撤"),
    pagination: PaginationParams = Depends(get_pagination_params),
    sort_params: SortParams = Depends(get_sort_params),
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取策略列表"""
    search_params = StrategySearchRequest(
        keyword=keyword,
        status=status,
        tags=tags,
        min_return=min_return,
        max_drawdown=max_drawdown,
    )
    
    strategy_service = StrategyService(db)
    strategies, total = strategy_service.get_strategies_list(
        user_id=current_user.id,
        search_params=search_params,
        pagination=pagination,
        sort_params=sort_params
    )
    
    return paginated_response(
        data=[strategy.dict() for strategy in strategies],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        message="获取策略列表成功"
    )


@router.get("/stats", response_model=StrategyStatsResponse)
async def get_strategy_stats(
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取策略统计信息"""
    strategy_service = StrategyService(db)
    stats = strategy_service.get_strategy_stats(current_user.id)
    
    return success_response(
        data=stats.dict(),
        message="获取策略统计成功"
    )


@router.get("/templates", response_model=List[StrategyTemplate])
async def get_strategy_templates(
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取策略模板"""
    strategy_service = StrategyService(db)
    templates = strategy_service.get_strategy_templates()
    
    return success_response(
        data=[template.dict() for template in templates],
        message="获取策略模板成功"
    )


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy_by_id(
    strategy_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """根据ID获取策略详情"""
    strategy_service = StrategyService(db)
    strategy_response = strategy_service.get_strategy_by_id(strategy_id, current_user.id)
    
    return success_response(
        data=strategy_response.dict(),
        message="获取策略详情成功"
    )


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: int,
    strategy_data: StrategyUpdate,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """更新策略"""
    strategy_service = StrategyService(db)
    strategy_response = strategy_service.update_strategy(
        strategy_id, strategy_data, current_user.id
    )
    
    return success_response(
        data=strategy_response.dict(),
        message="策略更新成功"
    )


@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """删除策略"""
    strategy_service = StrategyService(db)
    success = strategy_service.delete_strategy(strategy_id, current_user.id)
    
    if success:
        return deleted_response(message="策略删除成功")


@router.put("/{strategy_id}/status", response_model=StrategyResponse)
async def update_strategy_status(
    strategy_id: int,
    status_update: StrategyStatusUpdate,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """更新策略状态"""
    strategy_service = StrategyService(db)
    strategy_response = strategy_service.update_strategy_status(
        strategy_id, status_update, current_user.id
    )
    
    return success_response(
        data=strategy_response.dict(),
        message="策略状态更新成功"
    )


@router.post("/{strategy_id}/versions", response_model=StrategyVersionResponse)
async def create_strategy_version(
    strategy_id: int,
    version_data: StrategyVersionCreate,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """创建策略版本"""
    strategy_service = StrategyService(db)
    version_response = strategy_service.create_strategy_version(
        strategy_id, version_data, current_user.id
    )
    
    return created_response(
        data=version_response.dict(),
        message="策略版本创建成功"
    )


@router.get("/{strategy_id}/versions", response_model=List[StrategyVersionResponse])
async def get_strategy_versions(
    strategy_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取策略版本列表"""
    strategy_service = StrategyService(db)
    versions = strategy_service.get_strategy_versions(strategy_id, current_user.id)
    
    return success_response(
        data=[version.dict() for version in versions],
        message="获取策略版本列表成功"
    )


@router.post("/{strategy_id}/clone", response_model=StrategyResponse)
async def clone_strategy(
    strategy_id: int,
    clone_data: StrategyCloneRequest,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """克隆策略"""
    strategy_service = StrategyService(db)
    cloned_strategy = strategy_service.clone_strategy(
        strategy_id, clone_data, current_user.id
    )
    
    return created_response(
        data=cloned_strategy.dict(),
        message="策略克隆成功"
    )


@router.post("/batch-operation")
async def batch_strategy_operation(
    operation_data: BatchStrategyOperation,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """批量策略操作"""
    strategy_service = StrategyService(db)
    result = strategy_service.batch_strategy_operation(operation_data, current_user.id)
    
    return success_response(
        data=result,
        message=f"批量操作完成，成功: {result['success_count']}, 失败: {result['failed_count']}"
    )


# 策略验证和测试相关API
from ...services.strategy_validator import StrategyValidator
from ...services.strategy_tester import StrategyTester
from ...services.strategy_sandbox import StrategySandbox


@router.post("/validate", response_model=StrategyValidationResponse)
async def validate_strategy_code(
    validation_request: StrategyValidationRequest,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """验证策略代码"""
    validator = StrategyValidator()
    validation_result = validator.validate_strategy(validation_request)
    
    return success_response(
        data=validation_result.dict(),
        message="策略代码验证完成"
    )


@router.post("/{strategy_id}/test", response_model=StrategyTestResponse)
async def test_strategy(
    strategy_id: int,
    test_request: StrategyTestRequest,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """测试策略"""
    tester = StrategyTester(db)
    test_result = tester.test_strategy(test_request, current_user.id)
    
    return success_response(
        data=test_result.dict(),
        message="策略测试完成"
    )


@router.post("/sandbox", response_model=StrategySandboxResponse)
async def execute_in_sandbox(
    sandbox_request: StrategySandboxRequest,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """在沙盒中执行策略代码"""
    sandbox = StrategySandbox()
    execution_result = sandbox.execute(sandbox_request)
    
    return success_response(
        data=execution_result.dict(),
        message="沙盒执行完成"
    )


@router.post("/quick-test")
async def quick_test_strategy(
    code: str,
    test_params: Optional[dict] = None,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """快速测试策略代码"""
    tester = StrategyTester(db)
    test_result = tester.run_quick_test(code, test_params)
    
    return success_response(
        data=test_result,
        message="快速测试完成"
    )


@router.get("/{strategy_id}/analysis")
async def analyze_strategy_code(
    strategy_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """分析策略代码"""
    strategy_service = StrategyService(db)
    strategy = strategy_service.get_strategy_by_id(strategy_id, current_user.id)
    
    validator = StrategyValidator()
    code_analysis = validator.analyze_code(strategy.code)
    dependency_info = validator.get_dependency_info(strategy.code)
    security_report = validator.generate_security_report(strategy.code)
    
    return success_response(
        data={
            'code_analysis': code_analysis.dict(),
            'dependencies': [dep.dict() for dep in dependency_info],
            'security_report': security_report.dict()
        },
        message="策略代码分析完成"
    )


@router.get("/{strategy_id}/security-report")
async def get_strategy_security_report(
    strategy_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取策略安全报告"""
    strategy_service = StrategyService(db)
    strategy = strategy_service.get_strategy_by_id(strategy_id, current_user.id)
    
    validator = StrategyValidator()
    security_report = validator.generate_security_report(strategy.code)
    
    return success_response(
        data=security_report.dict(),
        message="获取安全报告成功"
    )


@router.get("/{strategy_id}/dependencies")
async def get_strategy_dependencies(
    strategy_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取策略依赖信息"""
    strategy_service = StrategyService(db)
    strategy = strategy_service.get_strategy_by_id(strategy_id, current_user.id)
    
    validator = StrategyValidator()
    dependency_info = validator.get_dependency_info(strategy.code)
    
    return success_response(
        data=[dep.dict() for dep in dependency_info],
        message="获取依赖信息成功"
    )

@r
outer.post("/{strategy_id}/unit-test")
async def run_strategy_unit_tests(
    strategy_id: int,
    test_data: Optional[dict] = None,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """运行策略单元测试"""
    from ...services.strategy_unittest import run_strategy_unit_tests
    
    strategy_service = StrategyService(db)
    strategy = strategy_service.get_strategy_by_id(strategy_id, current_user.id)
    
    test_results = run_strategy_unit_tests(strategy.code, test_data or {})
    
    return success_response(
        data=test_results,
        message="单元测试完成"
    )


@router.post("/unit-test")
async def run_code_unit_tests(
    code: str,
    test_data: Optional[dict] = None,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """运行代码单元测试"""
    from ...services.strategy_unittest import run_strategy_unit_tests
    
    test_results = run_strategy_unit_tests(code, test_data or {})
    
    return success_response(
        data=test_results,
        message="单元测试完成"
    )
@rout
er.post("/{strategy_id}/comprehensive-validation")
async def comprehensive_strategy_validation(
    strategy_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """综合策略验证"""
    from ...services.strategy_validation_service import StrategyValidationService
    
    validation_service = StrategyValidationService(db)
    validation_result = validation_service.comprehensive_validation(strategy_id, current_user.id)
    
    return success_response(
        data=validation_result,
        message="综合验证完成"
    )


@router.post("/quick-validation")
async def quick_strategy_validation(
    code: str,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """快速策略验证"""
    from ...services.strategy_validation_service import StrategyValidationService
    
    validation_service = StrategyValidationService(db)
    validation_result = validation_service.quick_validation(code)
    
    return success_response(
        data=validation_result,
        message="快速验证完成"
    )