"""
实时算法交易引擎 - 基于 tqsdk 的自动化交易系统
"""
import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import uuid

from .simple_trading_service import simple_trading_service
from .market_data_service import market_data_service
from .technical_analysis_service import technical_analysis_service
# Mock risk monitoring service for now
class MockRiskMonitoringService:
    async def calculate_real_time_risk_metrics(self, user_id: str = "default"):
        return {
            "overall_risk_score": 25,
            "account_metrics": {
                "margin_ratio": 0.05,
                "profit_ratio": 0.0025
            },
            "risk_alerts": []
        }

risk_monitoring_service = MockRiskMonitoringService()
# Mock strategy management service for now
class MockStrategyManagementService:
    async def initialize(self):
        return True
    
    @property
    def is_initialized(self):
        return True

strategy_management_service = MockStrategyManagementService()
from ..core.database import get_redis_client

logger = logging.getLogger(__name__)


class EngineStatus(Enum):
    """交易引擎状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class SignalType(Enum):
    """交易信号类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"


class AlgoTradingEngine:
    """实时算法交易引擎"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self.status = EngineStatus.STOPPED
        self.is_initialized = False
        
        # 运行时状态
        self.active_strategies = {}  # 活跃策略实例
        self.pending_orders = {}     # 待处理订单
        self.position_tracker = {}   # 持仓跟踪
        self.signal_history = []     # 信号历史
        
        # 配置参数
        self.config = {
            "max_concurrent_strategies": 10,
            "order_timeout": 300,  # 订单超时时间(秒)
            "risk_check_interval": 30,  # 风险检查间隔(秒)
            "signal_check_interval": 5,  # 信号检查间隔(秒)
            "max_daily_trades": 100,  # 每日最大交易次数
            "emergency_stop_loss": 0.05,  # 紧急止损比例
        }
        
        # 异步任务
        self._running_tasks = []
        self._stop_event = asyncio.Event()
    
    async def initialize(self):
        """初始化交易引擎"""
        try:
            # 确保依赖服务已初始化
            services = [
                simple_trading_service,
                market_data_service,
                technical_analysis_service,
                risk_monitoring_service,
                strategy_management_service
            ]
            
            for service in services:
                if hasattr(service, 'is_initialized') and not service.is_initialized:
                    await service.initialize()
            
            # 加载配置
            await self._load_config()
            
            # 恢复运行状态
            await self._restore_state()
            
            self.is_initialized = True
            logger.info("算法交易引擎初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"算法交易引擎初始化失败: {e}")
            self.status = EngineStatus.ERROR
            return False
    
    async def start_engine(self, user_id: str = "default"):
        """启动交易引擎"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            if self.status == EngineStatus.RUNNING:
                return {"success": True, "message": "引擎已在运行中"}
            
            self.status = EngineStatus.STARTING
            self._stop_event.clear()
            
            # 启动核心任务
            self._running_tasks = [
                asyncio.create_task(self._signal_monitoring_loop()),
                asyncio.create_task(self._order_management_loop()),
                asyncio.create_task(self._risk_monitoring_loop()),
                asyncio.create_task(self._position_tracking_loop()),
            ]
            
            self.status = EngineStatus.RUNNING
            
            # 记录启动事件
            await self._log_engine_event("ENGINE_STARTED", {"user_id": user_id})
            
            logger.info(f"算法交易引擎已启动 - 用户: {user_id}")
            return {"success": True, "message": "引擎启动成功"}
            
        except Exception as e:
            logger.error(f"启动交易引擎失败: {e}")
            self.status = EngineStatus.ERROR
            return {"success": False, "error": str(e)}
    
    async def stop_engine(self, user_id: str = "default"):
        """停止交易引擎"""
        try:
            if self.status == EngineStatus.STOPPED:
                return {"success": True, "message": "引擎已停止"}
            
            # 设置停止信号
            self._stop_event.set()
            
            # 取消所有待处理订单
            await self._cancel_all_pending_orders()
            
            # 停止所有任务
            for task in self._running_tasks:
                if not task.done():
                    task.cancel()
            
            # 等待任务完成
            if self._running_tasks:
                await asyncio.gather(*self._running_tasks, return_exceptions=True)
            
            self._running_tasks.clear()
            self.status = EngineStatus.STOPPED
            
            # 保存状态
            await self._save_state()
            
            # 记录停止事件
            await self._log_engine_event("ENGINE_STOPPED", {"user_id": user_id})
            
            logger.info(f"算法交易引擎已停止 - 用户: {user_id}")
            return {"success": True, "message": "引擎停止成功"}
            
        except Exception as e:
            logger.error(f"停止交易引擎失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def add_strategy(self, strategy_config: Dict[str, Any]) -> Dict[str, Any]:
        """添加交易策略"""
        try:
            strategy_id = strategy_config.get("strategy_id")
            if not strategy_id:
                return {"success": False, "error": "缺少策略ID"}
            
            if strategy_id in self.active_strategies:
                return {"success": False, "error": "策略已存在"}
            
            # 验证策略配置
            validation_result = await self._validate_strategy_config(strategy_config)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}
            
            # 创建策略实例
            strategy_instance = await self._create_strategy_instance(strategy_config)
            if not strategy_instance:
                return {"success": False, "error": "创建策略实例失败"}
            
            # 添加到活跃策略
            self.active_strategies[strategy_id] = strategy_instance
            
            # 记录事件
            await self._log_engine_event("STRATEGY_ADDED", {
                "strategy_id": strategy_id,
                "config": strategy_config
            })
            
            logger.info(f"策略已添加: {strategy_id}")
            return {"success": True, "strategy_id": strategy_id}
            
        except Exception as e:
            logger.error(f"添加策略失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def remove_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """移除交易策略"""
        try:
            if strategy_id not in self.active_strategies:
                return {"success": False, "error": "策略不存在"}
            
            # 停止策略
            strategy = self.active_strategies[strategy_id]
            if hasattr(strategy, 'stop'):
                await strategy.stop()
            
            # 取消该策略的所有待处理订单
            await self._cancel_strategy_orders(strategy_id)
            
            # 从活跃策略中移除
            del self.active_strategies[strategy_id]
            
            # 记录事件
            await self._log_engine_event("STRATEGY_REMOVED", {"strategy_id": strategy_id})
            
            logger.info(f"策略已移除: {strategy_id}")
            return {"success": True, "message": "策略移除成功"}
            
        except Exception as e:
            logger.error(f"移除策略失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        try:
            # 获取基本状态
            status_info = {
                "status": self.status.value,
                "is_initialized": self.is_initialized,
                "active_strategies": len(self.active_strategies),
                "pending_orders": len(self.pending_orders),
                "total_positions": len(self.position_tracker),
                "uptime": self._calculate_uptime(),
                "last_update": datetime.now().isoformat()
            }
            
            # 获取策略详情
            strategy_details = []
            for strategy_id, strategy in self.active_strategies.items():
                strategy_info = {
                    "strategy_id": strategy_id,
                    "name": getattr(strategy, 'name', strategy_id),
                    "status": getattr(strategy, 'status', 'unknown'),
                    "symbols": getattr(strategy, 'symbols', []),
                    "last_signal": getattr(strategy, 'last_signal', None),
                    "total_trades": getattr(strategy, 'total_trades', 0),
                    "profit_loss": getattr(strategy, 'profit_loss', 0.0)
                }
                strategy_details.append(strategy_info)
            
            status_info["strategies"] = strategy_details
            
            # 获取最近信号
            status_info["recent_signals"] = self.signal_history[-10:] if self.signal_history else []
            
            return status_info
            
        except Exception as e:
            logger.error(f"获取引擎状态失败: {e}")
            return {"error": str(e)}
    
    async def _signal_monitoring_loop(self):
        """信号监控循环"""
        logger.info("信号监控循环已启动")
        
        while not self._stop_event.is_set():
            try:
                # 检查所有活跃策略的信号
                for strategy_id, strategy in self.active_strategies.items():
                    if hasattr(strategy, 'generate_signals'):
                        signals = await strategy.generate_signals()
                        if signals:
                            await self._process_signals(strategy_id, signals)
                
                # 等待下次检查
                await asyncio.sleep(self.config["signal_check_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"信号监控循环错误: {e}")
                await asyncio.sleep(5)
        
        logger.info("信号监控循环已停止")
    
    async def _order_management_loop(self):
        """订单管理循环"""
        logger.info("订单管理循环已启动")
        
        while not self._stop_event.is_set():
            try:
                # 检查待处理订单状态
                current_time = datetime.now()
                expired_orders = []
                
                for order_id, order_info in self.pending_orders.items():
                    # 检查订单是否超时
                    if (current_time - order_info["created_at"]).seconds > self.config["order_timeout"]:
                        expired_orders.append(order_id)
                        continue
                    
                    # 更新订单状态
                    await self._update_order_status(order_id, order_info)
                
                # 处理超时订单
                for order_id in expired_orders:
                    await self._handle_expired_order(order_id)
                
                await asyncio.sleep(1)  # 订单检查频率较高
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"订单管理循环错误: {e}")
                await asyncio.sleep(5)
        
        logger.info("订单管理循环已停止")
    
    async def _risk_monitoring_loop(self):
        """风险监控循环"""
        logger.info("风险监控循环已启动")
        
        while not self._stop_event.is_set():
            try:
                # 获取风险指标
                risk_metrics = await risk_monitoring_service.calculate_real_time_risk_metrics()
                
                # 检查是否需要紧急停止
                if await self._check_emergency_stop(risk_metrics):
                    logger.warning("触发紧急停止条件，暂停所有交易")
                    await self._emergency_stop()
                
                # 检查策略级别风险
                for strategy_id in self.active_strategies:
                    await self._check_strategy_risk(strategy_id, risk_metrics)
                
                await asyncio.sleep(self.config["risk_check_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"风险监控循环错误: {e}")
                await asyncio.sleep(10)
        
        logger.info("风险监控循环已停止")
    
    async def _position_tracking_loop(self):
        """持仓跟踪循环"""
        logger.info("持仓跟踪循环已启动")
        
        while not self._stop_event.is_set():
            try:
                # 获取最新持仓
                positions = await simple_trading_service.get_positions()
                
                # 更新持仓跟踪
                await self._update_position_tracker(positions)
                
                # 检查止损止盈
                await self._check_stop_loss_take_profit()
                
                await asyncio.sleep(5)  # 持仓检查频率
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"持仓跟踪循环错误: {e}")
                await asyncio.sleep(10)
        
        logger.info("持仓跟踪循环已停止")
    
    async def _process_signals(self, strategy_id: str, signals: List[Dict[str, Any]]):
        """处理交易信号"""
        try:
            for signal in signals:
                # 验证信号
                if not await self._validate_signal(signal):
                    continue
                
                # 风险检查
                if not await self._risk_check_for_signal(signal):
                    logger.warning(f"信号未通过风险检查: {signal}")
                    continue
                
                # 生成订单
                order = await self._create_order_from_signal(strategy_id, signal)
                if order:
                    # 提交订单
                    result = await self._submit_order(order)
                    if result["success"]:
                        # 记录信号历史
                        signal_record = {
                            "strategy_id": strategy_id,
                            "signal": signal,
                            "order_id": result["order_id"],
                            "timestamp": datetime.now().isoformat()
                        }
                        self.signal_history.append(signal_record)
                        
                        # 限制历史记录长度
                        if len(self.signal_history) > 1000:
                            self.signal_history = self.signal_history[-500:]
                
        except Exception as e:
            logger.error(f"处理信号失败: {e}")
    
    async def _create_strategy_instance(self, config: Dict[str, Any]):
        """创建策略实例"""
        try:
            strategy_type = config.get("strategy_type")
            
            if strategy_type == "dual_ma":
                return DualMAStrategy(config)
            elif strategy_type == "rsi_reversal":
                return RSIReversalStrategy(config)
            else:
                # 通用策略实例
                return GenericStrategy(config)
                
        except Exception as e:
            logger.error(f"创建策略实例失败: {e}")
            return None
    
    def _calculate_uptime(self) -> str:
        """计算运行时间"""
        # 这里可以从Redis或数据库获取启动时间
        return "运行中"
    
    async def _load_config(self):
        """加载配置"""
        try:
            config_key = "algo_engine:config"
            config_data = await self.redis_client.get(config_key)
            if config_data:
                saved_config = json.loads(config_data)
                self.config.update(saved_config)
        except Exception as e:
            logger.warning(f"加载配置失败，使用默认配置: {e}")
    
    async def _save_state(self):
        """保存状态"""
        try:
            state_data = {
                "status": self.status.value,
                "active_strategies": list(self.active_strategies.keys()),
                "config": self.config,
                "last_save": datetime.now().isoformat()
            }
            
            state_key = "algo_engine:state"
            await self.redis_client.setex(
                state_key, 
                3600 * 24,  # 24小时过期
                json.dumps(state_data)
            )
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    async def _restore_state(self):
        """恢复状态"""
        try:
            state_key = "algo_engine:state"
            state_data = await self.redis_client.get(state_key)
            if state_data:
                saved_state = json.loads(state_data)
                # 这里可以恢复一些状态，但不自动启动策略
                logger.info("状态恢复成功")
        except Exception as e:
            logger.warning(f"恢复状态失败: {e}")
    
    async def _log_engine_event(self, event_type: str, data: Dict[str, Any]):
        """记录引擎事件"""
        try:
            event_record = {
                "event_type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            # 存储到Redis列表
            events_key = "algo_engine:events"
            await self.redis_client.lpush(events_key, json.dumps(event_record))
            await self.redis_client.ltrim(events_key, 0, 999)  # 保留最近1000条
            
        except Exception as e:
            logger.error(f"记录引擎事件失败: {e}")

    async def _validate_strategy_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证策略配置"""
        try:
            required_fields = ["strategy_id", "strategy_type", "symbols"]
            for field in required_fields:
                if field not in config:
                    return {"valid": False, "error": f"缺少必需字段: {field}"}
            
            # 验证symbols格式
            symbols = config["symbols"]
            if not isinstance(symbols, list) or not symbols:
                return {"valid": False, "error": "symbols必须是非空列表"}
            
            # 验证策略类型
            valid_types = ["dual_ma", "rsi_reversal", "custom"]
            if config["strategy_type"] not in valid_types:
                return {"valid": False, "error": f"不支持的策略类型: {config['strategy_type']}"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": str(e)}

    async def _validate_signal(self, signal: Dict[str, Any]) -> bool:
        """验证交易信号"""
        try:
            required_fields = ["symbol", "signal_type", "price"]
            for field in required_fields:
                if field not in signal:
                    return False
            
            # 验证信号类型
            valid_signals = [s.value for s in SignalType]
            if signal["signal_type"] not in valid_signals:
                return False
            
            # 验证价格
            price = signal["price"]
            if not isinstance(price, (int, float)) or price <= 0:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证信号失败: {e}")
            return False

    async def _risk_check_for_signal(self, signal: Dict[str, Any]) -> bool:
        """信号风险检查"""
        try:
            # 获取当前风险指标
            risk_metrics = await risk_monitoring_service.calculate_real_time_risk_metrics()
            
            # 检查整体风险评分
            overall_risk = risk_metrics.get("overall_risk_score", 0)
            if overall_risk > 80:  # 高风险时停止交易
                return False
            
            # 检查保证金使用率
            account_metrics = risk_metrics.get("account_metrics", {})
            margin_ratio = account_metrics.get("margin_ratio", 0)
            if margin_ratio > 0.8:  # 保证金使用率过高
                return False
            
            # 检查单日交易次数
            today_trades = await self._get_today_trade_count()
            if today_trades >= self.config["max_daily_trades"]:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"信号风险检查失败: {e}")
            return False

    async def _create_order_from_signal(self, strategy_id: str, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从信号创建订单"""
        try:
            symbol = signal["symbol"]
            signal_type = signal["signal_type"]
            price = signal["price"]
            
            # 计算订单数量
            volume = await self._calculate_order_volume(symbol, signal)
            if volume <= 0:
                return None
            
            # 创建订单
            order = {
                "order_id": str(uuid.uuid4()),
                "strategy_id": strategy_id,
                "symbol": symbol,
                "direction": "BUY" if signal_type in ["buy"] else "SELL",
                "volume": volume,
                "price": price,
                "order_type": "LIMIT",
                "status": OrderStatus.PENDING.value,
                "created_at": datetime.now(),
                "signal_info": signal
            }
            
            return order
            
        except Exception as e:
            logger.error(f"创建订单失败: {e}")
            return None

    async def _calculate_order_volume(self, symbol: str, signal: Dict[str, Any]) -> int:
        """计算订单数量"""
        try:
            # 获取账户信息
            account_info = await simple_trading_service.get_account_info()
            available = float(account_info.get("available", 0))
            
            # 获取合约信息
            contract_info = await market_data_service.get_contract_info(symbol)
            if not contract_info:
                return 0
            
            multiplier = contract_info.get("multiplier", 1)
            margin_rate = contract_info.get("margin_rate", 0.1)
            
            # 计算可用于此次交易的资金（风险控制）
            max_position_value = available * 0.1  # 单次交易最多使用10%资金
            
            # 计算数量
            price = signal["price"]
            required_margin = price * multiplier * margin_rate
            
            if required_margin > 0:
                volume = int(max_position_value / required_margin)
                return max(1, volume)  # 至少1手
            
            return 0
            
        except Exception as e:
            logger.error(f"计算订单数量失败: {e}")
            return 0

    async def _submit_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """提交订单"""
        try:
            # 添加到待处理订单
            order_id = order["order_id"]
            self.pending_orders[order_id] = order
            
            # 调用交易服务提交订单
            result = await simple_trading_service.place_order(
                symbol=order["symbol"],
                direction=order["direction"],
                volume=order["volume"],
                price=order["price"],
                order_type=order["order_type"]
            )
            
            if result.get("success"):
                # 更新订单状态
                order["status"] = OrderStatus.SUBMITTED.value
                order["exchange_order_id"] = result.get("order_id")
                
                logger.info(f"订单提交成功: {order_id}")
                return {"success": True, "order_id": order_id}
            else:
                # 订单提交失败
                order["status"] = OrderStatus.REJECTED.value
                order["error"] = result.get("error", "未知错误")
                
                logger.error(f"订单提交失败: {order_id}, 错误: {order['error']}")
                return {"success": False, "error": order["error"]}
                
        except Exception as e:
            logger.error(f"提交订单失败: {e}")
            return {"success": False, "error": str(e)}

    async def _get_today_trade_count(self) -> int:
        """获取今日交易次数"""
        try:
            today = datetime.now().date()
            count = 0
            
            for order_info in self.pending_orders.values():
                if (order_info["created_at"].date() == today and 
                    order_info["status"] == OrderStatus.FILLED.value):
                    count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"获取今日交易次数失败: {e}")
            return 0

    async def _cancel_strategy_orders(self, strategy_id: str):
        """取消指定策略的所有订单"""
        try:
            for order_id, order_info in self.pending_orders.items():
                if (order_info.get("strategy_id") == strategy_id and 
                    order_info["status"] == OrderStatus.SUBMITTED.value):
                    
                    exchange_order_id = order_info.get("exchange_order_id")
                    if exchange_order_id:
                        await simple_trading_service.cancel_order(exchange_order_id)
                    
                    order_info["status"] = OrderStatus.CANCELLED.value
                    order_info["cancel_reason"] = "strategy_removed"
            
            logger.info(f"策略 {strategy_id} 的所有订单已取消")
            
        except Exception as e:
            logger.error(f"取消策略订单失败: {e}")

    async def _cancel_all_pending_orders(self):
        """取消所有待处理订单"""
        try:
            for order_id, order_info in self.pending_orders.items():
                if order_info["status"] == OrderStatus.SUBMITTED.value:
                    exchange_order_id = order_info.get("exchange_order_id")
                    if exchange_order_id:
                        await simple_trading_service.cancel_order(exchange_order_id)
                    
                    order_info["status"] = OrderStatus.CANCELLED.value
                    order_info["cancel_reason"] = "engine_stop"
            
            logger.info("所有待处理订单已取消")
            
        except Exception as e:
            logger.error(f"取消待处理订单失败: {e}")


class GenericStrategy:
    """通用策略基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.strategy_id = config["strategy_id"]
        self.name = config.get("name", self.strategy_id)
        self.symbols = config.get("symbols", [])
        self.status = "active"
        self.last_signal = None
        self.total_trades = 0
        self.profit_loss = 0.0
    
    async def generate_signals(self) -> List[Dict[str, Any]]:
        """生成交易信号 - 子类需要实现"""
        return []
    
    async def stop(self):
        """停止策略"""
        self.status = "stopped"


class DualMAStrategy(GenericStrategy):
    """双均线策略"""
    
    async def generate_signals(self) -> List[Dict[str, Any]]:
        """生成双均线交易信号"""
        signals = []
        
        try:
            for symbol in self.symbols:
                # 获取技术指标
                indicators = await technical_analysis_service.calculate_indicators(
                    symbol, period="1m", limit=50
                )
                
                if not indicators or "latest_values" not in indicators:
                    continue
                
                latest = indicators["latest_values"]
                ma5 = latest.get("ma5")
                ma10 = latest.get("ma10")
                
                if ma5 and ma10:
                    # 生成信号
                    if ma5 > ma10 * 1.001:  # 短期均线上穿长期均线
                        signals.append({
                            "symbol": symbol,
                            "signal_type": SignalType.BUY.value,
                            "price": latest.get("close"),
                            "confidence": 0.8,
                            "reason": "MA5上穿MA10"
                        })
                    elif ma5 < ma10 * 0.999:  # 短期均线下穿长期均线
                        signals.append({
                            "symbol": symbol,
                            "signal_type": SignalType.SELL.value,
                            "price": latest.get("close"),
                            "confidence": 0.8,
                            "reason": "MA5下穿MA10"
                        })
        
        except Exception as e:
            logger.error(f"双均线策略生成信号失败: {e}")
        
        return signals


class RSIReversalStrategy(GenericStrategy):
    """RSI反转策略"""
    
    async def generate_signals(self) -> List[Dict[str, Any]]:
        """生成RSI反转交易信号"""
        signals = []
        
        try:
            for symbol in self.symbols:
                # 获取技术指标
                indicators = await technical_analysis_service.calculate_indicators(
                    symbol, period="1m", limit=50
                )
                
                if not indicators or "latest_values" not in indicators:
                    continue
                
                latest = indicators["latest_values"]
                rsi = latest.get("rsi")
                
                if rsi:
                    # 生成信号
                    if rsi < 30:  # 超卖
                        signals.append({
                            "symbol": symbol,
                            "signal_type": SignalType.BUY.value,
                            "price": latest.get("close"),
                            "confidence": 0.7,
                            "reason": f"RSI超卖({rsi:.1f})"
                        })
                    elif rsi > 70:  # 超买
                        signals.append({
                            "symbol": symbol,
                            "signal_type": SignalType.SELL.value,
                            "price": latest.get("close"),
                            "confidence": 0.7,
                            "reason": f"RSI超买({rsi:.1f})"
                        })
        
        except Exception as e:
            logger.error(f"RSI反转策略生成信号失败: {e}")
        
        return signals


# 创建全局算法交易引擎实例
algo_trading_engine = AlgoTradingEngine()
