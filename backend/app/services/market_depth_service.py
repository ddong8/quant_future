"""
市场深度和价格提醒服务
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func
from decimal import Decimal

from ..models.market_data import (
    Symbol, Quote, DepthData, PriceAlert, MarketAnomaly
)
from ..models.user import User
from ..core.database import get_db

logger = logging.getLogger(__name__)

class MarketDepthService:
    """市场深度服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 深度数据管理 ====================
    
    def get_market_depth(self, symbol_code: str, depth_level: int = 20) -> Optional[Dict[str, Any]]:
        """获取市场深度数据"""
        try:
            # 获取标的信息
            symbol = self.db.query(Symbol).filter(Symbol.symbol == symbol_code).first()
            if not symbol:
                return None
            
            # 获取最新深度数据
            depth_data = self.db.query(DepthData).filter(
                DepthData.symbol_id == symbol.id
            ).order_by(desc(DepthData.snapshot_time)).first()
            
            if not depth_data:
                return None
            
            # 处理买卖盘数据
            bids = depth_data.bids[:depth_level] if depth_data.bids else []
            asks = depth_data.asks[:depth_level] if depth_data.asks else []
            
            # 计算累计量
            cumulative_bid_volume = 0
            cumulative_ask_volume = 0
            
            processed_bids = []
            for price, volume in bids:
                cumulative_bid_volume += volume
                processed_bids.append({
                    'price': float(price),
                    'volume': float(volume),
                    'cumulative_volume': float(cumulative_bid_volume),
                    'amount': float(price * volume)
                })
            
            processed_asks = []
            for price, volume in asks:
                cumulative_ask_volume += volume
                processed_asks.append({
                    'price': float(price),
                    'volume': float(volume),
                    'cumulative_volume': float(cumulative_ask_volume),
                    'amount': float(price * volume)
                })
            
            # 计算深度统计
            best_bid = processed_bids[0]['price'] if processed_bids else 0
            best_ask = processed_asks[0]['price'] if processed_asks else 0
            spread = best_ask - best_bid if best_bid and best_ask else 0
            spread_percent = (spread / best_ask * 100) if best_ask else 0
            
            return {
                'symbol': symbol_code,
                'timestamp': depth_data.snapshot_time.timestamp() * 1000,
                'bids': processed_bids,
                'asks': processed_asks,
                'statistics': {
                    'best_bid': best_bid,
                    'best_ask': best_ask,
                    'spread': spread,
                    'spread_percent': round(spread_percent, 4),
                    'total_bid_volume': float(depth_data.total_bid_quantity or 0),
                    'total_ask_volume': float(depth_data.total_ask_quantity or 0),
                    'bid_count': depth_data.bid_count or 0,
                    'ask_count': depth_data.ask_count or 0
                }
            }
            
        except Exception as e:
            logger.error(f"获取市场深度失败: {e}")
            return None
    
    def analyze_depth_imbalance(self, symbol_code: str) -> Dict[str, Any]:
        """分析深度失衡"""
        try:
            depth_data = self.get_market_depth(symbol_code)
            if not depth_data:
                return {}
            
            bids = depth_data['bids']
            asks = depth_data['asks']
            
            if not bids or not asks:
                return {}
            
            # 计算买卖盘力量对比
            total_bid_amount = sum(item['amount'] for item in bids[:10])  # 前10档
            total_ask_amount = sum(item['amount'] for item in asks[:10])  # 前10档
            
            total_amount = total_bid_amount + total_ask_amount
            bid_ratio = (total_bid_amount / total_amount * 100) if total_amount else 50
            ask_ratio = (total_ask_amount / total_amount * 100) if total_amount else 50
            
            # 判断失衡程度
            imbalance_ratio = abs(bid_ratio - ask_ratio)
            if imbalance_ratio > 30:
                imbalance_level = 'HIGH'
            elif imbalance_ratio > 15:
                imbalance_level = 'MEDIUM'
            else:
                imbalance_level = 'LOW'
            
            # 判断倾向
            if bid_ratio > ask_ratio + 10:
                bias = 'BUY_HEAVY'
            elif ask_ratio > bid_ratio + 10:
                bias = 'SELL_HEAVY'
            else:
                bias = 'BALANCED'
            
            return {
                'symbol': symbol_code,
                'bid_ratio': round(bid_ratio, 2),
                'ask_ratio': round(ask_ratio, 2),
                'imbalance_ratio': round(imbalance_ratio, 2),
                'imbalance_level': imbalance_level,
                'bias': bias,
                'total_bid_amount': total_bid_amount,
                'total_ask_amount': total_ask_amount
            }
            
        except Exception as e:
            logger.error(f"分析深度失衡失败: {e}")
            return {}
    
    # ==================== 价格提醒管理 ====================
    
    def create_price_alert(self, user_id: int, alert_data: Dict[str, Any]) -> Optional[PriceAlert]:
        """创建价格提醒"""
        try:
            # 验证标的是否存在
            symbol = self.db.query(Symbol).filter(Symbol.symbol == alert_data['symbol_code']).first()
            if not symbol:
                raise ValueError("标的不存在")
            
            # 创建提醒
            alert = PriceAlert(
                user_id=user_id,
                symbol_id=symbol.id,
                alert_type=alert_data['alert_type'],
                condition_value=Decimal(str(alert_data['condition_value'])),
                comparison_operator=alert_data['comparison_operator'],
                is_active=alert_data.get('is_active', True),
                is_repeatable=alert_data.get('is_repeatable', False),
                notification_methods=alert_data.get('notification_methods', ['websocket']),
                expires_at=alert_data.get('expires_at'),
                note=alert_data.get('note')
            )
            
            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)
            
            logger.info(f"创建价格提醒成功: {user_id}, {alert_data['symbol_code']}")
            return alert
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建价格提醒失败: {e}")
            return None
    
    def get_user_alerts(self, user_id: int, is_active: bool = None) -> List[Dict[str, Any]]:
        """获取用户的价格提醒"""
        try:
            query = self.db.query(PriceAlert).filter(PriceAlert.user_id == user_id)
            
            if is_active is not None:
                query = query.filter(PriceAlert.is_active == is_active)
            
            # 过滤未过期的提醒
            query = query.filter(
                or_(
                    PriceAlert.expires_at.is_(None),
                    PriceAlert.expires_at > datetime.now()
                )
            )
            
            alerts = query.order_by(desc(PriceAlert.created_at)).all()
            
            result = []
            for alert in alerts:
                result.append({
                    'id': alert.id,
                    'symbol': {
                        'id': alert.symbol.id,
                        'symbol': alert.symbol.symbol,
                        'name': alert.symbol.name
                    },
                    'alert_type': alert.alert_type,
                    'condition_value': float(alert.condition_value),
                    'comparison_operator': alert.comparison_operator,
                    'is_active': alert.is_active,
                    'is_repeatable': alert.is_repeatable,
                    'notification_methods': alert.notification_methods,
                    'triggered_at': alert.triggered_at.isoformat() if alert.triggered_at else None,
                    'triggered_price': float(alert.triggered_price) if alert.triggered_price else None,
                    'trigger_count': alert.trigger_count,
                    'expires_at': alert.expires_at.isoformat() if alert.expires_at else None,
                    'note': alert.note,
                    'created_at': alert.created_at.isoformat()
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取用户提醒失败: {e}")
            return []
    
    def update_price_alert(self, user_id: int, alert_id: int, update_data: Dict[str, Any]) -> bool:
        """更新价格提醒"""
        try:
            alert = self.db.query(PriceAlert).filter(
                and_(
                    PriceAlert.id == alert_id,
                    PriceAlert.user_id == user_id
                )
            ).first()
            
            if not alert:
                return False
            
            # 更新字段
            for key, value in update_data.items():
                if hasattr(alert, key) and key not in ['id', 'user_id', 'created_at']:
                    if key == 'condition_value' and value is not None:
                        setattr(alert, key, Decimal(str(value)))
                    else:
                        setattr(alert, key, value)
            
            alert.updated_at = datetime.now()
            self.db.commit()
            
            logger.info(f"更新价格提醒成功: {alert_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新价格提醒失败: {e}")
            return False
    
    def delete_price_alert(self, user_id: int, alert_id: int) -> bool:
        """删除价格提醒"""
        try:
            alert = self.db.query(PriceAlert).filter(
                and_(
                    PriceAlert.id == alert_id,
                    PriceAlert.user_id == user_id
                )
            ).first()
            
            if not alert:
                return False
            
            self.db.delete(alert)
            self.db.commit()
            
            logger.info(f"删除价格提醒成功: {alert_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除价格提醒失败: {e}")
            return False
    
    def check_price_alerts(self, symbol_code: str, current_price: float) -> List[Dict[str, Any]]:
        """检查价格提醒"""
        try:
            # 获取标的信息
            symbol = self.db.query(Symbol).filter(Symbol.symbol == symbol_code).first()
            if not symbol:
                return []
            
            # 获取活跃的提醒
            alerts = self.db.query(PriceAlert).filter(
                and_(
                    PriceAlert.symbol_id == symbol.id,
                    PriceAlert.is_active == True,
                    or_(
                        PriceAlert.expires_at.is_(None),
                        PriceAlert.expires_at > datetime.now()
                    )
                )
            ).all()
            
            triggered_alerts = []
            
            for alert in alerts:
                condition_value = float(alert.condition_value)
                operator = alert.comparison_operator
                
                # 检查触发条件
                triggered = False
                if operator == '>' and current_price > condition_value:
                    triggered = True
                elif operator == '<' and current_price < condition_value:
                    triggered = True
                elif operator == '>=' and current_price >= condition_value:
                    triggered = True
                elif operator == '<=' and current_price <= condition_value:
                    triggered = True
                elif operator == '=' and abs(current_price - condition_value) < 0.01:
                    triggered = True
                
                if triggered:
                    # 更新触发信息
                    alert.triggered_at = datetime.now()
                    alert.triggered_price = Decimal(str(current_price))
                    alert.trigger_count += 1
                    
                    # 如果不可重复触发，则停用
                    if not alert.is_repeatable:
                        alert.is_active = False
                    
                    triggered_alerts.append({
                        'alert_id': alert.id,
                        'user_id': alert.user_id,
                        'symbol_code': symbol_code,
                        'alert_type': alert.alert_type,
                        'condition_value': condition_value,
                        'triggered_price': current_price,
                        'notification_methods': alert.notification_methods,
                        'note': alert.note
                    })
            
            if triggered_alerts:
                self.db.commit()
            
            return triggered_alerts
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"检查价格提醒失败: {e}")
            return []
    
    # ==================== 市场异动监控 ====================
    
    def detect_market_anomalies(self, symbol_code: str) -> List[Dict[str, Any]]:
        """检测市场异动"""
        try:
            # 获取标的信息
            symbol = self.db.query(Symbol).filter(Symbol.symbol == symbol_code).first()
            if not symbol:
                return []
            
            # 获取最新报价
            latest_quote = self.db.query(Quote).filter(
                Quote.symbol_id == symbol.id
            ).order_by(desc(Quote.quote_time)).first()
            
            if not latest_quote:
                return []
            
            anomalies = []
            current_time = datetime.now()
            
            # 检测价格异动
            if latest_quote.change_percent:
                change_percent = float(latest_quote.change_percent)
                
                # 价格暴涨
                if change_percent > 10:
                    severity = 'CRITICAL' if change_percent > 20 else 'HIGH'
                    anomalies.append({
                        'type': 'PRICE_SPIKE',
                        'severity': severity,
                        'title': f'{symbol_code} 价格暴涨 {change_percent:.2f}%',
                        'description': f'价格从 {float(latest_quote.prev_close or 0):.2f} 涨至 {float(latest_quote.price):.2f}',
                        'price_change_percent': change_percent,
                        'trigger_price': float(latest_quote.price)
                    })
                
                # 价格暴跌
                elif change_percent < -10:
                    severity = 'CRITICAL' if change_percent < -20 else 'HIGH'
                    anomalies.append({
                        'type': 'PRICE_DROP',
                        'severity': severity,
                        'title': f'{symbol_code} 价格暴跌 {abs(change_percent):.2f}%',
                        'description': f'价格从 {float(latest_quote.prev_close or 0):.2f} 跌至 {float(latest_quote.price):.2f}',
                        'price_change_percent': change_percent,
                        'trigger_price': float(latest_quote.price)
                    })
            
            # 检测成交量异动
            if latest_quote.volume:
                # 获取历史平均成交量
                avg_volume_result = self.db.query(func.avg(Quote.volume)).filter(
                    and_(
                        Quote.symbol_id == symbol.id,
                        Quote.quote_time >= current_time - timedelta(days=30)
                    )
                ).scalar()
                
                if avg_volume_result:
                    avg_volume = float(avg_volume_result)
                    current_volume = float(latest_quote.volume)
                    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
                    
                    # 成交量暴增
                    if volume_ratio > 5:
                        severity = 'CRITICAL' if volume_ratio > 10 else 'HIGH'
                        anomalies.append({
                            'type': 'VOLUME_SURGE',
                            'severity': severity,
                            'title': f'{symbol_code} 成交量暴增 {volume_ratio:.1f}倍',
                            'description': f'成交量从平均 {avg_volume:.0f} 增至 {current_volume:.0f}',
                            'volume_ratio': volume_ratio,
                            'trigger_price': float(latest_quote.price)
                        })
            
            # 保存异动记录
            for anomaly in anomalies:
                market_anomaly = MarketAnomaly(
                    symbol_id=symbol.id,
                    anomaly_type=anomaly['type'],
                    severity=anomaly['severity'],
                    trigger_price=Decimal(str(anomaly['trigger_price'])),
                    price_change=Decimal(str(latest_quote.change or 0)),
                    price_change_percent=Decimal(str(anomaly.get('price_change_percent', 0))),
                    volume_ratio=Decimal(str(anomaly.get('volume_ratio', 1))),
                    title=anomaly['title'],
                    description=anomaly['description'],
                    detected_at=current_time
                )
                self.db.add(market_anomaly)
            
            if anomalies:
                self.db.commit()
            
            return anomalies
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"检测市场异动失败: {e}")
            return []
    
    def get_market_anomalies(self, hours: int = 24, severity: str = None) -> List[Dict[str, Any]]:
        """获取市场异动"""
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            
            query = self.db.query(MarketAnomaly).filter(
                MarketAnomaly.detected_at >= start_time
            )
            
            if severity:
                query = query.filter(MarketAnomaly.severity == severity)
            
            anomalies = query.order_by(desc(MarketAnomaly.detected_at)).all()
            
            result = []
            for anomaly in anomalies:
                result.append({
                    'id': anomaly.id,
                    'symbol': {
                        'id': anomaly.symbol.id,
                        'symbol': anomaly.symbol.symbol,
                        'name': anomaly.symbol.name
                    },
                    'anomaly_type': anomaly.anomaly_type,
                    'severity': anomaly.severity,
                    'title': anomaly.title,
                    'description': anomaly.description,
                    'trigger_price': float(anomaly.trigger_price or 0),
                    'price_change': float(anomaly.price_change or 0),
                    'price_change_percent': float(anomaly.price_change_percent or 0),
                    'volume_ratio': float(anomaly.volume_ratio or 0),
                    'detected_at': anomaly.detected_at.isoformat(),
                    'is_processed': anomaly.is_processed,
                    'is_notified': anomaly.is_notified
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取市场异动失败: {e}")
            return []