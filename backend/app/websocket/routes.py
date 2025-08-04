"""
WebSocket路由处理
"""

import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional
import jwt

from .connection_manager import connection_manager
from ..core.config import settings
from ..models.user import User
from ..core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def get_current_user_from_token(token: Optional[str] = None, db: Session = Depends(get_db)) -> Optional[User]:
    """从token获取当前用户（WebSocket使用）"""
    if not token:
        return None
    
    try:
        # 移除Bearer前缀
        if token.startswith('Bearer '):
            token = token[7:]
        
        # 解码JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        
        if user_id is None:
            return None
        
        # 查询用户
        user = db.query(User).filter(User.id == user_id).first()
        return user
    
    except jwt.PyJWTError:
        return None
    except Exception as e:
        logger.error(f"获取用户信息时出错: {e}")
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """WebSocket连接端点"""
    
    # 验证用户身份
    user = None
    if token:
        user = await get_current_user_from_token(token, db)
    
    user_id = user.id if user else None
    
    # 建立连接
    connection_id = await connection_manager.connect(websocket, user_id)
    
    try:
        while True:
            # 接收消息
            message = await websocket.receive_text()
            
            # 处理消息
            await connection_manager.handle_message(connection_id, message)
    
    except WebSocketDisconnect:
        # 连接断开
        await connection_manager.disconnect(connection_id)
    
    except Exception as e:
        logger.error(f"WebSocket连接出错: {e}")
        await connection_manager.disconnect(connection_id)


@router.websocket("/market")
async def websocket_market_endpoint(websocket: WebSocket):
    """市场数据WebSocket连接端点"""
    
    try:
        # 接受连接
        await websocket.accept()
        
        # 发送连接成功消息
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "message": "市场数据连接已建立"
        }))
        
        while True:
            # 接收消息
            message = await websocket.receive_text()
            
            # 回显消息
            await websocket.send_text(json.dumps({
                "type": "echo",
                "message": f"收到消息: {message}"
            }))
    
    except WebSocketDisconnect:
        logger.info("WebSocket连接断开")
    
    except Exception as e:
        logger.error(f"市场数据WebSocket连接出错: {e}")
        await websocket.close()


@router.get("/ws/stats")
async def get_websocket_stats():
    """获取WebSocket统计信息"""
    return {
        "connection_stats": connection_manager.get_connection_stats(),
        "topic_stats": connection_manager.get_topic_stats()
    }