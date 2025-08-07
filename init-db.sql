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

-- 注意：用户表和索引将由 Alembic 迁移创建
-- 默认管理员用户将在应用启动时创建

-- 插入一些示例数据（可选）
-- 这里可以添加一些测试用的市场数据、策略模板等

COMMIT;