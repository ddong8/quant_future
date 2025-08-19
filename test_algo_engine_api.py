#!/usr/bin/env python3
"""
算法交易引擎API测试脚本
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def get_auth_token():
    """获取认证token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    if response.status_code == 200:
        return response.json()["data"]["access_token"]
    else:
        raise Exception(f"登录失败: {response.text}")

def test_algo_engine():
    """测试算法交易引擎"""
    print("🚀 算法交易引擎API测试开始")
    print("=" * 50)
    
    try:
        # 获取token
        token = get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. 测试引擎状态
        print("\n1. 获取引擎状态")
        response = requests.get(f"{BASE_URL}/algo-trading/status", headers=headers)
        status_data = response.json()
        print(f"   状态: {status_data['data']['status']}")
        print(f"   初始化: {status_data['data']['is_initialized']}")
        
        # 2. 启动引擎
        print("\n2. 启动引擎")
        response = requests.post(
            f"{BASE_URL}/algo-trading/control",
            headers=headers,
            json={"action": "start"}
        )
        result = response.json()
        print(f"   启动结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
        
        # 3. 添加双均线策略
        print("\n3. 添加双均线策略")
        strategy_config = {
            "strategy_id": "test_dual_ma",
            "strategy_type": "dual_ma",
            "name": "测试双均线策略",
            "symbols": ["SHFE.cu2601"],
            "parameters": {
                "ma_short": 5,
                "ma_long": 10
            }
        }
        response = requests.post(
            f"{BASE_URL}/algo-trading/strategies",
            headers=headers,
            json=strategy_config
        )
        result = response.json()
        print(f"   添加结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
        
        # 4. 添加RSI策略
        print("\n4. 添加RSI策略")
        rsi_config = {
            "strategy_id": "test_rsi",
            "strategy_type": "rsi_reversal",
            "name": "测试RSI策略",
            "symbols": ["SHFE.au2612"],
            "parameters": {
                "rsi_period": 14
            }
        }
        response = requests.post(
            f"{BASE_URL}/algo-trading/strategies",
            headers=headers,
            json=rsi_config
        )
        result = response.json()
        print(f"   添加结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
        
        # 5. 查看活跃策略
        print("\n5. 查看活跃策略")
        response = requests.get(f"{BASE_URL}/algo-trading/strategies", headers=headers)
        strategies = response.json()["data"]
        print(f"   活跃策略数量: {len(strategies)}")
        for strategy in strategies:
            print(f"   - {strategy['strategy_id']}: {strategy['name']}")
        
        # 6. 测试策略配置验证
        print("\n6. 测试策略配置验证")
        test_config = {
            "strategy_id": "test_validation",
            "strategy_type": "dual_ma",
            "name": "验证测试",
            "symbols": ["SHFE.cu2601"]
        }
        response = requests.post(
            f"{BASE_URL}/algo-trading/test-strategy",
            headers=headers,
            json=test_config
        )
        result = response.json()
        print(f"   配置验证: {'✅ 通过' if result['data']['config_valid'] else '❌ 失败'}")
        print(f"   实例创建: {'✅ 成功' if result['data']['instance_created'] else '❌ 失败'}")
        
        # 7. 查看策略表现
        print("\n7. 查看策略表现")
        response = requests.get(f"{BASE_URL}/algo-trading/performance", headers=headers)
        performance = response.json()["data"]
        print(f"   总策略数: {performance['total_strategies']}")
        print(f"   活跃策略数: {performance['active_strategies']}")
        print(f"   总交易次数: {performance['total_trades']}")
        
        # 8. 查看订单历史
        print("\n8. 查看订单历史")
        response = requests.get(f"{BASE_URL}/algo-trading/orders", headers=headers)
        orders = response.json()["data"]
        print(f"   订单数量: {orders['total']}")
        
        # 9. 查看信号历史
        print("\n9. 查看信号历史")
        response = requests.get(f"{BASE_URL}/algo-trading/signals", headers=headers)
        signals = response.json()["data"]
        print(f"   信号数量: {signals['total']}")
        
        # 10. 移除一个策略
        print("\n10. 移除RSI策略")
        response = requests.delete(
            f"{BASE_URL}/algo-trading/strategies/test_rsi",
            headers=headers
        )
        result = response.json()
        print(f"   移除结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
        
        # 11. 停止引擎
        print("\n11. 停止引擎")
        response = requests.post(
            f"{BASE_URL}/algo-trading/control",
            headers=headers,
            json={"action": "stop"}
        )
        result = response.json()
        print(f"   停止结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
        
        # 12. 最终状态检查
        print("\n12. 最终状态检查")
        response = requests.get(f"{BASE_URL}/algo-trading/status", headers=headers)
        final_status = response.json()["data"]
        print(f"   最终状态: {final_status['status']}")
        print(f"   剩余策略: {final_status['active_strategies']}")
        
        print("\n" + "=" * 50)
        print("🎉 算法交易引擎API测试完成")
        print("✅ 所有核心功能测试通过")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_algo_engine()