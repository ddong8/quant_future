"""
策略API集成测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.models.user import User


class TestStrategyAPI:
    """策略API测试类"""
    
    def test_create_strategy(self, client: TestClient, auth_headers: dict, test_user: User, db_session: Session):
        """测试创建策略"""
        strategy_data = {
            "name": "New Strategy",
            "description": "A new trading strategy",
            "code": """
def initialize(context):
    context.symbol = 'SHFE.cu2401'

def handle_bar(context, bar_dict):
    if context.portfolio.available_cash > 100000:
        context.order_target_percent(context.symbol, 0.5)
            """,
            "parameters": {
                "symbol": "SHFE.cu2401",
                "position_size": 0.5
            }
        }
        
        response = client.post("/api/v1/strategies/", json=strategy_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == strategy_data["name"]
        assert data["description"] == strategy_data["description"]
        assert data["user_id"] == str(test_user.id)
        assert data["status"] == "draft"
        
        # 验证数据库中的策略
        strategy = db_session.query(Strategy).filter(Strategy.id == data["id"]).first()
        assert strategy is not None
        assert strategy.name == strategy_data["name"]
    
    def test_create_strategy_without_auth(self, client: TestClient):
        """测试未认证创建策略"""
        strategy_data = {
            "name": "Unauthorized Strategy",
            "description": "Should fail",
            "code": "def initialize(context): pass"
        }
        
        response = client.post("/api/v1/strategies/", json=strategy_data)
        assert response.status_code == 401
    
    def test_get_strategies(self, client: TestClient, auth_headers: dict, test_strategy: Strategy):
        """测试获取策略列表"""
        response = client.get("/api/v1/strategies/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1
        
        strategy_data = data[0]
        assert strategy_data["id"] == str(test_strategy.id)
        assert strategy_data["name"] == test_strategy.name
    
    def test_get_strategy_by_id(self, client: TestClient, auth_headers: dict, test_strategy: Strategy):
        """测试根据ID获取策略"""
        response = client.get(f"/api/v1/strategies/{test_strategy.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(test_strategy.id)
        assert data["name"] == test_strategy.name
        assert data["code"] == test_strategy.code
    
    def test_get_nonexistent_strategy(self, client: TestClient, auth_headers: dict):
        """测试获取不存在的策略"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/strategies/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_update_strategy(self, client: TestClient, auth_headers: dict, test_strategy: Strategy, db_session: Session):
        """测试更新策略"""
        update_data = {
            "name": "Updated Strategy",
            "description": "Updated description",
            "code": """
def initialize(context):
    context.symbol = 'DCE.i2401'

def handle_bar(context, bar_dict):
    pass
            """
        }
        
        response = client.put(f"/api/v1/strategies/{test_strategy.id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        
        # 验证数据库更新
        db_session.refresh(test_strategy)
        assert test_strategy.name == update_data["name"]
        assert test_strategy.description == update_data["description"]
    
    def test_update_nonexistent_strategy(self, client: TestClient, auth_headers: dict):
        """测试更新不存在的策略"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"name": "Should Fail"}
        
        response = client.put(f"/api/v1/strategies/{fake_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 404
    
    def test_delete_strategy(self, client: TestClient, auth_headers: dict, test_strategy: Strategy, db_session: Session):
        """测试删除策略"""
        strategy_id = test_strategy.id
        
        response = client.delete(f"/api/v1/strategies/{strategy_id}", headers=auth_headers)
        assert response.status_code == 204
        
        # 验证策略已删除
        deleted_strategy = db_session.query(Strategy).filter(Strategy.id == strategy_id).first()
        assert deleted_strategy is None
    
    def test_delete_nonexistent_strategy(self, client: TestClient, auth_headers: dict):
        """测试删除不存在的策略"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.delete(f"/api/v1/strategies/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_validate_strategy_code(self, client: TestClient, auth_headers: dict):
        """测试策略代码验证"""
        valid_code = """
def initialize(context):
    context.symbol = 'SHFE.cu2401'

def handle_bar(context, bar_dict):
    if context.portfolio.available_cash > 100000:
        context.order_target_percent(context.symbol, 0.5)
        """
        
        validation_data = {"code": valid_code}
        
        response = client.post("/api/v1/strategies/validate", json=validation_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is True
        assert "errors" not in data or len(data["errors"]) == 0
    
    def test_validate_invalid_strategy_code(self, client: TestClient, auth_headers: dict):
        """测试无效策略代码验证"""
        invalid_code = """
def initialize(context):
    context.symbol = 'SHFE.cu2401'
    invalid_syntax here

def handle_bar(context, bar_dict):
    context.order_target_percent(context.symbol, 0.5)
        """
        
        validation_data = {"code": invalid_code}
        
        response = client.post("/api/v1/strategies/validate", json=validation_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is False
        assert "errors" in data
        assert len(data["errors"]) > 0
    
    def test_test_strategy(self, client: TestClient, auth_headers: dict, test_strategy: Strategy):
        """测试策略测试"""
        test_data = {
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
            "initial_capital": 100000.0,
            "symbols": ["SHFE.cu2401"]
        }
        
        response = client.post(f"/api/v1/strategies/{test_strategy.id}/test", json=test_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "test_id" in data
        assert data["status"] == "running"
    
    def test_deploy_strategy(self, client: TestClient, auth_headers: dict, test_strategy: Strategy, db_session: Session):
        """测试策略部署"""
        deploy_data = {
            "environment": "paper",
            "initial_capital": 100000.0,
            "risk_params": {
                "max_position_size": 0.3,
                "stop_loss": 0.05
            }
        }
        
        response = client.post(f"/api/v1/strategies/{test_strategy.id}/deploy", json=deploy_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "deployed"
        
        # 验证策略状态更新
        db_session.refresh(test_strategy)
        assert test_strategy.status == "active"
    
    def test_stop_strategy(self, client: TestClient, auth_headers: dict, test_strategy: Strategy, db_session: Session):
        """测试停止策略"""
        # 先部署策略
        test_strategy.status = "active"
        db_session.commit()
        
        response = client.post(f"/api/v1/strategies/{test_strategy.id}/stop", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "stopped"
        
        # 验证策略状态更新
        db_session.refresh(test_strategy)
        assert test_strategy.status == "stopped"
    
    def test_get_strategy_performance(self, client: TestClient, auth_headers: dict, test_strategy: Strategy):
        """测试获取策略性能"""
        response = client.get(f"/api/v1/strategies/{test_strategy.id}/performance", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_return" in data
        assert "sharpe_ratio" in data
        assert "max_drawdown" in data
        assert "win_rate" in data
    
    def test_get_strategy_logs(self, client: TestClient, auth_headers: dict, test_strategy: Strategy):
        """测试获取策略日志"""
        response = client.get(f"/api/v1/strategies/{test_strategy.id}/logs", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_clone_strategy(self, client: TestClient, auth_headers: dict, test_strategy: Strategy, db_session: Session):
        """测试克隆策略"""
        clone_data = {
            "name": "Cloned Strategy",
            "description": "Cloned from original"
        }
        
        response = client.post(f"/api/v1/strategies/{test_strategy.id}/clone", json=clone_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == clone_data["name"]
        assert data["code"] == test_strategy.code
        assert data["id"] != str(test_strategy.id)
        
        # 验证克隆的策略存在
        cloned_strategy = db_session.query(Strategy).filter(Strategy.id == data["id"]).first()
        assert cloned_strategy is not None
        assert cloned_strategy.name == clone_data["name"]


class TestStrategyPermissions:
    """策略权限测试"""
    
    def test_user_cannot_access_others_strategy(self, client: TestClient, db_session: Session):
        """测试用户无法访问他人策略"""
        # 创建两个用户
        from app.core.security import get_password_hash, create_access_token
        
        user1 = User(
            username="user1",
            email="user1@example.com",
            hashed_password=get_password_hash("pass123"),
            is_active=True
        )
        user2 = User(
            username="user2",
            email="user2@example.com",
            hashed_password=get_password_hash("pass123"),
            is_active=True
        )
        
        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)
        
        # 用户1创建策略
        strategy = Strategy(
            name="User1 Strategy",
            description="Private strategy",
            code="def initialize(context): pass",
            user_id=user1.id
        )
        db_session.add(strategy)
        db_session.commit()
        db_session.refresh(strategy)
        
        # 用户2尝试访问用户1的策略
        user2_token = create_access_token(data={"sub": user2.username})
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        response = client.get(f"/api/v1/strategies/{strategy.id}", headers=user2_headers)
        assert response.status_code == 404  # 应该返回404而不是403，避免信息泄露
    
    def test_admin_can_access_all_strategies(self, client: TestClient, admin_headers: dict, test_strategy: Strategy):
        """测试管理员可以访问所有策略"""
        response = client.get(f"/api/v1/strategies/{test_strategy.id}", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(test_strategy.id)


class TestStrategyValidation:
    """策略验证测试"""
    
    def test_create_strategy_with_invalid_code(self, client: TestClient, auth_headers: dict):
        """测试创建包含无效代码的策略"""
        strategy_data = {
            "name": "Invalid Strategy",
            "description": "Strategy with syntax error",
            "code": "def initialize(context):\n    invalid syntax here"
        }
        
        response = client.post("/api/v1/strategies/", json=strategy_data, headers=auth_headers)
        assert response.status_code == 400
        assert "code validation failed" in response.json()["detail"].lower()
    
    def test_create_strategy_with_dangerous_code(self, client: TestClient, auth_headers: dict):
        """测试创建包含危险代码的策略"""
        strategy_data = {
            "name": "Dangerous Strategy",
            "description": "Strategy with dangerous operations",
            "code": """
import os
def initialize(context):
    os.system('rm -rf /')
            """
        }
        
        response = client.post("/api/v1/strategies/", json=strategy_data, headers=auth_headers)
        assert response.status_code == 400
        assert "dangerous" in response.json()["detail"].lower() or "forbidden" in response.json()["detail"].lower()
    
    def test_strategy_name_length_validation(self, client: TestClient, auth_headers: dict):
        """测试策略名称长度验证"""
        strategy_data = {
            "name": "x" * 256,  # 超长名称
            "description": "Valid description",
            "code": "def initialize(context): pass"
        }
        
        response = client.post("/api/v1/strategies/", json=strategy_data, headers=auth_headers)
        assert response.status_code == 422  # 验证错误