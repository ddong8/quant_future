"""
账户管理服务
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from decimal import Decimal
import uuid

from ..models.account import Account, Transaction, AccountBalance, AccountType, AccountStatus, TransactionType, TransactionStatus
from ..models.user import User
from ..models.position import Position
from ..models.order import Order
from ..core.database import get_db

logger = logging.getLogger(__name__)


class AccountService:
    """账户管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 账户管理 ====================
    
    def create_account(self, user_id: int, account_data: Dict[str, Any]) -> Account:
        """创建账户"""
        try:
            # 生成账户号
            account_number = self._generate_account_number()
            
            account = Account(
                user_id=user_id,
                account_number=account_number,
                account_name=account_data.get('account_name', f'账户-{account_number}'),
                account_type=AccountType(account_data.get('account_type', 'CASH')),
                base_currency=account_data.get('base_currency', 'USD'),
                risk_level=account_data.get('risk_level', 'MEDIUM'),
                settings=account_data.get('settings', {})
            )
            
            self.db.add(account)
            self.db.commit()
            self.db.refresh(account)
            
            logger.info(f"创建账户成功: {account.account_number} (用户: {user_id})")
            return account
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建账户失败: {e}")
            raise
    
    def get_account(self, account_id: int, user_id: Optional[int] = None) -> Optional[Account]:
        """获取账户"""
        query = self.db.query(Account).filter(Account.id == account_id)
        
        if user_id is not None:
            query = query.filter(Account.user_id == user_id)
        
        return query.first()
    
    def get_user_accounts(self, user_id: int, status: Optional[AccountStatus] = None) -> List[Account]:
        """获取用户账户列表"""
        query = self.db.query(Account).filter(Account.user_id == user_id)
        
        if status is not None:
            query = query.filter(Account.status == status)
        
        return query.order_by(Account.created_at).all()
    
    def update_account(self, account_id: int, user_id: int, update_data: Dict[str, Any]) -> Optional[Account]:
        """更新账户信息"""
        try:
            account = self.get_account(account_id, user_id)
            if not account:
                return None
            
            # 更新允许的字段
            allowed_fields = ['account_name', 'risk_level', 'settings', 'max_position_value', 'max_daily_loss']
            
            for field, value in update_data.items():
                if field in allowed_fields and hasattr(account, field):
                    setattr(account, field, value)
            
            self.db.commit()
            self.db.refresh(account)
            
            logger.info(f"更新账户成功: {account.account_number}")
            return account
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新账户失败: {e}")
            raise
    
    def close_account(self, account_id: int, user_id: int) -> bool:
        """关闭账户"""
        try:
            account = self.get_account(account_id, user_id)
            if not account:
                return False
            
            # 检查是否可以关闭
            if not self._can_close_account(account):
                raise ValueError("账户有未平仓位或未完成订单，无法关闭")
            
            account.status = AccountStatus.CLOSED
            self.db.commit()
            
            logger.info(f"关闭账户成功: {account.account_number}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"关闭账户失败: {e}")
            raise
    
    # ==================== 资金管理 ====================
    
    def deposit(self, account_id: int, amount: Decimal, description: str = None, 
               reference_id: str = None) -> Transaction:
        """入金"""
        try:
            account = self.get_account(account_id)
            if not account:
                raise ValueError("账户不存在")
            
            if account.status != AccountStatus.ACTIVE:
                raise ValueError("账户状态不允许入金")
            
            if amount <= 0:
                raise ValueError("入金金额必须大于0")
            
            # 记录交易前余额
            balance_before = account.cash_balance
            
            # 创建交易记录
            transaction = Transaction(
                account_id=account_id,
                transaction_id=self._generate_transaction_id(),
                transaction_type=TransactionType.DEPOSIT,
                amount=amount,
                currency=account.base_currency,
                balance_before=balance_before,
                balance_after=balance_before + amount,
                description=description or f"入金 {amount}",
                reference_id=reference_id,
                status=TransactionStatus.COMPLETED
            )
            
            # 更新账户余额
            account.add_cash(amount)
            account.total_deposits += amount
            account.update_balances()
            
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
            
            logger.info(f"入金成功: 账户 {account.account_number}, 金额 {amount}")
            return transaction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"入金失败: {e}")
            raise
    
    def withdraw(self, account_id: int, amount: Decimal, description: str = None,
                reference_id: str = None) -> Transaction:
        """出金"""
        try:
            account = self.get_account(account_id)
            if not account:
                raise ValueError("账户不存在")
            
            if account.status != AccountStatus.ACTIVE:
                raise ValueError("账户状态不允许出金")
            
            if amount <= 0:
                raise ValueError("出金金额必须大于0")
            
            if account.available_cash < amount:
                raise ValueError("可用资金不足")
            
            # 记录交易前余额
            balance_before = account.cash_balance
            
            # 创建交易记录
            transaction = Transaction(
                account_id=account_id,
                transaction_id=self._generate_transaction_id(),
                transaction_type=TransactionType.WITHDRAWAL,
                amount=-amount,  # 出金为负数
                currency=account.base_currency,
                balance_before=balance_before,
                balance_after=balance_before - amount,
                description=description or f"出金 {amount}",
                reference_id=reference_id,
                status=TransactionStatus.COMPLETED
            )
            
            # 更新账户余额
            account.subtract_cash(amount)
            account.total_withdrawals += amount
            account.update_balances()
            
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
            
            logger.info(f"出金成功: 账户 {account.account_number}, 金额 {amount}")
            return transaction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"出金失败: {e}")
            raise   
 
    def freeze_funds(self, account_id: int, amount: Decimal, description: str = None) -> bool:
        """冻结资金"""
        try:
            account = self.get_account(account_id)
            if not account:
                return False
            
            if not account.freeze_cash(amount):
                return False
            
            # 记录冻结交易
            transaction = Transaction(
                account_id=account_id,
                transaction_id=self._generate_transaction_id(),
                transaction_type=TransactionType.ADJUSTMENT,
                amount=Decimal('0'),  # 冻结不改变总余额
                currency=account.base_currency,
                balance_before=account.cash_balance,
                balance_after=account.cash_balance,
                description=description or f"冻结资金 {amount}",
                status=TransactionStatus.COMPLETED,
                metadata={'action': 'freeze', 'amount': float(amount)}
            )
            
            self.db.add(transaction)
            self.db.commit()
            
            logger.info(f"冻结资金成功: 账户 {account.account_number}, 金额 {amount}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"冻结资金失败: {e}")
            return False
    
    def unfreeze_funds(self, account_id: int, amount: Decimal, description: str = None) -> bool:
        """解冻资金"""
        try:
            account = self.get_account(account_id)
            if not account:
                return False
            
            if not account.unfreeze_cash(amount):
                return False
            
            # 记录解冻交易
            transaction = Transaction(
                account_id=account_id,
                transaction_id=self._generate_transaction_id(),
                transaction_type=TransactionType.ADJUSTMENT,
                amount=Decimal('0'),  # 解冻不改变总余额
                currency=account.base_currency,
                balance_before=account.cash_balance,
                balance_after=account.cash_balance,
                description=description or f"解冻资金 {amount}",
                status=TransactionStatus.COMPLETED,
                metadata={'action': 'unfreeze', 'amount': float(amount)}
            )
            
            self.db.add(transaction)
            self.db.commit()
            
            logger.info(f"解冻资金成功: 账户 {account.account_number}, 金额 {amount}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"解冻资金失败: {e}")
            return False
    
    def record_trade_transaction(self, account_id: int, order_id: int, position_id: int,
                               amount: Decimal, fee: Decimal = Decimal('0'), 
                               symbol: str = None, description: str = None) -> Transaction:
        """记录交易流水"""
        try:
            account = self.get_account(account_id)
            if not account:
                raise ValueError("账户不存在")
            
            # 确定交易类型
            transaction_type = TransactionType.TRADE_BUY if amount < 0 else TransactionType.TRADE_SELL
            
            # 记录交易前余额
            balance_before = account.cash_balance
            
            # 创建交易记录
            transaction = Transaction(
                account_id=account_id,
                transaction_id=self._generate_transaction_id(),
                transaction_type=transaction_type,
                amount=amount,
                currency=account.base_currency,
                balance_before=balance_before,
                balance_after=balance_before + amount,
                order_id=order_id,
                position_id=position_id,
                symbol=symbol,
                description=description or f"交易 {symbol}",
                fee_amount=fee,
                status=TransactionStatus.COMPLETED
            )
            
            # 更新账户余额
            if amount > 0:
                account.add_cash(amount, update_total=False)  # 卖出收到现金
            else:
                account.subtract_cash(abs(amount), update_total=False)  # 买入支付现金
            
            # 扣除手续费
            if fee > 0:
                account.subtract_cash(fee, update_total=False)
                account.total_fees += fee
            
            account.update_balances()
            
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
            
            logger.info(f"记录交易流水成功: 账户 {account.account_number}, 金额 {amount}")
            return transaction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"记录交易流水失败: {e}")
            raise
    
    # ==================== 余额计算和更新 ====================
    
    def calculate_account_totals(self, account_id: int) -> Dict[str, Decimal]:
        """计算账户总资产"""
        try:
            account = self.get_account(account_id)
            if not account:
                return {}
            
            # 获取持仓市值
            positions = self.db.query(Position).filter(
                Position.account_id == account_id,
                Position.status == 'OPEN'
            ).all()
            
            total_market_value = sum(float(pos.market_value or 0) for pos in positions)
            total_unrealized_pnl = sum(float(pos.unrealized_pnl or 0) for pos in positions)
            
            # 计算总资产
            total_assets = account.cash_balance + Decimal(str(total_market_value))
            
            # 更新账户
            account.market_value = Decimal(str(total_market_value))
            account.unrealized_pnl = Decimal(str(total_unrealized_pnl))
            account.total_assets = total_assets
            account.update_balances()
            
            self.db.commit()
            
            return {
                'cash_balance': account.cash_balance,
                'market_value': account.market_value,
                'total_assets': account.total_assets,
                'unrealized_pnl': account.unrealized_pnl,
                'net_assets': account.net_assets
            }
            
        except Exception as e:
            logger.error(f"计算账户总资产失败: {e}")
            return {}
    
    def update_account_pnl(self, account_id: int) -> bool:
        """更新账户盈亏"""
        try:
            account = self.get_account(account_id)
            if not account:
                return False
            
            # 计算已实现盈亏（从交易记录）
            realized_pnl = self.db.query(func.sum(Transaction.amount)).filter(
                Transaction.account_id == account_id,
                Transaction.transaction_type.in_([TransactionType.TRADE_BUY, TransactionType.TRADE_SELL]),
                Transaction.status == TransactionStatus.COMPLETED
            ).scalar() or Decimal('0')
            
            # 计算未实现盈亏（从持仓）
            positions = self.db.query(Position).filter(
                Position.account_id == account_id,
                Position.status == 'OPEN'
            ).all()
            
            unrealized_pnl = sum(float(pos.unrealized_pnl or 0) for pos in positions)
            
            # 更新账户盈亏
            account.realized_pnl = realized_pnl
            account.unrealized_pnl = Decimal(str(unrealized_pnl))
            account.update_balances()
            
            self.db.commit()
            
            logger.debug(f"更新账户盈亏成功: {account.account_number}")
            return True
            
        except Exception as e:
            logger.error(f"更新账户盈亏失败: {e}")
            return False
    
    # ==================== 交易流水管理 ====================
    
    def get_transactions(self, account_id: int, transaction_type: Optional[TransactionType] = None,
                        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                        skip: int = 0, limit: int = 100) -> List[Transaction]:
        """获取交易流水"""
        query = self.db.query(Transaction).filter(Transaction.account_id == account_id)
        
        if transaction_type is not None:
            query = query.filter(Transaction.transaction_type == transaction_type)
        
        if start_date is not None:
            query = query.filter(Transaction.transaction_time >= start_date)
        
        if end_date is not None:
            query = query.filter(Transaction.transaction_time <= end_date)
        
        return query.order_by(desc(Transaction.transaction_time)).offset(skip).limit(limit).all()
    
    def get_transaction_summary(self, account_id: int, period: str = 'month') -> Dict[str, Any]:
        """获取交易汇总"""
        try:
            # 确定时间范围
            end_date = datetime.now()
            if period == 'day':
                start_date = end_date - timedelta(days=1)
            elif period == 'week':
                start_date = end_date - timedelta(weeks=1)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
            
            # 查询交易记录
            transactions = self.get_transactions(
                account_id=account_id,
                start_date=start_date,
                end_date=end_date,
                limit=1000
            )
            
            # 统计汇总
            summary = {
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_transactions': len(transactions),
                'deposits': Decimal('0'),
                'withdrawals': Decimal('0'),
                'trade_amount': Decimal('0'),
                'fees': Decimal('0'),
                'by_type': {}
            }
            
            for transaction in transactions:
                transaction_type = transaction.transaction_type.value
                
                if transaction_type not in summary['by_type']:
                    summary['by_type'][transaction_type] = {
                        'count': 0,
                        'amount': Decimal('0')
                    }
                
                summary['by_type'][transaction_type]['count'] += 1
                summary['by_type'][transaction_type]['amount'] += transaction.amount
                
                # 分类统计
                if transaction.transaction_type == TransactionType.DEPOSIT:
                    summary['deposits'] += transaction.amount
                elif transaction.transaction_type == TransactionType.WITHDRAWAL:
                    summary['withdrawals'] += abs(transaction.amount)
                elif transaction.transaction_type in [TransactionType.TRADE_BUY, TransactionType.TRADE_SELL]:
                    summary['trade_amount'] += abs(transaction.amount)
                
                summary['fees'] += transaction.fee_amount
            
            # 转换为float以便JSON序列化
            for key in ['deposits', 'withdrawals', 'trade_amount', 'fees']:
                summary[key] = float(summary[key])
            
            for type_data in summary['by_type'].values():
                type_data['amount'] = float(type_data['amount'])
            
            return summary
            
        except Exception as e:
            logger.error(f"获取交易汇总失败: {e}")
            return {}
    
    # ==================== 账户余额快照 ====================
    
    def create_balance_snapshot(self, account_id: int, snapshot_type: str = 'daily') -> AccountBalance:
        """创建余额快照"""
        try:
            account = self.get_account(account_id)
            if not account:
                raise ValueError("账户不存在")
            
            # 更新账户总资产
            self.calculate_account_totals(account_id)
            
            # 计算当日盈亏
            today = datetime.now().date()
            yesterday_snapshot = self.db.query(AccountBalance).filter(
                AccountBalance.account_id == account_id,
                func.date(AccountBalance.snapshot_date) == today - timedelta(days=1)
            ).first()
            
            daily_pnl = Decimal('0')
            if yesterday_snapshot:
                daily_pnl = account.total_pnl - yesterday_snapshot.total_pnl
            
            # 创建快照
            snapshot = AccountBalance(
                account_id=account_id,
                snapshot_date=datetime.now(),
                snapshot_type=snapshot_type,
                cash_balance=account.cash_balance,
                available_cash=account.available_cash,
                frozen_cash=account.frozen_cash,
                total_assets=account.total_assets,
                total_liabilities=account.total_liabilities,
                net_assets=account.net_assets,
                market_value=account.market_value,
                realized_pnl=account.realized_pnl,
                unrealized_pnl=account.unrealized_pnl,
                total_pnl=account.total_pnl,
                daily_pnl=daily_pnl,
                total_deposits=account.total_deposits,
                total_withdrawals=account.total_withdrawals,
                total_fees=account.total_fees
            )
            
            self.db.add(snapshot)
            self.db.commit()
            self.db.refresh(snapshot)
            
            logger.info(f"创建余额快照成功: 账户 {account.account_number}")
            return snapshot
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建余额快照失败: {e}")
            raise
    
    def get_balance_history(self, account_id: int, days: int = 30) -> List[AccountBalance]:
        """获取余额历史"""
        start_date = datetime.now() - timedelta(days=days)
        
        return self.db.query(AccountBalance).filter(
            AccountBalance.account_id == account_id,
            AccountBalance.snapshot_date >= start_date
        ).order_by(AccountBalance.snapshot_date).all()
    
    # ==================== 账户一致性检查 ====================
    
    def check_account_consistency(self, account_id: int) -> Dict[str, Any]:
        """检查账户一致性"""
        try:
            account = self.get_account(account_id)
            if not account:
                return {'error': '账户不存在'}
            
            issues = []
            
            # 检查现金余额一致性
            if account.cash_balance != account.available_cash + account.frozen_cash:
                issues.append({
                    'type': 'cash_balance_mismatch',
                    'message': f'现金余额不一致: 总额={account.cash_balance}, 可用+冻结={account.available_cash + account.frozen_cash}'
                })
            
            # 检查总资产计算
            expected_total_assets = account.cash_balance + account.market_value
            if abs(account.total_assets - expected_total_assets) > Decimal('0.01'):
                issues.append({
                    'type': 'total_assets_mismatch',
                    'message': f'总资产计算不一致: 记录={account.total_assets}, 计算={expected_total_assets}'
                })
            
            # 检查净资产计算
            expected_net_assets = account.total_assets - account.total_liabilities
            if abs(account.net_assets - expected_net_assets) > Decimal('0.01'):
                issues.append({
                    'type': 'net_assets_mismatch',
                    'message': f'净资产计算不一致: 记录={account.net_assets}, 计算={expected_net_assets}'
                })
            
            # 检查总盈亏计算
            expected_total_pnl = account.realized_pnl + account.unrealized_pnl
            if abs(account.total_pnl - expected_total_pnl) > Decimal('0.01'):
                issues.append({
                    'type': 'total_pnl_mismatch',
                    'message': f'总盈亏计算不一致: 记录={account.total_pnl}, 计算={expected_total_pnl}'
                })
            
            return {
                'account_id': account_id,
                'is_consistent': len(issues) == 0,
                'issues': issues,
                'checked_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"检查账户一致性失败: {e}")
            return {'error': str(e)}
    
    def reconcile_account(self, account_id: int) -> bool:
        """对账修复"""
        try:
            account = self.get_account(account_id)
            if not account:
                return False
            
            # 重新计算所有余额
            self.calculate_account_totals(account_id)
            self.update_account_pnl(account_id)
            
            # 修复现金余额一致性
            if account.available_cash < 0:
                account.available_cash = Decimal('0')
            
            if account.frozen_cash < 0:
                account.frozen_cash = Decimal('0')
            
            # 确保现金余额一致性
            total_cash = account.available_cash + account.frozen_cash
            if account.cash_balance != total_cash:
                account.cash_balance = total_cash
            
            account.update_balances()
            self.db.commit()
            
            logger.info(f"账户对账修复成功: {account.account_number}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"账户对账修复失败: {e}")
            return False
    
    # ==================== 私有方法 ====================
    
    def _generate_account_number(self) -> str:
        """生成账户号"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"ACC{timestamp}{random_suffix}"
    
    def _generate_transaction_id(self) -> str:
        """生成交易ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"TXN{timestamp}{random_suffix}"
    
    def _can_close_account(self, account: Account) -> bool:
        """检查是否可以关闭账户"""
        # 检查是否有未平仓位
        open_positions = self.db.query(Position).filter(
            Position.account_id == account.id,
            Position.status == 'OPEN'
        ).count()
        
        if open_positions > 0:
            return False
        
        # 检查是否有未完成订单
        pending_orders = self.db.query(Order).filter(
            Order.account_id == account.id,
            Order.status.in_(['PENDING', 'PARTIALLY_FILLED'])
        ).count()
        
        if pending_orders > 0:
            return False
        
        # 检查是否有冻结资金
        if account.frozen_cash > 0:
            return False
        
        return True