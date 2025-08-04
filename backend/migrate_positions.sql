-- 添加持仓表缺失的列

-- 添加 uuid 列
ALTER TABLE positions ADD COLUMN IF NOT EXISTS uuid VARCHAR(36) UNIQUE;

-- 添加 position_type 列 (替换 direction)
ALTER TABLE positions ADD COLUMN IF NOT EXISTS position_type VARCHAR(20);

-- 添加 status 列
ALTER TABLE positions ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'open';

-- 添加数量相关列
ALTER TABLE positions ADD COLUMN IF NOT EXISTS quantity DECIMAL(20,8) DEFAULT 0;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS available_quantity DECIMAL(20,8) DEFAULT 0;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS frozen_quantity DECIMAL(20,8) DEFAULT 0;

-- 添加成本相关列
ALTER TABLE positions ADD COLUMN IF NOT EXISTS average_cost DECIMAL(20,8) DEFAULT 0;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS total_cost DECIMAL(20,8) DEFAULT 0;

-- 添加价格相关列
ALTER TABLE positions ADD COLUMN IF NOT EXISTS current_price DECIMAL(20,8);
ALTER TABLE positions ADD COLUMN IF NOT EXISTS market_value DECIMAL(20,8);

-- 添加盈亏相关列
ALTER TABLE positions ADD COLUMN IF NOT EXISTS total_pnl DECIMAL(20,8) DEFAULT 0;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS return_rate DECIMAL(10,4) DEFAULT 0;

-- 添加止损止盈列
ALTER TABLE positions ADD COLUMN IF NOT EXISTS stop_loss_price DECIMAL(20,8);
ALTER TABLE positions ADD COLUMN IF NOT EXISTS take_profit_price DECIMAL(20,8);

-- 添加时间列
ALTER TABLE positions ADD COLUMN IF NOT EXISTS opened_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS closed_at TIMESTAMP WITH TIME ZONE;

-- 添加其他列
ALTER TABLE positions ADD COLUMN IF NOT EXISTS user_id INTEGER;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS backtest_id INTEGER;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS tags JSON;

-- 从现有数据迁移
UPDATE positions SET 
    quantity = volume,
    available_quantity = volume,
    average_cost = avg_price,
    total_cost = volume * avg_price,
    position_type = CASE WHEN direction = 'long' THEN 'long' ELSE 'short' END,
    opened_at = created_at
WHERE quantity IS NULL OR quantity = 0;

-- 为现有记录生成 UUID
UPDATE positions SET uuid = gen_random_uuid()::text WHERE uuid IS NULL;

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_positions_uuid ON positions(uuid);
CREATE INDEX IF NOT EXISTS ix_positions_position_type ON positions(position_type);
CREATE INDEX IF NOT EXISTS ix_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS ix_positions_user_id ON positions(user_id);

-- 添加外键约束
ALTER TABLE positions ADD CONSTRAINT IF NOT EXISTS positions_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE positions ADD CONSTRAINT IF NOT EXISTS positions_backtest_id_fkey 
    FOREIGN KEY (backtest_id) REFERENCES backtests(id);