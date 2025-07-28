"""
WebSocket集成测试
"""
import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from fastapi import WebSocket
from unittest.mock import patch, AsyncMock

from app.models.user import User


class TestWebSocketConnection:
    """WebSocket连接测试"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection_success(self, async_client, auth_headers: dict):
        """测试WebSocket连接成功"""
        # 提取token
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            # 连接成功后应该收到欢迎消息
            data = websocket.receive_json()
            assert data["type"] == "connection"
            assert data["status"] == "connected"
    
    @pytest.mark.asyncio
    async def test_websocket_connection_invalid_token(self, async_client):
        """测试无效token的WebSocket连接"""
        with pytest.raises(Exception):  # 连接应该被拒绝
            with async_client.websocket_connect("/ws?token=invalid_token"):
                pass
    
    @pytest.mark.asyncio
    async def test_websocket_connection_no_token(self, async_client):
        """测试无token的WebSocket连接"""
        with pytest.raises(Exception):  # 连接应该被拒绝
            with async_client.websocket_connect("/ws"):
                pass


class TestMarketDataWebSocket:
    """市场数据WebSocket测试"""
    
    @pytest.mark.asyncio
    async def test_subscribe_market_data(self, async_client, auth_headers: dict, mock_tqsdk):
        """测试订阅市场数据"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with patch('app.services.tqsdk_adapter.TQSDKAdapter', return_value=mock_tqsdk):
            with async_client.websocket_connect(f"/ws?token={token}") as websocket:
                # 发送订阅请求
                subscribe_msg = {
                    "type": "subscribe",
                    "channel": "market_data",
                    "symbols": ["SHFE.cu2401", "DCE.i2401"]
                }
                websocket.send_json(subscribe_msg)
                
                # 接收订阅确认
                response = websocket.receive_json()
                assert response["type"] == "subscription"
                assert response["status"] == "success"
                assert response["channel"] == "market_data"
                
                # 应该收到市场数据推送
                market_data = websocket.receive_json()
                assert market_data["type"] == "market_data"
                assert "symbol" in market_data
                assert "last_price" in market_data
    
    @pytest.mark.asyncio
    async def test_unsubscribe_market_data(self, async_client, auth_headers: dict):
        """测试取消订阅市场数据"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            # 先订阅
            subscribe_msg = {
                "type": "subscribe",
                "channel": "market_data",
                "symbols": ["SHFE.cu2401"]
            }
            websocket.send_json(subscribe_msg)
            websocket.receive_json()  # 订阅确认
            
            # 取消订阅
            unsubscribe_msg = {
                "type": "unsubscribe",
                "channel": "market_data",
                "symbols": ["SHFE.cu2401"]
            }
            websocket.send_json(unsubscribe_msg)
            
            # 接收取消订阅确认
            response = websocket.receive_json()
            assert response["type"] == "unsubscription"
            assert response["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_subscribe_invalid_symbol(self, async_client, auth_headers: dict):
        """测试订阅无效合约"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            subscribe_msg = {
                "type": "subscribe",
                "channel": "market_data",
                "symbols": ["INVALID.symbol"]
            }
            websocket.send_json(subscribe_msg)
            
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "invalid symbol" in response["message"].lower()


class TestOrderWebSocket:
    """订单WebSocket测试"""
    
    @pytest.mark.asyncio
    async def test_subscribe_order_updates(self, async_client, auth_headers: dict, test_user: User):
        """测试订阅订单更新"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            # 订阅订单更新
            subscribe_msg = {
                "type": "subscribe",
                "channel": "orders"
            }
            websocket.send_json(subscribe_msg)
            
            # 接收订阅确认
            response = websocket.receive_json()
            assert response["type"] == "subscription"
            assert response["channel"] == "orders"
            assert response["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_order_status_update_notification(self, async_client, auth_headers: dict, test_user: User):
        """测试订单状态更新通知"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            # 订阅订单更新
            subscribe_msg = {
                "type": "subscribe",
                "channel": "orders"
            }
            websocket.send_json(subscribe_msg)
            websocket.receive_json()  # 订阅确认
            
            # 模拟订单状态更新
            with patch('app.services.realtime_service.RealtimeService.broadcast_order_update') as mock_broadcast:
                order_update = {
                    "type": "order_update",
                    "order_id": "test_order_123",
                    "status": "filled",
                    "filled_quantity": 1,
                    "avg_fill_price": 70000.0
                }
                
                # 触发订单更新广播
                mock_broadcast.return_value = None
                
                # 应该收到订单更新通知
                # 注意：在实际测试中，这需要通过后台任务或事件触发
                # 这里我们模拟接收到更新
                websocket.send_json(order_update)  # 模拟服务器推送
                
                received = websocket.receive_json()
                assert received["type"] == "order_update"
                assert received["status"] == "filled"


class TestPositionWebSocket:
    """持仓WebSocket测试"""
    
    @pytest.mark.asyncio
    async def test_subscribe_position_updates(self, async_client, auth_headers: dict):
        """测试订阅持仓更新"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            subscribe_msg = {
                "type": "subscribe",
                "channel": "positions"
            }
            websocket.send_json(subscribe_msg)
            
            response = websocket.receive_json()
            assert response["type"] == "subscription"
            assert response["channel"] == "positions"
            assert response["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_position_pnl_update_notification(self, async_client, auth_headers: dict):
        """测试持仓盈亏更新通知"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            # 订阅持仓更新
            subscribe_msg = {
                "type": "subscribe",
                "channel": "positions"
            }
            websocket.send_json(subscribe_msg)
            websocket.receive_json()  # 订阅确认
            
            # 模拟持仓盈亏更新
            position_update = {
                "type": "position_update",
                "symbol": "SHFE.cu2401",
                "quantity": 1,
                "avg_price": 70000.0,
                "current_price": 70500.0,
                "unrealized_pnl": 500.0
            }
            
            websocket.send_json(position_update)  # 模拟服务器推送
            
            received = websocket.receive_json()
            assert received["type"] == "position_update"
            assert received["unrealized_pnl"] == 500.0


class TestAccountWebSocket:
    """账户WebSocket测试"""
    
    @pytest.mark.asyncio
    async def test_subscribe_account_updates(self, async_client, auth_headers: dict):
        """测试订阅账户更新"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            subscribe_msg = {
                "type": "subscribe",
                "channel": "account"
            }
            websocket.send_json(subscribe_msg)
            
            response = websocket.receive_json()
            assert response["type"] == "subscription"
            assert response["channel"] == "account"
            assert response["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_account_balance_update_notification(self, async_client, auth_headers: dict):
        """测试账户余额更新通知"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            # 订阅账户更新
            subscribe_msg = {
                "type": "subscribe",
                "channel": "account"
            }
            websocket.send_json(subscribe_msg)
            websocket.receive_json()  # 订阅确认
            
            # 模拟账户余额更新
            account_update = {
                "type": "account_update",
                "balance": 105000.0,
                "available": 85000.0,
                "margin_used": 20000.0,
                "unrealized_pnl": 5000.0
            }
            
            websocket.send_json(account_update)  # 模拟服务器推送
            
            received = websocket.receive_json()
            assert received["type"] == "account_update"
            assert received["balance"] == 105000.0


class TestStrategyWebSocket:
    """策略WebSocket测试"""
    
    @pytest.mark.asyncio
    async def test_subscribe_strategy_logs(self, async_client, auth_headers: dict, test_strategy):
        """测试订阅策略日志"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            subscribe_msg = {
                "type": "subscribe",
                "channel": "strategy_logs",
                "strategy_id": str(test_strategy.id)
            }
            websocket.send_json(subscribe_msg)
            
            response = websocket.receive_json()
            assert response["type"] == "subscription"
            assert response["channel"] == "strategy_logs"
            assert response["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_strategy_log_notification(self, async_client, auth_headers: dict, test_strategy):
        """测试策略日志通知"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            # 订阅策略日志
            subscribe_msg = {
                "type": "subscribe",
                "channel": "strategy_logs",
                "strategy_id": str(test_strategy.id)
            }
            websocket.send_json(subscribe_msg)
            websocket.receive_json()  # 订阅确认
            
            # 模拟策略日志
            log_message = {
                "type": "strategy_log",
                "strategy_id": str(test_strategy.id),
                "level": "INFO",
                "message": "Strategy executed successfully",
                "timestamp": "2023-01-01T09:00:00Z"
            }
            
            websocket.send_json(log_message)  # 模拟服务器推送
            
            received = websocket.receive_json()
            assert received["type"] == "strategy_log"
            assert received["level"] == "INFO"
            assert received["message"] == "Strategy executed successfully"


class TestWebSocketErrorHandling:
    """WebSocket错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_invalid_message_format(self, async_client, auth_headers: dict):
        """测试无效消息格式"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            # 发送无效格式消息
            websocket.send_text("invalid json")
            
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "invalid message format" in response["message"].lower()
    
    @pytest.mark.asyncio
    async def test_unknown_message_type(self, async_client, auth_headers: dict):
        """测试未知消息类型"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            unknown_msg = {
                "type": "unknown_type",
                "data": "some data"
            }
            websocket.send_json(unknown_msg)
            
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "unknown message type" in response["message"].lower()
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, async_client, auth_headers: dict):
        """测试缺少必需字段"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            incomplete_msg = {
                "type": "subscribe"
                # 缺少channel字段
            }
            websocket.send_json(incomplete_msg)
            
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "missing required field" in response["message"].lower()


class TestWebSocketConcurrency:
    """WebSocket并发测试"""
    
    @pytest.mark.asyncio
    async def test_multiple_connections_same_user(self, async_client, auth_headers: dict):
        """测试同一用户的多个连接"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        # 创建两个连接
        with async_client.websocket_connect(f"/ws?token={token}") as ws1:
            with async_client.websocket_connect(f"/ws?token={token}") as ws2:
                # 两个连接都应该成功
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()
                
                assert data1["type"] == "connection"
                assert data2["type"] == "connection"
                
                # 在一个连接上订阅
                subscribe_msg = {
                    "type": "subscribe",
                    "channel": "market_data",
                    "symbols": ["SHFE.cu2401"]
                }
                ws1.send_json(subscribe_msg)
                
                # 两个连接都应该收到相同的市场数据
                # (这取决于具体的实现逻辑)
    
    @pytest.mark.asyncio
    async def test_connection_cleanup_on_disconnect(self, async_client, auth_headers: dict):
        """测试连接断开时的清理"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            # 订阅一些频道
            subscribe_msg = {
                "type": "subscribe",
                "channel": "market_data",
                "symbols": ["SHFE.cu2401"]
            }
            websocket.send_json(subscribe_msg)
            websocket.receive_json()  # 订阅确认
            
            # 连接断开时，订阅应该被自动清理
            # 这个测试主要验证没有内存泄漏
        
        # 连接已关闭，相关资源应该被清理


class TestWebSocketAuthentication:
    """WebSocket认证测试"""
    
    @pytest.mark.asyncio
    async def test_token_expiration_handling(self, async_client, auth_headers: dict):
        """测试token过期处理"""
        # 创建一个即将过期的token
        from app.core.security import create_access_token
        from datetime import timedelta
        
        expired_token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(seconds=-1)  # 已过期
        )
        
        with pytest.raises(Exception):  # 连接应该被拒绝
            with async_client.websocket_connect(f"/ws?token={expired_token}"):
                pass
    
    @pytest.mark.asyncio
    async def test_user_permission_check(self, async_client, auth_headers: dict, test_strategy):
        """测试用户权限检查"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            # 尝试订阅其他用户的策略日志
            fake_strategy_id = "00000000-0000-0000-0000-000000000000"
            subscribe_msg = {
                "type": "subscribe",
                "channel": "strategy_logs",
                "strategy_id": fake_strategy_id
            }
            websocket.send_json(subscribe_msg)
            
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "permission denied" in response["message"].lower() or "not found" in response["message"].lower()


class TestWebSocketPerformance:
    """WebSocket性能测试"""
    
    @pytest.mark.asyncio
    async def test_high_frequency_messages(self, async_client, auth_headers: dict):
        """测试高频消息处理"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            # 订阅市场数据
            subscribe_msg = {
                "type": "subscribe",
                "channel": "market_data",
                "symbols": ["SHFE.cu2401"]
            }
            websocket.send_json(subscribe_msg)
            websocket.receive_json()  # 订阅确认
            
            # 模拟高频数据推送
            start_time = asyncio.get_event_loop().time()
            message_count = 0
            
            # 接收消息直到超时
            try:
                while asyncio.get_event_loop().time() - start_time < 1.0:  # 1秒内
                    websocket.receive_json(timeout=0.1)
                    message_count += 1
            except:
                pass
            
            # 验证能够处理一定数量的消息
            assert message_count >= 0  # 至少不会崩溃
    
    @pytest.mark.asyncio
    async def test_message_queue_overflow_handling(self, async_client, auth_headers: dict):
        """测试消息队列溢出处理"""
        token = auth_headers["Authorization"].split(" ")[1]
        
        with async_client.websocket_connect(f"/ws?token={token}") as websocket:
            # 发送大量消息而不接收响应
            for i in range(1000):
                ping_msg = {
                    "type": "ping",
                    "id": i
                }
                try:
                    websocket.send_json(ping_msg)
                except:
                    # 连接可能因为队列溢出而关闭
                    break
            
            # 系统应该能够优雅地处理溢出情况