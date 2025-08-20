"""
测试配置和夹具
"""
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.user import User
from app.models.strategy import Strategy
from app.models.backtest import Backtest
from app.models.trading import Order, Position
from app.core.security import create_access_token, get_password_hash


# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """创建数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    """创建测试客户端"""
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture
async def async_client():
    """创建异步测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """创建管理员用户"""
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_superuser=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """创建认证头"""
    access_token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_headers(admin_user):
    """创建管理员认证头"""
    access_token = create_access_token(data={"sub": admin_user.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def test_strategy(db_session, test_user):
    """创建测试策略"""
    strategy = Strategy(
        name="Test Strategy",
        description="A test strategy",
        code="""
def initialize(context):
    pass

def handle_bar(context, bar_dict):
    pass
        """,
        user_id=test_user.id,
        status="draft"
    )
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)
    return strategy


@pytest.fixture
def test_backtest(db_session, test_strategy):
    """创建测试回测"""
    backtest = Backtest(
        name="Test Backtest",
        strategy_id=test_strategy.id,
        user_id=test_strategy.user_id,
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=100000.0,
        status="pending"
    )
    db_session.add(backtest)
    db_session.commit()
    db_session.refresh(backtest)
    return backtest


@pytest.fixture
def test_order(db_session, test_user):
    """创建测试订单"""
    order = Order(
        user_id=test_user.id,
        symbol="SHFE.cu2601",
        side="buy",
        order_type="limit",
        quantity=1,
        price=70000.0,
        status="pending"
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


@pytest.fixture
def test_position(db_session, test_user):
    """创建测试持仓"""
    position = Position(
        user_id=test_user.id,
        symbol="SHFE.cu2601",
        quantity=1,
        avg_price=70000.0,
        current_price=70500.0
    )
    db_session.add(position)
    db_session.commit()
    db_session.refresh(position)
    return position


@pytest.fixture
def mock_tqsdk():
    """模拟TQSDK"""
    class MockTQSDK:
        def __init__(self):
            self.connected = True
            self.quotes = {}
            self.klines = {}
        
        def get_quote(self, symbol):
            return {
                "symbol": symbol,
                "last_price": 70000.0,
                "bid_price1": 69990.0,
                "ask_price1": 70010.0,
                "volume": 1000,
                "datetime": "2023-01-01 09:00:00"
            }
        
        def get_kline_serial(self, symbol, duration_seconds):
            return [
                {
                    "datetime": "2023-01-01 09:00:00",
                    "open": 69900.0,
                    "high": 70100.0,
                    "low": 69800.0,
                    "close": 70000.0,
                    "volume": 100
                }
            ]
        
        def insert_order(self, symbol, direction, offset, volume, limit_price=None):
            return {
                "order_id": "test_order_123",
                "status": "ALIVE",
                "symbol": symbol,
                "direction": direction,
                "offset": offset,
                "volume_orign": volume,
                "volume_left": volume,
                "limit_price": limit_price
            }
        
        def cancel_order(self, order_id):
            return {"order_id": order_id, "status": "FINISHED"}
    
    return MockTQSDK()


@pytest.fixture
def mock_redis():
    """模拟Redis"""
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        def get(self, key):
            return self.data.get(key)
        
        def set(self, key, value, ex=None):
            self.data[key] = value
            return True
        
        def delete(self, key):
            if key in self.data:
                del self.data[key]
                return 1
            return 0
        
        def exists(self, key):
            return key in self.data
        
        def hget(self, name, key):
            hash_data = self.data.get(name, {})
            return hash_data.get(key) if isinstance(hash_data, dict) else None
        
        def hset(self, name, key, value):
            if name not in self.data:
                self.data[name] = {}
            self.data[name][key] = value
            return 1
        
        def publish(self, channel, message):
            return 1
    
    return MockRedis()


@pytest.fixture
def mock_influxdb():
    """模拟InfluxDB"""
    class MockInfluxDB:
        def __init__(self):
            self.data = []
        
        def write_api(self):
            return self
        
        def write(self, bucket, org, record):
            self.data.append(record)
        
        def query_api(self):
            return self
        
        def query(self, query):
            # 返回模拟查询结果
            return [
                {
                    "_time": "2023-01-01T09:00:00Z",
                    "_value": 70000.0,
                    "_field": "close",
                    "_measurement": "kline",
                    "symbol": "SHFE.cu2601"
                }
            ]
    
    return MockInfluxDB()


# 测试数据
TEST_SYMBOLS = ["SHFE.cu2601", "DCE.i2601", "CZCE.MA2601"]

TEST_KLINE_DATA = [
    {
        "datetime": "2023-01-01 09:00:00",
        "open": 69900.0,
        "high": 70100.0,
        "low": 69800.0,
        "close": 70000.0,
        "volume": 100
    },
    {
        "datetime": "2023-01-01 09:01:00",
        "open": 70000.0,
        "high": 70200.0,
        "low": 69900.0,
        "close": 70100.0,
        "volume": 120
    }
]

TEST_QUOTE_DATA = {
    "symbol": "SHFE.cu2601",
    "last_price": 70000.0,
    "bid_price1": 69990.0,
    "ask_price1": 70010.0,
    "volume": 1000,
    "datetime": "2023-01-01 09:00:00"
}