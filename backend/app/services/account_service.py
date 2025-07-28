"""
账户和资金管理服务
"""
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import logging

from ..models import TradingAccount, User, Order, Position, AccountTransaction
from ..models.enums import OrderStatus, TransactionType
from ..core.exceptions import NotFoundError, ValidationError, InsufficientFundsError
from ..core.dependencies import PaginationParams, SortParams

logger = logging.getLogger(__name__)


class AccountService:
    """账户和资金管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_account(self, user_id: int) -> Optional[TradingAccount]:
        """获取用户交易账户"""
        return self.db.query(TradingAccount).filter(
            TradingAccount.user_id == user_id
        ).first()
    
    def create_account(self, user_id: int, initial_balance: float = 0.0) -> TradingAccount:
        """创建交易账户"""
        try:
            # 检查是否已存在账户
            existing_account = self.get_account(user_id)
            if existing_account:
                raise ValidationError("用户已存在交易账户")
            
            # 创建新账户
            account = TradingAccount(
                user_id=user_id,
                account_id=self._generate_account_id(user_id),
                total_balance=Decimal(str(initial_balance)),
                available_balance=Decimal(str(initial_balance)),
                used_margin=Decimal('0'),
                frozen_balance=Decimal('0'),
                commission_paid=Decimal('0'),
                realized_pnl=Decimal('0'),
                unrealized_pnl=Decimal('0'),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(account)
            self.db.commit()
            self.db.refresh(account)
            
            # 记录初始资金流水
            if initial_balance > 0:
                self._record_transaction(
                    account_id=account.id,
                    transaction_type=TransactionType.DEPOSIT,
                    amount=Decimal(str(initial_balance)),
                    description="初始资金"
                )
            
            logger.info(f"创建交易账户成功: {account.account_id}")
            return account
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建交易账户失败: {e}")
            raise
    
    def update_balance(self, user_id: int, amount: Decimal, 
                      transaction_type: TransactionType, 
                      description: str = "") -> TradingAccount:
        """更新账户余额"""
        try:
            account = self.get_account(user_id)
            if not account:
                raise NotFoundError("交易账户不存在")
            
            # 检查余额是否足够（对于支出类型）
            if transaction_type in [TransactionType.WITHDRAW, TransactionType.COMMISSION, 
                                  TransactionType.LOSS] and amount > account.available_balance:
                raise InsufficientFundsError("可用余额不足")
            
            # 更新余额
            if transaction_type in [TransactionType.DEPOSIT, TransactionType.PROFIT]:
                account.total_balance += amount
                account.available_balance += amount
            elif transaction_type in [TransactionType.WITHDRAW, TransactionType.COMMISSION, 
                                    TransactionType.LOSS]:
                account.total_balance -= amount
                account.available_balance -= amount
            
            # 更新相关统计
            if transaction_type == TransactionType.COMMISSION:
                account.commission_paid += amount
            elif transaction_type == TransactionType.PROFIT:
                account.realized_pnl += amount
            elif transaction_type == TransactionType.LOSS:
                account.realized_pnl -= amount
            
            account.updated_at = datetime.utcnow()
            
            # 记录交易流水
            self._record_transaction(
                account_id=account.id,
                transaction_type=transaction_type,
                amount=amount,
                description=description
            )
            
            self.db.commit()
            self.db.refresh(account)
            
            logger.info(f"账户余额更新成功: {account.account_id}, 变动: {amount}")
            return account
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新账户余额失败: {e}")
            raise
    
    def freeze_balance(self, user_id: int, amount: Decimal, description: str = "") -> bool:
        """冻结资金"""
        try:
            account = self.get_account(user_id)
            if not account:
                raise NotFoundError("交易账户不存在")
            
            if amount > account.available_balance:
                raise InsufficientFundsError("可用余额不足")
            
            account.available_balance -= amount
            account.frozen_balance += amount
            account.updated_at = datetime.utcnow()
            
            # 记录冻结流水
            self._record_transaction(
                account_id=account.id,
                transaction_type=TransactionType.FREEZE,
                amount=amount,
                description=description
            )
            
            self.db.commit()
            
            logger.info(f"资金冻结成功: {account.account_id}, 金额: {amount}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"冻结资金失败: {e}")
            return False
    
    def unfreeze_balance(self, user_id: int, amount: Decimal, description: str = "") -> bool:
        """解冻资金"""
        try:
            account = self.get_account(user_id)
            if not account:
                raise NotFoundError("交易账户不存在")
            
            if amount > account.frozen_balance:
                raise ValidationError("解冻金额超过冻结余额")
            
            account.available_balance += amount
            account.frozen_balance -= amount
            account.updated_at = datetime.utcnow()
            
            # 记录解冻流水
            self._record_transaction(
                account_id=account.id,
                transaction_type=TransactionType.UNFREEZE,
                amount=amount,
                description=description
            )
            
            self.db.commit()
            
            logger.info(f"资金解冻成功: {account.account_id}, 金额: {amount}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"解冻资金失败: {e}")
            return False
    
    def update_margin(self, user_id: int, used_margin: Decimal):
        """更新保证金使用情况"""
        try:
            account = self.get_account(user_id)
            if not account:
                raise NotFoundError("交易账户不存在")
            
            # 计算保证金变化
            margin_change = used_margin - account.used_margin
            
            # 更新可用余额
            account.available_balance -= margin_change
            account.used_margin = used_margin
            account.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"保证金更新成功: {account.account_id}, 使用保证金: {used_margin}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新保证金失败: {e}")
            raise
    
    def update_unrealized_pnl(self, user_id: int, unrealized_pnl: Decimal):
        """更新未实现盈亏"""
        try:
            account = self.get_account(user_id)
            if not account:
                raise NotFoundError("交易账户不存在")
            
            account.unrealized_pnl = unrealized_pnl
            account.updated_at = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新未实现盈亏失败: {e}")
    
    def calculate_account_metrics(self, user_id: int) -> Dict[str, Any]:
        """计算账户指标"""
        try:
            account = self.get_account(user_id)
            if not account:
                return {}
            
            # 获取持仓信息
            positions = self.db.query(Position).filter(
                Position.user_id == user_id
            ).all()
            
            total_market_value = sum(float(pos.market_value or 0) for pos in positions)
            total_unrealized_pnl = sum(float(pos.unrealized_pnl or 0) for pos in positions)
            
            # 计算净值
            net_value = float(account.total_balance) + total_unrealized_pnl
            
            # 计算保证金比例
            margin_ratio = float(account.used_margin) / float(account.total_balance) if float(account.total_balance) > 0 else 0
            
            # 计算可用资金比例
            available_ratio = float(account.available_balance) / float(account.total_balance) if float(account.total_balance) > 0 else 0
            
            # 获取今日盈亏
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_pnl = self.db.query(func.sum(AccountTransaction.amount)).filter(
                and_(
                    AccountTransaction.account_id == account.id,
                    AccountTransaction.transaction_type.in_([TransactionType.PROFIT, TransactionType.LOSS]),
                    AccountTransaction.created_at >= today_start
                )
            ).scalar() or Decimal('0')
            
            return {
                'account_id': account.account_id,
                'total_balance': float(account.total_balance),
                'available_balance': float(account.available_balance),
                'used_margin': float(account.used_margin),
                'frozen_balance': float(account.frozen_balance),
                'realized_pnl': float(account.realized_pnl),
                'unrealized_pnl': total_unrealized_pnl,
                'net_value': net_value,
                'total_market_value': total_market_value,
                'margin_ratio': margin_ratio,
                'available_ratio': available_ratio,
                'today_pnl': float(today_pnl),
                'commission_paid': float(account.commission_paid),
                'position_count': len([pos for pos in positions if pos.quantity != 0]),
                'last_update': account.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"计算账户指标失败: {e}")
            return {}
    
    def get_transaction_history(self, user_id: int, 
                              transaction_type: Optional[TransactionType] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              pagination: Optional[PaginationParams] = None) -> Tuple[List[AccountTransaction], int]:
        """获取交易流水"""
        try:
            account = self.get_account(user_id)
            if not account:
                return [], 0
            
            query = self.db.query(AccountTransaction).filter(
                AccountTransaction.account_id == account.id
            )
            
            # 类型过滤
            if transaction_type:
                query = query.filter(AccountTransaction.transaction_type == transaction_type)
            
            # 时间范围过滤
            if start_date:
                query = query.filter(AccountTransaction.created_at >= start_date)
            
            if end_date:
                query = query.filter(AccountTransaction.created_at <= end_date)
            
            # 获取总数
            total = query.count()
            
            # 排序
            query = query.order_by(desc(AccountTransaction.created_at))
            
            # 分页
            if pagination:
                query = query.offset(pagination.offset).limit(pagination.page_size)
            
            transactions = query.all()
            
            return transactions, total
            
        except Exception as e:
            logger.error(f"获取交易流水失败: {e}")
            return [], 0
    
    def get_daily_balance_history(self, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """获取每日余额历史"""
        try:
            account = self.get_account(user_id)
            if not account:
                return []
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # 获取每日交易流水汇总
            daily_transactions = self.db.query(
                func.date(AccountTransaction.created_at).label('date'),
                func.sum(
                    func.case(
                        (AccountTransaction.transaction_type.in_([
                            TransactionType.DEPOSIT, TransactionType.PROFIT
                        ]), AccountTransaction.amount),
                        else_=-AccountTransaction.amount
                    )
                ).label('net_change')
            ).filter(
                and_(
                    AccountTransaction.account_id == account.id,
                    AccountTransaction.created_at >= start_date
                )
            ).group_by(
                func.date(AccountTransaction.created_at)
            ).order_by('date').all()
            
            # 构建每日余额历史
            history = []
            current_balance = float(account.total_balance)
            
            # 从最新日期开始倒推
            for i in range(days):
                date = (datetime.utcnow() - timedelta(days=i)).date()
                
                # 查找当日变化
                daily_change = 0
                for trans in daily_transactions:
                    if trans.date == date:
                        daily_change = float(trans.net_change or 0)
                        break
                
                # 如果是今天，使用当前余额
                if i == 0:
                    balance = current_balance
                else:
                    # 倒推前一天的余额
                    current_balance -= daily_change
                    balance = current_balance
                
                history.append({
                    'date': date.isoformat(),
                    'balance': balance,
                    'change': daily_change
                })
            
            # 反转列表，使其按时间正序
            history.reverse()
            
            return history
            
        except Exception as e:
            logger.error(f"获取每日余额历史失败: {e}")
            return []
    
    def calculate_risk_indicators(self, user_id: int) -> Dict[str, Any]:
        """计算风险指标"""
        try:
            account = self.get_account(user_id)
            if not account:
                return {}
            
            metrics = self.calculate_account_metrics(user_id)
            
            # 风险度计算
            risk_ratio = metrics.get('margin_ratio', 0)
            
            # 资金使用率
            fund_usage_ratio = 1 - metrics.get('available_ratio', 0)
            
            # 盈亏比
            total_pnl = metrics.get('realized_pnl', 0) + metrics.get('unrealized_pnl', 0)
            pnl_ratio = total_pnl / metrics.get('total_balance', 1) * 100
            
            # 风险等级评估
            risk_level = "LOW"
            if risk_ratio > 0.8:
                risk_level = "HIGH"
            elif risk_ratio > 0.6:
                risk_level = "MEDIUM"
            
            return {
                'risk_ratio': risk_ratio,
                'fund_usage_ratio': fund_usage_ratio,
                'pnl_ratio': pnl_ratio,
                'risk_level': risk_level,
                'margin_call_threshold': 0.8,  # 保证金追缴阈值
                'force_close_threshold': 0.9,  # 强制平仓阈值
                'available_margin': max(0, metrics.get('total_balance', 0) * 0.8 - metrics.get('used_margin', 0))
            }
            
        except Exception as e:
            logger.error(f"计算风险指标失败: {e}")
            return {}
    
    def _generate_account_id(self, user_id: int) -> str:
        """生成账户ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        return f"ACC_{user_id:06d}_{timestamp}"
    
    def _record_transaction(self, account_id: int, transaction_type: TransactionType, 
                          amount: Decimal, description: str = ""):
        """记录交易流水"""
        try:
            transaction = AccountTransaction(
                account_id=account_id,
                transaction_type=transaction_type,
                amount=amount,
                description=description,
                created_at=datetime.utcnow()
            )
            
            self.db.add(transaction)
            # 注意：这里不提交，由调用方统一提交
            
        except Exception as e:
            logger.error(f"记录交易流水失败: {e}")
            raise
    
    def deposit(self, user_id: int, amount: float, description: str = "充值") -> TradingAccount:
        """充值"""
        return self.update_balance(
            user_id=user_id,
            amount=Decimal(str(amount)),
            transaction_type=TransactionType.DEPOSIT,
            description=description
        )
    
    def withdraw(self, user_id: int, amount: float, description: str = "提现") -> TradingAccount:
        """提现"""
        return self.update_balance(
            user_id=user_id,
            amount=Decimal(str(amount)),
            transaction_type=TransactionType.WITHDRAW,
            description=description
        )
    
    def process_order_commission(self, user_id: int, commission: Decimal, order_id: str):
        """处理订单手续费"""
        self.update_balance(
            user_id=user_id,
            amount=commission,
            transaction_type=TransactionType.COMMISSION,
            description=f"订单手续费 - {order_id}"
        )
    
    def process_trade_pnl(self, user_id: int, pnl: Decimal, order_id: str):
        """处理交易盈亏"""
        if pnl > 0:
            self.update_balance(
                user_id=user_id,
                amount=pnl,
                transaction_type=TransactionType.PROFIT,
                description=f"交易盈利 - {order_id}"
            )
        elif pnl < 0:
            self.update_balance(
                user_id=user_id,
                amount=abs(pnl),
                transaction_type=TransactionType.LOSS,
                description=f"交易亏损 - {order_id}"
            )