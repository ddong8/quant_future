"""
策略管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...models.strategy import StrategyStatus, StrategyType, StrategyVersion
from sqlalchemy import and_, desc
from datetime import datetime
from ...schemas.strategy import (
    StrategyCreate, StrategyUpdate, StrategyResponse, StrategyListResponse,
    StrategySearchParams, StrategyStatsResponse, StrategyExecutionRequest,
    StrategyExecutionResponse
)
from ...services.strategy_service import strategy_service
from ...services.strategy_validation_service import StrategyCodeValidator, StrategyTestFramework, create_default_test_framework
from ...core.response import success_response, error_response

router = APIRouter(prefix="/strategies", tags=["策略管理"])


@router.post("/", response_model=StrategyResponse, summary="创建策略")
async def create_strategy(
    strategy_data: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新策略"""
    try:
        strategy = strategy_service.create_strategy(db, strategy_data, current_user.id)
        return success_response(data=strategy)
    except Exception as e:
        return error_response(message=str(e))


@router.get("/", response_model=List[StrategyListResponse], summary="获取策略列表")
async def get_strategies(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    strategy_type: Optional[StrategyType] = Query(None, description="策略类型"),
    status: Optional[StrategyStatus] = Query(None, description="策略状态"),
    is_public: Optional[bool] = Query(None, description="是否公开"),
    is_template: Optional[bool] = Query(None, description="是否为模板"),
    is_running: Optional[bool] = Query(None, description="是否正在运行"),
    sort_by: str = Query("updated_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取策略列表"""
    try:
        search_params = StrategySearchParams(
            keyword=keyword,
            strategy_type=strategy_type,
            status=status,
            is_public=is_public,
            is_template=is_template,
            is_running=is_running,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size
        )
        
        strategies, total = strategy_service.search_strategies(db, search_params, current_user.id)
        
        return success_response(
            data=strategies,
            meta={
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        )
    except Exception as e:
        return error_response(message=str(e))


@router.get("/my", response_model=List[StrategyListResponse], summary="获取我的策略")
async def get_my_strategies(
    status: Optional[StrategyStatus] = Query(None, description="策略状态"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的策略列表"""
    try:
        strategies = strategy_service.get_user_strategies(db, current_user.id, status)
        return success_response(data=strategies)
    except Exception as e:
        return error_response(message=str(e))


@router.get("/stats", response_model=StrategyStatsResponse, summary="获取策略统计")
async def get_strategy_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取策略统计信息"""
    try:
        stats = strategy_service.get_strategy_statistics(db, current_user.id)
        return success_response(data=stats)
    except Exception as e:
        return error_response(message=str(e))


@router.get("/{strategy_id}", response_model=StrategyResponse, summary="获取策略详情")
async def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取策略详情"""
    try:
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        return success_response(data=strategy)
    except Exception as e:
        return error_response(message=str(e))


@router.get("/uuid/{strategy_uuid}", response_model=StrategyResponse, summary="通过UUID获取策略")
async def get_strategy_by_uuid(
    strategy_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """通过UUID获取策略详情"""
    try:
        strategy = strategy_service.get_strategy_by_uuid(db, strategy_uuid, current_user.id)
        return success_response(data=strategy)
    except Exception as e:
        return error_response(message=str(e))


@router.put("/{strategy_id}", response_model=StrategyResponse, summary="更新策略")
async def update_strategy(
    strategy_id: int,
    strategy_data: StrategyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新策略"""
    try:
        strategy = strategy_service.update_strategy(db, strategy_id, strategy_data, current_user.id)
        return success_response(data=strategy)
    except Exception as e:
        return error_response(message=str(e))


@router.delete("/{strategy_id}", summary="删除策略")
async def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除策略"""
    try:
        success = strategy_service.delete_strategy(db, strategy_id, current_user.id)
        return success_response(data={"deleted": success})
    except Exception as e:
        return error_response(message=str(e))


@router.post("/{strategy_id}/copy", response_model=StrategyResponse, summary="复制策略")
async def copy_strategy(
    strategy_id: int,
    new_name: Optional[str] = Query(None, description="新策略名称"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """复制策略"""
    try:
        strategy = strategy_service.copy_strategy(db, strategy_id, current_user.id, new_name)
        return success_response(data=strategy)
    except Exception as e:
        return error_response(message=str(e))


@router.post("/{strategy_id}/execute", response_model=StrategyExecutionResponse, summary="执行策略操作")
async def execute_strategy(
    strategy_id: int,
    execution_request: StrategyExecutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行策略操作（启动、停止、暂停、恢复）"""
    try:
        # 获取策略
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        # 检查权限
        if strategy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        # TODO: 实现策略执行逻辑
        # 这里应该调用策略执行引擎
        
        response = StrategyExecutionResponse(
            strategy_id=strategy_id,
            action=execution_request.action,
            success=True,
            message=f"策略{execution_request.action}操作已提交",
            execution_id=f"exec_{strategy_id}_{int(datetime.now().timestamp())}",
            timestamp=datetime.now()
        )
        
        return success_response(data=response)
    except Exception as e:
        return error_response(message=str(e))


@router.get("/{strategy_id}/versions", summary="获取策略版本列表")
async def get_strategy_versions(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取策略版本列表"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        # 获取版本列表
        versions = db.query(StrategyVersion).filter(
            StrategyVersion.strategy_id == strategy_id
        ).order_by(desc(StrategyVersion.version_number)).all()
        
        return success_response(data=versions)
    except Exception as e:
        return error_response(message=str(e))


@router.get("/{strategy_id}/versions/{version_id}", summary="获取策略版本详情")
async def get_strategy_version(
    strategy_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取策略版本详情"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        # 获取版本详情
        version = db.query(StrategyVersion).filter(
            and_(
                StrategyVersion.id == version_id,
                StrategyVersion.strategy_id == strategy_id
            )
        ).first()
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="版本不存在"
            )
        
        return success_response(data=version)
    except Exception as e:
        return error_response(message=str(e))


@router.post("/{strategy_id}/versions/{version_id}/restore", summary="恢复到指定版本")
async def restore_strategy_version(
    strategy_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """恢复策略到指定版本"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        if strategy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        # 检查策略是否正在运行
        if strategy.is_running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="策略正在运行，无法恢复版本"
            )
        
        # 获取目标版本
        target_version = db.query(StrategyVersion).filter(
            and_(
                StrategyVersion.id == version_id,
                StrategyVersion.strategy_id == strategy_id
            )
        ).first()
        
        if not target_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="目标版本不存在"
            )
        
        # 恢复策略代码
        strategy.code = target_version.code
        strategy.entry_point = target_version.entry_point
        strategy.parameters = target_version.parameters
        strategy.version += 1
        
        # 创建新版本记录
        new_version = StrategyVersion(
            version_number=strategy.version,
            version_name=f"恢复到版本 {target_version.version_number}",
            description=f"从版本 {target_version.version_number} 恢复",
            code=target_version.code,
            entry_point=target_version.entry_point,
            parameters=target_version.parameters,
            change_log=f"恢复到版本 {target_version.version_number}",
            strategy_id=strategy_id,
            user_id=current_user.id
        )
        
        db.add(new_version)
        db.commit()
        db.refresh(strategy)
        
        return success_response(data=strategy)
    except Exception as e:
        db.rollback()
        return error_response(message=str(e))


@router.post("/{strategy_id}/validate", summary="验证策略代码")
async def validate_strategy_code(
    strategy_id: int,
    code_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """验证策略代码"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        if strategy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        code = code_data.get('code', '')
        entry_point = code_data.get('entry_point', 'main')
        
        # 执行代码验证
        from ...services.code_validation_service import code_validation_service
        validation_result = code_validation_service.validate_python_code(code, entry_point)
        
        return success_response(data={
            'is_valid': validation_result.is_valid,
            'errors': [
                {
                    'line': error.line,
                    'column': error.column,
                    'message': error.message,
                    'severity': error.severity,
                    'rule': error.rule
                }
                for error in validation_result.errors
            ],
            'warnings': [
                {
                    'line': warning.line,
                    'column': warning.column,
                    'message': warning.message,
                    'severity': warning.severity,
                    'rule': warning.rule
                }
                for warning in validation_result.warnings
            ],
            'metrics': {
                'lines_of_code': validation_result.metrics.lines_of_code,
                'functions_count': validation_result.metrics.functions_count,
                'classes_count': validation_result.metrics.classes_count,
                'imports_count': validation_result.metrics.imports_count,
                'complexity': validation_result.metrics.complexity,
                'maintainability_index': validation_result.metrics.maintainability_index
            },
            'suggestions': validation_result.suggestions
        })
    except Exception as e:
        return error_response(message=str(e))


@router.post("/{strategy_id}/format", summary="格式化策略代码")
async def format_strategy_code(
    strategy_id: int,
    code_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """格式化策略代码"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        if strategy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        code = code_data.get('code', '')
        language = code_data.get('language', 'python')
        
        # 执行代码格式化
        from ...services.code_validation_service import code_validation_service
        success, formatted_code, error_message = code_validation_service.format_code(code, language)
        
        if success:
            return success_response(data={
                'formatted_code': formatted_code
            })
        else:
            return error_response(message=error_message)
    except Exception as e:
        return error_response(message=str(e))


@router.get("/{strategy_id}/versions/compare", summary="比较策略版本")
async def compare_strategy_versions(
    strategy_id: int,
    version1_id: int,
    version2_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """比较两个策略版本的差异"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        # 执行版本比较
        from ...services.version_control_service import version_control_service
        version_diff = version_control_service.compare_versions(
            db, version1_id, version2_id, current_user.id
        )
        
        return success_response(data={
            'old_version': {
                'id': version_diff.old_version.id,
                'version_number': version_diff.old_version.version_number,
                'version_name': version_diff.old_version.version_name,
                'created_at': version_diff.old_version.created_at.isoformat() if version_diff.old_version.created_at else None
            },
            'new_version': {
                'id': version_diff.new_version.id,
                'version_number': version_diff.new_version.version_number,
                'version_name': version_diff.new_version.version_name,
                'created_at': version_diff.new_version.created_at.isoformat() if version_diff.new_version.created_at else None
            },
            'diff_blocks': [
                {
                    'old_start': block.old_start,
                    'old_count': block.old_count,
                    'new_start': block.new_start,
                    'new_count': block.new_count,
                    'lines': [
                        {
                            'line_number': line.line_number,
                            'content': line.content,
                            'type': line.type,
                            'old_line_number': line.old_line_number,
                            'new_line_number': line.new_line_number
                        }
                        for line in block.lines
                    ]
                }
                for block in version_diff.diff_blocks
            ],
            'stats': version_diff.stats
        })
    except Exception as e:
        return error_response(message=str(e))


@router.get("/{strategy_id}/versions/tree", summary="获取版本树")
async def get_strategy_version_tree(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取策略版本树结构"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        # 获取版本树
        from ...services.version_control_service import version_control_service
        version_tree = version_control_service.get_version_tree(
            db, strategy_id, current_user.id
        )
        
        return success_response(data=version_tree)
    except Exception as e:
        return error_response(message=str(e))


@router.post("/{strategy_id}/versions/create", summary="创建新版本")
async def create_strategy_version(
    strategy_id: int,
    version_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从代码创建新版本"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        if strategy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        # 提取版本数据
        code = version_data.get('code', '')
        version_name = version_data.get('version_name', '')
        description = version_data.get('description', '')
        change_log = version_data.get('change_log', '')
        is_major_version = version_data.get('is_major_version', False)
        
        if not code or not version_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="代码和版本名称不能为空"
            )
        
        # 创建新版本
        from ...services.version_control_service import version_control_service
        new_version = version_control_service.create_version_from_code(
            db=db,
            strategy_id=strategy_id,
            code=code,
            version_name=version_name,
            description=description,
            change_log=change_log,
            user_id=current_user.id,
            is_major_version=is_major_version
        )
        
        return success_response(data=new_version.to_dict())
    except Exception as e:
        return error_response(message=str(e))


@router.post("/{strategy_id}/versions/{version_id}/rollback", summary="回滚到指定版本")
async def rollback_strategy_version(
    strategy_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """回滚策略到指定版本"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        if strategy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        # 执行回滚
        from ...services.version_control_service import version_control_service
        updated_strategy = version_control_service.rollback_to_version(
            db=db,
            strategy_id=strategy_id,
            target_version_id=version_id,
            user_id=current_user.id
        )
        
        return success_response(data=updated_strategy.to_dict())
    except Exception as e:
        return error_response(message=str(e))


@router.post("/{strategy_id}/versions/branch", summary="创建版本分支")
async def create_strategy_branch(
    strategy_id: int,
    branch_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建策略版本分支"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        if strategy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        # 提取分支数据
        branch_name = branch_data.get('branch_name', '')
        description = branch_data.get('description', '')
        base_version_id = branch_data.get('base_version_id')
        
        if not branch_name or not base_version_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="分支名称和基础版本ID不能为空"
            )
        
        # 创建分支
        from ...services.version_control_service import version_control_service
        branch = version_control_service.create_branch(
            db=db,
            strategy_id=strategy_id,
            branch_name=branch_name,
            description=description,
            base_version_id=base_version_id,
            user_id=current_user.id
        )
        
        return success_response(data={
            'name': branch.name,
            'description': branch.description,
            'base_version_id': branch.base_version_id,
            'head_version_id': branch.head_version_id,
            'created_at': branch.created_at.isoformat(),
            'is_active': branch.is_active
        })
    except Exception as e:
        return error_response(message=str(e))


@router.post("/{strategy_id}/versions/merge", summary="合并版本")
async def merge_strategy_versions(
    strategy_id: int,
    merge_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """合并策略版本"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        if strategy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        # 提取合并数据
        source_version_id = merge_data.get('source_version_id')
        target_version_id = merge_data.get('target_version_id')
        merge_message = merge_data.get('merge_message', '')
        
        if not source_version_id or not target_version_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="源版本ID和目标版本ID不能为空"
            )
        
        # 执行合并
        from ...services.version_control_service import version_control_service
        merged_version = version_control_service.merge_versions(
            db=db,
            strategy_id=strategy_id,
            source_version_id=source_version_id,
            target_version_id=target_version_id,
            merge_message=merge_message,
            user_id=current_user.id
        )
        
        return success_response(data=merged_version.to_dict())
    except Exception as e:
        return error_response(message=str(e))


@router.get("/{strategy_id}/versions/compare/export", summary="导出版本差异")
async def export_version_diff(
    strategy_id: int,
    version1_id: int,
    version2_id: int,
    format: str = "unified",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出版本差异文件"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        # 获取版本差异
        from ...services.version_control_service import version_control_service
        version_diff = version_control_service.compare_versions(
            db, version1_id, version2_id, current_user.id
        )
        
        # 导出差异
        diff_content = version_control_service.export_version_diff(version_diff, format)
        
        return success_response(data={
            'diff_content': diff_content,
            'format': format,
            'filename': f"strategy_{strategy_id}_v{version_diff.old_version.version_number}_vs_v{version_diff.new_version.version_number}.diff"
        })
    except Exception as e:
        return error_response(message=str(e))


@router.post("/{strategy_id}/test/unit", summary="运行单元测试")
async def run_unit_tests(
    strategy_id: int,
    test_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """运行策略单元测试"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        if strategy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        code = test_data.get('code', strategy.code)
        entry_point = test_data.get('entry_point', strategy.entry_point)
        
        # 运行单元测试
        from ...services.strategy_test_service import strategy_test_service
        test_suite = strategy_test_service.run_unit_tests(code, entry_point)
        
        return success_response(data={
            'name': test_suite.name,
            'description': test_suite.description,
            'total_tests': test_suite.total_tests,
            'passed_tests': test_suite.passed_tests,
            'failed_tests': test_suite.failed_tests,
            'total_time': test_suite.total_time,
            'coverage': test_suite.coverage,
            'tests': [
                {
                    'test_name': test.test_name,
                    'passed': test.passed,
                    'execution_time': test.execution_time,
                    'error_message': test.error_message,
                    'output': test.output
                }
                for test in test_suite.tests
            ]
        })
    except Exception as e:
        return error_response(message=str(e))


@router.post("/{strategy_id}/test/integration", summary="运行集成测试")
async def run_integration_tests(
    strategy_id: int,
    test_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """运行策略集成测试"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        if strategy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        code = test_data.get('code', strategy.code)
        entry_point = test_data.get('entry_point', strategy.entry_point)
        
        # 运行集成测试
        from ...services.strategy_test_service import strategy_test_service
        test_suite = strategy_test_service.run_integration_test(code, entry_point)
        
        return success_response(data={
            'name': test_suite.name,
            'description': test_suite.description,
            'total_tests': test_suite.total_tests,
            'passed_tests': test_suite.passed_tests,
            'failed_tests': test_suite.failed_tests,
            'total_time': test_suite.total_time,
            'coverage': test_suite.coverage,
            'tests': [
                {
                    'test_name': test.test_name,
                    'passed': test.passed,
                    'execution_time': test.execution_time,
                    'error_message': test.error_message,
                    'output': test.output
                }
                for test in test_suite.tests
            ]
        })
    except Exception as e:
        return error_response(message=str(e))


@router.post("/{strategy_id}/test/performance", summary="运行性能测试")
async def run_performance_test(
    strategy_id: int,
    test_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """运行策略性能测试"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        if strategy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        code = test_data.get('code', strategy.code)
        entry_point = test_data.get('entry_point', strategy.entry_point)
        
        # 运行性能测试
        from ...services.strategy_test_service import strategy_test_service
        performance_metrics = strategy_test_service.run_performance_test(code, entry_point)
        
        return success_response(data={
            'execution_time': performance_metrics.execution_time,
            'memory_usage': performance_metrics.memory_usage,
            'cpu_usage': performance_metrics.cpu_usage,
            'function_calls': performance_metrics.function_calls,
            'complexity_score': performance_metrics.complexity_score
        })
    except Exception as e:
        return error_response(message=str(e))


@router.post("/{strategy_id}/test/full", summary="运行完整测试套件")
async def run_full_test_suite(
    strategy_id: int,
    test_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """运行完整的测试套件"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        if strategy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        code = test_data.get('code', strategy.code)
        entry_point = test_data.get('entry_point', strategy.entry_point)
        
        # 运行所有测试
        from ...services.strategy_test_service import strategy_test_service
        
        # 1. 单元测试
        unit_test_suite = strategy_test_service.run_unit_tests(code, entry_point)
        
        # 2. 集成测试
        integration_test_suite = strategy_test_service.run_integration_test(code, entry_point)
        
        # 3. 性能测试
        performance_metrics = strategy_test_service.run_performance_test(code, entry_point)
        
        # 4. 生成完整报告
        test_suites = [unit_test_suite, integration_test_suite]
        test_report = strategy_test_service.generate_test_report(test_suites, performance_metrics)
        
        return success_response(data=test_report)
    except Exception as e:
        return error_response(message=str(e))

@router.post("/{strategy_id}/validate", summary="验证策略代码")
async def validate_strategy_code(
    strategy_id: int,
    code_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """验证策略代码"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        if strategy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        code = code_data.get('code', strategy.code)
        strategy_name = code_data.get('name', strategy.name)
        
        # 创建验证器并执行验证
        validator = StrategyCodeValidator()
        validation_result = validator.validate_code(code, strategy_name)
        
        return {
            "success": True,
            "data": {
                "is_valid": validation_result.is_valid,
                "execution_time": validation_result.execution_time,
                "issues": [
                    {
                        "level": issue.level,
                        "category": issue.category,
                        "message": issue.message,
                        "line_number": issue.line_number,
                        "column_number": issue.column_number,
                        "code": issue.code,
                        "suggestion": issue.suggestion
                    }
                    for issue in validation_result.issues
                ],
                "code_metrics": validation_result.code_metrics,
                "dependencies": validation_result.dependencies,
                "entry_points": validation_result.entry_points
            },
            "message": "代码验证完成"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{strategy_id}/test", summary="运行策略测试")
async def run_strategy_tests(
    strategy_id: int,
    test_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """运行策略测试用例"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        if strategy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        code = test_data.get('code', strategy.code)
        test_type = test_data.get('test_type', 'default')  # default, custom
        
        # 创建测试框架
        if test_type == 'default':
            test_framework = create_default_test_framework()
        else:
            # 自定义测试用例
            test_framework = StrategyTestFramework()
            custom_tests = test_data.get('custom_tests', [])
            for test_case in custom_tests:
                # 这里需要更安全的方式来处理自定义测试
                pass
        
        # 运行测试
        test_results = test_framework.run_tests(code)
        
        return {
            "success": True,
            "data": test_results,
            "message": "测试执行完成"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{strategy_id}/analyze", summary="分析策略代码质量")
async def analyze_strategy_quality(
    strategy_id: int,
    analysis_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """分析策略代码质量"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        if strategy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        code = analysis_data.get('code', strategy.code)
        
        # 执行代码验证（包含质量分析）
        validator = StrategyCodeValidator()
        validation_result = validator.validate_code(code, strategy.name)
        
        # 计算质量评分
        quality_score = 100
        error_count = len([issue for issue in validation_result.issues if issue.level == "error"])
        warning_count = len([issue for issue in validation_result.issues if issue.level == "warning"])
        
        quality_score -= error_count * 20  # 每个错误扣20分
        quality_score -= warning_count * 5  # 每个警告扣5分
        quality_score = max(0, quality_score)
        
        # 生成改进建议
        suggestions = []
        if error_count > 0:
            suggestions.append("修复所有语法和安全错误")
        if warning_count > 5:
            suggestions.append("减少代码警告数量")
        if validation_result.code_metrics.get('complexity_score', 0) > 10:
            suggestions.append("降低代码复杂度")
        if validation_result.code_metrics.get('maintainability_index', 100) < 60:
            suggestions.append("提高代码可维护性")
        
        return {
            "success": True,
            "data": {
                "quality_score": quality_score,
                "grade": "A" if quality_score >= 90 else "B" if quality_score >= 80 else "C" if quality_score >= 70 else "D",
                "error_count": error_count,
                "warning_count": warning_count,
                "code_metrics": validation_result.code_metrics,
                "suggestions": suggestions,
                "detailed_issues": [
                    {
                        "level": issue.level,
                        "category": issue.category,
                        "message": issue.message,
                        "line_number": issue.line_number,
                        "suggestion": issue.suggestion
                    }
                    for issue in validation_result.issues
                ]
            },
            "message": "代码质量分析完成"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{strategy_id}/dependencies/check", summary="检查策略依赖")
async def check_strategy_dependencies(
    strategy_id: int,
    dependency_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查策略依赖和环境"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        if strategy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        code = dependency_data.get('code', strategy.code)
        
        # 执行依赖检查
        validator = StrategyCodeValidator()
        validation_result = validator.validate_code(code, strategy.name)
        
        # 检查依赖可用性
        dependency_status = {}
        for dep in validation_result.dependencies:
            try:
                __import__(dep)
                dependency_status[dep] = {
                    "available": True,
                    "version": "unknown",
                    "status": "installed"
                }
            except ImportError:
                dependency_status[dep] = {
                    "available": False,
                    "version": None,
                    "status": "missing"
                }
        
        # 统计依赖信息
        total_deps = len(validation_result.dependencies)
        available_deps = len([dep for dep, status in dependency_status.items() if status["available"]])
        missing_deps = total_deps - available_deps
        
        return {
            "success": True,
            "data": {
                "total_dependencies": total_deps,
                "available_dependencies": available_deps,
                "missing_dependencies": missing_deps,
                "dependency_status": dependency_status,
                "dependency_issues": [
                    issue for issue in validation_result.issues 
                    if issue.category == "dependency"
                ],
                "recommendations": [
                    f"安装缺失的依赖: {dep}" 
                    for dep, status in dependency_status.items() 
                    if not status["available"]
                ]
            },
            "message": "依赖检查完成"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{strategy_id}/security/scan", summary="安全扫描")
async def scan_strategy_security(
    strategy_id: int,
    scan_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """扫描策略代码安全问题"""
    try:
        # 验证策略权限
        strategy = strategy_service.get_strategy(db, strategy_id, current_user.id)
        
        if strategy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        code = scan_data.get('code', strategy.code)
        
        # 执行安全扫描
        validator = StrategyCodeValidator()
        validation_result = validator.validate_code(code, strategy.name)
        
        # 提取安全相关问题
        security_issues = [
            issue for issue in validation_result.issues 
            if issue.category == "security"
        ]
        
        # 计算安全评分
        security_score = 100
        critical_issues = len([issue for issue in security_issues if issue.level == "error"])
        warning_issues = len([issue for issue in security_issues if issue.level == "warning"])
        
        security_score -= critical_issues * 30  # 每个严重问题扣30分
        security_score -= warning_issues * 10   # 每个警告问题扣10分
        security_score = max(0, security_score)
        
        return {
            "success": True,
            "data": {
                "security_score": security_score,
                "risk_level": "low" if security_score >= 80 else "medium" if security_score >= 60 else "high",
                "critical_issues": critical_issues,
                "warning_issues": warning_issues,
                "security_issues": [
                    {
                        "level": issue.level,
                        "message": issue.message,
                        "line_number": issue.line_number,
                        "suggestion": issue.suggestion
                    }
                    for issue in security_issues
                ],
                "recommendations": [
                    "移除所有危险函数调用",
                    "避免导入不安全的模块",
                    "使用安全的编程实践"
                ] if security_issues else ["代码安全检查通过"]
            },
            "message": "安全扫描完成"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))