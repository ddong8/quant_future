"""性能优化索引

Revision ID: 002
Revises: 001
Create Date: 2023-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """添加性能优化索引"""
    
    # 用户表索引
    op.create_index('idx_users_email_active', 'users', ['email', 'is_active'])
    op.create_index('idx_users_username_active', 'users', ['username', 'is_active'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    
    # 策略表索引
    op.create_index('idx_strategies_user_status', 'strategies', ['user_id', 'status'])
    op.create_index('idx_strategies_status_created', 'strategies', ['status', 'created_at'])
    op.create_index('idx_strategies_name_user', 'strategies', ['name', 'user_id'])
    op.create_index('idx_strategies_updated_at', 'strategies', ['updated_at'])
    
    # 回测表索引
    op.create_index('idx_backtests_strategy_status', 'backtests', ['strategy_id', 'status'])
    op.create_index('idx_backtests_user_status', 'backtests', ['user_id', 'status'])
    op.create_index('idx_backtests_created_at', 'backtests', ['created_at'])
    op.create_index('idx_backtests_completed_at', 'backtests', ['completed_at'])
    op.create_index('idx_backtests_performance', 'backtests', ['total_return', 'sharpe_ratio'])
    
    # 订单表索引
    op.create_index('idx_orders_user_status', 'orders', ['user_id', 'status'])
    op.create_index('idx_orders_symbol_status', 'orders', ['symbol', 'status'])
    op.create_index('idx_orders_strategy_status', 'orders', ['strategy_id', 'status'])
    op.create_index('idx_orders_created_at', 'orders', ['created_at'])
    op.create_index('idx_orders_filled_at', 'orders', ['filled_at'])
    op.create_index('idx_orders_side_type', 'orders', ['side', 'order_type'])
    
    # 持仓表索引
    op.create_index('idx_positions_user_symbol', 'positions', ['user_id', 'symbol'])
    op.create_index('idx_positions_symbol_updated', 'positions', ['symbol', 'updated_at'])
    op.create_index('idx_positions_quantity', 'positions', ['quantity'])
    
    # 交易记录表索引（如果存在）
    try:
        op.create_index('idx_trades_user_symbol', 'trades', ['user_id', 'symbol'])
        op.create_index('idx_trades_strategy_symbol', 'trades', ['strategy_id', 'symbol'])
        op.create_index('idx_trades_created_at', 'trades', ['created_at'])
        op.create_index('idx_trades_symbol_side', 'trades', ['symbol', 'side'])
    except:
        pass  # 表可能不存在
    
    # 风险规则表索引
    try:
        op.create_index('idx_risk_rules_user_active', 'risk_rules', ['user_id', 'is_active'])
        op.create_index('idx_risk_rules_type_active', 'risk_rules', ['rule_type', 'is_active'])
    except:
        pass
    
    # 系统日志表索引
    try:
        op.create_index('idx_system_logs_level_created', 'system_logs', ['level', 'created_at'])
        op.create_index('idx_system_logs_user_created', 'system_logs', ['user_id', 'created_at'])
        op.create_index('idx_system_logs_module_created', 'system_logs', ['module', 'created_at'])
    except:
        pass
    
    # 复合索引用于常见查询
    op.create_index('idx_strategies_user_status_updated', 'strategies', 
                   ['user_id', 'status', 'updated_at'])
    op.create_index('idx_backtests_strategy_created_status', 'backtests', 
                   ['strategy_id', 'created_at', 'status'])
    op.create_index('idx_orders_user_created_status', 'orders', 
                   ['user_id', 'created_at', 'status'])


def downgrade():
    """删除性能优化索引"""
    
    # 删除复合索引
    op.drop_index('idx_orders_user_created_status', table_name='orders')
    op.drop_index('idx_backtests_strategy_created_status', table_name='backtests')
    op.drop_index('idx_strategies_user_status_updated', table_name='strategies')
    
    # 删除系统日志表索引
    try:
        op.drop_index('idx_system_logs_module_created', table_name='system_logs')
        op.drop_index('idx_system_logs_user_created', table_name='system_logs')
        op.drop_index('idx_system_logs_level_created', table_name='system_logs')
    except:
        pass
    
    # 删除风险规则表索引
    try:
        op.drop_index('idx_risk_rules_type_active', table_name='risk_rules')
        op.drop_index('idx_risk_rules_user_active', table_name='risk_rules')
    except:
        pass
    
    # 删除交易记录表索引
    try:
        op.drop_index('idx_trades_symbol_side', table_name='trades')
        op.drop_index('idx_trades_created_at', table_name='trades')
        op.drop_index('idx_trades_strategy_symbol', table_name='trades')
        op.drop_index('idx_trades_user_symbol', table_name='trades')
    except:
        pass
    
    # 删除持仓表索引
    op.drop_index('idx_positions_quantity', table_name='positions')
    op.drop_index('idx_positions_symbol_updated', table_name='positions')
    op.drop_index('idx_positions_user_symbol', table_name='positions')
    
    # 删除订单表索引
    op.drop_index('idx_orders_side_type', table_name='orders')
    op.drop_index('idx_orders_filled_at', table_name='orders')
    op.drop_index('idx_orders_created_at', table_name='orders')
    op.drop_index('idx_orders_strategy_status', table_name='orders')
    op.drop_index('idx_orders_symbol_status', table_name='orders')
    op.drop_index('idx_orders_user_status', table_name='orders')
    
    # 删除回测表索引
    op.drop_index('idx_backtests_performance', table_name='backtests')
    op.drop_index('idx_backtests_completed_at', table_name='backtests')
    op.drop_index('idx_backtests_created_at', table_name='backtests')
    op.drop_index('idx_backtests_user_status', table_name='backtests')
    op.drop_index('idx_backtests_strategy_status', table_name='backtests')
    
    # 删除策略表索引
    op.drop_index('idx_strategies_updated_at', table_name='strategies')
    op.drop_index('idx_strategies_name_user', table_name='strategies')
    op.drop_index('idx_strategies_status_created', table_name='strategies')
    op.drop_index('idx_strategies_user_status', table_name='strategies')
    
    # 删除用户表索引
    op.drop_index('idx_users_created_at', table_name='users')
    op.drop_index('idx_users_username_active', table_name='users')
    op.drop_index('idx_users_email_active', table_name='users')