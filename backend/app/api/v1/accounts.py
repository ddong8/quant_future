"""
账户管理API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ...core.database import get_db
from ...core.dependencies import get_current_user, PaginationParams
from ...core.response import success_response, error_response
from ...models import User
from ...models.enums import TransactionType
from ...schemas.account import (
    AccountResponse,
    AccountMetricsResponse,
    TransactionHistoryResponse,
    BalanceHistoryResponse,
    RiskIndicatorsResponse,
    DepositRequest,
    WithdrawRequest,
    TransactionResponse
)
from ...services.account_service import AccountService

router = APIRouter()


@router.get("/", response_model=AccountResponse)
async def get_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取账户信息"""
    try:
        account_service = AccountService(db)
        account = account_service.get_account(current_user.id)
        
        if not account:
            return error_response(message="账户不存在", status_code=404)
        
        return success_response(data=account)
        
    except Exception as e:
        return error_response(message=f"获取账户信息失败: {str(e)}")


@router.post("/create")
async def create_account(
    initial_balance: float = Query(0.0, description="初始余额"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建交易账户"""
    try:
        account_service = AccountService(db)
        account = account_service.create_account(current_user.id, initial_balance)
        
        return success_response(
            data=account,
            message="交易账户创建成功"
        )
        
    except Exception as e:
        return error_response(message=f"创建交易账户失败: {str(e)}")


@router.get("/metrics", response_model=AccountMetricsResponse)
async def get_account_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取账户指标"""
    try:
        account_service = AccountService(db)
        metrics = account_service.calculate_account_metrics(current_user.id)
        
        return success_response(data=metrics)
        
    except Exception as e:
        return error_response(message=f"获取账户指标失败: {str(e)}")


@router.get("/transactions", response_model=TransactionHistoryResponse)
async def get_transaction_history(
    transaction_type: Optional[str] = Query(None, description="交易类型"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取交易流水"""
    try:
        account_service = AccountService(db)
        
        # 转换交易类型
        trans_type = None
        if transaction_type:
            try:
                trans_type = TransactionType(transaction_type)
            except ValueError:
                return error_response(message="无效的交易类型")
        
        transactions, total = account_service.get_transaction_history(
            user_id=current_user.id,
            transaction_type=trans_type,
            start_date=start_date,
            end_date=end_date,
            pagination=pagination
        )
        
        return success_response(
            data={
                "transactions": transactions,
                "total": total,
                "page": pagination.page,
                "page_size": pagination.page_size
            }
        )
        
    except Exception as e:
        return error_response(message=f"获取交易流水失败: {str(e)}")


@router.get("/balance-history", response_model=BalanceHistoryResponse)
async def get_balance_history(
    days: int = Query(30, ge=1, le=365, description="历史天数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取余额历史"""
    try:
        account_service = AccountService(db)
        history = account_service.get_daily_balance_history(current_user.id, days)
        
        return success_response(data=history)
        
    except Exception as e:
        return error_response(message=f"获取余额历史失败: {str(e)}")


@router.get("/risk-indicators", response_model=RiskIndicatorsResponse)
async def get_risk_indicators(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取风险指标"""
    try:
        account_service = AccountService(db)
        indicators = account_service.calculate_risk_indicators(current_user.id)
        
        return success_response(data=indicators)
        
    except Exception as e:
        return error_response(message=f"获取风险指标失败: {str(e)}")


@router.post("/deposit", response_model=TransactionResponse)
async def deposit(
    request: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """充值"""
    try:
        account_service = AccountService(db)
        account = account_service.deposit(
            user_id=current_user.id,
            amount=request.amount,
            description=request.description or "充值"
        )
        
        return success_response(
            data={
                "account_id": account.account_id,
                "total_balance": float(account.total_balance),
                "available_balance": float(account.available_balance),
                "transaction_amount": request.amount
            },
            message="充值成功"
        )
        
    except Exception as e:
        return error_response(message=f"充值失败: {str(e)}")


@router.post("/withdraw", response_model=TransactionResponse)
async def withdraw(
    request: WithdrawRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提现"""
    try:
        account_service = AccountService(db)
        account = account_service.withdraw(
            user_id=current_user.id,
            amount=request.amount,
            description=request.description or "提现"
        )
        
        return success_response(
            data={
                "account_id": account.account_id,
                "total_balance": float(account.total_balance),
                "available_balance": float(account.available_balance),
                "transaction_amount": request.amount
            },
            message="提现成功"
        )
        
    except Exception as e:
        return error_response(message=f"提现失败: {str(e)}")


@router.post("/freeze-balance")
async def freeze_balance(
    amount: float = Query(..., gt=0, description="冻结金额"),
    description: str = Query("", description="描述"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """冻结资金"""
    try:
        account_service = AccountService(db)
        success = account_service.freeze_balance(
            user_id=current_user.id,
            amount=amount,
            description=description
        )
        
        if success:
            return success_response(message="资金冻结成功")
        else:
            return error_response(message="资金冻结失败")
        
    except Exception as e:
        return error_response(message=f"冻结资金失败: {str(e)}")


@router.post("/unfreeze-balance")
async def unfreeze_balance(
    amount: float = Query(..., gt=0, description="解冻金额"),
    description: str = Query("", description="描述"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """解冻资金"""
    try:
        account_service = AccountService(db)
        success = account_service.unfreeze_balance(
            user_id=current_user.id,
            amount=amount,
            description=description
        )
        
        if success:
            return success_response(message="资金解冻成功")
        else:
            return error_response(message="资金解冻失败")
        
    except Exception as e:
        return error_response(message=f"解冻资金失败: {str(e)}")