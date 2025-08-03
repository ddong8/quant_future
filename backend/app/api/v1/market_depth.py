"""
市场深度和价格提醒API接口
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...services.market_depth_service import MarketDepthService
from ...schemas.market_data import PriceAlertCreate, PriceAlertUpdate, PriceAlertResponse

router = APIRouter()

@router.get("/depth/{symbol_code}")
async def get_market_depth(
    symbol_code: str,
    depth_level: int = Query(20, ge=1, le=50, description="深度档数"),
    db: Session = Depends(get_db)
):
    """获取市场深度数据"""
    try:
        service = MarketDepthService(db)
        depth_data = service.get_market_depth(symbol_code, depth_level)
        
        if not depth_data:
            raise HTTPException(status_code=404, detail="未找到深度数据")
        
        return depth_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取市场深度失败: {str(e)}")

@router.get("/depth/{symbol_code}/analysis")
async def analyze_depth_imbalance(
    symbol_code: str,
    db: Session = Depends(get_db)
):
    """分析深度失衡"""
    try:
        service = MarketDepthService(db)
        analysis = service.analyze_depth_imbalance(symbol_code)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="无法分析深度数据")
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析深度失衡失败: {str(e)}")

@router.post("/alerts")
async def create_price_alert(
    alert_data: PriceAlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建价格提醒"""
    try:
        service = MarketDepthService(db)
        
        alert = service.create_price_alert(
            user_id=current_user.id,
            alert_data=alert_data.dict()
        )
        
        if not alert:
            raise HTTPException(status_code=400, detail="创建价格提醒失败")
        
        return {"message": "价格提醒创建成功", "alert_id": alert.id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建价格提醒失败: {str(e)}")

@router.get("/alerts")
async def get_user_alerts(
    is_active: Optional[bool] = Query(None, description="是否只获取活跃提醒"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的价格提醒"""
    try:
        service = MarketDepthService(db)
        alerts = service.get_user_alerts(current_user.id, is_active)
        
        return {
            'alerts': alerts,
            'count': len(alerts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取价格提醒失败: {str(e)}")

@router.put("/alerts/{alert_id}")
async def update_price_alert(
    alert_id: int,
    update_data: PriceAlertUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新价格提醒"""
    try:
        service = MarketDepthService(db)
        
        success = service.update_price_alert(
            user_id=current_user.id,
            alert_id=alert_id,
            update_data=update_data.dict(exclude_unset=True)
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="价格提醒不存在")
        
        return {"message": "价格提醒更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新价格提醒失败: {str(e)}")

@router.delete("/alerts/{alert_id}")
async def delete_price_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除价格提醒"""
    try:
        service = MarketDepthService(db)
        
        success = service.delete_price_alert(
            user_id=current_user.id,
            alert_id=alert_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="价格提醒不存在")
        
        return {"message": "价格提醒删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除价格提醒失败: {str(e)}")

@router.get("/anomalies")
async def get_market_anomalies(
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    severity: Optional[str] = Query(None, description="严重程度筛选"),
    db: Session = Depends(get_db)
):
    """获取市场异动"""
    try:
        service = MarketDepthService(db)
        anomalies = service.get_market_anomalies(hours, severity)
        
        return {
            'anomalies': anomalies,
            'count': len(anomalies)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取市场异动失败: {str(e)}")

@router.post("/anomalies/detect/{symbol_code}")
async def detect_symbol_anomalies(
    symbol_code: str,
    db: Session = Depends(get_db)
):
    """检测指定标的的市场异动"""
    try:
        service = MarketDepthService(db)
        anomalies = service.detect_market_anomalies(symbol_code)
        
        return {
            'symbol': symbol_code,
            'anomalies': anomalies,
            'count': len(anomalies)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检测市场异动失败: {str(e)}")

@router.post("/alerts/check/{symbol_code}")
async def check_symbol_alerts(
    symbol_code: str,
    current_price: float,
    db: Session = Depends(get_db)
):
    """检查指定标的的价格提醒"""
    try:
        service = MarketDepthService(db)
        triggered_alerts = service.check_price_alerts(symbol_code, current_price)
        
        return {
            'symbol': symbol_code,
            'current_price': current_price,
            'triggered_alerts': triggered_alerts,
            'count': len(triggered_alerts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查价格提醒失败: {str(e)}")