"""
行情数据API接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...models.market_data import Symbol, Quote, Watchlist
from ...schemas.market_data import (
    QuoteResponse, SymbolResponse, WatchlistResponse,
    WatchlistCreate, WatchlistUpdate, SymbolSearch
)
from ...services.market_data_service import MarketDataService

router = APIRouter()

@router.get("/quotes", response_model=List[QuoteResponse])
async def get_market_quotes(
    symbols: Optional[str] = Query(None, description="逗号分隔的标的代码列表"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """获取市场行情数据"""
    try:
        market_service = MarketDataService(db)
        
        if symbols:
            symbol_codes = [s.strip() for s in symbols.split(',')]
            quotes = market_service.get_latest_quotes(symbol_codes)
        else:
            # 获取热门标的的行情
            quotes = market_service.get_popular_quotes(limit)
        
        return quotes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取行情数据失败: {str(e)}")

@router.get("/quotes/{symbol_code}", response_model=QuoteResponse)
async def get_symbol_quote(
    symbol_code: str,
    db: Session = Depends(get_db)
):
    """获取单个标的的行情数据"""
    try:
        market_service = MarketDataService(db)
        quote = market_service.get_symbol_quote(symbol_code)
        
        if not quote:
            raise HTTPException(status_code=404, detail="标的不存在或无行情数据")
        
        return quote
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取行情数据失败: {str(e)}")

@router.get("/symbols/search", response_model=List[SymbolResponse])
async def search_symbols(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """搜索标的"""
    try:
        # 按代码和名称搜索
        query = db.query(Symbol).filter(
            or_(
                Symbol.code.ilike(f"%{q}%"),
                Symbol.name.ilike(f"%{q}%"),
                Symbol.name_en.ilike(f"%{q}%")
            )
        ).filter(Symbol.is_active == True)
        
        # 优先显示代码匹配的结果
        symbols = query.order_by(
            func.case(
                (Symbol.code.ilike(f"{q}%"), 1),
                (Symbol.name.ilike(f"{q}%"), 2),
                else_=3
            ),
            Symbol.code
        ).limit(limit).all()
        
        return [SymbolResponse.from_orm(symbol) for symbol in symbols]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索标的失败: {str(e)}")

@router.get("/symbols/popular", response_model=List[SymbolResponse])
async def get_popular_symbols(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """获取热门标的"""
    try:
        # 按交易量排序获取热门标的
        symbols = db.query(Symbol).filter(
            Symbol.is_active == True
        ).order_by(
            desc(Symbol.volume_24h)
        ).limit(limit).all()
        
        return [SymbolResponse.from_orm(symbol) for symbol in symbols]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取热门标的失败: {str(e)}")

@router.get("/watchlist", response_model=List[WatchlistResponse])
async def get_user_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户自选股列表"""
    try:
        watchlist = db.query(Watchlist).filter(
            Watchlist.user_id == current_user.id
        ).order_by(Watchlist.sort_order, Watchlist.created_at).all()
        
        result = []
        for item in watchlist:
            # 获取最新行情
            market_service = MarketDataService(db)
            quote = market_service.get_symbol_quote(item.symbol.code)
            
            result.append(WatchlistResponse(
                id=item.id,
                symbol=SymbolResponse.from_orm(item.symbol),
                quote=quote,
                sort_order=item.sort_order,
                created_at=item.created_at
            ))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取自选股失败: {str(e)}")

@router.post("/watchlist", response_model=WatchlistResponse)
async def add_to_watchlist(
    watchlist_data: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加到自选股"""
    try:
        # 检查标的是否存在
        symbol = db.query(Symbol).filter(Symbol.code == watchlist_data.symbol_code).first()
        if not symbol:
            raise HTTPException(status_code=404, detail="标的不存在")
        
        # 检查是否已经在自选股中
        existing = db.query(Watchlist).filter(
            and_(
                Watchlist.user_id == current_user.id,
                Watchlist.symbol_id == symbol.id
            )
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="标的已在自选股中")
        
        # 获取当前最大排序号
        max_order = db.query(func.max(Watchlist.sort_order)).filter(
            Watchlist.user_id == current_user.id
        ).scalar() or 0
        
        # 创建自选股记录
        watchlist_item = Watchlist(
            user_id=current_user.id,
            symbol_id=symbol.id,
            sort_order=max_order + 1
        )
        
        db.add(watchlist_item)
        db.commit()
        db.refresh(watchlist_item)
        
        # 获取最新行情
        market_service = MarketDataService(db)
        quote = market_service.get_symbol_quote(symbol.code)
        
        return WatchlistResponse(
            id=watchlist_item.id,
            symbol=SymbolResponse.from_orm(symbol),
            quote=quote,
            sort_order=watchlist_item.sort_order,
            created_at=watchlist_item.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"添加自选股失败: {str(e)}")

@router.delete("/watchlist/{watchlist_id}")
async def remove_from_watchlist(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """从自选股中移除"""
    try:
        watchlist_item = db.query(Watchlist).filter(
            and_(
                Watchlist.id == watchlist_id,
                Watchlist.user_id == current_user.id
            )
        ).first()
        
        if not watchlist_item:
            raise HTTPException(status_code=404, detail="自选股记录不存在")
        
        db.delete(watchlist_item)
        db.commit()
        
        return {"message": "已从自选股中移除"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"移除自选股失败: {str(e)}")

@router.put("/watchlist/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist_item(
    watchlist_id: int,
    update_data: WatchlistUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新自选股排序"""
    try:
        watchlist_item = db.query(Watchlist).filter(
            and_(
                Watchlist.id == watchlist_id,
                Watchlist.user_id == current_user.id
            )
        ).first()
        
        if not watchlist_item:
            raise HTTPException(status_code=404, detail="自选股记录不存在")
        
        if update_data.sort_order is not None:
            watchlist_item.sort_order = update_data.sort_order
        
        db.commit()
        db.refresh(watchlist_item)
        
        # 获取最新行情
        market_service = MarketDataService(db)
        quote = market_service.get_symbol_quote(watchlist_item.symbol.code)
        
        return WatchlistResponse(
            id=watchlist_item.id,
            symbol=SymbolResponse.from_orm(watchlist_item.symbol),
            quote=quote,
            sort_order=watchlist_item.sort_order,
            created_at=watchlist_item.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新自选股失败: {str(e)}")

@router.post("/watchlist/reorder")
async def reorder_watchlist(
    watchlist_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重新排序自选股"""
    try:
        # 验证所有ID都属于当前用户
        watchlist_items = db.query(Watchlist).filter(
            and_(
                Watchlist.id.in_(watchlist_ids),
                Watchlist.user_id == current_user.id
            )
        ).all()
        
        if len(watchlist_items) != len(watchlist_ids):
            raise HTTPException(status_code=400, detail="包含无效的自选股ID")
        
        # 更新排序
        for index, watchlist_id in enumerate(watchlist_ids):
            db.query(Watchlist).filter(
                and_(
                    Watchlist.id == watchlist_id,
                    Watchlist.user_id == current_user.id
                )
            ).update({"sort_order": index + 1})
        
        db.commit()
        
        return {"message": "自选股排序已更新"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"重新排序失败: {str(e)}")