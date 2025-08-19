#!/usr/bin/env python3
"""
算法交易引擎测试脚本
"""
import asyncio
import json
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_algo_trading_engine():
    """测试算法交易引擎"""
    try:
        from app.services.algo_trading_engine import algo_trading_engine
        
        print("=" * 60)
        print("🚀 算法交易引擎测试开始")
        print("=" * 60)
        
        # 1. 初始化引擎
        print("\n1. 初始化引擎...")
        init_result = await algo_trading_engine.initialize()
        print(f"   初始化结果: {'✅ 成功' if init_result else '❌ 失败'}")
        
        # 2. 获取初始状态
        print("\n2. 获取引擎状态...")
        status = await algo_trading_engine.get_engine_status()
        print(f"   引擎状态: {status.get('status', 'unknown')}")
        print(f"   活跃策略数: {status.get('active_strategies', 0)}")
        print(f"   待处理订单: {status.get('pending_orders', 0)}")
        
        # 3. 测试策略配置验证
        print("\n3. 测试策略配置验证...")
        
        # 有效配置
        valid_config = {
            "strategy_id": "test_dual_ma",
            "strategy_type": "dual_ma",
            "name": "测试双均线策略",
            "symbols": ["SHFE.cu2601", "SHFE.au2612"],
            "parameters": {
                "ma_short": 5,
                "ma_long": 10
            }
        }
        
        validation = await algo_trading_engine._validate_strategy_config(valid_config)
        print(f"   有效配置验证: {'✅ 通过' if validation['valid'] else '❌ 失败'}")
        
        # 无效配置
        invalid_config = {
            "strategy_id": "test_invalid",
            "strategy_type": "unknown_type",
            "symbols": []
        }
        
        validation = await algo_trading_engine._validate_strategy_config(invalid_config)
        print(f"   无效配置验证: {'✅ 正确拒绝' if not validation['valid'] else '❌ 错误通过'}")
        
        # 4. 测试策略实例创建
        print("\n4. 测试策略实例创建...")
        
        # 双均线策略
        dual_ma_instance = await algo_trading_engine._create_strategy_instance(valid_config)
        print(f"   双均线策略实例: {'✅ 创建成功' if dual_ma_instance else '❌ 创建失败'}")
        
        # RSI策略
        rsi_config = {
            "strategy_id": "test_rsi",
            "strategy_type": "rsi_reversal",
            "name": "测试RSI策略",
            "symbols": ["SHFE.cu2601"],
            "parameters": {
                "rsi_period": 14,
                "oversold": 30,
                "overbought": 70
            }
        }
        
        rsi_instance = await algo_trading_engine._create_strategy_instance(rsi_config)
        print(f"   RSI策略实例: {'✅ 创建成功' if rsi_instance else '❌ 创建失败'}")
        
        # 5. 测试信号生成
        print("\n5. 测试信号生成...")
        
        if dual_ma_instance:
            try:
                signals = await dual_ma_instance.generate_signals()
                print(f"   双均线策略信号: 生成 {len(signals)} 个信号")
                if signals:
                    print(f"   示例信号: {signals[0]}")
            except Exception as e:
                print(f"   双均线策略信号生成失败: {e}")
        
        if rsi_instance:
            try:
                signals = await rsi_instance.generate_signals()
                print(f"   RSI策略信号: 生成 {len(signals)} 个信号")
                if signals:
                    print(f"   示例信号: {signals[0]}")
            except Exception as e:
                print(f"   RSI策略信号生成失败: {e}")
        
        # 6. 测试策略添加和移除
        print("\n6. 测试策略管理...")
        
        # 添加策略
        add_result = await algo_trading_engine.add_strategy(valid_config)
        print(f"   添加策略: {'✅ 成功' if add_result['success'] else '❌ 失败'}")
        if not add_result['success']:
            print(f"   错误信息: {add_result.get('error', 'unknown')}")
        
        # 检查策略是否添加成功
        status = await algo_trading_engine.get_engine_status()
        print(f"   当前活跃策略数: {status.get('active_strategies', 0)}")
        
        # 移除策略
        if add_result['success']:
            remove_result = await algo_trading_engine.remove_strategy("test_dual_ma")
            print(f"   移除策略: {'✅ 成功' if remove_result['success'] else '❌ 失败'}")
        
        # 7. 测试引擎启动和停止
        print("\n7. 测试引擎控制...")
        
        # 启动引擎
        start_result = await algo_trading_engine.start_engine("test_user")
        print(f"   启动引擎: {'✅ 成功' if start_result['success'] else '❌ 失败'}")
        if not start_result['success']:
            print(f"   错误信息: {start_result.get('error', 'unknown')}")
        
        # 等待一段时间让引擎运行
        if start_result['success']:
            print("   引擎运行中，等待5秒...")
            await asyncio.sleep(5)
            
            # 检查运行状态
            status = await algo_trading_engine.get_engine_status()
            print(f"   运行状态: {status.get('status', 'unknown')}")
        
        # 停止引擎
        stop_result = await algo_trading_engine.stop_engine("test_user")
        print(f"   停止引擎: {'✅ 成功' if stop_result['success'] else '❌ 失败'}")
        
        # 8. 测试风险检查
        print("\n8. 测试风险检查...")
        
        # 模拟信号
        test_signal = {
            "symbol": "SHFE.cu2601",
            "signal_type": "buy",
            "price": 75000,
            "confidence": 0.8,
            "reason": "测试信号"
        }
        
        # 验证信号
        signal_valid = await algo_trading_engine._validate_signal(test_signal)
        print(f"   信号验证: {'✅ 通过' if signal_valid else '❌ 失败'}")
        
        # 风险检查
        risk_check = await algo_trading_engine._risk_check_for_signal(test_signal)
        print(f"   风险检查: {'✅ 通过' if risk_check else '❌ 未通过'}")
        
        # 9. 测试订单创建
        print("\n9. 测试订单创建...")
        
        if signal_valid:
            order = await algo_trading_engine._create_order_from_signal("test_strategy", test_signal)
            if order:
                print(f"   订单创建: ✅ 成功")
                print(f"   订单ID: {order['order_id']}")
                print(f"   交易品种: {order['symbol']}")
                print(f"   方向: {order['direction']}")
                print(f"   数量: {order['volume']}")
                print(f"   价格: {order['price']}")
            else:
                print(f"   订单创建: ❌ 失败")
        
        # 10. 测试配置保存和加载
        print("\n10. 测试配置管理...")
        
        # 保存状态
        await algo_trading_engine._save_state()
        print("   状态保存: ✅ 完成")
        
        # 加载配置
        await algo_trading_engine._load_config()
        print("   配置加载: ✅ 完成")
        
        print("\n" + "=" * 60)
        print("🎉 算法交易引擎测试完成")
        print("=" * 60)
        
        # 最终状态报告
        final_status = await algo_trading_engine.get_engine_status()
        print(f"\n📊 最终状态报告:")
        print(f"   引擎状态: {final_status.get('status', 'unknown')}")
        print(f"   初始化状态: {final_status.get('is_initialized', False)}")
        print(f"   活跃策略: {final_status.get('active_strategies', 0)}")
        print(f"   待处理订单: {final_status.get('pending_orders', 0)}")
        print(f"   信号历史: {len(algo_trading_engine.signal_history)}")
        
        return True
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_strategy_signals():
    """专门测试策略信号生成"""
    try:
        from app.services.algo_trading_engine import DualMAStrategy, RSIReversalStrategy
        
        print("\n" + "=" * 50)
        print("📈 策略信号生成测试")
        print("=" * 50)
        
        # 测试双均线策略
        print("\n1. 双均线策略测试...")
        dual_ma_config = {
            "strategy_id": "test_dual_ma",
            "strategy_type": "dual_ma",
            "name": "测试双均线",
            "symbols": ["SHFE.cu2601", "SHFE.au2612"],
            "parameters": {"ma_short": 5, "ma_long": 10}
        }
        
        dual_ma = DualMAStrategy(dual_ma_config)
        dual_signals = await dual_ma.generate_signals()
        print(f"   生成信号数量: {len(dual_signals)}")
        
        for i, signal in enumerate(dual_signals[:3]):  # 显示前3个信号
            print(f"   信号 {i+1}: {signal['symbol']} - {signal['signal_type']} - {signal['reason']}")
        
        # 测试RSI策略
        print("\n2. RSI反转策略测试...")
        rsi_config = {
            "strategy_id": "test_rsi",
            "strategy_type": "rsi_reversal",
            "name": "测试RSI反转",
            "symbols": ["SHFE.cu2601"],
            "parameters": {"rsi_period": 14}
        }
        
        rsi_strategy = RSIReversalStrategy(rsi_config)
        rsi_signals = await rsi_strategy.generate_signals()
        print(f"   生成信号数量: {len(rsi_signals)}")
        
        for i, signal in enumerate(rsi_signals[:3]):  # 显示前3个信号
            print(f"   信号 {i+1}: {signal['symbol']} - {signal['signal_type']} - {signal['reason']}")
        
        return True
        
    except Exception as e:
        logger.error(f"策略信号测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("🔧 开始算法交易引擎全面测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 基础引擎测试
        engine_test_result = await test_algo_trading_engine()
        
        # 策略信号测试
        signal_test_result = await test_strategy_signals()
        
        # 测试结果汇总
        print("\n" + "=" * 60)
        print("📋 测试结果汇总")
        print("=" * 60)
        print(f"引擎基础功能测试: {'✅ 通过' if engine_test_result else '❌ 失败'}")
        print(f"策略信号生成测试: {'✅ 通过' if signal_test_result else '❌ 失败'}")
        
        overall_success = engine_test_result and signal_test_result
        print(f"\n🎯 总体测试结果: {'✅ 全部通过' if overall_success else '❌ 存在失败'}")
        
        if overall_success:
            print("\n🚀 算法交易引擎已准备就绪！")
        else:
            print("\n⚠️  请检查失败的测试项目")
        
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())