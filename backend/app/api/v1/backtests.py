"""
回测管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...models.backtest import BacktestStatus
from ...schemas.backtest import (
    BacktestCreate, BacktestUpdate, BacktestResponse, BacktestListResponse,
    BacktestStatsResponse, BacktestSearchRequest,
    BacktestComparisonRequest, BacktestComparisonResponse
)
from ...services.backtest_service import BacktestService
from ...core.exceptions import ValidationError, NotFoundError
from ...core.response import success_response, error_response

router = APIRouter()


@router.post("/", response_model=BacktestResponse, status_code=status.HTTP_201_CREATED)
async def create_backtest(
    backtest_data: BacktestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建回测"""
    try:
        service = BacktestService(db)
        backtest = service.create_backtest(backtest_data, current_user.id)
        return success_response(data=backtest.to_dict(), message="回测创建成功")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建回测失败")


@router.get("/", response_model=List[BacktestListResponse])
async def search_backtests(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    strategy_id: Optional[int] = Query(None, description="策略ID"),
    backtest_type: Optional[str] = Query(None, description="回测类型"),
    status: Optional[BacktestStatus] = Query(None, description="回测状态"),
    tags: Optional[List[str]] = Query(None, description="标签筛选"),
    is_public: Optional[bool] = Query(None, description="是否公开"),
    start_date_from: Optional[str] = Query(None, description="开始日期起始"),
    start_date_to: Optional[str] = Query(None, description="开始日期结束"),
    created_after: Optional[str] = Query(None, description="创建时间起始"),
    created_before: Optional[str] = Query(None, description="创建时间结束"),
    sort_by: str = Query("updated_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """搜索回测"""
    try:
        # 构建搜索参数
        search_params = BacktestSearchParams(
            keyword=keyword,
            strategy_id=strategy_id,
            backtest_type=backtest_type,
            status=status,
            tags=tags or [],
            is_public=is_public,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size
        )
        
        # 处理日期参数
        if start_date_from:
            from datetime import datetime
            search_params.start_date_from = datetime.fromisoformat(start_date_from)
        if start_date_to:
            from datetime import datetime
            search_params.start_date_to = datetime.fromisoformat(start_date_to)
        if created_after:
            from datetime import datetime
            search_params.created_after = datetime.fromisoformat(created_after)
        if created_before:
            from datetime import datetime
            search_params.created_before = datetime.fromisoformat(created_before)
        
        service = BacktestService(db)
        backtests, total = service.search_backtests(search_params, current_user.id)
        
        return success_response(
            data=[backtest.to_dict() for backtest in backtests],
            message="获取回测列表成功",
            meta={
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取回测列表失败")


@router.get("/stats", response_model=BacktestStatsResponse)
async def get_backtest_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取回测统计信息"""
    try:
        service = BacktestService(db)
        stats = service.get_backtest_stats(current_user.id)
        return success_response(data=stats, message="获取统计信息成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取统计信息失败")


@router.get("/{backtest_id}", response_model=BacktestResponse)
async def get_backtest(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取回测详情"""
    try:
        service = BacktestService(db)
        backtest = service.get_backtest(backtest_id, current_user.id)
        return success_response(data=backtest.to_dict(), message="获取回测详情成功")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取回测详情失败")


@router.get("/uuid/{backtest_uuid}", response_model=BacktestResponse)
async def get_backtest_by_uuid(
    backtest_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """通过UUID获取回测详情"""
    try:
        service = BacktestService(db)
        backtest = service.get_backtest_by_uuid(backtest_uuid, current_user.id)
        return success_response(data=backtest.to_dict(), message="获取回测详情成功")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取回测详情失败")


@router.put("/{backtest_id}", response_model=BacktestResponse)
async def update_backtest(
    backtest_id: int,
    backtest_data: BacktestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新回测"""
    try:
        service = BacktestService(db)
        backtest = service.update_backtest(backtest_id, backtest_data, current_user.id)
        return success_response(data=backtest.to_dict(), message="回测更新成功")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新回测失败")


@router.delete("/{backtest_id}")
async def delete_backtest(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除回测"""
    try:
        service = BacktestService(db)
        service.delete_backtest(backtest_id, current_user.id)
        return success_response(message="回测删除成功")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="删除回测失败")


@router.post("/{backtest_id}/execute")
async def execute_backtest(
    backtest_id: int,
    execution_request: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行回测操作"""
    try:
        service = BacktestService(db)
        backtest = service.get_backtest(backtest_id, current_user.id)
        
        if not backtest:
            raise NotFoundError("回测不存在或无权限访问")
        
        # 验证操作权限
        if backtest.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限执行此操作")
        
        # 根据动作执行相应操作
        if execution_request.action == "start":
            if backtest.status != BacktestStatus.PENDING:
                raise ValidationError("只能启动待执行状态的回测")
            
            # 更新状态为运行中
            service.update_backtest_status(backtest_id, BacktestStatus.RUNNING, 0.0)
            
            # 添加后台任务执行回测
            # background_tasks.add_task(run_backtest_task, backtest_id)
            
            return success_response(
                data={
                    "backtest_id": backtest_id,
                    "action": "start",
                    "success": True,
                    "message": "回测已开始执行",
                    "execution_id": f"exec_{backtest_id}_{int(datetime.now().timestamp())}",
                    "timestamp": datetime.now()
                },
                message="回测启动成功"
            )
        
        elif execution_request.action == "stop":
            if backtest.status != BacktestStatus.RUNNING:
                raise ValidationError("只能停止运行中的回测")
            
            service.update_backtest_status(backtest_id, BacktestStatus.CANCELLED)
            
            return success_response(
                data={
                    "backtest_id": backtest_id,
                    "action": "stop",
                    "success": True,
                    "message": "回测已停止",
                    "timestamp": datetime.now()
                },
                message="回测停止成功"
            )
        
        elif execution_request.action == "pause":
            if backtest.status != BacktestStatus.RUNNING:
                raise ValidationError("只能暂停运行中的回测")
            
            service.update_backtest_status(backtest_id, BacktestStatus.PAUSED)
            
            return success_response(
                data={
                    "backtest_id": backtest_id,
                    "action": "pause",
                    "success": True,
                    "message": "回测已暂停",
                    "timestamp": datetime.now()
                },
                message="回测暂停成功"
            )
        
        elif execution_request.action == "resume":
            if backtest.status != BacktestStatus.PAUSED:
                raise ValidationError("只能恢复暂停状态的回测")
            
            service.update_backtest_status(backtest_id, BacktestStatus.RUNNING)
            
            return success_response(
                data={
                    "backtest_id": backtest_id,
                    "action": "resume",
                    "success": True,
                    "message": "回测已恢复",
                    "timestamp": datetime.now()
                },
                message="回测恢复成功"
            )
        
        else:
            raise ValidationError("不支持的执行动作")
            
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="执行回测操作失败")


# 回测模板相关路由
@router.get("/templates/")
async def get_backtest_templates(
    category: Optional[str] = Query(None, description="模板分类"),
    is_official: Optional[bool] = Query(None, description="是否官方模板"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取回测模板列表"""
    try:
        service = BacktestTemplateService(db)
        templates = service.get_templates(category, is_official)
        return success_response(
            data=[template.to_dict() for template in templates],
            message="获取模板列表成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取模板列表失败")


@router.post("/templates/", status_code=status.HTTP_201_CREATED)
async def create_backtest_template(
    template_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建回测模板"""
    try:
        service = BacktestTemplateService(db)
        template = service.create_template(template_data, current_user.id)
        return success_response(data=template.to_dict(), message="模板创建成功")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建模板失败")


@router.get("/templates/{template_id}")
async def get_backtest_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取回测模板详情"""
    try:
        service = BacktestTemplateService(db)
        template = service.get_template(template_id)
        return success_response(data=template.to_dict(), message="获取模板详情成功")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取模板详情失败")


# 回测比较相关路由
@router.post("/comparisons/", status_code=status.HTTP_201_CREATED)
async def create_backtest_comparison(
    comparison_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建回测比较"""
    try:
        service = BacktestComparisonService(db)
        comparison = service.create_comparison(comparison_data, current_user.id)
        return success_response(data=comparison.to_dict(), message="比较创建成功")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建比较失败")


@router.get("/my", response_model=List[BacktestListResponse])
async def get_my_backtests(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取我的回测列表"""
    try:
        service = BacktestService(db)
        backtests = service.get_user_backtests(current_user.id, limit)
        return success_response(
            data=[backtest.to_dict() for backtest in backtests],
            message="获取我的回测列表成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取回测列表失败")
# 任务管理相关路由
@router.post("/{backtest_id}/tasks", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_backtest_task(
    backtest_id: int,
    task_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建回测任务"""
    try:
        from ...services.backtest_task_service import get_task_service, TaskPriority
        
        task_service = get_task_service(db)
        priority = TaskPriority(task_data.get('priority', 2))  # 默认普通优先级
        
        task = task_service.create_task(backtest_id, current_user.id, priority)
        
        return success_response(data=task.to_dict(), message="回测任务创建成功")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建回测任务失败")


@router.get("/tasks/{task_id}", response_model=dict)
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务状态"""
    try:
        from ...services.backtest_task_service import get_task_service
        
        task_service = get_task_service(db)
        task = task_service.get_task_status(task_id, current_user.id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
        
        return success_response(data=task.to_dict(), message="获取任务状态成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取任务状态失败")


@router.post("/tasks/{task_id}/control", response_model=dict)
async def control_task(
    task_id: str,
    control_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """控制任务执行"""
    try:
        from ...services.backtest_task_service import get_task_service, TaskAction
        
        action_str = control_data.get('action')
        if not action_str:
            raise HTTPException(status_code=400, detail="缺少操作参数")
        
        try:
            action = TaskAction(action_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的操作类型")
        
        task_service = get_task_service(db)
        success = task_service.control_task(task_id, action, current_user.id)
        
        if success:
            return success_response(message=f"任务{action_str}操作成功")
        else:
            return error_response(message=f"任务{action_str}操作失败")
            
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="控制任务失败")


@router.get("/tasks", response_model=dict)
async def get_user_tasks(
    status: Optional[str] = Query(None, description="任务状态筛选"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户任务列表"""
    try:
        from ...services.backtest_task_service import get_task_service
        from ...models.backtest import BacktestStatus
        
        task_service = get_task_service(db)
        
        # 状态过滤
        status_filter = None
        if status:
            try:
                status_filter = BacktestStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的状态参数")
        
        tasks = task_service.get_user_tasks(current_user.id, status_filter, limit)
        
        return success_response(
            data=[task.to_dict() for task in tasks],
            message="获取任务列表成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取任务列表失败")


@router.get("/queue/statistics", response_model=dict)
async def get_queue_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取队列统计信息"""
    try:
        from ...services.backtest_task_service import get_task_service
        
        task_service = get_task_service(db)
        stats = task_service.get_queue_statistics()
        
        return success_response(data=stats, message="获取队列统计成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取队列统计失败")


@router.get("/tasks/history", response_model=dict)
async def get_task_history(
    days: int = Query(30, ge=1, le=365, description="历史天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务历史记录"""
    try:
        from ...services.backtest_task_service import get_task_service
        
        task_service = get_task_service(db)
        history = task_service.get_task_history(current_user.id, days)
        
        return success_response(data=history, message="获取任务历史成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取任务历史失败")


@router.post("/compare", response_model=dict)
async def compare_backtests(
    comparison_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """比较回测结果"""
    try:
        from ...services.backtest_task_service import get_task_service
        
        backtest_ids = comparison_data.get('backtest_ids', [])
        if len(backtest_ids) < 2:
            raise HTTPException(status_code=400, detail="至少需要2个回测进行比较")
        
        task_service = get_task_service(db)
        comparison_result = task_service.compare_backtest_results(backtest_ids, current_user.id)
        
        return success_response(data=comparison_result, message="回测比较完成")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="回测比较失败")


# WebSocket路由
from fastapi import WebSocket, WebSocketDisconnect
from ...core.websocket import websocket_manager, websocket_handler

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket连接端点"""
    await websocket_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket_handler.handle_message(websocket, data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket连接异常: {str(e)}")
        websocket_manager.disconnect(websocket)