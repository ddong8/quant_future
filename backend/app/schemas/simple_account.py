"""
简化的账户管理数据模式 - 兼容现有数据库结构
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SimpleAccountResponse(BaseModel):
    """简化的账户响应"""
    id: int = Field(..., description="账户ID")
    user_id: int = Field(..., description="用户ID")
    account_id: str = Field(..., description="账户标识")
    account_name: Optional[str] = Field(None, description="账户名称")
    broker: Optional[str] = Field(None, description="券商")
    
    # 资金信息
    balance: Optional[float] = Field(None, description="总余额")
    available: Optional[float] = Field(None, description="可用资金")
    margin: Optional[float] = Field(None, description="保证金")
    frozen: Optional[float] = Field(None, description="冻结资金")
    
    # 盈亏信息
    realized_pnl: Optional[float] = Field(None, description="已实现盈亏")
    unrealized_pnl: Optional[float] = Field(None, description="未实现盈亏")
    total_pnl: Optional[float] = Field(None, description="总盈亏")
    risk_ratio: Optional[float] = Field(None, description="风险比率")
    
    # 状态
    is_active: Optional[bool] = Field(None, description="是否活跃")
    
    # 时间信息
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class SimpleAccountCreate(BaseModel):
    """简化的创建账户请求"""
    account_name: str = Field(..., description="账户名称")
    broker: Optional[str] = Field("default", description="券商")
    initial_balance: Optional[float] = Field(0.0, description="初始资金")