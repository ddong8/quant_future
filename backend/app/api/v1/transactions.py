"""
交易流水API接口
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...models.account import TransactionType, TransactionStatus
from ...services.transaction_service import TransactionService
from ...schemas.transaction import (
    TransactionCreate, TransactionResponse, TransactionSearch,
    TransactionStatistics, TransactionReport, TransactionExport
)

router = APIRouter()

@router.post("/", response_model=TransactionResponse)
async def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建交易流水记录"""
    try:
        service = TransactionService(db)
        
        # 验证账户权限
        from ...services.account_service import AccountService
        account_service = AccountService(db)
        account = account_service.get_account(transaction_data.account_id)
        
        if not account or account.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限访问该账户")
        
        # 创建交易记录
        transaction = service.create_transaction(transaction_data.dict())
        
        return TransactionResponse.from_orm(transaction)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/search", response_model=Dict[str, Any])
async def search_transactions(
    account_ids: Optional[List[int]] = Query(None),
    transaction_types: Optional[List[str]] = Query(None),
    status_list: Optional[List[str]] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    symbols: Optional[List[str]] = Query(None),
    keyword: Optional[str] = Query(None),
    sort_field: str = Query("transaction_time"),
    sort_order: str = Query("desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """搜索交易流水"""
    try:
        service = TransactionService(db)
        
        # 构建搜索参数
        search_params = {
            'user_id': current_user.id,
            'skip': skip,
            'limit': limit,
            'sort_field': sort_field,
            'sort_order': sort_order
        }
        
        if account_ids:
            search_params['account_ids'] = account_ids
        if transaction_types:
            search_params['transaction_types'] = [TransactionType(t) for t in transaction_types]
        if status_list:
            search_params['status_list'] = [TransactionStatus(s) for s in status_list]
        if start_date:
            search_params['start_date'] = start_date
        if end_date:
            search_params['end_date'] = end_date
        if min_amount is not None:
            search_params['min_amount'] = min_amount
        if max_amount is not None:
            search_params['max_amount'] = max_amount
        if symbols:
            search_params['symbols'] = symbols
        if keyword:
            search_params['keyword'] = keyword
        
        result = service.search_transactions(search_params)
        
        # 转换为响应格式
        return {
            'transactions': [TransactionResponse.from_orm(t) for t in result['transactions']],
            'total_count': result['total_count'],
            'page_info': result['page_info']
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个交易流水"""
    try:
        service = TransactionService(db)
        transaction = service.get_transaction(transaction_id)
        
        if not transaction:
            raise HTTPException(status_code=404, detail="交易记录不存在")
        
        # 验证权限
        from ...services.account_service import AccountService
        account_service = AccountService(db)
        account = account_service.get_account(transaction.account_id)
        
        if not account or account.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限访问该交易记录")
        
        return TransactionResponse.from_orm(transaction)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/account/{account_id}")
async def get_account_transactions(
    account_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    transaction_types: Optional[List[str]] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取账户交易流水"""
    try:
        # 验证账户权限
        from ...services.account_service import AccountService
        account_service = AccountService(db)
        account = account_service.get_account(account_id)
        
        if not account or account.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限访问该账户")
        
        service = TransactionService(db)
        
        # 构建筛选条件
        filters = {}
        if transaction_types:
            filters['transaction_types'] = [TransactionType(t) for t in transaction_types]
        if status:
            filters['status'] = TransactionStatus(status)
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        
        transactions = service.get_transactions_by_account(
            account_id=account_id,
            filters=filters,
            skip=skip,
            limit=limit
        )
        
        return [TransactionResponse.from_orm(t) for t in transactions]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{transaction_id}/status")
async def update_transaction_status(
    transaction_id: str,
    status: str,
    metadata: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新交易状态"""
    try:
        service = TransactionService(db)
        
        # 验证交易存在和权限
        transaction = service.get_transaction(transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="交易记录不存在")
        
        from ...services.account_service import AccountService
        account_service = AccountService(db)
        account = account_service.get_account(transaction.account_id)
        
        if not account or account.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限修改该交易记录")
        
        # 更新状态
        updated_transaction = service.update_transaction_status(
            transaction_id=transaction_id,
            status=TransactionStatus(status),
            metadata=metadata
        )
        
        return TransactionResponse.from_orm(updated_transaction)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/categories/statistics")
async def get_transaction_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取交易分类统计"""
    try:
        service = TransactionService(db)
        categories = service.get_transaction_categories(current_user.id)
        return categories
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/statistics/summary")
async def get_transaction_statistics(
    period: str = Query("month", pattern="^(day|week|month|quarter|year)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取交易统计分析"""
    try:
        service = TransactionService(db)
        statistics = service.get_transaction_statistics(current_user.id, period)
        return statistics
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/analysis/cash-flow")
async def get_cash_flow_analysis(
    period: str = Query("month", pattern="^(month|quarter|year)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """现金流分析"""
    try:
        service = TransactionService(db)
        analysis = service.get_cash_flow_analysis(current_user.id, period)
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/reports/generate")
async def generate_transaction_report(
    report_type: str = Query("summary", pattern="^(summary|detailed|tax|audit)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成交易报表"""
    try:
        service = TransactionService(db)
        
        # 设置默认时间范围
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        report = service.generate_transaction_report(
            user_id=current_user.id,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date
        )
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/export")
async def export_transactions(
    export_format: str = Query("csv", pattern="^(csv|excel|json)$"),
    account_ids: Optional[List[int]] = Query(None),
    transaction_types: Optional[List[str]] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出交易流水"""
    try:
        service = TransactionService(db)
        
        # 构建筛选条件
        filters = {}
        if account_ids:
            filters['account_ids'] = account_ids
        if transaction_types:
            filters['transaction_types'] = [TransactionType(t) for t in transaction_types]
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        
        result = service.export_transactions(
            user_id=current_user.id,
            export_format=export_format,
            filters=filters
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        # 返回文件
        return Response(
            content=result['file_content'],
            media_type=result['content_type'],
            headers={
                "Content-Disposition": f"attachment; filename={result['file_name']}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/audit/check")
async def audit_transactions(
    audit_type: str = Query("consistency", pattern="^(consistency|completeness|accuracy|timeline)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """交易流水审计"""
    try:
        service = TransactionService(db)
        audit_result = service.audit_transactions(current_user.id, audit_type)
        return audit_result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/audit/suspicious")
async def get_suspicious_transactions(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取可疑交易"""
    try:
        service = TransactionService(db)
        suspicious = service.get_suspicious_transactions(current_user.id, days)
        return suspicious
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))