"""
账户管理API接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...core.permissions import require_permission
from ...models.user import User
from ...models.account import Account
from ...schemas.simple_account import SimpleAccountResponse, SimpleAccountCreate
from ...services.account_service import AccountService

router = APIRouter()


# ==================== 账户管理 ====================

@router.post("/", response_model=SimpleAccountResponse)
async def create_account(
    account_data: SimpleAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建账户"""
    try:
        import uuid
        
        # 创建新账户
        account = Account(
            user_id=current_user.id,
            account_id=f"ACC{str(uuid.uuid4())[:8].upper()}",
            account_name=account_data.account_name,
            broker=account_data.broker,
            balance=account_data.initial_balance,
            available=account_data.initial_balance,
            margin=0.0,
            frozen=0.0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            total_pnl=0.0,
            risk_ratio=0.0,
            is_active=True
        )
        
        db.add(account)
        db.commit()
        db.refresh(account)
        
        return SimpleAccountResponse.from_orm(account)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建账户失败: {str(e)}"
        )


@router.get("/", response_model=List[SimpleAccountResponse])
async def get_user_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户账户列表"""
    try:
        # 直接查询数据库，避免复杂的服务层
        accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
        
        return [SimpleAccountResponse.from_orm(account) for account in accounts]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取账户列表失败: {str(e)}"
        )


@router.get("/{account_id}", response_model=SimpleAccountResponse)
async def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取账户详情"""
    try:
        account = db.query(Account).filter(
            Account.id == account_id,
            Account.user_id == current_user.id
        ).first()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="账户不存在"
            )
        
        return SimpleAccountResponse.from_orm(account)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取账户详情失败: {str(e)}"
        )


# 其他API端点暂时注释掉，专注于基本功能