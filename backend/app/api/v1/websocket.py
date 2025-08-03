"""
WebSocket API路由
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
import json

from ...core.database import get_db
from ...core.websocket import websocket_manager, websocket_handler
from ...websocket.routes import get_current_user_from_token
from ...models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/orders/{user_id}")
async def websocket_orders_endpoint(
    websocket: WebSocket,
    user_id: int,
    token: str = None,
    db: Session = Depends(get_db)
):
    """订单WebSocket连接端点"""
    try:
        # 验证用户身份
        if token:
            try:
                current_user = get_current_user_from_token(token, db)
                if current_user.id != user_id:
                    await websocket.close(code=1008, reason="Unauthorized")
                    return
            except Exception:
                await websocket.close(code=1008, reason="Invalid token")
                return
        
        # 建立连接
        await websocket_manager.connect(websocket, user_id)
        
        # 发送连接确认消息
        await websocket_manager.send_to_user(user_id, {
            'type': 'connection_established',
            'message': '订单WebSocket连接已建立',
            'timestamp': datetime.now().isoformat()
        })
        
        try:
            while True:
                # 接收消息
                data = await websocket.receive_text()
                await websocket_handler.handle_message(websocket, data)
                
        except WebSocketDisconnect:
            logger.info(f"用户 {user_id} 断开订单WebSocket连接")
        
    except Exception as e:
        logger.error(f"订单WebSocket连接错误: {str(e)}")
    finally:
        websocket_manager.disconnect(websocket)


@router.websocket("/general/{user_id}")
async def websocket_general_endpoint(
    websocket: WebSocket,
    user_id: int,
    token: str = None,
    db: Session = Depends(get_db)
):
    """通用WebSocket连接端点"""
    try:
        # 验证用户身份
        if token:
            try:
                current_user = get_current_user_from_token(token, db)
                if current_user.id != user_id:
                    await websocket.close(code=1008, reason="Unauthorized")
                    return
            except Exception:
                await websocket.close(code=1008, reason="Invalid token")
                return
        
        # 建立连接
        await websocket_manager.connect(websocket, user_id)
        
        try:
            while True:
                data = await websocket.receive_text()
                await websocket_handler.handle_message(websocket, data)
                
        except WebSocketDisconnect:
            logger.info(f"用户 {user_id} 断开通用WebSocket连接")
        
    except Exception as e:
        logger.error(f"通用WebSocket连接错误: {str(e)}")
    finally:
        websocket_manager.disconnect(websocket)
from datetime import datetime