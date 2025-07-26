"""
WebSocket API路由
"""
import json
import uuid
import logging
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from jose import JWTError, jwt

from ...core.config import settings
from ...core.exceptions import AuthenticationError
from ...services.realtime_service import realtime_service
from ...models import User
from ...core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_current_user_from_token(token: str, db: Session) -> User:
    """从token获取当前用户"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise AuthenticationError("无效的认证令牌")
        
        user_id = int(user_id_str)
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AuthenticationError("用户不存在")
        
        if not user.is_active:
            raise AuthenticationError("用户账户已被禁用")
        
        return user
        
    except JWTError:
        raise AuthenticationError("认证令牌验证失败")


@router.websocket("/quotes")
async def websocket_quotes(
    websocket: WebSocket,
    token: str = Query(..., description="JWT认证令牌"),
):
    """WebSocket实时行情推送"""
    connection_id = str(uuid.uuid4())
    
    try:
        # 验证用户身份
        db = next(get_db())
        user = await get_current_user_from_token(token, db)
        
        # 添加连接
        connection = await realtime_service.add_connection(
            websocket, user.id, connection_id
        )
        
        logger.info(f"WebSocket连接建立: {connection_id}, 用户: {user.username}")
        
        # 消息处理循环
        while connection.is_active:
            try:
                # 接收客户端消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                await handle_websocket_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket连接断开: {connection_id}")
                break
            except json.JSONDecodeError:
                await connection.send_message({
                    "type": "error",
                    "message": "消息格式错误，请发送有效的JSON",
                })
            except Exception as e:
                logger.error(f"WebSocket消息处理异常: {e}")
                await connection.send_message({
                    "type": "error",
                    "message": f"消息处理失败: {str(e)}",
                })
    
    except AuthenticationError as e:
        logger.warning(f"WebSocket认证失败: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
    except Exception as e:
        logger.error(f"WebSocket连接异常: {e}")
        await websocket.close(code=4000, reason="Internal server error")
    finally:
        # 清理连接
        await realtime_service.remove_connection(connection_id)


async def handle_websocket_message(connection_id: str, message: Dict[str, Any]):
    """处理WebSocket消息"""
    action = message.get("action")
    
    if action == "subscribe_quotes":
        # 订阅行情
        symbols = message.get("symbols", [])
        if not symbols:
            await send_error_message(connection_id, "symbols参数不能为空")
            return
        
        success = await realtime_service.subscribe_quotes(connection_id, symbols)
        if not success:
            await send_error_message(connection_id, "订阅行情失败")
    
    elif action == "unsubscribe_quotes":
        # 取消订阅行情
        symbols = message.get("symbols", [])
        if not symbols:
            await send_error_message(connection_id, "symbols参数不能为空")
            return
        
        success = await realtime_service.unsubscribe_quotes(connection_id, symbols)
        if not success:
            await send_error_message(connection_id, "取消订阅失败")
    
    elif action == "ping":
        # 心跳响应
        if connection_id in realtime_service.connections:
            connection = realtime_service.connections[connection_id]
            await connection.send_message({
                "type": "pong",
                "timestamp": message.get("timestamp"),
            })
    
    elif action == "get_subscriptions":
        # 获取当前订阅
        if connection_id in realtime_service.connections:
            connection = realtime_service.connections[connection_id]
            await connection.send_message({
                "type": "subscriptions",
                "symbols": list(connection.subscribed_symbols),
            })
    
    else:
        await send_error_message(connection_id, f"未知的操作类型: {action}")


async def send_error_message(connection_id: str, error_message: str):
    """发送错误消息"""
    if connection_id in realtime_service.connections:
        connection = realtime_service.connections[connection_id]
        await connection.send_message({
            "type": "error",
            "message": error_message,
        })


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(..., description="JWT认证令牌"),
):
    """WebSocket通知推送"""
    connection_id = str(uuid.uuid4())
    
    try:
        # 验证用户身份
        db = next(get_db())
        user = await get_current_user_from_token(token, db)
        
        # 添加连接
        connection = await realtime_service.add_connection(
            websocket, user.id, connection_id
        )
        
        logger.info(f"通知WebSocket连接建立: {connection_id}, 用户: {user.username}")
        
        # 发送连接成功消息
        await connection.send_message({
            "type": "notification_service_ready",
            "message": "通知服务已就绪",
        })
        
        # 保持连接
        while connection.is_active:
            try:
                # 接收心跳消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("action") == "ping":
                    await connection.send_message({
                        "type": "pong",
                        "timestamp": message.get("timestamp"),
                    })
                
            except WebSocketDisconnect:
                logger.info(f"通知WebSocket连接断开: {connection_id}")
                break
            except Exception as e:
                logger.error(f"通知WebSocket异常: {e}")
                break
    
    except AuthenticationError as e:
        logger.warning(f"通知WebSocket认证失败: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
    except Exception as e:
        logger.error(f"通知WebSocket连接异常: {e}")
        await websocket.close(code=4000, reason="Internal server error")
    finally:
        # 清理连接
        await realtime_service.remove_connection(connection_id)