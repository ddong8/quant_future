"""
市场数据服务
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func
from decimal import Decimal
from ..models.market_data import (
    Symbol, Quote, Kline, Trade, DepthData, DataProvider as DataProviderModel,
    DataSubscription, WatchlistItem, DataQualityMetric, MarketHours
)
from ..models.user import User

logger = logging.getLogger(__name__)

class MarketDataService:
    """市场数据服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 标的管理 ====================
    
    def create_symbol(self, symbol_data: Dict[str, Any]) -> Symbol:
        """创建交易标的"""
        try:
            symbol = Symbol(**symbol_data)
            self.db.add(symbol)
            self.db.commit()
            self.db.refresh(symbol)
            
            logger.info(f"创建交易标的成功: {symbol.symbol}")
            return symbol
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建交易标的失败: {e}")
            raise
    
    def get_symbol(self, symbol_code: str) -> Optional[Symbol]:
        """获取交易标的"""
        try:
            return self.db.query(Symbol).filter(
                Symbol.symbol == symbol_code.upper(),
                Symbol.is_active == True
            ).first()
            
        except Exception as e:
            logger.error(f"获取交易标的失败: {e}")
            raise
    
    def search_symbols(self, query: str, asset_types: List[str] = None, 
                      exchanges: List[str] = None, limit: int = 20) -> List[Symbol]:
        """搜索交易标的"""
        try:
            db_query = self.db.query(Symbol).filter(Symbol.is_active == True)
            
            # 关键词搜索
            if query:
                search_term = f"%{query.upper()}%"
                db_query = db_query.filter(
                    or_(
                        Symbol.symbol.ilike(search_term),
                        Symbol.name.ilike(search_term)
                    )
                )
            
            # 资产类型筛选
            if asset_types:
                db_query = db_query.filter(Symbol.asset_type.in_(asset_types))
            
            # 交易所筛选
            if exchanges:
                db_query = db_query.filter(Symbol.exchange.in_(exchanges))
            
            return db_query.limit(limit).all()
            
        except Exception as e:
            logger.error(f"搜索交易标的失败: {e}")
            raise
    
    def update_symbol(self, symbol_id: int, update_data: Dict[str, Any]) -> Optional[Symbol]:
        """更新交易标的"""
        try:
            symbol = self.db.query(Symbol).filter(Symbol.id == symbol_id).first()
            if not symbol:
                return None
            
            for key, value in update_data.items():
                if hasattr(symbol, key):
                    setattr(symbol, key, value)
            
            symbol.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(symbol)
            
            logger.info(f"更新交易标的成功: {symbol.symbol}")
            return symbol
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新交易标的失败: {e}")
            raise    
 
   # ==================== 实时报价管理 ====================
    
    def save_quote(self, quote_data: Dict[str, Any]) -> Quote:
        """保存实时报价"""
        try:
            quote = Quote(**quote_data)
            self.db.add(quote)
            self.db.commit()
            self.db.refresh(quote)
            
            return quote
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存实时报价失败: {e}")
            raise
    
    def get_latest_quote(self, symbol_id: int) -> Optional[Quote]:
        """获取最新报价"""
        try:
            return self.db.query(Quote).filter(
                Quote.symbol_id == symbol_id
            ).order_by(desc(Quote.quote_time)).first()
            
        except Exception as e:
            logger.error(f"获取最新报价失败: {e}")
            raise
    
    def get_quotes(self, symbol_ids: List[int], limit: int = 100) -> List[Quote]:
        """批量获取报价"""
        try:
            # 获取每个标的的最新报价
            subquery = self.db.query(
                Quote.symbol_id,
                func.max(Quote.quote_time).label('max_time')
            ).filter(
                Quote.symbol_id.in_(symbol_ids)
            ).group_by(Quote.symbol_id).subquery()
            
            return self.db.query(Quote).join(
                subquery,
                and_(
                    Quote.symbol_id == subquery.c.symbol_id,
                    Quote.quote_time == subquery.c.max_time
                )
            ).limit(limit).all()
            
        except Exception as e:
            logger.error(f"批量获取报价失败: {e}")
            raise
    
    # ==================== K线数据管理 ====================
    
    def save_kline(self, kline_data: Dict[str, Any]) -> Kline:
        """保存K线数据"""
        try:
            # 检查是否已存在相同的K线数据
            existing = self.db.query(Kline).filter(
                Kline.symbol_id == kline_data['symbol_id'],
                Kline.interval == kline_data['interval'],
                Kline.open_time == kline_data['open_time']
            ).first()
            
            if existing:
                # 更新现有数据
                for key, value in kline_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.now()
                kline = existing
            else:
                # 创建新数据
                kline = Kline(**kline_data)
                self.db.add(kline)
            
            self.db.commit()
            self.db.refresh(kline)
            
            return kline
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存K线数据失败: {e}")
            raise
    
    def get_klines(self, symbol_id: int, interval: str, 
                   start_time: datetime = None, end_time: datetime = None,
                   limit: int = 1000) -> List[Kline]:
        """获取K线数据"""
        try:
            query = self.db.query(Kline).filter(
                Kline.symbol_id == symbol_id,
                Kline.interval == interval
            )
            
            if start_time:
                query = query.filter(Kline.open_time >= start_time)
            
            if end_time:
                query = query.filter(Kline.open_time <= end_time)
            
            return query.order_by(Kline.open_time).limit(limit).all()
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            raise
    
    def get_latest_kline(self, symbol_id: int, interval: str) -> Optional[Kline]:
        """获取最新K线"""
        try:
            return self.db.query(Kline).filter(
                Kline.symbol_id == symbol_id,
                Kline.interval == interval
            ).order_by(desc(Kline.open_time)).first()
            
        except Exception as e:
            logger.error(f"获取最新K线失败: {e}")
            raise
    
    # ==================== 成交数据管理 ====================
    
    def save_trade(self, trade_data: Dict[str, Any]) -> Trade:
        """保存成交数据"""
        try:
            trade = Trade(**trade_data)
            self.db.add(trade)
            self.db.commit()
            self.db.refresh(trade)
            
            return trade
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存成交数据失败: {e}")
            raise
    
    def get_trades(self, symbol_id: int, start_time: datetime = None,
                   end_time: datetime = None, limit: int = 1000) -> List[Trade]:
        """获取成交数据"""
        try:
            query = self.db.query(Trade).filter(Trade.symbol_id == symbol_id)
            
            if start_time:
                query = query.filter(Trade.trade_time >= start_time)
            
            if end_time:
                query = query.filter(Trade.trade_time <= end_time)
            
            return query.order_by(desc(Trade.trade_time)).limit(limit).all()
            
        except Exception as e:
            logger.error(f"获取成交数据失败: {e}")
            raise
    
    # ==================== 深度数据管理 ====================
    
    def save_depth_data(self, depth_data: Dict[str, Any]) -> DepthData:
        """保存深度数据"""
        try:
            # 计算统计信息
            bids = depth_data.get('bids', [])
            asks = depth_data.get('asks', [])
            
            if bids and asks:
                depth_data['bid_count'] = len(bids)
                depth_data['ask_count'] = len(asks)
                depth_data['total_bid_quantity'] = sum(Decimal(str(bid[1])) for bid in bids)
                depth_data['total_ask_quantity'] = sum(Decimal(str(ask[1])) for ask in asks)
                
                best_bid = Decimal(str(bids[0][0])) if bids else Decimal('0')
                best_ask = Decimal(str(asks[0][0])) if asks else Decimal('0')
                
                if best_bid > 0 and best_ask > 0:
                    depth_data['spread'] = best_ask - best_bid
                    depth_data['spread_percent'] = (best_ask - best_bid) / best_ask * 100
            
            depth = DepthData(**depth_data)
            self.db.add(depth)
            self.db.commit()
            self.db.refresh(depth)
            
            return depth
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存深度数据失败: {e}")
            raise
    
    def get_latest_depth(self, symbol_id: int) -> Optional[DepthData]:
        """获取最新深度数据"""
        try:
            return self.db.query(DepthData).filter(
                DepthData.symbol_id == symbol_id
            ).order_by(desc(DepthData.snapshot_time)).first()
            
        except Exception as e:
            logger.error(f"获取最新深度数据失败: {e}")
            raise
    
    # ==================== 数据订阅管理 ====================
    
    def create_subscription(self, user_id: int, subscription_data: Dict[str, Any]) -> DataSubscription:
        """创建数据订阅"""
        try:
            # 检查是否已存在订阅
            existing = self.db.query(DataSubscription).filter(
                DataSubscription.user_id == user_id,
                DataSubscription.symbol_id == subscription_data['symbol_id']
            ).first()
            
            if existing:
                # 更新现有订阅
                for key, value in subscription_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.last_updated_at = datetime.now()
                subscription = existing
            else:
                # 创建新订阅
                subscription_data['user_id'] = user_id
                subscription = DataSubscription(**subscription_data)
                self.db.add(subscription)
            
            self.db.commit()
            self.db.refresh(subscription)
            
            logger.info(f"创建数据订阅成功: {user_id}, {subscription_data['symbol_id']}")
            return subscription
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建数据订阅失败: {e}")
            raise
    
    def get_user_subscriptions(self, user_id: int) -> List[DataSubscription]:
        """获取用户订阅"""
        try:
            return self.db.query(DataSubscription).filter(
                DataSubscription.user_id == user_id,
                DataSubscription.is_active == True
            ).all()
            
        except Exception as e:
            logger.error(f"获取用户订阅失败: {e}")
            raise
    
    def cancel_subscription(self, user_id: int, subscription_id: int) -> bool:
        """取消订阅"""
        try:
            subscription = self.db.query(DataSubscription).filter(
                DataSubscription.id == subscription_id,
                DataSubscription.user_id == user_id
            ).first()
            
            if not subscription:
                return False
            
            subscription.is_active = False
            self.db.commit()
            
            logger.info(f"取消数据订阅成功: {subscription_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"取消数据订阅失败: {e}")
            raise
    
    # ==================== 自选股管理 ====================
    
    def add_to_watchlist(self, user_id: int, watchlist_data: Dict[str, Any]) -> WatchlistItem:
        """添加到自选股"""
        try:
            # 检查是否已存在
            existing = self.db.query(WatchlistItem).filter(
                WatchlistItem.user_id == user_id,
                WatchlistItem.symbol_id == watchlist_data['symbol_id'],
                WatchlistItem.group_name == watchlist_data.get('group_name', '默认')
            ).first()
            
            if existing:
                return existing
            
            watchlist_data['user_id'] = user_id
            item = WatchlistItem(**watchlist_data)
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            
            logger.info(f"添加自选股成功: {user_id}, {watchlist_data['symbol_id']}")
            return item
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"添加自选股失败: {e}")
            raise
    
    def get_watchlist(self, user_id: int, group_name: str = None) -> List[WatchlistItem]:
        """获取自选股列表"""
        try:
            query = self.db.query(WatchlistItem).filter(
                WatchlistItem.user_id == user_id
            )
            
            if group_name:
                query = query.filter(WatchlistItem.group_name == group_name)
            
            return query.order_by(
                WatchlistItem.group_name,
                WatchlistItem.sort_order,
                WatchlistItem.added_at
            ).all()
            
        except Exception as e:
            logger.error(f"获取自选股列表失败: {e}")
            raise
    
    def remove_from_watchlist(self, user_id: int, item_id: int) -> bool:
        """从自选股移除"""
        try:
            item = self.db.query(WatchlistItem).filter(
                WatchlistItem.id == item_id,
                WatchlistItem.user_id == user_id
            ).first()
            
            if not item:
                return False
            
            self.db.delete(item)
            self.db.commit()
            
            logger.info(f"移除自选股成功: {item_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"移除自选股失败: {e}")
            raise
    
    # ==================== 数据质量管理 ====================
    
    def calculate_data_quality(self, provider: str, symbol_id: int = None,
                             data_type: str = None, date: datetime = None) -> Dict[str, Any]:
        """计算数据质量指标"""
        try:
            if not date:
                date = datetime.now().date()
            
            start_time = datetime.combine(date, datetime.min.time())
            end_time = datetime.combine(date, datetime.max.time())
            
            # 根据数据类型获取相应的数据
            if data_type == 'QUOTE':
                query = self.db.query(Quote).filter(
                    Quote.data_provider == provider,
                    Quote.quote_time >= start_time,
                    Quote.quote_time <= end_time
                )
                if symbol_id:
                    query = query.filter(Quote.symbol_id == symbol_id)
                
                records = query.all()
                
            elif data_type == 'KLINE':
                query = self.db.query(Kline).filter(
                    Kline.data_provider == provider,
                    Kline.open_time >= start_time,
                    Kline.open_time <= end_time
                )
                if symbol_id:
                    query = query.filter(Kline.symbol_id == symbol_id)
                
                records = query.all()
                
            else:
                records = []
            
            # 计算质量指标
            total_records = len(records)
            missing_records = 0  # 需要根据预期记录数计算
            duplicate_records = 0  # 需要检测重复记录
            error_records = 0  # 需要检测错误记录
            
            # 计算各项评分
            completeness_score = 100.0 if total_records > 0 else 0.0
            accuracy_score = 100.0 - (error_records / max(1, total_records) * 100)
            timeliness_score = 100.0  # 需要根据延迟计算
            consistency_score = 100.0 - (duplicate_records / max(1, total_records) * 100)
            
            overall_score = (completeness_score + accuracy_score + timeliness_score + consistency_score) / 4
            
            # 保存质量指标
            metric = DataQualityMetric(
                data_provider=provider,
                symbol_id=symbol_id,
                data_type=data_type,
                completeness_score=Decimal(str(completeness_score)),
                accuracy_score=Decimal(str(accuracy_score)),
                timeliness_score=Decimal(str(timeliness_score)),
                consistency_score=Decimal(str(consistency_score)),
                overall_score=Decimal(str(overall_score)),
                total_records=total_records,
                missing_records=missing_records,
                duplicate_records=duplicate_records,
                error_records=error_records,
                metric_date=start_time,
                start_time=start_time,
                end_time=end_time
            )
            
            self.db.add(metric)
            self.db.commit()
            self.db.refresh(metric)
            
            return {
                'completeness_score': completeness_score,
                'accuracy_score': accuracy_score,
                'timeliness_score': timeliness_score,
                'consistency_score': consistency_score,
                'overall_score': overall_score,
                'total_records': total_records,
                'missing_records': missing_records,
                'duplicate_records': duplicate_records,
                'error_records': error_records
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"计算数据质量指标失败: {e}")
            raise
    
    def get_data_quality_metrics(self, provider: str = None, symbol_id: int = None,
                               data_type: str = None, days: int = 7) -> List[DataQualityMetric]:
        """获取数据质量指标"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            query = self.db.query(DataQualityMetric).filter(
                DataQualityMetric.metric_date >= start_date
            )
            
            if provider:
                query = query.filter(DataQualityMetric.data_provider == provider)
            
            if symbol_id:
                query = query.filter(DataQualityMetric.symbol_id == symbol_id)
            
            if data_type:
                query = query.filter(DataQualityMetric.data_type == data_type)
            
            return query.order_by(desc(DataQualityMetric.metric_date)).all()
            
        except Exception as e:
            logger.error(f"获取数据质量指标失败: {e}")
            raise
    
    # ==================== 市场时间管理 ====================
    
    def get_market_hours(self, exchange: str) -> Optional[MarketHours]:
        """获取市场交易时间"""
        try:
            return self.db.query(MarketHours).filter(
                MarketHours.exchange == exchange,
                MarketHours.is_active == True
            ).first()
            
        except Exception as e:
            logger.error(f"获取市场交易时间失败: {e}")
            raise
    
    def is_market_open(self, exchange: str, check_time: datetime = None) -> bool:
        """检查市场是否开放"""
        try:
            if not check_time:
                check_time = datetime.now()
            
            market_hours = self.get_market_hours(exchange)
            if not market_hours:
                return False
            
            # 简化的市场开放检查逻辑
            # 实际应该考虑时区、节假日等因素
            current_time = check_time.time()
            open_time = datetime.strptime(market_hours.open_time, '%H:%M:%S').time()
            close_time = datetime.strptime(market_hours.close_time, '%H:%M:%S').time()
            
            return open_time <= current_time <= close_time
            
        except Exception as e:
            logger.error(f"检查市场开放状态失败: {e}")
            return False
    
    # ==================== 数据提供商管理 ====================
    
    def create_data_provider(self, provider_data: Dict[str, Any]) -> DataProviderModel:
        """创建数据提供商"""
        try:
            provider = DataProviderModel(**provider_data)
            self.db.add(provider)
            self.db.commit()
            self.db.refresh(provider)
            
            logger.info(f"创建数据提供商成功: {provider.name}")
            return provider
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建数据提供商失败: {e}")
            raise
    
    def get_data_providers(self, active_only: bool = True) -> List[DataProviderModel]:
        """获取数据提供商列表"""
        try:
            query = self.db.query(DataProviderModel)
            
            if active_only:
                query = query.filter(DataProviderModel.is_active == True)
            
            return query.all()
            
        except Exception as e:
            logger.error(f"获取数据提供商列表失败: {e}")
            raise
    
    def update_provider_status(self, provider_name: str, is_connected: bool,
                             error_message: str = None) -> bool:
        """更新提供商状态"""
        try:
            provider = self.db.query(DataProviderModel).filter(
                DataProviderModel.name == provider_name
            ).first()
            
            if not provider:
                return False
            
            if is_connected:
                provider.last_connected_at = datetime.now()
                provider.error_count = 0
                provider.last_error = None
            else:
                provider.error_count += 1
                provider.last_error = error_message
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新提供商状态失败: {e}")
            raise 
   # ==================== 行情展示功能 ====================
    
    def get_latest_quotes(self, symbol_codes: List[str]) -> List[Dict[str, Any]]:
        """获取多个标的的最新行情"""
        try:
            quotes = []
            for symbol_code in symbol_codes:
                quote = self.get_symbol_quote(symbol_code)
                if quote:
                    quotes.append(quote)
            return quotes
        except Exception as e:
            logger.error(f"获取最新行情失败: {e}")
            return []
    
    def get_symbol_quote(self, symbol_code: str) -> Optional[Dict[str, Any]]:
        """获取单个标的的最新行情"""
        try:
            # 获取标的信息
            symbol = self.db.query(Symbol).filter(Symbol.symbol == symbol_code.upper()).first()
            if not symbol:
                return None
            
            # 获取最新报价
            latest_quote = self.db.query(Quote).filter(
                Quote.symbol_id == symbol.id
            ).order_by(desc(Quote.quote_time)).first()
            
            if not latest_quote:
                return None
            
            # 构建响应数据
            return {
                "id": latest_quote.id,
                "symbol_id": symbol.id,
                "symbol": {
                    "id": symbol.id,
                    "symbol": symbol.symbol,
                    "name": symbol.name,
                    "exchange": symbol.exchange,
                    "market": symbol.market,
                    "asset_type": symbol.asset_type,
                    "currency": symbol.currency,
                    "is_tradable": symbol.is_tradable,
                    "is_active": symbol.is_active
                },
                "price": float(latest_quote.price),
                "bid_price": float(latest_quote.bid_price) if latest_quote.bid_price else None,
                "ask_price": float(latest_quote.ask_price) if latest_quote.ask_price else None,
                "bid_size": float(latest_quote.bid_size) if latest_quote.bid_size else None,
                "ask_size": float(latest_quote.ask_size) if latest_quote.ask_size else None,
                "change": float(latest_quote.change) if latest_quote.change else None,
                "change_percent": float(latest_quote.change_percent) if latest_quote.change_percent else None,
                "volume": float(latest_quote.volume) if latest_quote.volume else None,
                "turnover": float(latest_quote.turnover) if latest_quote.turnover else None,
                "open_price": float(latest_quote.open_price) if latest_quote.open_price else None,
                "high_price": float(latest_quote.high_price) if latest_quote.high_price else None,
                "low_price": float(latest_quote.low_price) if latest_quote.low_price else None,
                "prev_close": float(latest_quote.prev_close) if latest_quote.prev_close else None,
                "data_provider": latest_quote.data_provider,
                "data_status": latest_quote.data_status,
                "delay_seconds": latest_quote.delay_seconds,
                "quote_time": latest_quote.quote_time.isoformat(),
                "received_at": latest_quote.received_at.isoformat()
            }
        except Exception as e:
            logger.error(f"获取标的行情失败: {symbol_code}, {e}")
            return None
    
    def get_popular_quotes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取热门标的行情"""
        try:
            # 获取有最新报价的活跃标的
            subquery = self.db.query(
                Quote.symbol_id,
                func.max(Quote.quote_time).label('latest_time')
            ).group_by(Quote.symbol_id).subquery()
            
            # 获取最新报价及对应的标的信息
            popular_quotes = self.db.query(Quote, Symbol).join(
                Symbol, Quote.symbol_id == Symbol.id
            ).join(
                subquery,
                and_(
                    Quote.symbol_id == subquery.c.symbol_id,
                    Quote.quote_time == subquery.c.latest_time
                )
            ).filter(
                Symbol.is_active == True,
                Symbol.is_tradable == True
            ).order_by(
                desc(Quote.volume)
            ).limit(limit).all()
            
            quotes = []
            for quote, symbol in popular_quotes:
                quotes.append({
                    "id": quote.id,
                    "symbol_id": symbol.id,
                    "symbol": {
                        "id": symbol.id,
                        "symbol": symbol.symbol,
                        "name": symbol.name,
                        "exchange": symbol.exchange,
                        "market": symbol.market,
                        "asset_type": symbol.asset_type,
                        "currency": symbol.currency,
                        "is_tradable": symbol.is_tradable,
                        "is_active": symbol.is_active
                    },
                    "price": float(quote.price),
                    "bid_price": float(quote.bid_price) if quote.bid_price else None,
                    "ask_price": float(quote.ask_price) if quote.ask_price else None,
                    "bid_size": float(quote.bid_size) if quote.bid_size else None,
                    "ask_size": float(quote.ask_size) if quote.ask_size else None,
                    "change": float(quote.change) if quote.change else None,
                    "change_percent": float(quote.change_percent) if quote.change_percent else None,
                    "volume": float(quote.volume) if quote.volume else None,
                    "turnover": float(quote.turnover) if quote.turnover else None,
                    "open_price": float(quote.open_price) if quote.open_price else None,
                    "high_price": float(quote.high_price) if quote.high_price else None,
                    "low_price": float(quote.low_price) if quote.low_price else None,
                    "prev_close": float(quote.prev_close) if quote.prev_close else None,
                    "data_provider": quote.data_provider,
                    "data_status": quote.data_status,
                    "delay_seconds": quote.delay_seconds,
                    "quote_time": quote.quote_time.isoformat(),
                    "received_at": quote.received_at.isoformat()
                })
            
            return quotes
        except Exception as e:
            logger.error(f"获取热门行情失败: {e}")
            return []