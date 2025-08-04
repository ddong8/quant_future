-- 添加策略表缺失的列

-- 添加 uuid 列
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS uuid VARCHAR(36) UNIQUE;

-- 添加 strategy_type 列
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS strategy_type VARCHAR(50) DEFAULT 'custom';

-- 添加 entry_point 列
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS entry_point VARCHAR(100) DEFAULT 'main';

-- 添加其他缺失的列
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS timeframe VARCHAR(20);
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS symbols JSON;
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS max_position_size DECIMAL(20,8);
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS stop_loss DECIMAL(20,8);
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS take_profit DECIMAL(20,8);
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS total_returns DECIMAL(20,8);
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS max_drawdown_pct DECIMAL(10,4);
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS total_trades INTEGER DEFAULT 0;
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS is_running BOOLEAN DEFAULT FALSE;
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS last_error TEXT;
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE;
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS is_template BOOLEAN DEFAULT FALSE;

-- 为现有记录生成 UUID
UPDATE strategies SET uuid = gen_random_uuid()::text WHERE uuid IS NULL;

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_strategies_uuid ON strategies(uuid);
CREATE INDEX IF NOT EXISTS ix_strategies_strategy_type ON strategies(strategy_type);
CREATE INDEX IF NOT EXISTS ix_strategies_status ON strategies(status);
CREATE INDEX IF NOT EXISTS ix_strategies_is_running ON strategies(is_running);
CREATE INDEX IF NOT EXISTS ix_strategies_is_public ON strategies(is_public);