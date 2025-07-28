"""
监控系统API
提供系统监控数据查询和管理接口
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.core.dependencies import get_db, get_current_user
from app.core.response import success_response, error_response
from app.models.user import User
from app.models.system import SystemMetrics, HealthCheck, AlertRule, AlertHistory
from app.schemas.monitoring import (
    SystemMetricsResponse,
    HealthCheckResponse,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleResponse,
    SystemStatusResponse,
    MetricsQueryParams,
    AlertHistoryResponse
)
from app.services.monitoring_service import monitoring_service

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    current_user: User = Depends(get_current_user)
):
    """获取系统状态概览"""
    try:
        status = await monitoring_service.get_system_status()
        return success_response(data=status)
    except Exception as e:
        return error_response(message=f"获取系统状态失败: {str(e)}")


@router.get("/metrics", response_model=List[SystemMetricsResponse])
async def get_system_metrics(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取系统性能指标"""
    try:
        query = db.query(SystemMetrics)
        
        # 时间范围过滤
        if start_time:
            query = query.filter(SystemMetrics.timestamp >= start_time)
        if end_time:
            query = query.filter(SystemMetrics.timestamp <= end_time)
        else:
            # 默认查询最近24小时
            query = query.filter(
                SystemMetrics.timestamp >= datetime.utcnow() - timedelta(hours=24)
            )
        
        metrics = query.order_by(desc(SystemMetrics.timestamp)).limit(limit).all()
        
        return success_response(data=metrics)
    except Exception as e:
        return error_response(message=f"获取系统指标失败: {str(e)}")


@router.get("/metrics/latest", response_model=SystemMetricsResponse)
async def get_latest_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取最新的系统指标"""
    try:
        latest_metrics = db.query(SystemMetrics).order_by(
            desc(SystemMetrics.timestamp)
        ).first()
        
        if not latest_metrics:
            raise HTTPException(status_code=404, detail="没有找到系统指标数据")
        
        return success_response(data=latest_metrics)
    except Exception as e:
        return error_response(message=f"获取最新指标失败: {str(e)}")


@router.get("/metrics/aggregated")
async def get_aggregated_metrics(
    metric_name: str = Query(..., description="指标名称"),
    aggregation: str = Query("avg", description="聚合方式: avg, max, min, sum"),
    interval: str = Query("1h", description="时间间隔: 1m, 5m, 1h, 1d"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_user)
):
    """获取聚合后的指标数据"""
    try:
        # 这里应该使用InfluxDB查询聚合数据
        # 由于示例中没有完整的InfluxDB集成，这里返回模拟数据
        
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        # 模拟聚合数据
        data_points = []
        current_time = start_time
        
        while current_time <= end_time:
            data_points.append({
                'timestamp': current_time.isoformat(),
                'value': 50 + (hash(str(current_time)) % 40)  # 模拟数据
            })
            
            # 根据间隔增加时间
            if interval == '1m':
                current_time += timedelta(minutes=1)
            elif interval == '5m':
                current_time += timedelta(minutes=5)
            elif interval == '1h':
                current_time += timedelta(hours=1)
            elif interval == '1d':
                current_time += timedelta(days=1)
            else:
                current_time += timedelta(hours=1)
        
        return success_response(data={
            'metric_name': metric_name,
            'aggregation': aggregation,
            'interval': interval,
            'data_points': data_points[-100:]  # 限制返回数量
        })
    except Exception as e:
        return error_response(message=f"获取聚合指标失败: {str(e)}")


@router.get("/health", response_model=List[HealthCheckResponse])
async def get_health_checks(
    check_name: Optional[str] = Query(None, description="检查名称"),
    status: Optional[str] = Query(None, description="状态过滤"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取健康检查结果"""
    try:
        query = db.query(HealthCheck)
        
        # 过滤条件
        if check_name:
            query = query.filter(HealthCheck.check_name == check_name)
        if status:
            query = query.filter(HealthCheck.status == status)
        if start_time:
            query = query.filter(HealthCheck.timestamp >= start_time)
        if end_time:
            query = query.filter(HealthCheck.timestamp <= end_time)
        else:
            # 默认查询最近1小时
            query = query.filter(
                HealthCheck.timestamp >= datetime.utcnow() - timedelta(hours=1)
            )
        
        health_checks = query.order_by(desc(HealthCheck.timestamp)).limit(limit).all()
        
        return success_response(data=health_checks)
    except Exception as e:
        return error_response(message=f"获取健康检查结果失败: {str(e)}")


@router.get("/health/summary")
async def get_health_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取健康检查摘要"""
    try:
        # 获取最近5分钟的健康检查结果
        recent_time = datetime.utcnow() - timedelta(minutes=5)
        
        health_checks = db.query(HealthCheck).filter(
            HealthCheck.timestamp >= recent_time
        ).all()
        
        # 按检查名称分组统计
        summary = {}
        for check in health_checks:
            if check.check_name not in summary:
                summary[check.check_name] = {
                    'check_name': check.check_name,
                    'latest_status': check.status,
                    'latest_timestamp': check.timestamp,
                    'latest_message': check.message,
                    'response_time': check.response_time,
                    'value': check.value
                }
            else:
                # 保留最新的检查结果
                if check.timestamp > summary[check.check_name]['latest_timestamp']:
                    summary[check.check_name].update({
                        'latest_status': check.status,
                        'latest_timestamp': check.timestamp,
                        'latest_message': check.message,
                        'response_time': check.response_time,
                        'value': check.value
                    })
        
        # 统计各状态数量
        status_counts = {'healthy': 0, 'warning': 0, 'critical': 0}
        for item in summary.values():
            status = item['latest_status']
            if status in status_counts:
                status_counts[status] += 1
        
        return success_response(data={
            'summary': list(summary.values()),
            'status_counts': status_counts,
            'total_checks': len(summary),
            'last_update': max([item['latest_timestamp'] for item in summary.values()]) if summary else None
        })
    except Exception as e:
        return error_response(message=f"获取健康检查摘要失败: {str(e)}")


@router.get("/alerts/rules", response_model=List[AlertRuleResponse])
async def get_alert_rules(
    enabled: Optional[bool] = Query(None, description="是否启用"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取告警规则列表"""
    try:
        query = db.query(AlertRule)
        
        if enabled is not None:
            query = query.filter(AlertRule.enabled == enabled)
        
        rules = query.order_by(AlertRule.created_at).all()
        
        return success_response(data=rules)
    except Exception as e:
        return error_response(message=f"获取告警规则失败: {str(e)}")


@router.post("/alerts/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建告警规则"""
    try:
        # 检查规则名称是否已存在
        existing_rule = db.query(AlertRule).filter(
            AlertRule.name == rule_data.name
        ).first()
        
        if existing_rule:
            raise HTTPException(status_code=400, detail="告警规则名称已存在")
        
        # 创建新规则
        alert_rule = AlertRule(
            name=rule_data.name,
            description=rule_data.description,
            metric_name=rule_data.metric_name,
            operator=rule_data.operator,
            threshold=rule_data.threshold,
            severity=rule_data.severity,
            enabled=rule_data.enabled,
            notification_channels=rule_data.notification_channels,
            silence_duration=rule_data.silence_duration,
            created_by=current_user.id,
            created_at=datetime.utcnow()
        )
        
        db.add(alert_rule)
        db.commit()
        db.refresh(alert_rule)
        
        return success_response(data=alert_rule, message="告警规则创建成功")
    except Exception as e:
        db.rollback()
        return error_response(message=f"创建告警规则失败: {str(e)}")


@router.put("/alerts/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: int,
    rule_data: AlertRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新告警规则"""
    try:
        alert_rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        
        if not alert_rule:
            raise HTTPException(status_code=404, detail="告警规则不存在")
        
        # 更新字段
        update_data = rule_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(alert_rule, field, value)
        
        alert_rule.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(alert_rule)
        
        return success_response(data=alert_rule, message="告警规则更新成功")
    except Exception as e:
        db.rollback()
        return error_response(message=f"更新告警规则失败: {str(e)}")


@router.delete("/alerts/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除告警规则"""
    try:
        alert_rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        
        if not alert_rule:
            raise HTTPException(status_code=404, detail="告警规则不存在")
        
        db.delete(alert_rule)
        db.commit()
        
        return success_response(message="告警规则删除成功")
    except Exception as e:
        db.rollback()
        return error_response(message=f"删除告警规则失败: {str(e)}")


@router.get("/alerts/history", response_model=List[AlertHistoryResponse])
async def get_alert_history(
    rule_id: Optional[int] = Query(None, description="规则ID"),
    severity: Optional[str] = Query(None, description="严重程度"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取告警历史"""
    try:
        from app.models.system import AlertHistory
        
        query = db.query(AlertHistory)
        
        # 过滤条件
        if rule_id:
            query = query.filter(AlertHistory.rule_id == rule_id)
        if severity:
            query = query.filter(AlertHistory.severity == severity)
        if start_time:
            query = query.filter(AlertHistory.created_at >= start_time)
        if end_time:
            query = query.filter(AlertHistory.created_at <= end_time)
        else:
            # 默认查询最近7天
            query = query.filter(
                AlertHistory.created_at >= datetime.utcnow() - timedelta(days=7)
            )
        
        alerts = query.order_by(desc(AlertHistory.created_at)).limit(limit).all()
        
        return success_response(data=alerts)
    except Exception as e:
        return error_response(message=f"获取告警历史失败: {str(e)}")


@router.post("/start")
async def start_monitoring(
    current_user: User = Depends(get_current_user)
):
    """启动监控服务"""
    try:
        if monitoring_service.is_running:
            return success_response(message="监控服务已在运行")
        
        # 在后台启动监控服务
        import asyncio
        asyncio.create_task(monitoring_service.start_monitoring())
        
        return success_response(message="监控服务启动成功")
    except Exception as e:
        return error_response(message=f"启动监控服务失败: {str(e)}")


@router.post("/stop")
async def stop_monitoring(
    current_user: User = Depends(get_current_user)
):
    """停止监控服务"""
    try:
        await monitoring_service.stop_monitoring()
        return success_response(message="监控服务停止成功")
    except Exception as e:
        return error_response(message=f"停止监控服务失败: {str(e)}")


@router.get("/dashboard")
async def get_monitoring_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取监控仪表板数据"""
    try:
        # 获取系统状态
        system_status = await monitoring_service.get_system_status()
        
        # 获取最近的指标数据
        recent_metrics = db.query(SystemMetrics).filter(
            SystemMetrics.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ).order_by(SystemMetrics.timestamp).all()
        
        # 获取健康检查摘要
        health_summary_response = await get_health_summary(db, current_user)
        health_summary = health_summary_response.get('data', {})
        
        # 获取最近的告警
        from app.models.system import AlertHistory
        recent_alerts = db.query(AlertHistory).filter(
            AlertHistory.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).order_by(desc(AlertHistory.created_at)).limit(10).all()
        
        # 构建仪表板数据
        dashboard_data = {
            'system_status': system_status,
            'metrics_trend': [
                {
                    'timestamp': metric.timestamp.isoformat(),
                    'cpu_percent': metric.cpu_percent,
                    'memory_percent': metric.memory_percent,
                    'disk_percent': metric.disk_percent,
                    'db_active_connections': metric.db_active_connections
                }
                for metric in recent_metrics
            ],
            'health_summary': health_summary,
            'recent_alerts': [
                {
                    'id': alert.id,
                    'rule_id': alert.rule_id,
                    'severity': alert.severity,
                    'message': alert.message,
                    'created_at': alert.created_at.isoformat()
                }
                for alert in recent_alerts
            ],
            'statistics': {
                'total_metrics_collected': len(recent_metrics),
                'active_alert_rules': db.query(AlertRule).filter(AlertRule.enabled == True).count(),
                'alerts_last_24h': len(recent_alerts),
                'system_uptime': system_status.get('monitoring_status') == 'running'
            }
        }
        
        return success_response(data=dashboard_data)
    except Exception as e:
        return error_response(message=f"获取监控仪表板数据失败: {str(e)}")


@router.get("/export/metrics")
async def export_metrics(
    format: str = Query("csv", description="导出格式: csv, json"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出监控数据"""
    try:
        from fastapi.responses import StreamingResponse
        import csv
        import json
        from io import StringIO
        
        query = db.query(SystemMetrics)
        
        if start_time:
            query = query.filter(SystemMetrics.timestamp >= start_time)
        if end_time:
            query = query.filter(SystemMetrics.timestamp <= end_time)
        else:
            # 默认导出最近7天
            query = query.filter(
                SystemMetrics.timestamp >= datetime.utcnow() - timedelta(days=7)
            )
        
        metrics = query.order_by(SystemMetrics.timestamp).all()
        
        if format.lower() == 'csv':
            output = StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            writer.writerow([
                'timestamp', 'cpu_percent', 'memory_percent', 'disk_percent',
                'network_bytes_sent', 'network_bytes_recv', 'db_active_connections',
                'db_cache_hit_ratio', 'app_user_count', 'app_running_strategies'
            ])
            
            # 写入数据
            for metric in metrics:
                writer.writerow([
                    metric.timestamp.isoformat(),
                    metric.cpu_percent,
                    metric.memory_percent,
                    metric.disk_percent,
                    metric.network_bytes_sent,
                    metric.network_bytes_recv,
                    metric.db_active_connections,
                    metric.db_cache_hit_ratio,
                    metric.app_user_count,
                    metric.app_running_strategies
                ])
            
            output.seek(0)
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=metrics.csv"}
            )
        
        elif format.lower() == 'json':
            data = []
            for metric in metrics:
                data.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'cpu_percent': metric.cpu_percent,
                    'memory_percent': metric.memory_percent,
                    'disk_percent': metric.disk_percent,
                    'network_bytes_sent': metric.network_bytes_sent,
                    'network_bytes_recv': metric.network_bytes_recv,
                    'db_active_connections': metric.db_active_connections,
                    'db_cache_hit_ratio': metric.db_cache_hit_ratio,
                    'app_user_count': metric.app_user_count,
                    'app_running_strategies': metric.app_running_strategies
                })
            
            json_data = json.dumps(data, indent=2, ensure_ascii=False)
            
            return StreamingResponse(
                iter([json_data]),
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=metrics.json"}
            )
        
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
            
    except Exception as e:
        return error_response(message=f"导出监控数据失败: {str(e)}")