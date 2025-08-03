"""
持仓相关数据模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON, Float, DECIMAL, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, Any

from ..core.database import Base


class PositionStatus(str, PyEnum):
    """持仓状态枚举"""
    OPEN = "open"           # 持仓中
    CLOSED = "closed"       # 已平仓
    SUSPENDED = "suspended" # 暂停交易


class PositionType(str, PyEnum):
    """持仓类型枚举"""
    LONG = "long"           # 多头持仓
    SHORT = "short"         # 空头持仓


class Position(Base):
    """持仓模型"""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # 基本信息
    symbol = Column(String(20), nullable=False, index=True)  # 交易标的
    position_type = Column(Enum(PositionType), nullable=False, index=True)
    status = Column(Enum(PositionStatus), default=PositionStatus.OPEN, index=True)
    
    # 持仓数量和成本
    quantity = Column(DECIMAL(20, 8), nullable=False, default=Decimal('0'))  # 持仓数量
    available_quantity = Column(DECIMAL(20, 8), nullable=False, default=Decimal('0'))  # 可用数量
    frozen_quantity = Column(DECIMAL(20, 8), nullable=False, default=Decimal('0'))  # 冻结数量
    
    # 成本信息
    average_cost = Column(DECIMAL(20, 8), nullable=False, default=Decimal('0'))  # 平均成本价
    total_cost = Column(DECIMAL(20, 8), nullable=False, default=Decimal('0'))  # 总成本
    
    # 盈亏信息
    realized_pnl = Column(DECIMAL(20, 8), default=Decimal('0'))  # 已实现盈亏
    unrealized_pnl = Column(DECIMAL(20, 8), default=Decimal('0'))  # 未实现盈亏
    unrealized_pnl_percent = Column(DECIMAL(10, 6), default=Decimal('0'))  # 未实现盈亏百分比
    total_pnl = Column(DECIMAL(20, 8), default=Decimal('0'))  # 总盈亏
    daily_pnl = Column(DECIMAL(20, 8), default=Decimal('0'))  # 今日盈亏
    daily_pnl_percent = Column(DECIMAL(10, 6), default=Decimal('0'))  # 今日盈亏百分比
    return_rate = Column(DECIMAL(10, 6), default=Decimal('0'))  # 总收益率
    
    # 市值信息
    current_price = Column(DECIMAL(20, 8))  # 当前价格
    market_value = Column(DECIMAL(20, 8))  # 市值
    
    # 风险指标
    max_drawdown = Column(DECIMAL(20, 8), default=Decimal('0'))  # 最大回撤
    max_profit = Column(DECIMAL(20, 8), default=Decimal('0'))  # 最大盈利
    
    # 止损止盈设置
    stop_loss_price = Column(DECIMAL(20, 8))  # 止损价格
    take_profit_price = Column(DECIMAL(20, 8))  # 止盈价格
    stop_loss_order_id = Column(Integer, ForeignKey("orders.id"))  # 止损订单ID
    take_profit_order_id = Column(Integer, ForeignKey("orders.id"))  # 止盈订单ID
    
    # 关联信息
    strategy_id = Column(Integer, ForeignKey("strategies.id"), index=True)
    strategy = relationship("Strategy")
    
    backtest_id = Column(Integer, ForeignKey("backtests.id"), index=True)
    backtest = relationship("Backtest")
    
    # 持仓来源
    source = Column(String(50), default="manual")  # manual, strategy, algorithm
    source_id = Column(String(100))  # 来源标识
    
    # 元数据
    tags = Column(JSON, default=list)  # 标签
    notes = Column(Text)  # 备注
    model_metadata = Column(JSON, default=dict)  # 元数据
    
    # 用户关联
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="positions")
    
    # 时间戳
    opened_at = Column(DateTime, server_default=func.now())  # 开仓时间
    closed_at = Column(DateTime)  # 平仓时间
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 持仓历史记录关联
    history_records = relationship("PositionHistory", back_populates="position", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_position_user_symbol', 'user_id', 'symbol'),
        Index('idx_position_user_status', 'user_id', 'status'),
        Index('idx_position_strategy', 'strategy_id'),
    )

    def __repr__(self):
        return f"<Position(id={self.id}, symbol='{self.symbol}', quantity={self.quantity}, status='{self.status}')>"
    
    @property
    def is_long(self) -> bool:
        """是否为多头持仓"""
        return self.position_type == PositionType.LONG
    
    @property
    def is_short(self) -> bool:
        """是否为空头持仓"""
        return self.position_type == PositionType.SHORT
    
    @property
    def is_open(self) -> bool:
        """持仓是否开放"""
        return self.status == PositionStatus.OPEN and self.quantity != 0
    
    @property
    def is_closed(self) -> bool:
        """持仓是否已关闭"""
        return self.status == PositionStatus.CLOSED or self.quantity == 0
    
    @property
    def return_rate(self) -> float:
        """收益率"""
        if self.total_cost == 0:
            return 0.0
        return float(self.total_pnl / self.total_cost)
    
    @property
    def unrealized_return_rate(self) -> float:
        """未实现收益率"""
        if self.total_cost == 0:
            return 0.0
        return float(self.unrealized_pnl / self.total_cost)
    
    def add_trade(self, quantity: Decimal, price: Decimal, commission: Decimal = Decimal('0')):
        """添加交易记录，更新持仓"""
        # 记录历史
        self._record_history("trade", {
            'quantity': float(quantity),
            'price': float(price),
            'commission': float(commission),
            'old_quantity': float(self.quantity),
            'old_average_cost': float(self.average_cost)
        })
        
        if self.quantity == 0:
            # 新建仓位
            self.quantity = abs(quantity)
            self.available_quantity = abs(quantity)
            self.position_type = PositionType.LONG if quantity > 0 else PositionType.SHORT
            self.average_cost = price
            self.total_cost = abs(quantity) * price + commission
            self.status = PositionStatus.OPEN
            if not self.opened_at:
                self.opened_at = datetime.now()
        else:
            # 判断是加仓还是减仓
            same_direction = (self.is_long and quantity > 0) or (self.is_short and quantity < 0)
            
            if same_direction:
                # 加仓
                new_quantity = self.quantity + abs(quantity)
                new_total_cost = self.total_cost + abs(quantity) * price + commission
                self.average_cost = new_total_cost / new_quantity
                self.quantity = new_quantity
                self.available_quantity = new_quantity - self.frozen_quantity
                self.total_cost = new_total_cost
            else:
                # 减仓或平仓
                trade_quantity = min(abs(quantity), self.quantity)
                
                # 计算已实现盈亏
                if self.is_long:
                    realized_pnl = trade_quantity * (price - self.average_cost) - commission
                else:
                    realized_pnl = trade_quantity * (self.average_cost - price) - commission
                
                self.realized_pnl += realized_pnl
                self.quantity -= trade_quantity
                self.available_quantity = max(Decimal('0'), self.quantity - self.frozen_quantity)
                
                # 如果完全平仓
                if self.quantity == 0:
                    self.status = PositionStatus.CLOSED
                    self.closed_at = datetime.now()
                    self.total_cost = Decimal('0')
                    self.average_cost = Decimal('0')
                    self.unrealized_pnl = Decimal('0')
                else:
                    # 调整总成本
                    self.total_cost = self.quantity * self.average_cost
        
        # 更新总盈亏
        self.total_pnl = self.realized_pnl + self.unrealized_pnl
    
    def update_market_price(self, current_price: Decimal):
        """更新市场价格和未实现盈亏"""
        if self.quantity == 0:
            self.current_price = current_price
            self.market_value = Decimal('0')
            self.unrealized_pnl = Decimal('0')
            return
        
        old_price = self.current_price
        self.current_price = current_price
        self.market_value = self.quantity * current_price
        
        # 计算未实现盈亏
        if self.is_long:
            self.unrealized_pnl = self.quantity * (current_price - self.average_cost)
        else:
            self.unrealized_pnl = self.quantity * (self.average_cost - current_price)
        
        # 更新总盈亏
        self.total_pnl = self.realized_pnl + self.unrealized_pnl
        
        # 更新风险指标
        if old_price and self.unrealized_pnl > self.max_profit:
            self.max_profit = self.unrealized_pnl
        
        if old_price and self.unrealized_pnl < -abs(self.max_drawdown):
            self.max_drawdown = abs(self.unrealized_pnl)
        
        # 记录价格更新历史
        self._record_history("price_update", {
            'old_price': float(old_price) if old_price else None,
            'new_price': float(current_price),
            'unrealized_pnl': float(self.unrealized_pnl),
            'market_value': float(self.market_value)
        })
    
    def freeze_quantity(self, quantity: Decimal) -> bool:
        """冻结数量"""
        if quantity <= 0 or quantity > self.available_quantity:
            return False
        
        self.frozen_quantity += quantity
        self.available_quantity -= quantity
        
        self._record_history("freeze", {
            'frozen_quantity': float(quantity),
            'total_frozen': float(self.frozen_quantity),
            'available_quantity': float(self.available_quantity)
        })
        
        return True
    
    def unfreeze_quantity(self, quantity: Decimal) -> bool:
        """解冻数量"""
        if quantity <= 0 or quantity > self.frozen_quantity:
            return False
        
        self.frozen_quantity -= quantity
        self.available_quantity += quantity
        
        self._record_history("unfreeze", {
            'unfrozen_quantity': float(quantity),
            'total_frozen': float(self.frozen_quantity),
            'available_quantity': float(self.available_quantity)
        })
        
        return True
    
    def set_stop_loss(self, stop_price: Decimal, order_id: Optional[int] = None):
        """设置止损"""
        self.stop_loss_price = stop_price
        self.stop_loss_order_id = order_id
        
        self._record_history("set_stop_loss", {
            'stop_price': float(stop_price),
            'order_id': order_id
        })
    
    def set_take_profit(self, profit_price: Decimal, order_id: Optional[int] = None):
        """设置止盈"""
        self.take_profit_price = profit_price
        self.take_profit_order_id = order_id
        
        self._record_history("set_take_profit", {
            'profit_price': float(profit_price),
            'order_id': order_id
        })
    
    def check_stop_loss_trigger(self) -> bool:
        """检查是否触发止损"""
        if not self.stop_loss_price or not self.current_price:
            return False
        
        if self.is_long:
            return self.current_price <= self.stop_loss_price
        else:
            return self.current_price >= self.stop_loss_price
    
    def check_take_profit_trigger(self) -> bool:
        """检查是否触发止盈"""
        if not self.take_profit_price or not self.current_price:
            return False
        
        if self.is_long:
            return self.current_price >= self.take_profit_price
        else:
            return self.current_price <= self.take_profit_price
    
    def _record_history(self, action: str, details: Dict[str, Any]):
        """记录持仓历史"""
        from sqlalchemy.orm import Session
        from ..core.database import SessionLocal
        
        # 创建历史记录
        history = PositionHistory(
            position_id=self.id,
            action=action,
            details=details,
            quantity_snapshot=self.quantity,
            average_cost_snapshot=self.average_cost,
            total_cost_snapshot=self.total_cost,
            realized_pnl_snapshot=self.realized_pnl,
            unrealized_pnl_snapshot=self.unrealized_pnl,
            current_price_snapshot=self.current_price
        )
        
        # 如果在事务中，直接添加到当前会话
        try:
            # 尝试获取当前会话
            from sqlalchemy.orm import object_session
            session = object_session(self)
            if session:
                session.add(history)
            else:
                # 如果没有当前会话，创建新会话
                db = SessionLocal()
                try:
                    db.add(history)
                    db.commit()
                finally:
                    db.close()
        except Exception as e:
            # 记录历史失败不应该影响主要业务逻辑
            import logging
            logging.warning(f"Failed to record position history: {e}")
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'symbol': self.symbol,
            'position_type': self.position_type,
            'status': self.status,
            'quantity': float(self.quantity),
            'available_quantity': float(self.available_quantity),
            'frozen_quantity': float(self.frozen_quantity),
            'average_cost': float(self.average_cost),
            'total_cost': float(self.total_cost),
            'realized_pnl': float(self.realized_pnl),
            'unrealized_pnl': float(self.unrealized_pnl),
            'total_pnl': float(self.total_pnl),
            'current_price': float(self.current_price) if self.current_price else None,
            'market_value': float(self.market_value) if self.market_value else None,
            'max_drawdown': float(self.max_drawdown),
            'max_profit': float(self.max_profit),
            'stop_loss_price': float(self.stop_loss_price) if self.stop_loss_price else None,
            'take_profit_price': float(self.take_profit_price) if self.take_profit_price else None,
            'stop_loss_order_id': self.stop_loss_order_id,
            'take_profit_order_id': self.take_profit_order_id,
            'strategy_id': self.strategy_id,
            'backtest_id': self.backtest_id,
            'source': self.source,
            'source_id': self.source_id,
            'tags': self.tags,
            'notes': self.notes,
            'metadata': self.model_metadata,
            'user_id': self.user_id,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'return_rate': self.return_rate,
            'unrealized_return_rate': self.unrealized_return_rate,
            'is_long': self.is_long,
            'is_short': self.is_short,
            'is_open': self.is_open,
            'is_closed': self.is_closed
        }


class PositionHistory(Base):
    """持仓历史记录模型"""
    __tablename__ = "position_history"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # 持仓关联
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False, index=True)
    position = relationship("Position", back_populates="history_records")
    
    # 操作信息
    action = Column(String(50), nullable=False, index=True)  # trade, price_update, freeze, unfreeze, etc.
    details = Column(JSON, default=dict)  # 操作详情
    
    # 快照信息（操作后的状态）
    quantity_snapshot = Column(DECIMAL(20, 8))
    average_cost_snapshot = Column(DECIMAL(20, 8))
    total_cost_snapshot = Column(DECIMAL(20, 8))
    realized_pnl_snapshot = Column(DECIMAL(20, 8))
    unrealized_pnl_snapshot = Column(DECIMAL(20, 8))
    current_price_snapshot = Column(DECIMAL(20, 8))
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    # 索引
    __table_args__ = (
        Index('idx_position_history_position_action', 'position_id', 'action'),
        Index('idx_position_history_created', 'created_at'),
    )

    def __repr__(self):
        return f"<PositionHistory(id={self.id}, position_id={self.position_id}, action='{self.action}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'position_id': self.position_id,
            'action': self.action,
            'details': self.details,
            'quantity_snapshot': float(self.quantity_snapshot) if self.quantity_snapshot else None,
            'average_cost_snapshot': float(self.average_cost_snapshot) if self.average_cost_snapshot else None,
            'total_cost_snapshot': float(self.total_cost_snapshot) if self.total_cost_snapshot else None,
            'realized_pnl_snapshot': float(self.realized_pnl_snapshot) if self.realized_pnl_snapshot else None,
            'unrealized_pnl_snapshot': float(self.unrealized_pnl_snapshot) if self.unrealized_pnl_snapshot else None,
            'current_price_snapshot': float(self.current_price_snapshot) if self.current_price_snapshot else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PositionSummary(Base):
    """持仓汇总模型（按用户和标的汇总）"""
    __tablename__ = "position_summaries"

    id = Column(Integer, primary_key=True, index=True)
    
    # 用户和标的
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    
    # 汇总数据
    total_quantity = Column(DECIMAL(20, 8), default=Decimal('0'))  # 总持仓数量
    total_cost = Column(DECIMAL(20, 8), default=Decimal('0'))  # 总成本
    average_cost = Column(DECIMAL(20, 8), default=Decimal('0'))  # 平均成本
    total_realized_pnl = Column(DECIMAL(20, 8), default=Decimal('0'))  # 总已实现盈亏
    total_unrealized_pnl = Column(DECIMAL(20, 8), default=Decimal('0'))  # 总未实现盈亏
    total_market_value = Column(DECIMAL(20, 8), default=Decimal('0'))  # 总市值
    
    # 统计信息
    position_count = Column(Integer, default=0)  # 持仓笔数
    last_trade_time = Column(DateTime)  # 最后交易时间
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 唯一约束
    __table_args__ = (
        Index('idx_position_summary_user_symbol', 'user_id', 'symbol', unique=True),
    )

    def __repr__(self):
        return f"<PositionSummary(user_id={self.user_id}, symbol='{self.symbol}', quantity={self.total_quantity})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'total_quantity': float(self.total_quantity),
            'total_cost': float(self.total_cost),
            'average_cost': float(self.average_cost),
            'total_realized_pnl': float(self.total_realized_pnl),
            'total_unrealized_pnl': float(self.total_unrealized_pnl),
            'total_market_value': float(self.total_market_value),
            'position_count': self.position_count,
            'last_trade_time': self.last_trade_time.isoformat() if self.last_trade_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

