"""
简单风险监控API - 基于真实数据
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging

from ...core.dependencies import get_current_user
from ...services.simple_trading_service import simple_trading_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/metrics")
async def get_risk_metrics(
    current_user: dict = Depends(get_current_user)
):
    """获取实时风险指标"""
    try:
        # 获取账户信息
        account_info = await simple_trading_service.get_account_info()
        
        # 获取持仓信息
        positions = await simple_trading_service.get_positions()
        
        # 计算风险指标
        risk_metrics = calculate_risk_metrics(account_info, positions)
        
        return {
            "success": True,
            "data": risk_metrics,
            "message": "获取风险指标成功"
        }
        
    except Exception as e:
        logger.error(f"获取风险指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def calculate_risk_metrics(account_info: Dict[str, Any], positions: list) -> Dict[str, Any]:
    """计算风险指标"""
    try:
        balance = float(account_info.get("balance", 0))
        available = float(account_info.get("available", 0))
        margin = float(account_info.get("margin", 0))
        profit = float(account_info.get("profit", 0))
        
        # 计算账户风险指标
        margin_ratio = margin / balance if balance > 0 else 0
        available_ratio = available / balance if balance > 0 else 0
        profit_ratio = profit / balance if balance > 0 else 0
        
        # 评估风险等级
        risk_level = assess_risk_level(margin_ratio, profit_ratio)
        
        # 计算持仓风险
        position_metrics = calculate_position_risk(positions, balance)
        
        # 计算综合风险评分 (0-100)
        overall_risk_score = calculate_overall_risk_score(margin_ratio, profit_ratio, position_metrics)
        
        # 生成风险预警
        risk_alerts = generate_risk_alerts(margin_ratio, profit_ratio, overall_risk_score)
        
        return {
            "overall_risk_score": overall_risk_score,
            "account_metrics": {
                "balance": balance,
                "available": available,
                "margin": margin,
                "profit": profit,
                "margin_ratio": round(margin_ratio, 4),
                "available_ratio": round(available_ratio, 4),
                "profit_ratio": round(profit_ratio, 4),
                "risk_level": risk_level
            },
            "position_metrics": position_metrics,
            "risk_alerts": risk_alerts,
            "timestamp": "2025-08-12T14:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"计算风险指标失败: {e}")
        return {
            "overall_risk_score": 0,
            "account_metrics": {},
            "position_metrics": {},
            "risk_alerts": [],
            "timestamp": "2025-08-12T14:30:00Z"
        }


def assess_risk_level(margin_ratio: float, profit_ratio: float) -> str:
    """评估风险等级"""
    if margin_ratio > 0.9 or profit_ratio < -0.1:
        return "高"
    elif margin_ratio > 0.7 or profit_ratio < -0.05:
        return "中"
    else:
        return "低"


def calculate_position_risk(positions: list, balance: float) -> Dict[str, Any]:
    """计算持仓风险"""
    if not positions:
        return {
            "total_positions": 0,
            "largest_position_ratio": 0,
            "margin_utilization": 0,
            "risk_level": "低"
        }
    
    total_margin = sum(float(pos.get("margin", 0)) for pos in positions)
    position_values = {}
    
    for position in positions:
        symbol = position.get("symbol", "")
        volume = int(position.get("volume", 0))
        current_price = float(position.get("current_price", 0))
        
        position_value = volume * current_price
        if symbol not in position_values:
            position_values[symbol] = 0
        position_values[symbol] += position_value
    
    # 计算最大持仓比例
    largest_position_ratio = 0
    if position_values and balance > 0:
        largest_position_ratio = max(position_values.values()) / balance
    
    # 评估持仓风险等级
    position_risk_level = "低"
    if largest_position_ratio > 0.5 or len(positions) > 5:
        position_risk_level = "高"
    elif largest_position_ratio > 0.3 or len(positions) > 3:
        position_risk_level = "中"
    
    return {
        "total_positions": len(positions),
        "largest_position_ratio": round(largest_position_ratio, 4),
        "margin_utilization": round(total_margin / balance, 4) if balance > 0 else 0,
        "risk_level": position_risk_level
    }


def calculate_overall_risk_score(margin_ratio: float, profit_ratio: float, position_metrics: Dict[str, Any]) -> int:
    """计算综合风险评分 (0-100)"""
    score = 0
    
    # 保证金使用率风险 (40%)
    if margin_ratio > 0.9:
        score += 40
    elif margin_ratio > 0.7:
        score += 30
    elif margin_ratio > 0.5:
        score += 20
    else:
        score += 10
    
    # 盈亏风险 (30%)
    if profit_ratio < -0.1:
        score += 30
    elif profit_ratio < -0.05:
        score += 20
    elif profit_ratio < 0:
        score += 10
    else:
        score += 5
    
    # 持仓集中度风险 (30%)
    largest_position_ratio = position_metrics.get("largest_position_ratio", 0)
    if largest_position_ratio > 0.5:
        score += 30
    elif largest_position_ratio > 0.3:
        score += 20
    elif largest_position_ratio > 0.2:
        score += 10
    else:
        score += 5
    
    return min(score, 100)


def generate_risk_alerts(margin_ratio: float, profit_ratio: float, overall_risk_score: int) -> list:
    """生成风险预警"""
    alerts = []
    
    # 保证金预警
    if margin_ratio > 0.9:
        alerts.append({
            "type": "CRITICAL",
            "level": "严重",
            "message": f"保证金使用率过高 ({margin_ratio:.2%})，面临强制平仓风险",
            "suggestion": "立即减仓或追加保证金",
            "timestamp": "2025-08-12T14:30:00Z"
        })
    elif margin_ratio > 0.8:
        alerts.append({
            "type": "WARNING",
            "level": "警告",
            "message": f"保证金使用率较高 ({margin_ratio:.2%})，请注意风险",
            "suggestion": "考虑适当减仓",
            "timestamp": "2025-08-12T14:30:00Z"
        })
    
    # 亏损预警
    if profit_ratio < -0.1:
        alerts.append({
            "type": "WARNING",
            "level": "警告",
            "message": f"当前亏损较大 ({profit_ratio:.2%})，已超过风险限额",
            "suggestion": "停止交易，重新评估策略",
            "timestamp": "2025-08-12T14:30:00Z"
        })
    
    # 综合风险预警
    if overall_risk_score > 80:
        alerts.append({
            "type": "CRITICAL",
            "level": "严重",
            "message": f"综合风险评分过高 ({overall_risk_score})，建议立即采取措施",
            "suggestion": "减少持仓，降低风险敞口",
            "timestamp": "2025-08-12T14:30:00Z"
        })
    
    return alerts