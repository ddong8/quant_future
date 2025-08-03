-- 量化交易平台数据库初始化脚本

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建测试数据库
CREATE DATABASE trading_platform_test;

-- 授权
GRANT ALL PRIVILEGES ON DATABASE trading_platform TO trading_user;
GRANT ALL PRIVILEGES ON DATABASE trading_platform_test TO trading_user;

-- 连接到主数据库
\c trading_platform;

-- 创建基础表结构（如果需要的话）
-- 这里可以添加一些基础数据或配置

-- 插入默认管理员用户（密码: admin123）
-- 注意：这个密码哈希是 bcrypt 加密的 "admin123"
INSERT INTO users (username, email, hashed_password, is_active, is_superuser, created_at, updated_at) 
VALUES (
    'admin', 
    'admin@trading-platform.com', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3L3jzjU3pO', 
    true, 
    true, 
    NOW(), 
    NOW()
) ON CONFLICT (username) DO NOTHING;

-- 创建索引以提高性能
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- 插入一些示例数据（可选）
-- 这里可以添加一些测试用的市场数据、策略模板等

COMMIT;