"""
交易API集成测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch

from app.models.trading import Order, Position
from app.models.user import User


class TestOrderAPI:
    """订单API测试类"""
    
    def test_create_order(self, client: TestClient, auth_headers: dict, test_user: User, db_session: Session):
        """测试创建订单"""
        order_data = {
            "symbol": "SHFE.cu2401",
            "side": "buy",
            "order_type": "limit",
            "quantity": 1,
            "price": 70000.0,
            "time_in_force": "GTC"
        }
        
        with patch('app.services.order_service.OrderService.create_order') as mock_create:
            mock_create.return_value = {
                "id": "test_order_123",
                "status": "pending",
                **order_data
            }
            
            response = client.post("/api/v1/orders/", json=order_data, headers=auth_headers)
            assert response.status_code == 201
            
            data = response.json()
            assert data["symbol"] == order_data["symbol"]
            assert data["side"] == order_data["side"]
            assert data["quantity"] == order_data["quantity"]
            assert data["price"] == order_data["price"]
            assert data["status"] == "pending"
    
    def test_create_market_order(self, client: TestClient, auth_headers: dict, test_user: User):
        """测试创建市价订单"""
        order_data = {
            "symbol": "SHFE.cu2401",
            "side": "sell",
            "order_type": "market",
            "quantity": 2
        }
        
        with patch('app.services.order_service.OrderService.create_order') as mock_create:
            mock_create.return_value = {
                "id": "test_market_order_123",
                "status": "pending",
                **order_data
            }
            
            response = client.post("/api/v1/orders/", json=order_data, headers=auth_headers)
            assert response.status_code == 201
            
            data = response.json()
            assert data["order_type"] == "market"
            assert "price" not in data or data["price"] is None
    
    def test_create_order_invalid_symbol(self, client: TestClient, auth_headers: dict):
        """测试创建无效合约订单"""
        order_data = {
            "symbol": "INVALID.symbol",
            "side": "buy",
            "order_type": "limit",
            "quantity": 1,
            "price": 70000.0
        }
        
        response = client.post("/api/v1/orders/", json=order_data, headers=auth_headers)
        assert response.status_code == 400
        assert "invalid symbol" in response.json()["detail"].lower()
    
    def test_create_order_insufficient_funds(self, client: TestClient, auth_headers: dict):
        """测试资金不足创建订单"""
        order_data = {
            "symbol": "SHFE.cu2401",
            "side": "buy",
            "order_type": "limit",
            "quantity": 1000,  # 大量订单
            "price": 70000.0
        }
        
        with patch('app.services.order_service.OrderService.create_order') as mock_create:
            mock_create.side_effect = ValueError("Insufficient funds")
            
            response = client.post("/api/v1/orders/", json=order_data, headers=auth_headers)
            assert response.status_code == 400
            assert "insufficient funds" in response.json()["detail"].lower()
    
    def test_get_orders(self, client: TestClient, auth_headers: dict, test_order: Order):
        """测试获取订单列表"""
        response = client.get("/api/v1/orders/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1
        
        order_data = data[0]
        assert order_data["id"] == str(test_order.id)
        assert order_data["symbol"] == test_order.symbol
        assert order_data["side"] == test_order.side
    
    def test_get_orders_with_filters(self, client: TestClient, auth_headers: dict, test_order: Order):
        """测试带过滤条件获取订单"""
        params = {
            "symbol": test_order.symbol,
            "status": "pending",
            "limit": 10
        }
        
        response = client.get("/api/v1/orders/", params=params, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        for order in data:
            assert order["symbol"] == test_order.symbol
            assert order["status"] == "pending"
    
    def test_get_order_by_id(self, client: TestClient, auth_headers: dict, test_order: Order):
        """测试根据ID获取订单"""
        response = client.get(f"/api/v1/orders/{test_order.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(test_order.id)
        assert data["symbol"] == test_order.symbol
        assert data["quantity"] == test_order.quantity
    
    def test_get_nonexistent_order(self, client: TestClient, auth_headers: dict):
        """测试获取不存在的订单"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/orders/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_cancel_order(self, client: TestClient, auth_headers: dict, test_order: Order, db_session: Session):
        """测试取消订单"""
        with patch('app.services.order_service.OrderService.cancel_order') as mock_cancel:
            mock_cancel.return_value = True
            
            response = client.post(f"/api/v1/orders/{test_order.id}/cancel", headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "cancelled"
    
    def test_cancel_nonexistent_order(self, client: TestClient, auth_headers: dict):
        """测试取消不存在的订单"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.post(f"/api/v1/orders/{fake_id}/cancel", headers=auth_headers)
        assert response.status_code == 404
    
    def test_cancel_filled_order(self, client: TestClient, auth_headers: dict, test_order: Order, db_session: Session):
        """测试取消已成交订单"""
        # 设置订单为已成交状态
        test_order.status = "filled"
        db_session.commit()
        
        response = client.post(f"/api/v1/orders/{test_order.id}/cancel", headers=auth_headers)
        assert response.status_code == 400
        assert "cannot be cancelled" in response.json()["detail"].lower()
    
    def test_modify_order(self, client: TestClient, auth_headers: dict, test_order: Order, db_session: Session):
        """测试修改订单"""
        modify_data = {
            "quantity": 2,
            "price": 71000.0
        }
        
        with patch('app.services.order_service.OrderService.modify_order') as mock_modify:
            mock_modify.return_value = {
                "id": str(test_order.id),
                "quantity": 2,
                "price": 71000.0,
                "status": "pending"
            }
            
            response = client.put(f"/api/v1/orders/{test_order.id}", json=modify_data, headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert data["quantity"] == modify_data["quantity"]
            assert data["price"] == modify_data["price"]
    
    def test_get_order_history(self, client: TestClient, auth_headers: dict, test_user: User):
        """测试获取订单历史"""
        response = client.get("/api/v1/orders/history", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestPositionAPI:
    """持仓API测试类"""
    
    def test_get_positions(self, client: TestClient, auth_headers: dict, test_position: Position):
        """测试获取持仓列表"""
        response = client.get("/api/v1/positions/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1
        
        position_data = data[0]
        assert position_data["symbol"] == test_position.symbol
        assert position_data["quantity"] == test_position.quantity
        assert position_data["avg_price"] == test_position.avg_price
    
    def test_get_position_by_symbol(self, client: TestClient, auth_headers: dict, test_position: Position):
        """测试根据合约获取持仓"""
        response = client.get(f"/api/v1/positions/{test_position.symbol}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["symbol"] == test_position.symbol
        assert data["quantity"] == test_position.quantity
        assert data["unrealized_pnl"] is not None
    
    def test_get_nonexistent_position(self, client: TestClient, auth_headers: dict):
        """测试获取不存在的持仓"""
        response = client.get("/api/v1/positions/NONEXISTENT.symbol", headers=auth_headers)
        assert response.status_code == 404
    
    def test_close_position(self, client: TestClient, auth_headers: dict, test_position: Position, db_session: Session):
        """测试平仓"""
        close_data = {
            "quantity": test_position.quantity,
            "price": 70500.0
        }
        
        with patch('app.services.position_service.PositionService.close_position') as mock_close:
            mock_close.return_value = {
                "order_id": "close_order_123",
                "status": "pending"
            }
            
            response = client.post(f"/api/v1/positions/{test_position.symbol}/close", json=close_data, headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert "order_id" in data
            assert data["status"] == "pending"
    
    def test_partial_close_position(self, client: TestClient, auth_headers: dict, test_position: Position):
        """测试部分平仓"""
        close_data = {
            "quantity": test_position.quantity // 2,  # 平一半
            "price": 70500.0
        }
        
        with patch('app.services.position_service.PositionService.close_position') as mock_close:
            mock_close.return_value = {
                "order_id": "partial_close_order_123",
                "status": "pending"
            }
            
            response = client.post(f"/api/v1/positions/{test_position.symbol}/close", json=close_data, headers=auth_headers)
            assert response.status_code == 200
    
    def test_get_position_pnl(self, client: TestClient, auth_headers: dict, test_position: Position):
        """测试获取持仓盈亏"""
        response = client.get(f"/api/v1/positions/{test_position.symbol}/pnl", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "realized_pnl" in data
        assert "unrealized_pnl" in data
        assert "total_pnl" in data


class TestAccountAPI:
    """账户API测试类"""
    
    def test_get_account_info(self, client: TestClient, auth_headers: dict):
        """测试获取账户信息"""
        with patch('app.services.account_service.AccountService.get_account_info') as mock_account:
            mock_account.return_value = {
                "balance": 100000.0,
                "available": 80000.0,
                "margin_used": 20000.0,
                "unrealized_pnl": 500.0
            }
            
            response = client.get("/api/v1/accounts/info", headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert data["balance"] == 100000.0
            assert data["available"] == 80000.0
            assert data["margin_used"] == 20000.0
    
    def test_get_account_summary(self, client: TestClient, auth_headers: dict):
        """测试获取账户摘要"""
        response = client.get("/api/v1/accounts/summary", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_equity" in data
        assert "day_pnl" in data
        assert "position_count" in data
        assert "order_count" in data
    
    def test_get_trading_statistics(self, client: TestClient, auth_headers: dict):
        """测试获取交易统计"""
        response = client.get("/api/v1/accounts/statistics", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_trades" in data
        assert "win_rate" in data
        assert "profit_factor" in data
        assert "max_drawdown" in data
    
    def test_get_margin_info(self, client: TestClient, auth_headers: dict):
        """测试获取保证金信息"""
        response = client.get("/api/v1/accounts/margin", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "initial_margin" in data
        assert "maintenance_margin" in data
        assert "margin_ratio" in data


class TestTradingFlow:
    """交易流程测试"""
    
    def test_complete_trading_flow(self, client: TestClient, auth_headers: dict, test_user: User, db_session: Session):
        """测试完整交易流程"""
        # 1. 检查账户信息
        with patch('app.services.account_service.AccountService.get_account_info') as mock_account:
            mock_account.return_value = {
                "balance": 100000.0,
                "available": 100000.0,
                "margin_used": 0.0
            }
            
            account_response = client.get("/api/v1/accounts/info", headers=auth_headers)
            assert account_response.status_code == 200
            assert account_response.json()["available"] > 0
        
        # 2. 创建买入订单
        buy_order_data = {
            "symbol": "SHFE.cu2401",
            "side": "buy",
            "order_type": "limit",
            "quantity": 1,
            "price": 70000.0
        }
        
        with patch('app.services.order_service.OrderService.create_order') as mock_create:
            mock_create.return_value = {
                "id": "buy_order_123",
                "status": "pending",
                **buy_order_data
            }
            
            buy_response = client.post("/api/v1/orders/", json=buy_order_data, headers=auth_headers)
            assert buy_response.status_code == 201
            buy_order_id = buy_response.json()["id"]
        
        # 3. 模拟订单成交，创建持仓
        position = Position(
            user_id=test_user.id,
            symbol="SHFE.cu2401",
            quantity=1,
            avg_price=70000.0,
            current_price=70500.0
        )
        db_session.add(position)
        db_session.commit()
        db_session.refresh(position)
        
        # 4. 检查持仓
        positions_response = client.get("/api/v1/positions/", headers=auth_headers)
        assert positions_response.status_code == 200
        positions = positions_response.json()
        assert len(positions) >= 1
        
        # 5. 检查持仓盈亏
        pnl_response = client.get(f"/api/v1/positions/{position.symbol}/pnl", headers=auth_headers)
        assert pnl_response.status_code == 200
        pnl_data = pnl_response.json()
        assert pnl_data["unrealized_pnl"] > 0  # 价格上涨，有浮盈
        
        # 6. 创建卖出订单平仓
        sell_order_data = {
            "symbol": "SHFE.cu2401",
            "side": "sell",
            "order_type": "market",
            "quantity": 1
        }
        
        with patch('app.services.order_service.OrderService.create_order') as mock_create_sell:
            mock_create_sell.return_value = {
                "id": "sell_order_123",
                "status": "filled",
                **sell_order_data
            }
            
            sell_response = client.post("/api/v1/orders/", json=sell_order_data, headers=auth_headers)
            assert sell_response.status_code == 201
        
        # 7. 检查订单历史
        history_response = client.get("/api/v1/orders/history", headers=auth_headers)
        assert history_response.status_code == 200
        history = history_response.json()
        assert len(history) >= 2  # 买入和卖出订单


class TestRiskControl:
    """风险控制测试"""
    
    def test_order_risk_check(self, client: TestClient, auth_headers: dict):
        """测试订单风险检查"""
        # 创建超过风险限制的大订单
        large_order_data = {
            "symbol": "SHFE.cu2401",
            "side": "buy",
            "order_type": "limit",
            "quantity": 100,  # 大量订单
            "price": 70000.0
        }
        
        with patch('app.services.risk_service.RiskService.check_order_risk') as mock_risk:
            mock_risk.side_effect = ValueError("Order exceeds position limit")
            
            response = client.post("/api/v1/orders/", json=large_order_data, headers=auth_headers)
            assert response.status_code == 400
            assert "position limit" in response.json()["detail"].lower()
    
    def test_margin_check(self, client: TestClient, auth_headers: dict):
        """测试保证金检查"""
        order_data = {
            "symbol": "SHFE.cu2401",
            "side": "buy",
            "order_type": "limit",
            "quantity": 1,
            "price": 70000.0
        }
        
        with patch('app.services.account_service.AccountService.check_margin') as mock_margin:
            mock_margin.return_value = False  # 保证金不足
            
            response = client.post("/api/v1/orders/", json=order_data, headers=auth_headers)
            assert response.status_code == 400
            assert "insufficient margin" in response.json()["detail"].lower()
    
    def test_daily_loss_limit(self, client: TestClient, auth_headers: dict):
        """测试日损失限制"""
        order_data = {
            "symbol": "SHFE.cu2401",
            "side": "buy",
            "order_type": "limit",
            "quantity": 1,
            "price": 70000.0
        }
        
        with patch('app.services.risk_service.RiskService.check_daily_loss') as mock_loss:
            mock_loss.side_effect = ValueError("Daily loss limit exceeded")
            
            response = client.post("/api/v1/orders/", json=order_data, headers=auth_headers)
            assert response.status_code == 400
            assert "daily loss limit" in response.json()["detail"].lower()


class TestTradingPermissions:
    """交易权限测试"""
    
    def test_user_cannot_access_others_orders(self, client: TestClient, db_session: Session):
        """测试用户无法访问他人订单"""
        from app.core.security import get_password_hash, create_access_token
        
        # 创建两个用户
        user1 = User(
            username="trader1",
            email="trader1@example.com",
            hashed_password=get_password_hash("pass123"),
            is_active=True
        )
        user2 = User(
            username="trader2",
            email="trader2@example.com",
            hashed_password=get_password_hash("pass123"),
            is_active=True
        )
        
        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)
        
        # 用户1创建订单
        order = Order(
            user_id=user1.id,
            symbol="SHFE.cu2401",
            side="buy",
            order_type="limit",
            quantity=1,
            price=70000.0,
            status="pending"
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        # 用户2尝试访问用户1的订单
        user2_token = create_access_token(data={"sub": user2.username})
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        response = client.get(f"/api/v1/orders/{order.id}", headers=user2_headers)
        assert response.status_code == 404  # 应该返回404而不是403，避免信息泄露