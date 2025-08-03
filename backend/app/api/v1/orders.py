"""
订单管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...models.order import OrderStatus, OrderType, OrderSide
from ...schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse, OrderListResponse,
    OrderSearchParams, OrderStatsResponse, OrderActionRequest, OrderActionResponse,
    OrderTemplateCreate, OrderTemplateUpdate, OrderTemplateResponse,
    OrderRiskCheckRequest, OrderRiskCheckResponse, OrderExecutionReport
)
from ...services.order_service import OrderService, OrderTemplateService
from ...services.order_execution_simulator import order_execution_simulator
from ...services.order_execution_service import order_execution_service
from ...core.exceptions import ValidationError, NotFoundError
from ...core.response import success_response, error_response

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建订单"""
    try:
        service = OrderService(db)
        order = service.create_order(order_data, current_user.id)
        return success_response(data=order.to_dict(), message="订单创建成功")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建订单失败")


@router.get("/", response_model=List[OrderListResponse])
async def search_orders(
    symbol: Optional[str] = Query(None, description="交易标的"),
    order_type: Optional[OrderType] = Query(None, description="订单类型"),
    side: Optional[OrderSide] = Query(None, description="订单方向"),
    status: Optional[OrderStatus] = Query(None, description="订单状态"),
    strategy_id: Optional[int] = Query(None, description="策略ID"),
    backtest_id: Optional[int] = Query(None, description="回测ID"),
    tags: Optional[List[str]] = Query(None, description="标签筛选"),
    created_after: Optional[str] = Query(None, description="创建时间起始"),
    created_before: Optional[str] = Query(None, description="创建时间结束"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """搜索订单"""
    try:
        # 构建搜索参数
        search_params = OrderSearchParams(
            symbol=symbol,
            order_type=order_type,
            side=side,
            status=status,
            strategy_id=strategy_id,
            backtest_id=backtest_id,
            tags=tags or [],
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size
        )
        
        # 处理日期参数
        if created_after:
            from datetime import datetime
            search_params.created_after = datetime.fromisoformat(created_after)
        if created_before:
            from datetime import datetime
            search_params.created_before = datetime.fromisoformat(created_before)
        
        service = OrderService(db)
        orders, total = service.search_orders(search_params, current_user.id)
        
        return success_response(
            data=[order.to_dict() for order in orders],
            message="获取订单列表成功",
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
        raise HTTPException(status_code=500, detail="获取订单列表失败")


@router.get("/stats", response_model=OrderStatsResponse)
async def get_order_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取订单统计信息"""
    try:
        service = OrderService(db)
        stats = service.get_order_stats(current_user.id)
        return success_response(data=stats, message="获取统计信息成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取统计信息失败")


@router.get("/active", response_model=List[OrderListResponse])
async def get_active_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取活跃订单"""
    try:
        service = OrderService(db)
        orders = service.get_active_orders(current_user.id)
        return success_response(
            data=[order.to_dict() for order in orders],
            message="获取活跃订单成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取活跃订单失败")


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取订单详情"""
    try:
        service = OrderService(db)
        order = service.get_order(order_id, current_user.id)
        return success_response(data=order.to_dict(), message="获取订单详情成功")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取订单详情失败")


@router.get("/uuid/{order_uuid}", response_model=OrderResponse)
async def get_order_by_uuid(
    order_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """通过UUID获取订单详情"""
    try:
        service = OrderService(db)
        order = service.get_order_by_uuid(order_uuid, current_user.id)
        return success_response(data=order.to_dict(), message="获取订单详情成功")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取订单详情失败")


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新订单"""
    try:
        service = OrderService(db)
        order = service.update_order(order_id, order_data, current_user.id)
        return success_response(data=order.to_dict(), message="订单更新成功")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="更新订单失败")


@router.delete("/{order_id}")
async def cancel_order(
    order_id: int,
    reason: Optional[str] = Query(None, description="取消原因"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消订单"""
    try:
        service = OrderService(db)
        order = service.cancel_order(order_id, current_user.id, reason or "")
        return success_response(data=order.to_dict(), message="订单取消成功")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="取消订单失败")


@router.post("/{order_id}/action", response_model=OrderActionResponse)
async def perform_order_action(
    order_id: int,
    action_request: OrderActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行订单操作"""
    try:
        service = OrderService(db)
        
        if action_request.action == "cancel":
            reason = action_request.parameters.get('reason', '') if action_request.parameters else ''
            order = service.cancel_order(order_id, current_user.id, reason)
            
            return success_response(
                data={
                    "order_id": order_id,
                    "action": "cancel",
                    "success": True,
                    "message": "订单取消成功",
                    "timestamp": datetime.now()
                },
                message="订单操作成功"
            )
        
        elif action_request.action == "modify":
            if not action_request.parameters:
                raise ValidationError("修改订单需要提供参数")
            
            # 构建更新数据
            update_data = OrderUpdate(**action_request.parameters)
            order = service.update_order(order_id, update_data, current_user.id)
            
            return success_response(
                data={
                    "order_id": order_id,
                    "action": "modify",
                    "success": True,
                    "message": "订单修改成功",
                    "timestamp": datetime.now()
                },
                message="订单操作成功"
            )
        
        else:
            raise ValidationError(f"不支持的操作: {action_request.action}")
            
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="执行订单操作失败")


@router.post("/batch/cancel")
async def batch_cancel_orders(
    order_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量取消订单"""
    try:
        service = OrderService(db)
        results = service.batch_cancel_orders(order_ids, current_user.id)
        return success_response(data=results, message="批量取消订单完成")
    except Exception as e:
        raise HTTPException(status_code=500, detail="批量取消订单失败")


@router.post("/risk-check", response_model=OrderRiskCheckResponse)
async def check_order_risk(
    risk_data: OrderRiskCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """订单风险检查"""
    try:
        service = OrderService(db)
        risk_result = service.perform_risk_check(risk_data, current_user.id)
        return success_response(data=risk_result, message="风险检查完成")
    except Exception as e:
        raise HTTPException(status_code=500, detail="风险检查失败")


@router.post("/{order_id}/fills")
async def add_order_fill(
    order_id: int,
    fill_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加订单成交记录"""
    try:
        service = OrderService(db)
        
        # 验证订单权限
        order = service.get_order(order_id, current_user.id)
        
        fill = service.add_order_fill(order_id, fill_data)
        return success_response(data=fill.to_dict(), message="成交记录添加成功")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="添加成交记录失败")


@router.get("/{order_id}/fills")
async def get_order_fills(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取订单成交记录"""
    try:
        service = OrderService(db)
        
        # 验证订单权限
        order = service.get_order(order_id, current_user.id)
        
        fills = [fill.to_dict() for fill in order.fills]
        return success_response(data=fills, message="获取成交记录成功")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取成交记录失败")


# 订单模板相关路由
@router.get("/templates/", response_model=List[OrderTemplateResponse])
async def get_order_templates(
    category: Optional[str] = Query(None, description="模板分类"),
    is_official: Optional[bool] = Query(None, description="是否官方模板"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取订单模板列表"""
    try:
        service = OrderTemplateService(db)
        templates = service.get_templates(category, is_official)
        return success_response(
            data=[template.to_dict() for template in templates],
            message="获取模板列表成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取模板列表失败")


@router.post("/templates/", response_model=OrderTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_order_template(
    template_data: OrderTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建订单模板"""
    try:
        service = OrderTemplateService(db)
        template = service.create_template(template_data, current_user.id)
        return success_response(data=template.to_dict(), message="模板创建成功")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建模板失败")


@router.get("/templates/{template_id}", response_model=OrderTemplateResponse)
async def get_order_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取订单模板详情"""
    try:
        service = OrderTemplateService(db)
        template = service.get_template(template_id)
        return success_response(data=template.to_dict(), message="获取模板详情成功")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取模板详情失败")


@router.get("/my", response_model=List[OrderListResponse])
async def get_my_orders(
    status: Optional[OrderStatus] = Query(None, description="订单状态"),
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取我的订单列表"""
    try:
        service = OrderService(db)
        orders = service.get_user_orders(current_user.id, status, limit)
        return success_response(
            data=[order.to_dict() for order in orders],
            message="获取我的订单列表成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取订单列表失败")


@router.post("/{order_id}/simulate")
async def start_order_simulation(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """启动订单执行模拟"""
    try:
        service = OrderService(db)
        order = service.get_order(order_id, current_user.id)
        
        if not order.is_active:
            raise ValidationError("只能模拟活跃状态的订单")
        
        # 启动模拟
        await order_execution_simulator.start_order_simulation(order_id)
        
        return success_response(
            data={"order_id": order_id, "simulation_started": True},
            message="订单执行模拟已启动"
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="启动模拟失败")


@router.delete("/{order_id}/simulate")
async def stop_order_simulation(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """停止订单执行模拟"""
    try:
        service = OrderService(db)
        order = service.get_order(order_id, current_user.id)
        
        # 停止模拟
        await order_execution_simulator.stop_order_simulation(order_id)
        
        return success_response(
            data={"order_id": order_id, "simulation_stopped": True},
            message="订单执行模拟已停止"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="停止模拟失败")


@router.get("/simulator/status")
async def get_simulator_status(
    current_user: User = Depends(get_current_user)
):
    """获取模拟器状态"""
    try:
        status = order_execution_simulator.get_simulation_status()
        return success_response(data=status, message="获取模拟器状态成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取模拟器状态失败")


@router.post("/{order_id}/execute")
async def execute_order(
    order_id: int,
    trading_system: Optional[str] = Query(None, description="交易系统类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行订单"""
    try:
        service = OrderService(db)
        order = service.get_order(order_id, current_user.id)
        
        if not order.is_active:
            raise ValidationError("只能执行活跃状态的订单")
        
        # 提交订单执行
        result = await order_execution_service.submit_order_for_execution(
            order, trading_system
        )
        
        return success_response(
            data={
                "order_id": order_id,
                "execution_result": result.value,
                "message": "订单执行请求已提交"
            },
            message="订单执行成功"
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="执行订单失败")


@router.get("/{order_id}/execution-status")
async def get_order_execution_status(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取订单执行状态"""
    try:
        service = OrderService(db)
        order = service.get_order(order_id, current_user.id)
        
        # 获取执行状态
        execution_status = await order_execution_service.get_order_execution_status(order)
        
        return success_response(
            data=execution_status,
            message="获取订单执行状态成功"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取订单执行状态失败")


@router.get("/execution/service-status")
async def get_execution_service_status(
    current_user: User = Depends(get_current_user)
):
    """获取订单执行服务状态"""
    try:
        status = order_execution_service.get_service_status()
        return success_response(data=status, message="获取执行服务状态成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取执行服务状态失败")


@router.get("/execution/statistics")
async def get_execution_statistics(
    current_user: User = Depends(get_current_user)
):
    """获取订单执行统计"""
    try:
        stats = order_execution_service.get_execution_statistics()
        return success_response(data=stats, message="获取执行统计成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取执行统计失败")


@router.post("/execution/start-service")
async def start_execution_service(
    current_user: User = Depends(get_current_user)
):
    """启动订单执行服务"""
    try:
        await order_execution_service.start_service()
        return success_response(
            data={"service_started": True},
            message="订单执行服务启动成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="启动执行服务失败")


@router.post("/execution/stop-service")
async def stop_execution_service(
    current_user: User = Depends(get_current_user)
):
    """停止订单执行服务"""
    try:
        await order_execution_service.stop_service()
        return success_response(
            data={"service_stopped": True},
            message="订单执行服务停止成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="停止执行服务失败")