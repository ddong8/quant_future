"""
交易流水服务测试
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from ..app.services.transaction_service import TransactionService
from ..app.models.account import Transaction, TransactionType, TransactionStatus
from ..app.models.user import User
from ..app.models.account import Account

class TestTransactionService:
    """交易流水服务测试类"""
    
    def test_create_transaction(self, db_session: Session, test_user: User, test_account: Account):
        """测试创建交易流水"""
        service = TransactionService(db_session)
        
        transaction_data = {
            'account_id': test_account.id,
            'transaction_type': 'DEPOSIT',
            'amount': Decimal('1000.00'),
            'currency': 'USD',
            'description': '测试入金',
            'balance_before': Decimal('0.00'),
            'balance_after': Decimal('1000.00')
        }
        
        transaction = service.create_transaction(transaction_data)
        
        assert transaction.id is not None
        assert transaction.account_id == test_account.id
        assert transaction.transaction_type == TransactionType.DEPOSIT
        assert transaction.amount == Decimal('1000.00')
        assert transaction.status == TransactionStatus.COMPLETED
        assert transaction.description == '测试入金'
    
    def test_get_transaction(self, db_session: Session, test_transaction: Transaction):
        """测试获取单个交易流水"""
        service = TransactionService(db_session)
        
        transaction = service.get_transaction(test_transaction.transaction_id)
        
        assert transaction is not None
        assert transaction.id == test_transaction.id
        assert transaction.transaction_id == test_transaction.transaction_id
    
    def test_search_transactions(self, db_session: Session, test_user: User, test_account: Account):
        """测试搜索交易流水"""
        service = TransactionService(db_session)
        
        # 创建多个测试交易
        for i in range(5):
            transaction_data = {
                'account_id': test_account.id,
                'transaction_type': 'DEPOSIT' if i % 2 == 0 else 'WITHDRAWAL',
                'amount': Decimal(f'{(i + 1) * 100}.00'),
                'currency': 'USD',
                'description': f'测试交易 {i + 1}'
            }
            service.create_transaction(transaction_data)
        
        # 搜索所有交易
        search_params = {
            'user_id': test_user.id,
            'limit': 10
        }
        result = service.search_transactions(search_params)
        
        assert result['total_count'] >= 5
        assert len(result['transactions']) >= 5
        
        # 按类型筛选
        search_params['transaction_types'] = [TransactionType.DEPOSIT]
        result = service.search_transactions(search_params)
        
        for transaction in result['transactions']:
            assert transaction.transaction_type == TransactionType.DEPOSIT
    
    def test_get_transaction_statistics(self, db_session: Session, test_user: User, test_account: Account):
        """测试获取交易统计"""
        service = TransactionService(db_session)
        
        # 创建测试数据
        transactions_data = [
            {
                'account_id': test_account.id,
                'transaction_type': 'DEPOSIT',
                'amount': Decimal('1000.00'),
                'currency': 'USD'
            },
            {
                'account_id': test_account.id,
                'transaction_type': 'WITHDRAWAL',
                'amount': Decimal('-500.00'),
                'currency': 'USD'
            },
            {
                'account_id': test_account.id,
                'transaction_type': 'TRADE_BUY',
                'amount': Decimal('-200.00'),
                'currency': 'USD',
                'fee_amount': Decimal('2.00')
            }
        ]
        
        for data in transactions_data:
            service.create_transaction(data)
        
        # 获取统计数据
        statistics = service.get_transaction_statistics(test_user.id, 'month')
        
        assert 'summary' in statistics
        assert 'daily_stats' in statistics
        assert 'type_breakdown' in statistics
        assert statistics['summary']['total_transactions'] >= 3
        assert statistics['summary']['total_income'] >= 1000.0
        assert statistics['summary']['total_expense'] >= 700.0
        assert statistics['summary']['total_fees'] >= 2.0
    
    def test_get_cash_flow_analysis(self, db_session: Session, test_user: User, test_account: Account):
        """测试现金流分析"""
        service = TransactionService(db_session)
        
        # 创建现金流测试数据
        base_date = datetime.now() - timedelta(days=10)
        for i in range(10):
            transaction_data = {
                'account_id': test_account.id,
                'transaction_type': 'DEPOSIT' if i % 3 == 0 else 'WITHDRAWAL',
                'amount': Decimal(f'{100 * (i + 1)}.00') if i % 3 == 0 else Decimal(f'-{50 * (i + 1)}.00'),
                'currency': 'USD',
                'transaction_time': base_date + timedelta(days=i)
            }
            service.create_transaction(transaction_data)
        
        # 获取现金流分析
        analysis = service.get_cash_flow_analysis(test_user.id, 'month')
        
        assert 'cash_flow_data' in analysis
        assert 'metrics' in analysis
        assert 'inflow_analysis' in analysis
        assert 'outflow_analysis' in analysis
        assert len(analysis['cash_flow_data']) > 0
    
    def test_export_transactions(self, db_session: Session, test_user: User, test_account: Account):
        """测试导出交易流水"""
        service = TransactionService(db_session)
        
        # 创建测试数据
        for i in range(3):
            transaction_data = {
                'account_id': test_account.id,
                'transaction_type': 'DEPOSIT',
                'amount': Decimal(f'{(i + 1) * 100}.00'),
                'currency': 'USD',
                'description': f'测试交易 {i + 1}'
            }
            service.create_transaction(transaction_data)
        
        # 测试CSV导出
        result = service.export_transactions(test_user.id, 'csv')
        
        assert result['success'] is True
        assert 'file_content' in result
        assert 'file_name' in result
        assert result['content_type'] == 'text/csv'
        assert result['record_count'] >= 3
    
    def test_audit_transactions(self, db_session: Session, test_user: User, test_account: Account):
        """测试交易审计"""
        service = TransactionService(db_session)
        
        # 创建正常交易
        transaction_data = {
            'account_id': test_account.id,
            'transaction_type': 'DEPOSIT',
            'amount': Decimal('1000.00'),
            'currency': 'USD',
            'balance_before': Decimal('0.00'),
            'balance_after': Decimal('1000.00')
        }
        service.create_transaction(transaction_data)
        
        # 执行一致性审计
        audit_result = service.audit_transactions(test_user.id, 'consistency')
        
        assert 'audit_type' in audit_result
        assert 'total_issues' in audit_result
        assert 'status' in audit_result
        assert audit_result['audit_type'] == 'consistency'
    
    def test_get_suspicious_transactions(self, db_session: Session, test_user: User, test_account: Account):
        """测试获取可疑交易"""
        service = TransactionService(db_session)
        
        # 创建正常交易
        normal_transaction = {
            'account_id': test_account.id,
            'transaction_type': 'DEPOSIT',
            'amount': Decimal('100.00'),
            'currency': 'USD'
        }
        service.create_transaction(normal_transaction)
        
        # 创建异常大额交易
        suspicious_transaction = {
            'account_id': test_account.id,
            'transaction_type': 'DEPOSIT',
            'amount': Decimal('1000000.00'),  # 异常大额
            'currency': 'USD'
        }
        service.create_transaction(suspicious_transaction)
        
        # 获取可疑交易
        suspicious = service.get_suspicious_transactions(test_user.id, 30)
        
        # 应该检测到异常大额交易
        assert len(suspicious) > 0
        suspicious_amounts = [t['amount'] for t in suspicious]
        assert 1000000.0 in suspicious_amounts
    
    def test_update_transaction_status(self, db_session: Session, test_transaction: Transaction):
        """测试更新交易状态"""
        service = TransactionService(db_session)
        
        # 更新状态为处理中
        updated_transaction = service.update_transaction_status(
            test_transaction.transaction_id,
            TransactionStatus.PROCESSING,
            {'updated_reason': '手动更新'}
        )
        
        assert updated_transaction is not None
        assert updated_transaction.status == TransactionStatus.PROCESSING
        assert 'updated_reason' in updated_transaction.metadata
    
    def test_generate_transaction_report(self, db_session: Session, test_user: User, test_account: Account):
        """测试生成交易报表"""
        service = TransactionService(db_session)
        
        # 创建测试数据
        transactions_data = [
            {
                'account_id': test_account.id,
                'transaction_type': 'DEPOSIT',
                'amount': Decimal('1000.00'),
                'currency': 'USD',
                'fee_amount': Decimal('5.00')
            },
            {
                'account_id': test_account.id,
                'transaction_type': 'WITHDRAWAL',
                'amount': Decimal('-300.00'),
                'currency': 'USD',
                'fee_amount': Decimal('3.00')
            }
        ]
        
        for data in transactions_data:
            service.create_transaction(data)
        
        # 生成汇总报表
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now() + timedelta(days=1)
        
        report = service.generate_transaction_report(
            test_user.id, 
            'summary', 
            start_date, 
            end_date
        )
        
        assert 'report_type' in report
        assert 'summary' in report
        assert report['report_type'] == 'summary'
        assert report['summary']['total_transactions'] >= 2
        assert report['summary']['total_income'] >= 1000.0
        assert report['summary']['total_expense'] >= 300.0
        assert report['summary']['total_fees'] >= 8.0

# 测试夹具
@pytest.fixture
def test_transaction(db_session: Session, test_account: Account) -> Transaction:
    """创建测试交易"""
    service = TransactionService(db_session)
    
    transaction_data = {
        'account_id': test_account.id,
        'transaction_type': 'DEPOSIT',
        'amount': Decimal('500.00'),
        'currency': 'USD',
        'description': '测试交易',
        'status': 'PENDING'
    }
    
    return service.create_transaction(transaction_data)