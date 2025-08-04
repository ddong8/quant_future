-- 添加持仓表所有缺失的列

-- 添加盈亏相关列
ALTER TABLE positions ADD COLUMN IF NOT EXISTS unrealized_pnl_percent DECIMAL(10,4) DEFAULT 0;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS daily_pnl DECIMAL(20,8) DEFAULT 0;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS daily_pnl_percent DECIMAL(10,4) DEFAULT 0;

-- 添加最大盈亏列
ALTER TABLE positions ADD COLUMN IF NOT EXISTS max_drawdown DECIMAL(20,8) DEFAULT 0;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS max_profit DECIMAL(20,8) DEFAULT 0;

-- 添加止损止盈订单ID列
ALTER TABLE positions ADD COLUMN IF NOT EXISTS stop_loss_order_id INTEGER;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS take_profit_order_id INTEGER;

-- 添加来源相关列
ALTER TABLE positions ADD COLUMN IF NOT EXISTS source VARCHAR(50);
ALTER TABLE positions ADD COLUMN IF NOT EXISTS source_id VARCHAR(100);

-- 添加元数据列
ALTER TABLE positions ADD COLUMN IF NOT EXISTS model_metadata JSON;