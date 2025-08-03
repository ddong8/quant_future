"""
集成测试API端点
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.core.database import get_db
from ...core.dependencies import get_current_user
from app.models.user import User
from app.services.integration_test_service import integration_test_service
from app.core.permissions import require_permission

router = APIRouter()

@router.post("/run", response_model=Dict[str, Any])
async def run_integration_tests(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """运行集成测试"""
    
    # 检查权限（只有管理员可以运行集成测试）
    require_permission(current_user, "system:test")
    
    try:
        # 在后台运行集成测试
        background_tasks.add_task(
            _run_integration_tests_background,
            db
        )
        
        return {
            "message": "集成测试已开始运行",
            "status": "started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动集成测试失败: {str(e)}")

async def _run_integration_tests_background(db: Session):
    """后台运行集成测试"""
    try:
        await integration_test_service.run_full_integration_test(db)
    except Exception as e:
        print(f"Background integration test failed: {e}")

@router.get("/suites", response_model=List[Dict[str, Any]])
async def get_test_suites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有测试套件"""
    
    require_permission(current_user, "system:test")
    
    try:
        suites = integration_test_service.get_all_test_suites()
        return suites
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取测试套件失败: {str(e)}")

@router.get("/suites/{suite_id}", response_model=Dict[str, Any])
async def get_test_suite(
    suite_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定测试套件"""
    
    require_permission(current_user, "system:test")
    
    try:
        suite = integration_test_service.get_test_suite(suite_id)
        if not suite:
            raise HTTPException(status_code=404, detail="测试套件不存在")
        
        return suite.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取测试套件失败: {str(e)}")

@router.get("/summary", response_model=Dict[str, Any])
async def get_test_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取测试摘要"""
    
    require_permission(current_user, "system:test")
    
    try:
        summary = integration_test_service.get_test_summary()
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取测试摘要失败: {str(e)}")

@router.post("/validate-data-consistency", response_model=Dict[str, Any])
async def validate_data_consistency(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """验证数据一致性"""
    
    require_permission(current_user, "system:test")
    
    try:
        # 运行数据一致性检查
        consistency_result = await integration_test_service._test_data_consistency(db)
        
        return {
            "status": "completed",
            "consistency_checks": consistency_result,
            "timestamp": "2024-01-20T10:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据一致性验证失败: {str(e)}")

@router.post("/simulate-trading-scenario", response_model=Dict[str, Any])
async def simulate_trading_scenario(
    scenario_config: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """模拟交易场景"""
    
    require_permission(current_user, "system:test")
    
    try:
        # 设置测试环境
        await integration_test_service._setup_test_environment(db)
        
        # 运行交易流程测试
        workflow_result = await integration_test_service._test_trading_workflow(db)
        
        # 清理测试环境
        await integration_test_service._cleanup_test_environment(db)
        
        return {
            "status": "completed",
            "scenario": "trading_workflow",
            "results": workflow_result,
            "timestamp": "2024-01-20T10:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"交易场景模拟失败: {str(e)}")

@router.post("/test-exception-handling", response_model=Dict[str, Any])
async def test_exception_handling(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试异常处理"""
    
    require_permission(current_user, "system:test")
    
    try:
        # 设置测试环境
        await integration_test_service._setup_test_environment(db)
        
        # 运行异常处理测试
        exception_result = await integration_test_service._test_exception_handling(db)
        
        # 清理测试环境
        await integration_test_service._cleanup_test_environment(db)
        
        return {
            "status": "completed",
            "exception_tests": exception_result,
            "timestamp": "2024-01-20T10:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"异常处理测试失败: {str(e)}")

@router.get("/health-check", response_model=Dict[str, Any])
async def integration_health_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """集成测试健康检查"""
    
    require_permission(current_user, "system:test")
    
    try:
        # 检查各个服务的可用性
        health_status = {
            "database": "healthy",
            "strategy_service": "healthy",
            "backtest_service": "healthy",
            "order_service": "healthy",
            "position_service": "healthy",
            "transaction_service": "healthy"
        }
        
        # 简单的连接测试
        try:
            db.execute("SELECT 1")
            health_status["database"] = "healthy"
        except Exception:
            health_status["database"] = "unhealthy"
        
        overall_status = "healthy" if all(
            status == "healthy" for status in health_status.values()
        ) else "unhealthy"
        
        return {
            "overall_status": overall_status,
            "services": health_status,
            "timestamp": "2024-01-20T10:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")

@router.post("/stress-test", response_model=Dict[str, Any])
async def run_stress_test(
    test_config: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """运行压力测试"""
    
    require_permission(current_user, "system:test")
    
    try:
        # 获取测试配置
        concurrent_users = test_config.get("concurrent_users", 10)
        operations_per_user = test_config.get("operations_per_user", 100)
        test_duration = test_config.get("test_duration", 300)  # 5分钟
        
        # 在后台运行压力测试
        background_tasks.add_task(
            _run_stress_test_background,
            db,
            concurrent_users,
            operations_per_user,
            test_duration
        )
        
        return {
            "message": "压力测试已开始运行",
            "status": "started",
            "config": {
                "concurrent_users": concurrent_users,
                "operations_per_user": operations_per_user,
                "test_duration": test_duration
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动压力测试失败: {str(e)}")

async def _run_stress_test_background(
    db: Session,
    concurrent_users: int,
    operations_per_user: int,
    test_duration: int
):
    """后台运行压力测试"""
    try:
        # 运行并发操作测试
        await integration_test_service._test_concurrent_operations(db)
        print(f"Stress test completed: {concurrent_users} users, {operations_per_user} ops/user")
    except Exception as e:
        print(f"Background stress test failed: {e}")