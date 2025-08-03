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
from ...models.account import AccountStatus, TransactionType
from ...schemas.account import (
    AccountCreate, AccountUpdate, AccountResponse,
    DepositRequest, WithdrawalRequest, TransactionResponse,
    AccountBalanceResponse, TransactionSummaryResponse,
    AccountConsistencyResponse, AccountTotalsResponse,
    FreezeRequest, UnfreezeRequest, TradeTransactionRequest
)
from ...services.account_service import AccountService

router = APIRouter()


# ==================== 账户管理 ====================

@router.post("/", response_model=AccountResponse)
@require_permission("account:create")
async def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建账户"""
    account_service = AccountService(db)
    
    try:
        account = account_service.create_account(
            user_id=current_user.id,
            account_data=account_data.dict()
        )
        return AccountResponse.from_orm(account)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建账户失败: {str(e)}"
        )


@router.get("/", response_model=List[AccountResponse])
@require_permission("account:read")
async def get_user_accounts(
    status_filter: Optional[AccountStatus] = Query(None, description="账户状态筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户账户列表"""
    account_service = AccountService(db)
    
    accounts = account_service.get_user_accounts(
        user_id=current_user.id,
        status=status_filter
    )
    
    return [AccountResponse.from_orm(account) for account in accounts]


@router.get("/{account_id}", response_model=AccountResponse)
@require_permission("account:read")
async def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取账户详情"""
    account_service = AccountService(db)
    
    account = account_service.get_account(account_id, current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在"
        )
    
    return AccountResponse.from_orm(account)


@router.put("/{account_id}", response_model=AccountResponse)
@require_permission("account:update")
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新账户信息"""
    account_service = AccountService(db)
    
    account = account_service.update_account(
        account_id=account_id,
        user_id=current_user.id,
        update_data=account_data.dict(exclude_unset=True)
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在"
        )
    
    return AccountResponse.from_orm(account)


@router.delete("/{account_id}")
@require_permission("account:delete")
async def close_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """关闭账户"""
    account_service = AccountService(db)
    
    try:
        success = account_service.close_account(account_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="账户不存在"
            )
        
        return {"message": "账户关闭成功"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== 资金管理 ====================

@router.post("/{account_id}/deposit", response_model=TransactionResponse)
@require_permission("account:deposit")
async def deposit(
    account_id: int,
    deposit_data: DepositRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """入金"""
    account_service = AccountService(db)
    
    # 验证账户所有权
    account = account_service.get_account(account_id, current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在"
        )
    
    try:
        transaction = account_service.deposit(
            account_id=account_id,
            amount=deposit_data.amount,
            description=deposit_data.description,
            reference_id=deposit_data.reference_id
        )
        return TransactionResponse.from_orm(transaction)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{account_id}/withdraw", response_model=TransactionResponse)
@require_permission("account:withdraw")
async def withdraw(
    account_id: int,
    withdraw_data: WithdrawalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """出金"""
    account_service = AccountService(db)
    
    # 验证账户所有权
    account = account_service.get_account(account_id, current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在"
        )
    
    try:
        transaction = account_service.withdraw(
            account_id=account_id,
            amount=withdraw_data.amount,
            description=withdraw_data.description,
            reference_id=withdraw_data.reference_id
        )
        return TransactionResponse.from_orm(transaction)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{account_id}/freeze")
@require_permission("account:manage")
async def freeze_funds(
    account_id: int,
    freeze_data: FreezeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """冻结资金"""
    account_service = AccountService(db)
    
    # 验证账户所有权
    account = account_service.get_account(account_id, current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在"
        )
    
    success = account_service.freeze_funds(
        account_id=account_id,
        amount=freeze_data.amount,
        description=freeze_data.description
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="冻结资金失败，可能是可用资金不足"
        )
    
    return {"message": f"成功冻结资金 {freeze_data.amount}"}


@router.post("/{account_id}/unfreeze")
@require_permission("account:manage")
async def unfreeze_funds(
    account_id: int,
    unfreeze_data: UnfreezeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """解冻资金"""
    account_service = AccountService(db)
    
    # 验证账户所有权
    account = account_service.get_account(account_id, current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在"
        )
    
    success = account_service.unfreeze_funds(
        account_id=account_id,
        amount=unfreeze_data.amount,
        description=unfreeze_data.description
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="解冻资金失败，可能是冻结资金不足"
        )
    
    return {"message": f"成功解冻资金 {unfreeze_data.amount}"}


# ==================== 交易流水 ====================

@router.get("/{account_id}/transactions", response_model=List[TransactionResponse])
@require_permission("account:read")
async def get_transactions(
    account_id: int,
    transaction_type: Optional[TransactionType] = Query(None, description="交易类型筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取交易流水"""
    account_service = AccountService(db)
    
    # 验证账户所有权
    account = account_service.get_account(account_id, current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在"
        )
    
    transactions = account_service.get_transactions(
        account_id=account_id,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    
    return [TransactionResponse.from_orm(transaction) for transaction in transactions]


@router.get("/{account_id}/transactions/summary", response_model=TransactionSummaryResponse)
@require_permission("account:read")
async def get_transaction_summary(
    account_id: int,
    period: str = Query('month', description="统计周期: day, week, month, year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取交易汇总"""
    account_service = AccountService(db)
    
    # 验证账户所有权
    account = account_service.get_account(account_id, current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在"
        )
    
    summary = account_service.get_transaction_summary(account_id, period)
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="获取交易汇总失败"
        )
    
    return TransactionSummaryResponse(**summary)


@router.post("/{account_id}/transactions/trade", response_model=TransactionResponse)
@require_permission("account:manage")
async def record_trade_transaction(
    account_id: int,
    trade_data: TradeTransactionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """记录交易流水"""
    account_service = AccountService(db)
    
    # 验证账户所有权
    account = account_service.get_account(account_id, current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在"
        )
    
    try:
        transaction = account_service.record_trade_transaction(
            account_id=account_id,
            order_id=trade_data.order_id,
            position_id=trade_data.position_id,
            amount=trade_data.amount,
            fee=trade_data.fee,
            symbol=trade_data.symbol,
            description=trade_data.description
        )
        return TransactionResponse.from_orm(transaction)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== 余额和统计 ====================

@router.get("/{account_id}/totals", response_model=AccountTotalsResponse)
@require_permission("account:read")
async def get_account_totals(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取账户总资产"""
    account_service = AccountService(db)
    
    # 验证账户所有权
    account = account_service.get_account(account_id, current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在"
        )
    
    totals = account_service.calculate_account_totals(account_id)
    
    if not totals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="计算账户总资产失败"
        )
    
    return AccountTotalsResponse(**totals)


@router.get("/{account_id}/balances", response_model=List[AccountBalanceResponse])
@require_permission("account:read")
async def get_balance_history(
    account_id: int,
    days: int = Query(30, ge=1, le=365, description="历史天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取余额历史"""
    account_service = AccountService(db)
    
    # 验证账户所有权
    account = account_service.get_account(account_id, current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在"
        )
    
    balances = account_service.get_balance_history(account_id, days)
    
    return [AccountBalanceResponse.from_orm(balance) for balance in balances]


@router.post("/{account_id}/snapshot")
@require_permission("account:manage")
async def create_balance_snapshot(
    account_id: int,
    snapshot_type: str = Query('manual', description="快照类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建余额快照"""
    account_service = AccountService(db)
    
    # 验证账户所有权
    account = account_service.get_account(account_id, current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在"
        )
    
    try:
        snapshot = account_service.create_balance_snapshot(account_id, snapshot_type)
        return AccountBalanceResponse.from_orm(snapshot)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== 账户一致性检查 ====================

@router.get("/{account_id}/consistency", response_model=AccountConsistencyResponse)
@require_permission("account:read")
async def check_account_consistency(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查账户一致性"""
    account_service = AccountService(db)
    
    # 验证账户所有权
    account = account_service.get_account(account_id, current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在"
        )
    
    result = account_service.check_account_consistency(account_id)
    
    if 'error' in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result['error']
        )
    
    return AccountConsistencyResponse(**result)


@router.post("/{account_id}/reconcile")
@require_permission("account:manage")
async def reconcile_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """对账修复"""
    account_service = AccountService(db)
    
    # 验证账户所有权
    account = account_service.get_account(account_id, current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在"
        )
    
    success = account_service.reconcile_account(account_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="对账修复失败"
        )
    
    return {"message": "对账修复成功"}


@router.put("/{account_id}/update-pnl")
@require_permission("account:manage")
async def update_account_pnl(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新账户盈亏"""
    account_service = AccountService(db)
    
    # 验证账户所有权
    account = account_service.get_account(account_id, current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账户不存在"
        )
    
    success = account_service.update_account_pnl(account_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新账户盈亏失败"
        )
    
    return {"message": "账户盈亏更新成功"}