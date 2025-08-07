#!/usr/bin/env python3
"""
临时认证端点，绕过ORM关系问题
"""
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import security_manager, jwt_manager
import uvicorn

app = FastAPI()

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800
    user_id: int
    username: str
    role: str

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """简化的登录端点"""
    # 查询用户
    result = db.execute(
        text('SELECT id, username, hashed_password, role, is_active FROM users WHERE username = :username'), 
        {'username': login_data.username}
    ).fetchone()
    
    if not result:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    user_id, username, hashed_password, role, is_active = result
    
    # 验证密码
    if not security_manager.verify_password(login_data.password, hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 检查用户状态
    if not is_active:
        raise HTTPException(status_code=401, detail="用户账户已被禁用")
    
    # 生成JWT令牌
    access_token = jwt_manager.create_access_token(
        data={'sub': str(user_id), 'username': username, 'role': role}
    )
    
    return TokenResponse(
        access_token=access_token,
        user_id=user_id,
        username=username,
        role=role
    )

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)