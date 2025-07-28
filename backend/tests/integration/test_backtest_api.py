"""
回测API集成测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.backtest import Backtest
from app.models.strategy import Strategy
from app.models.user import User


class TestBacktestAPI:
    """回测API测试类"""
    
    def test_create_backtest(self, client: TestClient, auth_headers: dict, test_strategy: Strategy, test_user: User, db_session: Session):
        """测试创建回测"""
        backtest_data = {
            "name": "New Backtest",
            "strategy_id": str(test_strategy.id),
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 100000.0,
            "benchmark": "SHFE.cu2401",
            "parameters": {
                "commission_rate": 0.0003,
                "slippage": 0.0001
            }
        }
        
        response = client.post("/api/v1/backtests/", json=backtest_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == backtest_data["name"]
        assert data["strategy_id"] == backtest_data["strategy_id"]
        assert data["user_id"] == str(test_user.id)
        assert data["status"] == "pending"
        
        # 验证数据库中的回测
        backtest = db_session.query(Backtest).filter(Backtest.id == data["id"]).first()
        assert backtest is not None
        assert backtest.name == backtest_data["name"]
    
    def test_create_backtest_with_nonexistent_strategy(self, client: TestClient, auth_headers: dict):
        """测试使用不存在策略创建回测"""
        fake_strategy_id = "00000000-0000-0000-0000-000000000000"
        backtest_data = {
            "name": "Invalid Backtest",
            "strategy_id": fake_strategy_id,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 100000.0
        }
        
        response = client.post("/api/v1/backtests/", json=backtest_data, headers=auth_headers)
        assert response.status_code == 404
        assert "Strategy not found" in response.json()["detail"]
    
    def test_get_backtests(self, client: TestClient, auth_headers: dict, test_backtest: Backtest):
        """测试获取回测列表"""
        response = client.get("/api/v1/backtests/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1
        
        backtest_data = data[0]
        assert backtest_data["id"] == str(test_backtest.id)
        assert backtest_data["name"] == test_backtest.name
    
    def test_get_backtest_by_id(self, client: TestClient, auth_headers: dict, test_backtest: Backtest):
        """测试根据ID获取回测"""
        response = client.get(f"/api/v1/backtests/{test_backtest.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(test_backtest.id)
        assert data["name"] == test_backtest.name
        assert data["start_date"] == test_backtest.start_date
        assert data["end_date"] == test_backtest.end_date
    
    def test_get_nonexistent_backtest(self, client: TestClient, auth_headers: dict):
        """测试获取不存在的回测"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/backtests/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_update_backtest(self, client: TestClient, auth_headers: dict, test_backtest: Backtest, db_session: Session):
        """测试更新回测"""
        update_data = {
            "name": "Updated Backtest",
            "initial_capital": 200000.0,
            "parameters": {
                "commission_rate": 0.0005,
                "slippage": 0.0002
            }
        }
        
        response = client.put(f"/api/v1/backtests/{test_backtest.id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["initial_capital"] == update_data["initial_capital"]
        
        # 验证数据库更新
        db_session.refresh(test_backtest)
        assert test_backtest.name == update_data["name"]
        assert test_backtest.initial_capital == update_data["initial_capital"]
    
    def test_delete_backtest(self, client: TestClient, auth_headers: dict, test_backtest: Backtest, db_session: Session):
        """测试删除回测"""
        backtest_id = test_backtest.id
        
        response = client.delete(f"/api/v1/backtests/{backtest_id}", headers=auth_headers)
        assert response.status_code == 204
        
        # 验证回测已删除
        deleted_backtest = db_session.query(Backtest).filter(Backtest.id == backtest_id).first()
        assert deleted_backtest is None
    
    def test_start_backtest(self, client: TestClient, auth_headers: dict, test_backtest: Backtest, db_session: Session):
        """测试启动回测"""
        response = client.post(f"/api/v1/backtests/{test_backtest.id}/start", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "running"
        
        # 验证状态更新
        db_session.refresh(test_backtest)
        assert test_backtest.status == "running"
    
    def test_start_already_running_backtest(self, client: TestClient, auth_headers: dict, test_backtest: Backtest, db_session: Session):
        """测试启动已运行的回测"""
        # 设置回测为运行状态
        test_backtest.status = "running"
        db_session.commit()
        
        response = client.post(f"/api/v1/backtests/{test_backtest.id}/start", headers=auth_headers)
        assert response.status_code == 400
        assert "already running" in response.json()["detail"].lower()
    
    def test_stop_backtest(self, client: TestClient, auth_headers: dict, test_backtest: Backtest, db_session: Session):
        """测试停止回测"""
        # 设置回测为运行状态
        test_backtest.status = "running"
        db_session.commit()
        
        response = client.post(f"/api/v1/backtests/{test_backtest.id}/stop", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "stopped"
        
        # 验证状态更新
        db_session.refresh(test_backtest)
        assert test_backtest.status == "stopped"
    
    def test_get_backtest_results(self, client: TestClient, auth_headers: dict, test_backtest: Backtest, db_session: Session):
        """测试获取回测结果"""
        # 设置回测为完成状态
        test_backtest.status = "completed"
        test_backtest.total_return = 0.15
        test_backtest.sharpe_ratio = 1.2
        test_backtest.max_drawdown = -0.08
        db_session.commit()
        
        response = client.get(f"/api/v1/backtests/{test_backtest.id}/results", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "performance_metrics" in data
        assert "equity_curve" in data
        assert "trades" in data
        
        metrics = data["performance_metrics"]
        assert metrics["total_return"] == 0.15
        assert metrics["sharpe_ratio"] == 1.2
        assert metrics["max_drawdown"] == -0.08
    
    def test_get_results_for_pending_backtest(self, client: TestClient, auth_headers: dict, test_backtest: Backtest):
        """测试获取未完成回测的结果"""
        response = client.get(f"/api/v1/backtests/{test_backtest.id}/results", headers=auth_headers)
        assert response.status_code == 400
        assert "not completed" in response.json()["detail"].lower()
    
    def test_get_backtest_progress(self, client: TestClient, auth_headers: dict, test_backtest: Backtest, db_session: Session):
        """测试获取回测进度"""
        # 设置回测为运行状态
        test_backtest.status = "running"
        db_session.commit()
        
        response = client.get(f"/api/v1/backtests/{test_backtest.id}/progress", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "progress_percentage" in data
        assert "current_date" in data
        assert "estimated_completion" in data
    
    def test_get_backtest_logs(self, client: TestClient, auth_headers: dict, test_backtest: Backtest):
        """测试获取回测日志"""
        response = client.get(f"/api/v1/backtests/{test_backtest.id}/logs", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_compare_backtests(self, client: TestClient, auth_headers: dict, test_backtest: Backtest, test_strategy: Strategy, db_session: Session):
        """测试比较回测"""
        # 创建第二个回测
        backtest2 = Backtest(
            name="Comparison Backtest",
            strategy_id=test_strategy.id,
            user_id=test_strategy.user_id,
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_capital=100000.0,
            status="completed",
            total_return=0.12,
            sharpe_ratio=1.0,
            max_drawdown=-0.06
        )
        db_session.add(backtest2)
        db_session.commit()
        db_session.refresh(backtest2)
        
        # 设置第一个回测为完成状态
        test_backtest.status = "completed"
        test_backtest.total_return = 0.15
        test_backtest.sharpe_ratio = 1.2
        test_backtest.max_drawdown = -0.08
        db_session.commit()
        
        compare_data = {
            "backtest_ids": [str(test_backtest.id), str(backtest2.id)]
        }
        
        response = client.post("/api/v1/backtests/compare", json=compare_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "comparison_metrics" in data
        assert "performance_chart" in data
        assert len(data["comparison_metrics"]) == 2
    
    def test_export_backtest_report(self, client: TestClient, auth_headers: dict, test_backtest: Backtest, db_session: Session):
        """测试导出回测报告"""
        # 设置回测为完成状态
        test_backtest.status = "completed"
        db_session.commit()
        
        export_data = {
            "format": "pdf",
            "include_charts": True,
            "include_trades": True
        }
        
        response = client.post(f"/api/v1/backtests/{test_backtest.id}/export", json=export_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "download_url" in data
        assert "file_size" in data
    
    def test_clone_backtest(self, client: TestClient, auth_headers: dict, test_backtest: Backtest, db_session: Session):
        """测试克隆回测"""
        clone_data = {
            "name": "Cloned Backtest",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }
        
        response = client.post(f"/api/v1/backtests/{test_backtest.id}/clone", json=clone_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == clone_data["name"]
        assert data["strategy_id"] == str(test_backtest.strategy_id)
        assert data["id"] != str(test_backtest.id)
        
        # 验证克隆的回测存在
        cloned_backtest = db_session.query(Backtest).filter(Backtest.id == data["id"]).first()
        assert cloned_backtest is not None
        assert cloned_backtest.name == clone_data["name"]


class TestBacktestValidation:
    """回测验证测试"""
    
    def test_create_backtest_invalid_date_range(self, client: TestClient, auth_headers: dict, test_strategy: Strategy):
        """测试无效日期范围创建回测"""
        backtest_data = {
            "name": "Invalid Date Backtest",
            "strategy_id": str(test_strategy.id),
            "start_date": "2023-12-31",
            "end_date": "2023-01-01",  # 结束日期早于开始日期
            "initial_capital": 100000.0
        }
        
        response = client.post("/api/v1/backtests/", json=backtest_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_create_backtest_negative_capital(self, client: TestClient, auth_headers: dict, test_strategy: Strategy):
        """测试负初始资金创建回测"""
        backtest_data = {
            "name": "Negative Capital Backtest",
            "strategy_id": str(test_strategy.id),
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": -100000.0
        }
        
        response = client.post("/api/v1/backtests/", json=backtest_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_create_backtest_future_dates(self, client: TestClient, auth_headers: dict, test_strategy: Strategy):
        """测试未来日期创建回测"""
        backtest_data = {
            "name": "Future Date Backtest",
            "strategy_id": str(test_strategy.id),
            "start_date": "2030-01-01",
            "end_date": "2030-12-31",
            "initial_capital": 100000.0
        }
        
        response = client.post("/api/v1/backtests/", json=backtest_data, headers=auth_headers)
        assert response.status_code == 400
        assert "future" in response.json()["detail"].lower()


class TestBacktestPermissions:
    """回测权限测试"""
    
    def test_user_cannot_access_others_backtest(self, client: TestClient, db_session: Session):
        """测试用户无法访问他人回测"""
        from app.core.security import get_password_hash, create_access_token
        
        # 创建两个用户
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
        
        # 用户1创建策略和回测
        strategy = Strategy(
            name="User1 Strategy",
            description="Private strategy",
            code="def initialize(context): pass",
            user_id=user1.id
        )
        db_session.add(strategy)
        db_session.commit()
        db_session.refresh(strategy)
        
        backtest = Backtest(
            name="User1 Backtest",
            strategy_id=strategy.id,
            user_id=user1.id,
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_capital=100000.0
        )
        db_session.add(backtest)
        db_session.commit()
        db_session.refresh(backtest)
        
        # 用户2尝试访问用户1的回测
        user2_token = create_access_token(data={"sub": user2.username})
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        response = client.get(f"/api/v1/backtests/{backtest.id}", headers=user2_headers)
        assert response.status_code == 404  # 应该返回404而不是403，避免信息泄露


class TestBacktestFlow:
    """回测流程测试"""
    
    def test_complete_backtest_flow(self, client: TestClient, auth_headers: dict, test_strategy: Strategy, db_session: Session):
        """测试完整回测流程"""
        # 1. 创建回测
        backtest_data = {
            "name": "Flow Test Backtest",
            "strategy_id": str(test_strategy.id),
            "start_date": "2023-01-01",
            "end_date": "2023-03-31",
            "initial_capital": 100000.0
        }
        
        create_response = client.post("/api/v1/backtests/", json=backtest_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        backtest_id = create_response.json()["id"]
        
        # 2. 启动回测
        start_response = client.post(f"/api/v1/backtests/{backtest_id}/start", headers=auth_headers)
        assert start_response.status_code == 200
        assert start_response.json()["status"] == "running"
        
        # 3. 检查进度
        progress_response = client.get(f"/api/v1/backtests/{backtest_id}/progress", headers=auth_headers)
        assert progress_response.status_code == 200
        
        # 4. 模拟完成回测
        backtest = db_session.query(Backtest).filter(Backtest.id == backtest_id).first()
        backtest.status = "completed"
        backtest.total_return = 0.15
        backtest.sharpe_ratio = 1.2
        backtest.max_drawdown = -0.08
        db_session.commit()
        
        # 5. 获取结果
        results_response = client.get(f"/api/v1/backtests/{backtest_id}/results", headers=auth_headers)
        assert results_response.status_code == 200
        
        results = results_response.json()
        assert results["performance_metrics"]["total_return"] == 0.15
        
        # 6. 导出报告
        export_data = {"format": "pdf"}
        export_response = client.post(f"/api/v1/backtests/{backtest_id}/export", json=export_data, headers=auth_headers)
        assert export_response.status_code == 200
        
        # 7. 克隆回测
        clone_data = {"name": "Cloned Flow Test"}
        clone_response = client.post(f"/api/v1/backtests/{backtest_id}/clone", json=clone_data, headers=auth_headers)
        assert clone_response.status_code == 201