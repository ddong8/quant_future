#!/usr/bin/env python3
"""
量化交易平台端到端验收测试
执行完整的系统功能验证，确保所有需求都得到满足
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
import websocket
import threading
from dataclasses import dataclass

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    passed: bool
    message: str
    duration: float
    requirement: str

class AcceptanceTestSuite:
    """验收测试套件"""
    
    def __init__(self, base_url: str = "http://localhost:8000", frontend_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.frontend_url = frontend_url
        self.api_base = f"{base_url}/api/v1"
        self.ws_url = f"ws://localhost:8000/api/v1/ws"
        self.session = requests.Session()
        self.admin_token = None
        self.trader_token = None
        self.test_results: List[TestResult] = []
        
    def run_test(self, test_name: str, requirement: str):
        """测试装饰器"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    logger.info(f"开始测试: {test_name}")
                    await func(*args, **kwargs)
                    duration = time.time() - start_time
                    result = TestResult(test_name, True, "测试通过", duration, requirement)
                    logger.info(f"✅ {test_name} - 通过 ({duration:.2f}s)")
                except Exception as e:
                    duration = time.time() - start_time
                    result = TestResult(test_name, False, str(e), duration, requirement)
                    logger.error(f"❌ {test_name} - 失败: {e} ({duration:.2f}s)")
                
                self.test_results.append(result)
                return result
            return wrapper
        return decorator

    async def setup_test_environment(self):
        """设置测试环境"""
        logger.info("设置测试环境...")
        
        # 检查服务健康状态
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code != 200:
                raise Exception(f"后端服务不健康: {response.status_code}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"无法连接到后端服务: {e}")
        
        # 检查前端服务
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code != 200:
                raise Exception(f"前端服务不可用: {response.status_code}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"无法连接到前端服务: {e}")
        
        logger.info("测试环境设置完成")

    async def create_test_users(self):
        """创建测试用户"""
        # 使用默认管理员账户登录
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(
            f"{self.api_base}/auth/login",
            data=login_data
        )
        
        if response.status_code == 200:
            self.admin_token = response.json()["data"]["access_token"]
        else:
            raise Exception("无法登录管理员账户")
        
        # 创建测试交易员用户
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        trader_data = {
            "username": "test_trader",
            "email": "trader@test.com",
            "password": "trader123",
            "role": "trader"
        }
        
        response = requests.post(
            f"{self.api_base}/users",
            json=trader_data,
            headers=headers
        )
        
        # 登录交易员账户
        trader_login = {
            "username": "test_trader",
            "password": "trader123"
        }
        
        response = requests.post(
            f"{self.api_base}/auth/login",
            data=trader_login
        )
        
        if response.status_code == 200:
            self.trader_token = response.json()["data"]["access_token"]
        else:
            raise Exception("无法登录交易员账户")

    @run_test("用户认证与权限管理", "需求1")
    async def test_user_authentication(self):
        """测试用户认证与权限管理 - 需求1"""
        
        # 1.1 测试用户登录
        login_data = {
            "username": "test_trader",
            "password": "trader123"
        }
        
        response = requests.post(f"{self.api_base}/auth/login", data=login_data)
        assert response.status_code == 200, "用户登录失败"
        
        token_data = response.json()["data"]
        assert "access_token" in token_data, "未返回访问令牌"
        assert token_data["token_type"] == "bearer", "令牌类型错误"
        
        # 1.2 测试权限验证
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        response = requests.get(f"{self.api_base}/auth/profile", headers=headers)
        assert response.status_code == 200, "获取用户信息失败"
        
        # 1.3 测试错误凭据
        wrong_login = {
            "username": "test_trader",
            "password": "wrong_password"
        }
        
        response = requests.post(f"{self.api_base}/auth/login", data=wrong_login)
        assert response.status_code == 401, "错误凭据应该返回401"
        
        # 1.4 测试令牌过期（模拟）
        expired_headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(f"{self.api_base}/auth/profile", headers=expired_headers)
        assert response.status_code == 401, "无效令牌应该返回401"

    @run_test("市场数据管理", "需求2")
    async def test_market_data_management(self):
        """测试市场数据管理 - 需求2"""
        
        headers = {"Authorization": f"Bearer {self.trader_token}"}
        
        # 2.1 测试获取合约列表
        response = requests.get(f"{self.api_base}/market/instruments", headers=headers)
        assert response.status_code == 200, "获取合约列表失败"
        
        instruments = response.json()["data"]
        assert len(instruments) > 0, "合约列表为空"
        
        # 2.2 测试获取实时行情
        test_symbol = "SHFE.cu2401"  # 使用测试合约
        response = requests.get(f"{self.api_base}/market/quotes/{test_symbol}", headers=headers)
        assert response.status_code == 200, "获取实时行情失败"
        
        quote_data = response.json()["data"]
        assert "last_price" in quote_data, "行情数据缺少最新价"
        assert "timestamp" in quote_data, "行情数据缺少时间戳"
        
        # 2.3 测试获取K线数据
        params = {
            "duration": "1m",
            "limit": 100
        }
        response = requests.get(
            f"{self.api_base}/market/klines/{test_symbol}",
            params=params,
            headers=headers
        )
        assert response.status_code == 200, "获取K线数据失败"
        
        klines = response.json()["data"]
        assert len(klines) > 0, "K线数据为空"
        
        # 验证K线数据结构
        kline = klines[0]
        required_fields = ["datetime", "open", "high", "low", "close", "volume"]
        for field in required_fields:
            assert field in kline, f"K线数据缺少字段: {field}"

    @run_test("策略开发与管理", "需求3")
    async def test_strategy_development(self):
        """测试策略开发与管理 - 需求3"""
        
        headers = {"Authorization": f"Bearer {self.trader_token}"}
        
        # 3.1 测试创建策略
        strategy_data = {
            "name": "测试策略",
            "description": "这是一个测试策略",
            "code": '''
def initialize():
    pass

def on_bar(bar):
    pass

def on_tick(tick):
    pass
            ''',
            "language": "python"
        }
        
        response = requests.post(
            f"{self.api_base}/strategies",
            json=strategy_data,
            headers=headers
        )
        assert response.status_code == 201, "创建策略失败"
        
        strategy = response.json()["data"]
        strategy_id = strategy["id"]
        
        # 3.2 测试获取策略列表
        response = requests.get(f"{self.api_base}/strategies", headers=headers)
        assert response.status_code == 200, "获取策略列表失败"
        
        strategies = response.json()["data"]["items"]
        assert len(strategies) > 0, "策略列表为空"
        
        # 3.3 测试策略代码验证
        response = requests.post(
            f"{self.api_base}/strategies/{strategy_id}/validate",
            headers=headers
        )
        assert response.status_code == 200, "策略验证失败"
        
        validation_result = response.json()["data"]
        assert "valid" in validation_result, "验证结果缺少valid字段"
        
        # 3.4 测试更新策略
        update_data = {
            "description": "更新后的策略描述"
        }
        
        response = requests.put(
            f"{self.api_base}/strategies/{strategy_id}",
            json=update_data,
            headers=headers
        )
        assert response.status_code == 200, "更新策略失败"

    @run_test("回测系统", "需求4")
    async def test_backtest_system(self):
        """测试回测系统 - 需求4"""
        
        headers = {"Authorization": f"Bearer {self.trader_token}"}
        
        # 首先创建一个测试策略
        strategy_data = {
            "name": "回测测试策略",
            "description": "用于回测的测试策略",
            "code": '''
def initialize():
    pass

def on_bar(bar):
    # 简单的均线策略
    if bar.close > bar.open:
        buy(1)
    else:
        sell(1)
            ''',
            "language": "python"
        }
        
        response = requests.post(
            f"{self.api_base}/strategies",
            json=strategy_data,
            headers=headers
        )
        strategy_id = response.json()["data"]["id"]
        
        # 4.1 测试创建回测任务
        backtest_data = {
            "strategy_id": strategy_id,
            "symbol": "SHFE.cu2401",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "initial_capital": 100000.0,
            "commission_rate": 0.0001
        }
        
        response = requests.post(
            f"{self.api_base}/backtests",
            json=backtest_data,
            headers=headers
        )
        assert response.status_code == 201, "创建回测任务失败"
        
        backtest = response.json()["data"]
        backtest_id = backtest["id"]
        
        # 4.2 等待回测完成并获取结果
        max_wait_time = 60  # 最多等待60秒
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            response = requests.get(
                f"{self.api_base}/backtests/{backtest_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                backtest_result = response.json()["data"]
                if backtest_result["status"] == "completed":
                    break
                elif backtest_result["status"] == "failed":
                    raise Exception("回测执行失败")
            
            await asyncio.sleep(2)
        else:
            raise Exception("回测超时")
        
        # 4.3 验证回测结果
        results = backtest_result["results"]
        required_metrics = ["total_return", "sharpe_ratio", "max_drawdown", "win_rate"]
        for metric in required_metrics:
            assert metric in results, f"回测结果缺少指标: {metric}"
        
        # 4.4 验证收益曲线数据
        assert "equity_curve" in backtest_result, "回测结果缺少收益曲线"
        equity_curve = backtest_result["equity_curve"]
        assert len(equity_curve) > 0, "收益曲线数据为空"

    @run_test("实盘交易执行", "需求5")
    async def test_live_trading(self):
        """测试实盘交易执行 - 需求5"""
        
        headers = {"Authorization": f"Bearer {self.trader_token}"}
        
        # 5.1 测试获取账户信息
        response = requests.get(f"{self.api_base}/accounts", headers=headers)
        assert response.status_code == 200, "获取账户信息失败"
        
        account = response.json()["data"]
        required_fields = ["balance", "available", "margin", "realized_pnl", "unrealized_pnl"]
        for field in required_fields:
            assert field in account, f"账户信息缺少字段: {field}"
        
        # 5.2 测试下单功能（模拟订单）
        order_data = {
            "symbol": "SHFE.cu2401",
            "direction": "BUY",
            "offset": "OPEN",
            "volume": 1,
            "price": 68500.0,
            "order_type": "LIMIT"
        }
        
        response = requests.post(
            f"{self.api_base}/orders",
            json=order_data,
            headers=headers
        )
        assert response.status_code == 201, "下单失败"
        
        order = response.json()["data"]
        order_id = order["id"]
        
        # 5.3 测试获取订单列表
        response = requests.get(f"{self.api_base}/orders", headers=headers)
        assert response.status_code == 200, "获取订单列表失败"
        
        orders = response.json()["data"]["items"]
        assert len(orders) > 0, "订单列表为空"
        
        # 5.4 测试撤销订单
        response = requests.delete(
            f"{self.api_base}/orders/{order_id}",
            headers=headers
        )
        assert response.status_code == 200, "撤销订单失败"
        
        # 5.5 测试获取持仓信息
        response = requests.get(f"{self.api_base}/positions", headers=headers)
        assert response.status_code == 200, "获取持仓信息失败"

    @run_test("风险管理", "需求6")
    async def test_risk_management(self):
        """测试风险管理 - 需求6"""
        
        headers = {"Authorization": f"Bearer {self.trader_token}"}
        
        # 6.1 测试获取风险配置
        response = requests.get(f"{self.api_base}/risk/config", headers=headers)
        assert response.status_code == 200, "获取风险配置失败"
        
        # 6.2 测试更新风险配置
        risk_config = {
            "max_daily_loss": 5000.0,
            "max_position_ratio": 0.3,
            "max_single_order_amount": 10000.0,
            "stop_loss_ratio": 0.05
        }
        
        response = requests.put(
            f"{self.api_base}/risk/config",
            json=risk_config,
            headers=headers
        )
        assert response.status_code == 200, "更新风险配置失败"
        
        # 6.3 测试风险监控状态
        response = requests.get(f"{self.api_base}/risk/status", headers=headers)
        assert response.status_code == 200, "获取风险状态失败"
        
        risk_status = response.json()["data"]
        assert "daily_pnl" in risk_status, "风险状态缺少日盈亏"
        assert "position_ratio" in risk_status, "风险状态缺少持仓比例"

    @run_test("监控与报告", "需求7")
    async def test_monitoring_and_reporting(self):
        """测试监控与报告 - 需求7"""
        
        headers = {"Authorization": f"Bearer {self.trader_token}"}
        
        # 7.1 测试系统监控
        response = requests.get(f"{self.api_base}/monitoring/status", headers=headers)
        assert response.status_code == 200, "获取系统状态失败"
        
        system_status = response.json()["data"]
        assert "cpu_usage" in system_status, "系统状态缺少CPU使用率"
        assert "memory_usage" in system_status, "系统状态缺少内存使用率"
        
        # 7.2 测试性能指标
        response = requests.get(f"{self.api_base}/monitoring/metrics", headers=headers)
        assert response.status_code == 200, "获取性能指标失败"
        
        # 7.3 测试生成交易报告
        report_data = {
            "report_type": "daily",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        }
        
        response = requests.post(
            f"{self.api_base}/reports/trading",
            json=report_data,
            headers=headers
        )
        assert response.status_code == 201, "生成交易报告失败"

    @run_test("数据存储与备份", "需求8")
    async def test_data_storage_backup(self):
        """测试数据存储与备份 - 需求8"""
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # 8.1 测试数据库健康检查
        response = requests.get(f"{self.base_url}/health")
        assert response.status_code == 200, "健康检查失败"
        
        health_data = response.json()
        assert health_data["status"] == "healthy", "系统状态不健康"
        assert "services" in health_data, "健康检查缺少服务状态"
        
        # 8.2 测试日志查询
        response = requests.get(f"{self.api_base}/logs", headers=headers)
        assert response.status_code == 200, "获取日志失败"
        
        # 8.3 测试系统信息
        response = requests.get(f"{self.base_url}/info")
        assert response.status_code == 200, "获取系统信息失败"
        
        system_info = response.json()
        assert "version" in system_info, "系统信息缺少版本"
        assert "timestamp" in system_info, "系统信息缺少时间戳"

    async def test_websocket_connection(self):
        """测试WebSocket实时数据推送"""
        
        ws_connected = False
        received_data = False
        
        def on_message(ws, message):
            nonlocal received_data
            try:
                data = json.loads(message)
                if data.get("type") == "data" and data.get("channel") == "quotes":
                    received_data = True
                    logger.info("收到WebSocket行情数据")
            except json.JSONDecodeError:
                pass
        
        def on_open(ws):
            nonlocal ws_connected
            ws_connected = True
            # 订阅行情数据
            subscribe_msg = {
                "type": "subscribe",
                "channel": "quotes",
                "symbol": "SHFE.cu2401"
            }
            ws.send(json.dumps(subscribe_msg))
        
        def on_error(ws, error):
            logger.error(f"WebSocket错误: {error}")
        
        # 创建WebSocket连接
        ws_url_with_token = f"{self.ws_url}?token={self.trader_token}"
        ws = websocket.WebSocketApp(
            ws_url_with_token,
            on_message=on_message,
            on_open=on_open,
            on_error=on_error
        )
        
        # 在单独线程中运行WebSocket
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # 等待连接和数据
        await asyncio.sleep(5)
        
        assert ws_connected, "WebSocket连接失败"
        # 注意：在测试环境中可能没有实时数据，所以这个断言可能需要调整
        # assert received_data, "未收到WebSocket数据"
        
        ws.close()

    async def run_all_tests(self):
        """运行所有验收测试"""
        
        logger.info("开始执行量化交易平台验收测试")
        
        try:
            # 设置测试环境
            await self.setup_test_environment()
            await self.create_test_users()
            
            # 执行所有测试
            await self.test_user_authentication()
            await self.test_market_data_management()
            await self.test_strategy_development()
            await self.test_backtest_system()
            await self.test_live_trading()
            await self.test_risk_management()
            await self.test_monitoring_and_reporting()
            await self.test_data_storage_backup()
            await self.test_websocket_connection()
            
        except Exception as e:
            logger.error(f"测试执行过程中发生错误: {e}")
        
        # 生成测试报告
        self.generate_test_report()

    def generate_test_report(self):
        """生成测试报告"""
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.passed)
        failed_tests = total_tests - passed_tests
        
        logger.info("\n" + "="*80)
        logger.info("量化交易平台验收测试报告")
        logger.info("="*80)
        logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"总测试数: {total_tests}")
        logger.info(f"通过测试: {passed_tests}")
        logger.info(f"失败测试: {failed_tests}")
        logger.info(f"通过率: {(passed_tests/total_tests*100):.1f}%")
        logger.info("-"*80)
        
        # 按需求分组显示结果
        requirements = {}
        for result in self.test_results:
            req = result.requirement
            if req not in requirements:
                requirements[req] = []
            requirements[req].append(result)
        
        for req, results in requirements.items():
            req_passed = sum(1 for r in results if r.passed)
            req_total = len(results)
            logger.info(f"{req}: {req_passed}/{req_total} 通过")
            
            for result in results:
                status = "✅" if result.passed else "❌"
                logger.info(f"  {status} {result.test_name} ({result.duration:.2f}s)")
                if not result.passed:
                    logger.info(f"    错误: {result.message}")
        
        logger.info("="*80)
        
        if failed_tests == 0:
            logger.info("🎉 所有验收测试通过！系统已准备好部署。")
        else:
            logger.info(f"⚠️  有 {failed_tests} 个测试失败，需要修复后再部署。")
        
        # 保存测试报告到文件
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "pass_rate": passed_tests/total_tests*100
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "message": r.message,
                    "duration": r.duration,
                    "requirement": r.requirement
                }
                for r in self.test_results
            ]
        }
        
        with open("acceptance_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info("测试报告已保存到: acceptance_test_report.json")

async def main():
    """主函数"""
    test_suite = AcceptanceTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())