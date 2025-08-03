"""
风险偏好和投资配置API接口
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...services.risk_profile_service import RiskProfileService
from ...schemas.risk_profile import (
    RiskAssessmentRequest, RiskProfileResponse, RiskProfileCreate, RiskProfileUpdate,
    PortfolioConfigurationCreate, PortfolioConfigurationUpdate, PortfolioConfigurationResponse,
    InvestmentRecommendationResponse, RiskAssessmentQuestionResponse,
    PortfolioOptimizationRequest, PortfolioOptimizationResponse,
    RiskAlertResponse, RiskProfileAnalysis
)

router = APIRouter()

@router.get("/assessment/questions", response_model=List[RiskAssessmentQuestionResponse])
async def get_assessment_questions(
    version: str = Query("1.0", description="问卷版本"),
    db: Session = Depends(get_db)
):
    """获取风险评估问卷"""
    try:
        service = RiskProfileService(db)
        questions = service.get_assessment_questions(version)
        return questions
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/assessment/submit", response_model=RiskProfileResponse)
async def submit_risk_assessment(
    assessment_data: RiskAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交风险评估"""
    try:
        service = RiskProfileService(db)
        
        # 执行风险评估
        profile = service.assess_risk_profile(
            user_id=current_user.id,
            answers=assessment_data.answers,
            personal_info=assessment_data.personal_info
        )
        
        return RiskProfileResponse.from_orm(profile)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/profile", response_model=Optional[RiskProfileResponse])
async def get_risk_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户风险偏好档案"""
    try:
        service = RiskProfileService(db)
        profile = service.get_risk_profile(current_user.id)
        
        if not profile:
            return None
        
        return RiskProfileResponse.from_orm(profile)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/profile", response_model=RiskProfileResponse)
async def update_risk_profile(
    profile_data: RiskProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新风险偏好档案"""
    try:
        service = RiskProfileService(db)
        
        # 获取现有档案
        existing_profile = service.get_risk_profile(current_user.id)
        if not existing_profile:
            raise HTTPException(status_code=404, detail="风险偏好档案不存在")
        
        # 更新档案
        updated_profile = service.create_or_update_risk_profile(
            current_user.id, 
            profile_data.dict(exclude_unset=True)
        )
        
        return RiskProfileResponse.from_orm(updated_profile)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/profile/analysis", response_model=RiskProfileAnalysis)
async def get_risk_profile_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取风险偏好分析"""
    try:
        service = RiskProfileService(db)
        profile = service.get_risk_profile(current_user.id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="请先完成风险评估")
        
        # 这里应该实现详细的分析逻辑
        # 现在返回基础信息
        analysis = {
            'current_profile': RiskProfileResponse.from_orm(profile),
            'risk_level_info': {
                'level': profile.risk_tolerance,
                'name': profile.risk_tolerance.value,
                'description': f'{profile.risk_tolerance.value}风险偏好',
                'characteristics': ['基于风险评估的特征'],
                'suitable_investments': ['适合的投资类型'],
                'max_loss_tolerance': profile.max_portfolio_loss_percentage or 10,
                'typical_allocation': {'stocks': 60, 'bonds': 30, 'cash': 10}
            },
            'objective_info': {
                'objective': profile.investment_objective,
                'name': profile.investment_objective.value,
                'description': f'{profile.investment_objective.value}投资目标',
                'time_horizon': [profile.time_horizon],
                'risk_tolerance': [profile.risk_tolerance],
                'typical_allocation': {'stocks': 60, 'bonds': 30, 'cash': 10}
            },
            'recommended_allocation': {'stocks': 60, 'bonds': 30, 'cash': 10},
            'portfolio_suggestions': [],
            'next_review_date': profile.next_review_date,
            'improvement_suggestions': ['定期复评风险偏好', '关注市场变化']
        }
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/portfolios", response_model=List[PortfolioConfigurationResponse])
async def get_portfolio_configurations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取投资组合配置列表"""
    try:
        service = RiskProfileService(db)
        configs = service.get_portfolio_configurations(current_user.id)
        return [PortfolioConfigurationResponse.from_orm(config) for config in configs]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/portfolios", response_model=PortfolioConfigurationResponse)
async def create_portfolio_configuration(
    config_data: PortfolioConfigurationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建投资组合配置"""
    try:
        service = RiskProfileService(db)
        config = service.create_portfolio_configuration(
            current_user.id, 
            config_data.dict()
        )
        return PortfolioConfigurationResponse.from_orm(config)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/portfolios/{config_id}", response_model=PortfolioConfigurationResponse)
async def update_portfolio_configuration(
    config_id: int,
    config_data: PortfolioConfigurationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新投资组合配置"""
    try:
        service = RiskProfileService(db)
        config = service.update_portfolio_configuration(
            config_id, 
            current_user.id, 
            config_data.dict(exclude_unset=True)
        )
        return PortfolioConfigurationResponse.from_orm(config)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/portfolios/optimize", response_model=PortfolioOptimizationResponse)
async def optimize_portfolio(
    optimization_params: PortfolioOptimizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """优化投资组合"""
    try:
        service = RiskProfileService(db)
        result = service.optimize_portfolio(
            current_user.id, 
            optimization_params.dict()
        )
        return PortfolioOptimizationResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/portfolios/{config_id}/rebalance")
async def rebalance_portfolio(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """再平衡投资组合"""
    try:
        service = RiskProfileService(db)
        result = service.rebalance_portfolio(config_id, current_user.id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/recommendations", response_model=List[InvestmentRecommendationResponse])
async def get_investment_recommendations(
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取投资建议"""
    try:
        service = RiskProfileService(db)
        recommendations = service.get_investment_recommendations(current_user.id, limit)
        return [InvestmentRecommendationResponse.from_orm(rec) for rec in recommendations]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/recommendations/generate", response_model=List[InvestmentRecommendationResponse])
async def generate_investment_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成投资建议"""
    try:
        service = RiskProfileService(db)
        recommendations = service.generate_recommendations(current_user.id)
        return [InvestmentRecommendationResponse.from_orm(rec) for rec in recommendations]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/recommendations/{recommendation_id}/status")
async def update_recommendation_status(
    recommendation_id: int,
    status: str,
    is_accepted: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新投资建议状态"""
    try:
        service = RiskProfileService(db)
        recommendation = service.update_recommendation_status(
            recommendation_id, 
            current_user.id, 
            status, 
            is_accepted
        )
        return InvestmentRecommendationResponse.from_orm(recommendation)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/alerts", response_model=List[RiskAlertResponse])
async def get_risk_alerts(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取风险提醒"""
    try:
        service = RiskProfileService(db)
        alerts = service.get_risk_alerts(current_user.id, limit)
        return [RiskAlertResponse.from_orm(alert) for alert in alerts]
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_risk_alert(
    alert_id: int,
    resolution_note: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """确认风险提醒"""
    try:
        service = RiskProfileService(db)
        alert = service.acknowledge_risk_alert(alert_id, current_user.id, resolution_note)
        return RiskAlertResponse.from_orm(alert)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/risk-levels")
async def get_risk_tolerance_levels():
    """获取风险承受能力等级信息"""
    try:
        levels = [
            {
                'level': 'CONSERVATIVE',
                'name': '保守型',
                'description': '追求资本保值，风险承受能力较低',
                'characteristics': ['注重本金安全', '收益预期较低', '投资期限灵活'],
                'suitable_investments': ['货币基金', '国债', '银行理财', '定期存款'],
                'max_loss_tolerance': 5,
                'typical_allocation': {'bonds': 60, 'stocks': 30, 'cash': 10}
            },
            {
                'level': 'MODERATE',
                'name': '稳健型',
                'description': '在控制风险的前提下追求稳定收益',
                'characteristics': ['平衡风险与收益', '中等收益预期', '中长期投资'],
                'suitable_investments': ['混合基金', '债券基金', '蓝筹股', '稳健理财'],
                'max_loss_tolerance': 10,
                'typical_allocation': {'bonds': 50, 'stocks': 40, 'cash': 10}
            },
            {
                'level': 'BALANCED',
                'name': '平衡型',
                'description': '追求长期资本增值，能承受一定波动',
                'characteristics': ['均衡配置', '中高收益预期', '长期投资导向'],
                'suitable_investments': ['股票基金', 'ETF', '成长股', '平衡基金'],
                'max_loss_tolerance': 15,
                'typical_allocation': {'stocks': 60, 'bonds': 30, 'cash': 10}
            },
            {
                'level': 'AGGRESSIVE',
                'name': '积极型',
                'description': '追求高收益，能承受较大风险',
                'characteristics': ['高收益预期', '高风险承受', '长期投资'],
                'suitable_investments': ['成长股', '小盘股', '新兴市场', '科技股'],
                'max_loss_tolerance': 25,
                'typical_allocation': {'stocks': 70, 'bonds': 20, 'cash': 10}
            },
            {
                'level': 'SPECULATIVE',
                'name': '投机型',
                'description': '追求超高收益，能承受极大风险',
                'characteristics': ['超高收益预期', '极高风险承受', '短中期投机'],
                'suitable_investments': ['期权', '期货', '加密货币', '高风险股票'],
                'max_loss_tolerance': 40,
                'typical_allocation': {'stocks': 80, 'alternatives': 10, 'cash': 10}
            }
        ]
        
        return levels
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/investment-objectives")
async def get_investment_objectives():
    """获取投资目标信息"""
    try:
        objectives = [
            {
                'objective': 'CAPITAL_PRESERVATION',
                'name': '资本保值',
                'description': '主要目标是保护本金，避免损失',
                'time_horizon': ['SHORT_TERM', 'MEDIUM_TERM'],
                'risk_tolerance': ['CONSERVATIVE', 'MODERATE'],
                'typical_allocation': {'bonds': 70, 'stocks': 20, 'cash': 10}
            },
            {
                'objective': 'INCOME_GENERATION',
                'name': '收益生成',
                'description': '追求稳定的现金流收入',
                'time_horizon': ['MEDIUM_TERM', 'LONG_TERM'],
                'risk_tolerance': ['CONSERVATIVE', 'MODERATE', 'BALANCED'],
                'typical_allocation': {'bonds': 50, 'dividend_stocks': 40, 'cash': 10}
            },
            {
                'objective': 'BALANCED_GROWTH',
                'name': '平衡增长',
                'description': '在控制风险的同时追求资本增值',
                'time_horizon': ['MEDIUM_TERM', 'LONG_TERM'],
                'risk_tolerance': ['MODERATE', 'BALANCED', 'AGGRESSIVE'],
                'typical_allocation': {'stocks': 60, 'bonds': 30, 'cash': 10}
            },
            {
                'objective': 'CAPITAL_APPRECIATION',
                'name': '资本增值',
                'description': '主要追求长期资本增值',
                'time_horizon': ['LONG_TERM'],
                'risk_tolerance': ['BALANCED', 'AGGRESSIVE', 'SPECULATIVE'],
                'typical_allocation': {'stocks': 80, 'bonds': 15, 'cash': 5}
            },
            {
                'objective': 'SPECULATION',
                'name': '投机交易',
                'description': '追求短期高收益，承担高风险',
                'time_horizon': ['SHORT_TERM'],
                'risk_tolerance': ['AGGRESSIVE', 'SPECULATIVE'],
                'typical_allocation': {'high_risk_assets': 90, 'cash': 10}
            }
        ]
        
        return objectives
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))