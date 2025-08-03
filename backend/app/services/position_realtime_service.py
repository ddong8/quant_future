"""
持仓实时更新服务
"""
import asyncio
import logging
from typing import Dict, List, Optional, Set
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..core.database import SessionLocal
from ..models.position import Position, PositionStatus
from ..models.user import User
from ..services.position_service import PositionService
from ..core.websocket import WebSocketManager
from ..utils.position_calculator import PositionCalculator, PositionRiskAnalyzer

logger = logging.getLogger(__name__)

class PositionRealtimeService:
    """持仓实时更新服务"""
    
    def __init__(self):
        self.websocket_manager = WebSocketManager()
        self.position_calculator = PositionCalculator()
        self.risk_analyzer = PositionRiskAnalyzer()
        self.subscribed_symbols: Set[str] = set()
        self.user_positions: Dict[int, List[Position]] = {}
        self.last_update_time = datetime.now()
        self.update_interval = 1  # 更新间隔（秒）
        
    async def start_realtime_updates(self):
        """启动实时更新服务"""
        logger.info("启动持仓实时更新服务")
        
        # 启动定时更新任务
        asyncio.create_task(self._periodic_update_task())
        
        # 启动WebSocket消息处理
        asyncio.create_task(self._websocket_message_handler())
        
    async def _periodic_update_task(self):
        """定期更新任务"""
        while True:
            try:
                await self._update_all_positions()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"定期更新任务出错: {e}")
                await asyncio.sleep(5)  # 出错后等待5秒再重试
    
    async def _websocket_message_handler(self):
        """WebSocket消息处理器"""
        while True:
            try:
                # 这里可以处理来自市场数据源的WebSocket消息
                # 暂时使用模拟数据
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"WebSocket消息处理出错: {e}")
                await asyncio.sleep(1)
    
    async def _update_all_positions(self):
        """更新所有持仓"""
        db = SessionLocal()
        try:
            # 获取所有开放持仓
            positions = db.query(Position).filter(
                Position.status == PositionStatus.OPEN
            ).all()
            
            if not positions:
                return
            
            # 获取需要更新的标的
            symbols = list(set(pos.symbol for pos in positions))
            
            # 获取市场数据（这里使用模拟数据）
            market_data = await self._get_market_data(symbols)
            
            # 更新持仓数据
            updated_positions = []
            for position in positions:
                if position.symbol in market_data:
                    old_price = position.current_price
                    new_price = market_data[position.symbol]['price']
                    
                    # 更新市场价格和盈亏计算
                    await self._update_position_pnl(position, new_price, market_data[position.symbol])
                    
                    # 检查是否有显著变化
                    if self._should_notify_update(position, old_price, new_price):
                        updated_positions.append(position)
            
            # 批量提交更新
            if updated_positions:
                db.commit()
                
                # 发送WebSocket通知
                await self._notify_position_updates(updated_positions)
                
                # 发送组合级别的盈亏更新
                await self._notify_portfolio_updates(updated_positions)
                
                logger.debug(f"更新了 {len(updated_positions)} 个持仓")
                
        except Exception as e:
            db.rollback()
            logger.error(f"更新持仓失败: {e}")
        finally:
            db.close()
    
    async def _update_position_pnl(self, position: Position, new_price: Decimal, market_info: Dict):
        """更新持仓盈亏计算"""
        try:
            # 保存旧值用于比较
            old_market_value = position.market_value
            old_total_pnl = position.total_pnl
            
            # 更新市场价格
            position.update_market_price(new_price)
            
            # 计算详细的盈亏指标
            pnl_metrics = self._calculate_detailed_pnl(position, market_info)
            
            # 更新持仓的盈亏相关字段
            position.unrealized_pnl = Decimal(str(pnl_metrics['unrealized_pnl']))
            position.unrealized_pnl_percent = Decimal(str(pnl_metrics['unrealized_pnl_percent']))
            position.daily_pnl = Decimal(str(pnl_metrics['daily_pnl']))
            position.daily_pnl_percent = Decimal(str(pnl_metrics['daily_pnl_percent']))
            
            # 计算风险指标
            risk_metrics = self._calculate_position_risk_metrics(position, market_info)
            position.risk_metrics = risk_metrics
            
            # 更新时间戳
            position.updated_at = datetime.now()
            
            logger.debug(f"更新持仓 {position.symbol} 盈亏: 未实现盈亏 {pnl_metrics['unrealized_pnl']:.2f}")
            
        except Exception as e:
            logger.error(f"更新持仓盈亏失败 {position.id}: {e}")
    
    def _calculate_detailed_pnl(self, position: Position, market_info: Dict) -> Dict:
        """计算详细的盈亏指标"""
        try:
            current_price = market_info['price']
            avg_cost = position.average_cost
            quantity = position.quantity
            
            # 基础计算
            market_value = quantity * current_price
            cost_basis = quantity * avg_cost
            
            # 未实现盈亏
            if position.position_type.value == 'LONG':
                unrealized_pnl = float(market_value - cost_basis)
            else:  # SHORT
                unrealized_pnl = float(cost_basis - market_value)
            
            # 未实现盈亏百分比
            unrealized_pnl_percent = (unrealized_pnl / float(abs(cost_basis))) * 100 if cost_basis != 0 else 0
            
            # 今日盈亏（需要今日开盘价，这里使用模拟）
            today_open_price = avg_cost * Decimal('0.99')  # 模拟今日开盘价
            if position.position_type.value == 'LONG':
                daily_pnl = float(quantity * (current_price - today_open_price))
            else:
                daily_pnl = float(quantity * (today_open_price - current_price))
            
            # 今日盈亏百分比
            daily_cost_basis = float(quantity * today_open_price)
            daily_pnl_percent = (daily_pnl / abs(daily_cost_basis)) * 100 if daily_cost_basis != 0 else 0
            
            return {
                'market_value': float(market_value),
                'cost_basis': float(cost_basis),
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_percent': unrealized_pnl_percent,
                'daily_pnl': daily_pnl,
                'daily_pnl_percent': daily_pnl_percent,
                'current_price': float(current_price),
                'price_change': float(market_info.get('change', 0)),
                'price_change_percent': market_info.get('change_percent', 0) * 100
            }
            
        except Exception as e:
            logger.error(f"计算详细盈亏失败: {e}")
            return {
                'market_value': 0,
                'cost_basis': 0,
                'unrealized_pnl': 0,
                'unrealized_pnl_percent': 0,
                'daily_pnl': 0,
                'daily_pnl_percent': 0,
                'current_price': 0,
                'price_change': 0,
                'price_change_percent': 0
            }
    
    def _calculate_position_risk_metrics(self, position: Position, market_info: Dict) -> Dict:
        """计算持仓风险指标"""
        try:
            current_price = float(market_info['price'])
            avg_cost = float(position.average_cost)
            
            # 价格波动率（简化计算）
            volatility = abs(market_info.get('change_percent', 0)) * 100
            
            # 距离止损止盈的距离
            stop_loss_distance = 0
            take_profit_distance = 0
            
            if position.stop_loss_price:
                stop_loss_distance = abs(current_price - float(position.stop_loss_price)) / current_price * 100
            
            if position.take_profit_price:
                take_profit_distance = abs(float(position.take_profit_price) - current_price) / current_price * 100
            
            # 持仓时间（天）
            holding_days = (datetime.now() - position.created_at).days
            
            # 风险评分（简化）
            risk_score = min(100, volatility * 10 + holding_days * 0.5)
            
            return {
                'volatility': volatility,
                'stop_loss_distance': stop_loss_distance,
                'take_profit_distance': take_profit_distance,
                'holding_days': holding_days,
                'risk_score': risk_score,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"计算持仓风险指标失败: {e}")
            return {}
    
    async def _get_market_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """获取市场数据（模拟实现）"""
        import random
        
        market_data = {}
        for symbol in symbols:
            # 模拟价格波动
            base_price = 100.0  # 基础价格
            if symbol == 'AAPL':
                base_price = 150.0
            elif symbol == 'GOOGL':
                base_price = 2500.0
            elif symbol == 'TSLA':
                base_price = 200.0
            elif symbol == 'MSFT':
                base_price = 300.0
            
            # 随机波动 ±2%
            change_percent = (random.random() - 0.5) * 0.04
            current_price = base_price * (1 + change_percent)
            
            market_data[symbol] = {
                'price': Decimal(str(round(current_price, 2))),
                'change': Decimal(str(round(current_price - base_price, 2))),
                'change_percent': change_percent,
                'volume': random.randint(1000000, 10000000),
                'timestamp': datetime.now()
            }
        
        return market_data
    
    def _should_notify_update(self, position: Position, old_price: Optional[Decimal], new_price: Decimal) -> bool:
        """判断是否需要通知更新"""
        if not old_price:
            return True
        
        # 价格变化超过0.1%时通知
        price_change_percent = abs(float(new_price - old_price) / float(old_price))
        if price_change_percent > 0.001:
            return True
        
        # 触发止损止盈时通知
        if position.check_stop_loss_trigger() or position.check_take_profit_trigger():
            return True
        
        return False
    
    async def _notify_position_updates(self, positions: List[Position]):
        """通知持仓更新"""
        # 按用户分组
        user_updates = {}
        for position in positions:
            user_id = position.user_id
            if user_id not in user_updates:
                user_updates[user_id] = []
            
            # 构建详细的持仓更新数据
            position_data = position.to_dict()
            position_data.update({
                'pnl_metrics': {
                    'unrealized_pnl': float(position.unrealized_pnl or 0),
                    'unrealized_pnl_percent': float(position.unrealized_pnl_percent or 0),
                    'daily_pnl': float(position.daily_pnl or 0),
                    'daily_pnl_percent': float(position.daily_pnl_percent or 0),
                    'market_value': float(position.market_value or 0),
                    'total_pnl': float(position.total_pnl or 0),
                    'return_rate': float(position.return_rate or 0)
                },
                'risk_metrics': getattr(position, 'risk_metrics', {}),
                'last_updated': position.updated_at.isoformat() if position.updated_at else None
            })
            
            user_updates[user_id].append(position_data)
        
        # 发送WebSocket通知
        for user_id, position_data in user_updates.items():
            await self.websocket_manager.send_to_user(
                user_id,
                {
                    'type': 'position_update',
                    'data': position_data,
                    'timestamp': datetime.now().isoformat()
                }
            )
    
    async def _notify_portfolio_updates(self, positions: List[Position]):
        """通知组合级别的盈亏更新"""
        # 按用户分组计算组合指标
        user_portfolios = {}
        for position in positions:
            user_id = position.user_id
            if user_id not in user_portfolios:
                user_portfolios[user_id] = []
            user_portfolios[user_id].append(position)
        
        # 为每个用户计算并发送组合更新
        for user_id, user_positions in user_portfolios.items():
            portfolio_metrics = await self._calculate_realtime_portfolio_metrics(user_positions)
            
            await self.websocket_manager.send_to_user(
                user_id,
                {
                    'type': 'portfolio_pnl_update',
                    'data': portfolio_metrics,
                    'timestamp': datetime.now().isoformat()
                }
            )
    
    async def _calculate_realtime_portfolio_metrics(self, positions: List[Position]) -> Dict:
        """计算实时组合指标"""
        try:
            if not positions:
                return {}
            
            # 基础指标
            total_market_value = sum(float(pos.market_value or 0) for pos in positions)
            total_cost_basis = sum(float(abs(pos.quantity * pos.average_cost)) for pos in positions)
            total_unrealized_pnl = sum(float(pos.unrealized_pnl or 0) for pos in positions)
            total_daily_pnl = sum(float(pos.daily_pnl or 0) for pos in positions)
            
            # 计算百分比
            total_unrealized_pnl_percent = (total_unrealized_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0
            total_daily_pnl_percent = (total_daily_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0
            
            # 持仓分布
            position_distribution = []
            for pos in positions:
                market_val = float(pos.market_value or 0)
                weight = (market_val / total_market_value * 100) if total_market_value > 0 else 0
                
                position_distribution.append({
                    'symbol': pos.symbol,
                    'weight': weight,
                    'market_value': market_val,
                    'pnl': float(pos.unrealized_pnl or 0),
                    'pnl_percent': float(pos.unrealized_pnl_percent or 0)
                })
            
            # 风险指标
            risk_metrics = self._calculate_portfolio_risk_metrics(positions)
            
            # 行业分布
            sector_distribution = self._calculate_sector_distribution(positions)
            
            return {
                'summary': {
                    'total_market_value': total_market_value,
                    'total_cost_basis': total_cost_basis,
                    'total_unrealized_pnl': total_unrealized_pnl,
                    'total_unrealized_pnl_percent': total_unrealized_pnl_percent,
                    'total_daily_pnl': total_daily_pnl,
                    'total_daily_pnl_percent': total_daily_pnl_percent,
                    'position_count': len(positions)
                },
                'position_distribution': position_distribution,
                'risk_metrics': risk_metrics,
                'sector_distribution': sector_distribution,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"计算实时组合指标失败: {e}")
            return {}
    
    def _calculate_portfolio_risk_metrics(self, positions: List[Position]) -> Dict:
        """计算组合风险指标"""
        try:
            if not positions:
                return {}
            
            # 计算总市值
            total_market_value = sum(float(pos.market_value or 0) for pos in positions)
            
            if total_market_value == 0:
                return {}
            
            # 计算最大持仓占比（集中度风险）
            max_position_weight = 0
            position_weights = []
            
            for pos in positions:
                weight = float(pos.market_value or 0) / total_market_value
                position_weights.append(weight)
                max_position_weight = max(max_position_weight, weight)
            
            # 赫芬达尔指数（集中度指标）
            herfindahl_index = sum(w**2 for w in position_weights)
            
            # 计算组合波动率（简化版本）
            portfolio_volatility = 0
            for pos in positions:
                risk_metrics = getattr(pos, 'risk_metrics', {})
                volatility = risk_metrics.get('volatility', 0)
                weight = float(pos.market_value or 0) / total_market_value
                portfolio_volatility += weight * volatility
            
            # VaR估算（简化）
            var_95 = total_market_value * 0.05  # 5% VaR
            
            # 风险评级
            risk_level = 'LOW'
            if max_position_weight > 0.4 or portfolio_volatility > 20:
                risk_level = 'HIGH'
            elif max_position_weight > 0.2 or portfolio_volatility > 10:
                risk_level = 'MEDIUM'
            
            return {
                'max_position_weight': max_position_weight * 100,
                'herfindahl_index': herfindahl_index,
                'portfolio_volatility': portfolio_volatility,
                'var_95': var_95,
                'risk_level': risk_level,
                'diversification_ratio': 1 / herfindahl_index if herfindahl_index > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"计算组合风险指标失败: {e}")
            return {}
    
    async def subscribe_user_positions(self, user_id: int):
        """订阅用户持仓更新"""
        db = SessionLocal()
        try:
            # 获取用户持仓
            positions = db.query(Position).filter(
                and_(
                    Position.user_id == user_id,
                    Position.status == PositionStatus.OPEN
                )
            ).all()
            
            # 添加到订阅列表
            self.user_positions[user_id] = positions
            
            # 订阅相关标的
            for position in positions:
                self.subscribed_symbols.add(position.symbol)
            
            logger.info(f"用户 {user_id} 订阅了 {len(positions)} 个持仓更新")
            
        finally:
            db.close()
    
    async def unsubscribe_user_positions(self, user_id: int):
        """取消订阅用户持仓更新"""
        if user_id in self.user_positions:
            del self.user_positions[user_id]
            logger.info(f"用户 {user_id} 取消订阅持仓更新")
    
    async def calculate_portfolio_metrics(self, user_id: int) -> Dict:
        """计算投资组合实时指标"""
        db = SessionLocal()
        try:
            position_service = PositionService(db)
            
            # 获取基础指标
            metrics = position_service.get_portfolio_summary(user_id)
            
            # 添加实时计算的指标
            positions = position_service.get_user_positions(user_id, PositionStatus.OPEN)
            
            if positions:
                # 计算今日盈亏
                today_pnl = self._calculate_today_pnl(positions)
                metrics['today_pnl'] = today_pnl
                
                # 计算风险指标
                risk_metrics = self._calculate_risk_metrics(positions)
                metrics['risk_metrics'] = risk_metrics
                
                # 计算持仓分布
                sector_distribution = self._calculate_sector_distribution(positions)
                metrics['sector_distribution'] = sector_distribution
            
            return metrics
            
        finally:
            db.close()
    
    def _calculate_today_pnl(self, positions: List[Position]) -> float:
        """计算今日盈亏"""
        today_pnl = 0.0
        today = datetime.now().date()
        
        for position in positions:
            # 这里需要获取今日开盘价，暂时使用模拟数据
            if position.current_price and position.average_cost:
                # 假设今日开盘价为平均成本的98%-102%
                import random
                open_price = position.average_cost * Decimal(str(0.98 + random.random() * 0.04))
                
                if position.position_type.value == 'LONG':
                    daily_change = position.current_price - open_price
                else:
                    daily_change = open_price - position.current_price
                
                today_pnl += float(position.quantity * daily_change)
        
        return today_pnl
    
    def _calculate_risk_metrics(self, positions: List[Position]) -> Dict:
        """计算风险指标"""
        if not positions:
            return {}
        
        # 计算总市值
        total_market_value = sum(
            float(pos.market_value or 0) for pos in positions
        )
        
        if total_market_value == 0:
            return {}
        
        # 计算集中度风险
        position_values = [float(pos.market_value or 0) for pos in positions]
        concentration_metrics = self.position_calculator.calculate_position_concentration(
            [{'market_value': val} for val in position_values]
        )
        
        # 计算VaR（简化版本）
        total_pnl = sum(float(pos.total_pnl) for pos in positions)
        var_95 = total_market_value * 0.05  # 简化的5% VaR
        
        return {
            'concentration': concentration_metrics,
            'var_95': var_95,
            'total_exposure': total_market_value,
            'leverage_ratio': total_market_value / max(total_market_value - abs(total_pnl), 1)
        }
    
    def _calculate_sector_distribution(self, positions: List[Position]) -> Dict:
        """计算行业分布（简化版本）"""
        # 简化的行业分类
        sector_map = {
            'AAPL': 'Technology',
            'GOOGL': 'Technology', 
            'MSFT': 'Technology',
            'TSLA': 'Automotive',
            'AMZN': 'E-commerce',
            'NVDA': 'Semiconductors'
        }
        
        sector_values = {}
        total_value = 0
        
        for position in positions:
            sector = sector_map.get(position.symbol, 'Other')
            value = float(position.market_value or 0)
            
            if sector not in sector_values:
                sector_values[sector] = 0
            sector_values[sector] += value
            total_value += value
        
        # 转换为百分比
        if total_value > 0:
            sector_distribution = {
                sector: (value / total_value) * 100
                for sector, value in sector_values.items()
            }
        else:
            sector_distribution = {}
        
        return sector_distribution
    
    async def check_risk_alerts(self, user_id: int) -> List[Dict]:
        """检查风险预警"""
        db = SessionLocal()
        try:
            position_service = PositionService(db)
            positions = position_service.get_user_positions(user_id, PositionStatus.OPEN)
            
            alerts = []
            
            for position in positions:
                # 检查止损止盈触发
                if position.check_stop_loss_trigger():
                    alerts.append({
                        'type': 'stop_loss_triggered',
                        'position_id': position.id,
                        'symbol': position.symbol,
                        'message': f'{position.symbol} 触发止损价格 {position.stop_loss_price}',
                        'severity': 'high',
                        'timestamp': datetime.now().isoformat()
                    })
                
                if position.check_take_profit_trigger():
                    alerts.append({
                        'type': 'take_profit_triggered',
                        'position_id': position.id,
                        'symbol': position.symbol,
                        'message': f'{position.symbol} 触发止盈价格 {position.take_profit_price}',
                        'severity': 'medium',
                        'timestamp': datetime.now().isoformat()
                    })
                
                # 检查大幅亏损
                if position.total_pnl < 0 and abs(position.return_rate) > 0.1:  # 亏损超过10%
                    alerts.append({
                        'type': 'large_loss',
                        'position_id': position.id,
                        'symbol': position.symbol,
                        'message': f'{position.symbol} 亏损超过10%，当前亏损率 {position.return_rate:.2%}',
                        'severity': 'medium',
                        'timestamp': datetime.now().isoformat()
                    })
            
            return alerts
            
        finally:
            db.close()
    
    async def get_position_trend_data(self, position_id: int, period: str = '1d') -> Dict:
        """获取持仓趋势数据"""
        db = SessionLocal()
        try:
            position = db.query(Position).filter(Position.id == position_id).first()
            if not position:
                return {}
            
            # 获取历史数据（这里使用模拟数据）
            trend_data = await self._generate_trend_data(position, period)
            
            return {
                'position_id': position_id,
                'symbol': position.symbol,
                'period': period,
                'data': trend_data,
                'generated_at': datetime.now().isoformat()
            }
            
        finally:
            db.close()
    
    async def _generate_trend_data(self, position: Position, period: str) -> List[Dict]:
        """生成趋势数据（模拟实现）"""
        import random
        from datetime import timedelta
        
        # 确定数据点数量
        if period == '1d':
            points = 24  # 24小时
            interval = timedelta(hours=1)
        elif period == '1w':
            points = 7   # 7天
            interval = timedelta(days=1)
        elif period == '1m':
            points = 30  # 30天
            interval = timedelta(days=1)
        else:
            points = 24
            interval = timedelta(hours=1)
        
        # 生成模拟数据
        trend_data = []
        base_price = float(position.current_price or position.average_cost)
        current_time = datetime.now() - interval * points
        
        for i in range(points):
            # 模拟价格波动
            price_change = (random.random() - 0.5) * 0.02  # ±1%波动
            price = base_price * (1 + price_change * (i / points))  # 添加趋势
            
            # 计算盈亏
            if position.position_type.value == 'LONG':
                pnl = float(position.quantity) * (price - float(position.average_cost))
            else:
                pnl = float(position.quantity) * (float(position.average_cost) - price)
            
            trend_data.append({
                'timestamp': current_time.isoformat(),
                'price': round(price, 2),
                'pnl': round(pnl, 2),
                'return_rate': round(pnl / float(position.total_cost), 4) if position.total_cost > 0 else 0
            })
            
            current_time += interval
        
        return trend_data

# 全局实例
realtime_service = PositionRealtimeService()