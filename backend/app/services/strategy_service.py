"""
策略管理服务 - 基于 tqsdk 的真实策略管理功能
"""

import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from ..core.database import get_redis_client
from ..models.strategy import Strategy

logger = logging.getLogger(__name__)


class StrategyService:
    """策略管理服务 - 基于 tqsdk 实现真实策略管理功能"""

    def __init__(self):
        self.redis_client = get_redis_client()
        self.is_initialized = False
        self.built_in_strategies = self._load_built_in_strategies()

    def _load_built_in_strategies(self) -> Dict[str, Dict[str, Any]]:
        """加载内置策略"""
        return {
            "dual_ma": {
                "name": "双均线策略",
                "description": "基于短期和长期移动平均线的交叉信号进行交易",
                "type": "trend_following",
                "parameters": {
                    "short_period": {"type": "int", "default": 5, "min": 3, "max": 20, "description": "短期均线周期"},
                    "long_period": {"type": "int", "default": 20, "min": 10, "max": 100, "description": "长期均线周期"},
                    "stop_loss": {"type": "float", "default": 0.02, "min": 0.01, "max": 0.1, "description": "止损比例"}
                },
                "created_time": datetime.now().isoformat(),
                "status": "active"
            },
            "rsi_reversal": {
                "name": "RSI反转策略",
                "description": "基于RSI指标的超买超卖信号进行反转交易",
                "type": "mean_reversion",
                "parameters": {
                    "rsi_period": {"type": "int", "default": 14, "min": 5, "max": 30, "description": "RSI计算周期"},
                    "oversold_level": {"type": "float", "default": 30, "min": 20, "max": 40, "description": "超卖阈值"},
                    "overbought_level": {"type": "float", "default": 70, "min": 60, "max": 80, "description": "超买阈值"}
                },
                "created_time": datetime.now().isoformat(),
                "status": "active"
            }
        }

    async def initialize(self):
        """初始化策略服务"""
        try:
            self.is_initialized = True
            logger.info("策略服务初始化成功")
            return True
        except Exception as e:
            logger.error(f"策略服务初始化失败: {e}")
            return False

    async def get_strategy_list(self, db: Session, user_id: str = "default") -> List[Dict[str, Any]]:
        """获取策略列表，包括用户策略和内置策略"""
        try:
            if not self.is_initialized:
                await self.initialize()

            strategies = []

            # 1. 获取用户自己的策略
            if user_id != "default":
                user_db_strategies = db.query(Strategy).filter(Strategy.user_id == user_id).all()
                for strategy in user_db_strategies:
                    strategy_dict = strategy.to_dict()
                    strategy_dict["is_built_in"] = False
                    strategies.append(strategy_dict)

            # 2. 添加内置策略
            for strategy_id, strategy_info in self.built_in_strategies.items():
                built_in_strategy = {
                    "id": f"built_in_{strategy_id}",
                    "uuid": f"built_in_{strategy_id}",
                    "name": strategy_info.get("name"),
                    "description": strategy_info.get("description"),
                    "strategy_type": strategy_info.get("type"),
                    "status": strategy_info.get("status"),
                    "code": "# Built-in strategy code is not exposed",
                    "entry_point": "main",
                    "language": "python",
                    "parameters": strategy_info.get("parameters", {}),
                    "symbols": [],
                    "timeframe": None,
                    "max_position_size": None,
                    "max_drawdown": None,
                    "stop_loss": None,
                    "take_profit": None,
                    "total_returns": 0.0,
                    "sharpe_ratio": None,
                    "max_drawdown_pct": None,
                    "win_rate": None,
                    "total_trades": 0,
                    "is_running": False,
                    "last_run_at": None,
                    "last_error": None,
                    "version": 1,
                    "tags": ["内置策略"],
                    "is_public": True,
                    "is_template": True,
                    "user_id": None,
                    "created_at": strategy_info.get("created_time"),
                    "updated_at": strategy_info.get("created_time"),
                    "is_built_in": True,
                }
                strategies.append(built_in_strategy)

            return strategies

        except Exception as e:
            logger.error(f"获取策略列表失败: {e}")
            return []


# 创建全局策略服务实例
strategy_service = StrategyService()