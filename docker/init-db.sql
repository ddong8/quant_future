-- 初始化数据库脚本

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- 创建索引优化查询性能
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

CREATE INDEX IF NOT EXISTS idx_strategies_user_id ON strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_strategies_status ON strategies(status);
CREATE INDEX IF NOT EXISTS idx_strategies_created_at ON strategies(created_at);

CREATE INDEX IF NOT EXISTS idx_backtests_strategy_id ON backtests(strategy_id);
CREATE INDEX IF NOT EXISTS idx_backtests_user_id ON backtests(user_id);
CREATE INDEX IF NOT EXISTS idx_backtests_status ON backtests(status);
CREATE INDEX IF NOT EXISTS idx_backtests_created_at ON backtests(created_at);

CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_strategy_id ON orders(strategy_id);
CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

CREATE INDEX IF NOT EXISTS idx_positions_user_id ON positions(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_positions_updated_at ON positions(updated_at);

-- 创建分区表（用于大数据量场景）
-- 按月分区交易记录表
CREATE TABLE IF NOT EXISTS trades_template (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL,
    strategy_id UUID,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    commission DECIMAL(20, 8) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

-- 创建当前月份的分区
DO $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
BEGIN
    start_date := DATE_TRUNC('month', CURRENT_DATE);
    end_date := start_date + INTERVAL '1 month';
    partition_name := 'trades_' || TO_CHAR(start_date, 'YYYY_MM');
    
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF trades_template 
                    FOR VALUES FROM (%L) TO (%L)', 
                   partition_name, start_date, end_date);
END $$;

-- 创建视图简化查询
CREATE OR REPLACE VIEW user_strategy_summary AS
SELECT 
    u.id as user_id,
    u.username,
    COUNT(s.id) as strategy_count,
    COUNT(CASE WHEN s.status = 'active' THEN 1 END) as active_strategies,
    COUNT(b.id) as backtest_count,
    AVG(b.total_return) as avg_return
FROM users u
LEFT JOIN strategies s ON u.id = s.user_id
LEFT JOIN backtests b ON s.id = b.strategy_id AND b.status = 'completed'
GROUP BY u.id, u.username;

-- 创建存储过程
CREATE OR REPLACE FUNCTION calculate_portfolio_value(p_user_id UUID)
RETURNS DECIMAL(20, 2) AS $$
DECLARE
    total_value DECIMAL(20, 2) := 0;
BEGIN
    SELECT COALESCE(SUM(quantity * current_price), 0)
    INTO total_value
    FROM positions p
    JOIN market_data m ON p.symbol = m.symbol
    WHERE p.user_id = p_user_id;
    
    RETURN total_value;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器函数
CREATE OR REPLACE FUNCTION update_position_on_trade()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO positions (user_id, symbol, quantity, avg_price, updated_at)
    VALUES (NEW.user_id, NEW.symbol, 
            CASE WHEN NEW.side = 'buy' THEN NEW.quantity ELSE -NEW.quantity END,
            NEW.price, NEW.created_at)
    ON CONFLICT (user_id, symbol)
    DO UPDATE SET
        quantity = positions.quantity + 
                  CASE WHEN NEW.side = 'buy' THEN NEW.quantity ELSE -NEW.quantity END,
        avg_price = CASE 
            WHEN positions.quantity + CASE WHEN NEW.side = 'buy' THEN NEW.quantity ELSE -NEW.quantity END = 0 
            THEN 0
            ELSE (positions.avg_price * positions.quantity + NEW.price * NEW.quantity) / 
                 (positions.quantity + CASE WHEN NEW.side = 'buy' THEN NEW.quantity ELSE -NEW.quantity END)
        END,
        updated_at = NEW.created_at;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
DROP TRIGGER IF EXISTS trigger_update_position_on_trade ON trades_template;
CREATE TRIGGER trigger_update_position_on_trade
    AFTER INSERT ON trades_template
    FOR EACH ROW
    EXECUTE FUNCTION update_position_on_trade();

-- 插入初始数据
INSERT INTO users (id, username, email, hashed_password, is_active, is_superuser, created_at)
VALUES (
    uuid_generate_v4(),
    'admin',
    'admin@quanttrading.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq/3Haa', -- password: admin123
    true,
    true,
    CURRENT_TIMESTAMP
) ON CONFLICT (email) DO NOTHING;

-- 创建系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认系统配置
INSERT INTO system_config (key, value, description) VALUES
('max_strategies_per_user', '10', '每个用户最大策略数量'),
('max_concurrent_backtests', '5', '最大并发回测数量'),
('default_commission_rate', '0.0003', '默认手续费率'),
('risk_max_position_size', '0.1', '最大仓位比例'),
('market_data_retention_days', '365', '市场数据保留天数')
ON CONFLICT (key) DO NOTHING;