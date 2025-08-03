-- 创建数据库
CREATE DATABASE trading_platform;
CREATE DATABASE trading_platform_test;

-- 创建用户
CREATE USER trading_user WITH PASSWORD 'trading_password';

-- 授权
GRANT ALL PRIVILEGES ON DATABASE trading_platform TO trading_user;
GRANT ALL PRIVILEGES ON DATABASE trading_platform_test TO trading_user;
