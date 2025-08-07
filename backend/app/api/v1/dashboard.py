"""
仪表板API路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.dependencies import get_db, get_current_user
from ...core.response import success_response, error_response
from ...models.user import User

router = APIRouter()


@router.get("/summary")
async def get_dashboard_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取仪表板摘要信息"""
    try:
        # 返回基本的仪表板数据
        summary_data = {
            "user": {
                "id": current_user["id"],
                "username": current_user["username"],
                "role": current_user["role"],
            },
            "stats": {
                "total_strategies": 0,
                "active_positions": 0,
                "total_orders": 0,
                "account_balance": 0.0,
            },
            "recent_activities": [],
            "market_status": "closed",
            "notifications": [],
        }
        
        return success_response(
            data=summary_data,
            message="获取仪表板摘要成功"
        )
        
    except Exception as e:
        return error_response(
            error_code="DASHBOARD_ERROR",
            message=f"获取仪表板摘要失败: {str(e)}"
        )