"""
系统监控服务
"""
import psutil
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque
import json
import os

from app.services.websocket_optimization_service import websocket_optimization_service
from app.services.query_optimization_service import query_optimization_service

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_available: int
    disk_percent: float
    disk_used: int
    disk_free: int
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    load_average: List[float]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class ApplicationMetrics:
    """应用指标"""
    timestamp: datetime
    active_users: int
    total_requests: int
    avg_response_time: float
    error_rate: float
    database_connections: int
    websocket_connections: int
    cache_hit_rate: float
    queue_size: int
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class SystemMonitoringService:
    """系统监控服务"""
    
    def __init__(self):
        self.system_metrics_history = deque(maxlen=1440)  # 24小时，每分钟一个点
        self.app_metrics_history = deque(maxlen=1440)
        self.alerts = deque(maxlen=100)
        self.monitoring_enabled = True
        self.collection_interval = 60  # 秒
        
        # 阈值配置
        self.thresholds = {
            "cpu_warning": 70.0,
            "cpu_critical": 90.0,
            "memory_warning": 80.0,
            "memory_critical": 95.0,
            "disk_warning": 80.0,
            "disk_critical": 95.0,
            "response_time_warning": 1.0,
            "response_time_critical": 3.0,
            "error_rate_warning": 5.0,
            "error_rate_critical": 10.0
        }
        
        # 请求统计
        self.request_stats = {
            "total_requests": 0,
            "total_response_time": 0.0,
            "total_errors": 0,
            "start_time": time.time()
        }
        
        # 启动监控任务
        asyncio.create_task(self._monitoring_loop())
    
    async def _monitoring_loop(self):
        """监控循环"""
        
        while self.monitoring_enabled:
            try:
                # 收集系统指标
                system_metrics = await self._collect_system_metrics()
                self.system_metrics_history.append(system_metrics)
                
                # 收集应用指标
                app_metrics = await self._collect_application_metrics()
                self.app_metrics_history.append(app_metrics)
                
                # 检查告警
                await self._check_alerts(system_metrics, app_metrics)
                
                # 广播指标到WebSocket客户端
                await self._broadcast_metrics(system_metrics, app_metrics)
                
                # 等待下一次收集
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        
        # 网络统计
        network = psutil.net_io_counters()
        
        # 系统负载
        load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
        
        # 活跃连接数
        active_connections = len(psutil.net_connections())
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used=memory.used,
            memory_available=memory.available,
            disk_percent=disk.percent,
            disk_used=disk.used,
            disk_free=disk.free,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            active_connections=active_connections,
            load_average=list(load_avg)
        )
    
    async def _collect_application_metrics(self) -> ApplicationMetrics:
        """收集应用指标"""
        
        # WebSocket连接数
        ws_metrics = websocket_optimization_service.get_global_metrics()
        websocket_connections = ws_metrics["total_connections"]
        
        # 计算平均响应时间和错误率
        total_requests = self.request_stats["total_requests"]
        avg_response_time = 0.0
        error_rate = 0.0
        
        if total_requests > 0:
            avg_response_time = self.request_stats["total_response_time"] / total_requests
            error_rate = (self.request_stats["total_errors"] / total_requests) * 100
        
        # 数据库连接数（模拟）
        database_connections = 10  # 实际应该从连接池获取
        
        # 缓存命中率（模拟）
        cache_hit_rate = 85.0  # 实际应该从缓存系统获取
        
        # 队列大小（模拟）
        queue_size = 0  # 实际应该从消息队列获取
        
        return ApplicationMetrics(
            timestamp=datetime.now(),
            active_users=len(set(websocket_optimization_service.user_connections.keys())),
            total_requests=total_requests,
            avg_response_time=avg_response_time,
            error_rate=error_rate,
            database_connections=database_connections,
            websocket_connections=websocket_connections,
            cache_hit_rate=cache_hit_rate,
            queue_size=queue_size
        )
    
    async def _check_alerts(
        self, 
        system_metrics: SystemMetrics, 
        app_metrics: ApplicationMetrics
    ):
        """检查告警条件"""
        
        alerts = []
        
        # CPU告警
        if system_metrics.cpu_percent >= self.thresholds["cpu_critical"]:
            alerts.append({
                "type": "critical",
                "category": "system",
                "message": f"CPU使用率过高: {system_metrics.cpu_percent:.1f}%",
                "value": system_metrics.cpu_percent,
                "threshold": self.thresholds["cpu_critical"]
            })
        elif system_metrics.cpu_percent >= self.thresholds["cpu_warning"]:
            alerts.append({
                "type": "warning",
                "category": "system",
                "message": f"CPU使用率较高: {system_metrics.cpu_percent:.1f}%",
                "value": system_metrics.cpu_percent,
                "threshold": self.thresholds["cpu_warning"]
            })
        
        # 内存告警
        if system_metrics.memory_percent >= self.thresholds["memory_critical"]:
            alerts.append({
                "type": "critical",
                "category": "system",
                "message": f"内存使用率过高: {system_metrics.memory_percent:.1f}%",
                "value": system_metrics.memory_percent,
                "threshold": self.thresholds["memory_critical"]
            })
        elif system_metrics.memory_percent >= self.thresholds["memory_warning"]:
            alerts.append({
                "type": "warning",
                "category": "system",
                "message": f"内存使用率较高: {system_metrics.memory_percent:.1f}%",
                "value": system_metrics.memory_percent,
                "threshold": self.thresholds["memory_warning"]
            })
        
        # 磁盘告警
        if system_metrics.disk_percent >= self.thresholds["disk_critical"]:
            alerts.append({
                "type": "critical",
                "category": "system",
                "message": f"磁盘使用率过高: {system_metrics.disk_percent:.1f}%",
                "value": system_metrics.disk_percent,
                "threshold": self.thresholds["disk_critical"]
            })
        elif system_metrics.disk_percent >= self.thresholds["disk_warning"]:
            alerts.append({
                "type": "warning",
                "category": "system",
                "message": f"磁盘使用率较高: {system_metrics.disk_percent:.1f}%",
                "value": system_metrics.disk_percent,
                "threshold": self.thresholds["disk_warning"]
            })
        
        # 响应时间告警
        if app_metrics.avg_response_time >= self.thresholds["response_time_critical"]:
            alerts.append({
                "type": "critical",
                "category": "application",
                "message": f"平均响应时间过长: {app_metrics.avg_response_time:.2f}s",
                "value": app_metrics.avg_response_time,
                "threshold": self.thresholds["response_time_critical"]
            })
        elif app_metrics.avg_response_time >= self.thresholds["response_time_warning"]:
            alerts.append({
                "type": "warning",
                "category": "application",
                "message": f"平均响应时间较长: {app_metrics.avg_response_time:.2f}s",
                "value": app_metrics.avg_response_time,
                "threshold": self.thresholds["response_time_warning"]
            })
        
        # 错误率告警
        if app_metrics.error_rate >= self.thresholds["error_rate_critical"]:
            alerts.append({
                "type": "critical",
                "category": "application",
                "message": f"错误率过高: {app_metrics.error_rate:.1f}%",
                "value": app_metrics.error_rate,
                "threshold": self.thresholds["error_rate_critical"]
            })
        elif app_metrics.error_rate >= self.thresholds["error_rate_warning"]:
            alerts.append({
                "type": "warning",
                "category": "application",
                "message": f"错误率较高: {app_metrics.error_rate:.1f}%",
                "value": app_metrics.error_rate,
                "threshold": self.thresholds["error_rate_warning"]
            })
        
        # 记录告警
        for alert in alerts:
            alert["timestamp"] = datetime.now().isoformat()
            self.alerts.append(alert)
            logger.warning(f"Alert: {alert['message']}")
    
    async def _broadcast_metrics(
        self, 
        system_metrics: SystemMetrics, 
        app_metrics: ApplicationMetrics
    ):
        """广播指标到WebSocket客户端"""
        
        metrics_message = {
            "type": "system_metrics",
            "system": system_metrics.to_dict(),
            "application": app_metrics.to_dict()
        }
        
        await websocket_optimization_service.broadcast_to_topic(
            "system_monitoring",
            metrics_message
        )
    
    def record_request(self, response_time: float, is_error: bool = False):
        """记录请求统计"""
        
        self.request_stats["total_requests"] += 1
        self.request_stats["total_response_time"] += response_time
        
        if is_error:
            self.request_stats["total_errors"] += 1
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        
        if not self.system_metrics_history or not self.app_metrics_history:
            return {}
        
        latest_system = self.system_metrics_history[-1]
        latest_app = self.app_metrics_history[-1]
        
        return {
            "system": latest_system.to_dict(),
            "application": latest_app.to_dict(),
            "websocket": websocket_optimization_service.get_global_metrics()
        }
    
    def get_metrics_history(
        self, 
        hours: int = 1
    ) -> Dict[str, List[Dict[str, Any]]]:
        """获取指标历史"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        system_history = [
            metrics.to_dict() 
            for metrics in self.system_metrics_history
            if metrics.timestamp >= cutoff_time
        ]
        
        app_history = [
            metrics.to_dict()
            for metrics in self.app_metrics_history
            if metrics.timestamp >= cutoff_time
        ]
        
        return {
            "system": system_history,
            "application": app_history
        }
    
    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取告警列表"""
        
        return list(self.alerts)[-limit:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        
        if not self.system_metrics_history or not self.app_metrics_history:
            return {}
        
        # 计算最近1小时的平均值
        recent_system = [
            m for m in self.system_metrics_history
            if (datetime.now() - m.timestamp).total_seconds() <= 3600
        ]
        
        recent_app = [
            m for m in self.app_metrics_history
            if (datetime.now() - m.timestamp).total_seconds() <= 3600
        ]
        
        if not recent_system or not recent_app:
            return {}
        
        avg_cpu = sum(m.cpu_percent for m in recent_system) / len(recent_system)
        avg_memory = sum(m.memory_percent for m in recent_system) / len(recent_system)
        avg_response_time = sum(m.avg_response_time for m in recent_app) / len(recent_app)
        avg_error_rate = sum(m.error_rate for m in recent_app) / len(recent_app)
        
        # 获取WebSocket指标
        ws_metrics = websocket_optimization_service.get_global_metrics()
        
        return {
            "system_health": {
                "avg_cpu_percent": round(avg_cpu, 2),
                "avg_memory_percent": round(avg_memory, 2),
                "current_load": recent_system[-1].load_average[0],
                "status": self._get_system_health_status(avg_cpu, avg_memory)
            },
            "application_performance": {
                "avg_response_time": round(avg_response_time, 3),
                "avg_error_rate": round(avg_error_rate, 2),
                "total_requests": self.request_stats["total_requests"],
                "active_users": recent_app[-1].active_users,
                "status": self._get_app_performance_status(avg_response_time, avg_error_rate)
            },
            "websocket_performance": {
                "total_connections": ws_metrics["total_connections"],
                "total_messages_sent": ws_metrics["total_messages_sent"],
                "avg_latency": round(ws_metrics["avg_latency"], 3),
                "error_rate": ws_metrics["total_errors"] / max(ws_metrics["total_messages_sent"], 1) * 100
            },
            "recent_alerts": len([
                a for a in self.alerts
                if (datetime.now() - datetime.fromisoformat(a["timestamp"])).total_seconds() <= 3600
            ])
        }
    
    def _get_system_health_status(self, avg_cpu: float, avg_memory: float) -> str:
        """获取系统健康状态"""
        
        if avg_cpu >= self.thresholds["cpu_critical"] or avg_memory >= self.thresholds["memory_critical"]:
            return "critical"
        elif avg_cpu >= self.thresholds["cpu_warning"] or avg_memory >= self.thresholds["memory_warning"]:
            return "warning"
        else:
            return "healthy"
    
    def _get_app_performance_status(self, avg_response_time: float, avg_error_rate: float) -> str:
        """获取应用性能状态"""
        
        if (avg_response_time >= self.thresholds["response_time_critical"] or 
            avg_error_rate >= self.thresholds["error_rate_critical"]):
            return "critical"
        elif (avg_response_time >= self.thresholds["response_time_warning"] or 
              avg_error_rate >= self.thresholds["error_rate_warning"]):
            return "warning"
        else:
            return "good"
    
    def update_thresholds(self, new_thresholds: Dict[str, float]):
        """更新告警阈值"""
        
        self.thresholds.update(new_thresholds)
        logger.info(f"Updated monitoring thresholds: {new_thresholds}")
    
    def reset_request_stats(self):
        """重置请求统计"""
        
        self.request_stats = {
            "total_requests": 0,
            "total_response_time": 0.0,
            "total_errors": 0,
            "start_time": time.time()
        }
    
    def stop_monitoring(self):
        """停止监控"""
        
        self.monitoring_enabled = False
        logger.info("System monitoring stopped")

# 创建全局实例
system_monitoring_service = SystemMonitoringService()