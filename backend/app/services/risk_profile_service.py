"""
风险偏好和投资配置服务
"""
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from decimal import Decimal
from ..models.risk_profile import (
    RiskProfile, PortfolioConfiguration, InvestmentRecommendation,
    RiskAssessmentQuestion, MarketRegime, RiskAlert,
    RiskToleranceLevel, InvestmentObjective, TimeHorizon, AllocationHistory
)
from ..models.user import User

logger = logging.getLogger(__name__)

class RiskProfileService:
    """风险偏好服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 风险评估 ====================
    
    def get_assessment_questions(self, version: str = "1.0") -> List[Dict[str, Any]]:
        """获取风险评估问卷"""
        try:
            questions = self.db.query(RiskAssessmentQuestion).filter(
                RiskAssessmentQuestion.version == version,
                RiskAssessmentQuestion.is_active == True
            ).order_by(RiskAssessmentQuestion.order_index).all()
            
            return [
                {
                    'id': q.id,
                    'question_text': q.question_text,
                    'question_type': q.question_type,
                    'category': q.category,
                    'options': q.options,
                    'order_index': q.order_index
                }
                for q in questions
            ]
            
        except Exception as e:
            logger.error(f"获取风险评估问卷失败: {e}")
            raise
    
    def calculate_risk_score(self, answers: List[Dict[str, Any]], version: str = "1.0") -> Tuple[int, RiskToleranceLevel]:
        """计算风险评分"""
        try:
            total_score = 0
            total_weight = 0
            
            # 获取问题和评分规则
            questions = self.db.query(RiskAssessmentQuestion).filter(
                RiskAssessmentQuestion.version == version,
                RiskAssessmentQuestion.is_active == True
            ).all()
            
            question_map = {q.id: q for q in questions}
            
            for answer in answers:
                question_id = answer['question_id']
                answer_value = answer['answer']
                
                if question_id not in question_map:
                    continue
                
                question = question_map[question_id]
                weight = float(question.weight or 1.0)
                
                # 根据评分规则计算分数
                score = self._calculate_answer_score(question, answer_value)
                
                total_score += score * weight
                total_weight += weight
            
            # 计算平均分数并转换为0-100范围
            if total_weight > 0:
                average_score = total_score / total_weight
                risk_score = int(min(100, max(0, average_score)))
            else:
                risk_score = 50  # 默认中等风险
            
            # 根据分数确定风险承受能力等级
            risk_tolerance = self._score_to_risk_tolerance(risk_score)
            
            return risk_score, risk_tolerance
            
        except Exception as e:
            logger.error(f"计算风险评分失败: {e}")
            raise
    
    def create_or_update_risk_profile(self, user_id: int, profile_data: Dict[str, Any]) -> RiskProfile:
        """创建或更新风险偏好档案"""
        try:
            # 查找现有档案
            existing_profile = self.db.query(RiskProfile).filter(
                RiskProfile.user_id == user_id
            ).first()
            
            if existing_profile:
                # 更新现有档案
                for key, value in profile_data.items():
                    if hasattr(existing_profile, key):
                        setattr(existing_profile, key, value)
                
                existing_profile.updated_at = datetime.now()
                existing_profile.last_assessment_date = datetime.now()
                existing_profile.next_review_date = datetime.now() + timedelta(days=365)  # 一年后复评
                
                profile = existing_profile
            else:
                # 创建新档案
                profile_data.update({
                    'user_id': user_id,
                    'last_assessment_date': datetime.now(),
                    'next_review_date': datetime.now() + timedelta(days=365)
                })
                
                profile = RiskProfile(**profile_data)
                self.db.add(profile)
            
            self.db.commit()
            self.db.refresh(profile)
            
            logger.info(f"风险偏好档案创建/更新成功: {user_id}")
            return profile
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建/更新风险偏好档案失败: {e}")
            raise
    
    def get_risk_profile(self, user_id: int) -> Optional[RiskProfile]:
        """获取用户风险偏好档案"""
        try:
            return self.db.query(RiskProfile).filter(
                RiskProfile.user_id == user_id,
                RiskProfile.is_active == True
            ).first()
            
        except Exception as e:
            logger.error(f"获取风险偏好档案失败: {e}")
            raise
    
    def assess_risk_profile(self, user_id: int, answers: List[Dict[str, Any]], 
                          personal_info: Dict[str, Any] = None) -> RiskProfile:
        """执行风险评估"""
        try:
            # 计算风险评分
            risk_score, risk_tolerance = self.calculate_risk_score(answers)
            
            # 根据个人信息和答案推断投资目标和时间范围
            investment_objective = self._infer_investment_objective(answers, personal_info)
            time_horizon = self._infer_time_horizon(answers, personal_info)
            
            # 构建档案数据
            profile_data = {
                'risk_score': risk_score,
                'risk_tolerance': risk_tolerance,
                'investment_objective': investment_objective,
                'time_horizon': time_horizon,
                'questionnaire_answers': {str(a['question_id']): a['answer'] for a in answers},
                'questionnaire_version': '1.0'
            }
            
            # 添加个人信息
            if personal_info:
                profile_data.update({
                    'age': personal_info.get('age'),
                    'annual_income': personal_info.get('annual_income'),
                    'net_worth': personal_info.get('net_worth'),
                    'investment_experience_years': personal_info.get('investment_experience_years')
                })
            
            # 设置默认风险参数
            profile_data.update(self._get_default_risk_parameters(risk_tolerance))
            
            # 创建或更新档案
            profile = self.create_or_update_risk_profile(user_id, profile_data)
            
            # 生成默认投资组合配置
            self._create_default_portfolio_config(user_id, profile.id, risk_tolerance)
            
            # 生成投资建议
            self._generate_initial_recommendations(user_id, profile.id)
            
            return profile
            
        except Exception as e:
            logger.error(f"执行风险评估失败: {e}")
            raise
    
    # ==================== 投资组合配置 ====================
    
    def create_portfolio_configuration(self, user_id: int, config_data: Dict[str, Any]) -> PortfolioConfiguration:
        """创建投资组合配置"""
        try:
            # 获取用户风险档案
            risk_profile = self.get_risk_profile(user_id)
            if not risk_profile:
                raise ValueError("用户尚未完成风险评估")
            
            # 验证资产分配
            self._validate_asset_allocation(config_data['asset_allocation'])
            
            config_data.update({
                'user_id': user_id,
                'risk_profile_id': risk_profile.id
            })
            
            config = PortfolioConfiguration(**config_data)
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            
            # 记录分配历史
            self._record_allocation_history(config.id, config_data['asset_allocation'], "initial_creation")
            
            logger.info(f"投资组合配置创建成功: {user_id}")
            return config
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建投资组合配置失败: {e}")
            raise
    
    def get_portfolio_configurations(self, user_id: int) -> List[PortfolioConfiguration]:
        """获取用户投资组合配置"""
        try:
            return self.db.query(PortfolioConfiguration).filter(
                PortfolioConfiguration.user_id == user_id,
                PortfolioConfiguration.is_active == True
            ).order_by(desc(PortfolioConfiguration.is_default), desc(PortfolioConfiguration.created_at)).all()
            
        except Exception as e:
            logger.error(f"获取投资组合配置失败: {e}")
            raise
    
    def update_portfolio_configuration(self, config_id: int, user_id: int, 
                                     update_data: Dict[str, Any]) -> PortfolioConfiguration:
        """更新投资组合配置"""
        try:
            config = self.db.query(PortfolioConfiguration).filter(
                PortfolioConfiguration.id == config_id,
                PortfolioConfiguration.user_id == user_id
            ).first()
            
            if not config:
                raise ValueError("投资组合配置不存在")
            
            # 如果更新资产分配，验证并记录历史
            if 'asset_allocation' in update_data:
                self._validate_asset_allocation(update_data['asset_allocation'])
                self._record_allocation_history(config_id, update_data['asset_allocation'], "manual_update")
            
            # 更新配置
            for key, value in update_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            config.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(config)
            
            logger.info(f"投资组合配置更新成功: {config_id}")
            return config
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新投资组合配置失败: {e}")
            raise
    
    def optimize_portfolio(self, user_id: int, optimization_params: Dict[str, Any]) -> Dict[str, Any]:
        """优化投资组合"""
        try:
            risk_profile = self.get_risk_profile(user_id)
            if not risk_profile:
                raise ValueError("用户尚未完成风险评估")
            
            # 获取市场数据和预期收益率
            market_data = self._get_market_data()
            
            # 执行均值方差优化
            optimized_allocation = self._mean_variance_optimization(
                market_data,
                risk_profile,
                optimization_params
            )
            
            # 计算优化后的指标
            metrics = self._calculate_portfolio_metrics(optimized_allocation, market_data)
            
            # 生成建议
            suggestions = self._generate_allocation_suggestions(optimized_allocation, risk_profile)
            
            return {
                'optimized_allocation': optimized_allocation,
                'expected_return': metrics['expected_return'],
                'expected_volatility': metrics['expected_volatility'],
                'sharpe_ratio': metrics['sharpe_ratio'],
                'optimization_score': metrics['optimization_score'],
                'suggestions': suggestions
            }
            
        except Exception as e:
            logger.error(f"投资组合优化失败: {e}")
            raise
    
    def rebalance_portfolio(self, config_id: int, user_id: int) -> Dict[str, Any]:
        """再平衡投资组合"""
        try:
            config = self.db.query(PortfolioConfiguration).filter(
                PortfolioConfiguration.id == config_id,
                PortfolioConfiguration.user_id == user_id
            ).first()
            
            if not config:
                raise ValueError("投资组合配置不存在")
            
            # 获取当前持仓
            current_positions = self._get_current_positions(user_id)
            
            # 计算目标分配
            target_allocation = config.asset_allocation
            
            # 计算再平衡操作
            rebalance_actions = self._calculate_rebalance_actions(
                current_positions, 
                target_allocation, 
                config.rebalance_threshold
            )
            
            # 更新再平衡日期
            config.last_rebalance_date = datetime.now()
            config.next_rebalance_date = self._calculate_next_rebalance_date(config.rebalance_frequency)
            self.db.commit()
            
            # 记录分配历史
            self._record_allocation_history(config_id, target_allocation, "rebalance")
            
            return {
                'rebalance_needed': len(rebalance_actions) > 0,
                'actions': rebalance_actions,
                'target_allocation': target_allocation,
                'current_allocation': current_positions,
                'next_rebalance_date': config.next_rebalance_date
            }
            
        except Exception as e:
            logger.error(f"再平衡投资组合失败: {e}")
            raise
    
    # ==================== 投资建议 ====================
    
    def get_investment_recommendations(self, user_id: int, limit: int = 10) -> List[InvestmentRecommendation]:
        """获取投资建议"""
        try:
            return self.db.query(InvestmentRecommendation).filter(
                InvestmentRecommendation.user_id == user_id,
                InvestmentRecommendation.status == 'active',
                or_(
                    InvestmentRecommendation.valid_until.is_(None),
                    InvestmentRecommendation.valid_until > datetime.now()
                )
            ).order_by(
                desc(InvestmentRecommendation.priority),
                desc(InvestmentRecommendation.created_at)
            ).limit(limit).all()
            
        except Exception as e:
            logger.error(f"获取投资建议失败: {e}")
            raise
    
    def generate_recommendations(self, user_id: int) -> List[InvestmentRecommendation]:
        """生成投资建议"""
        try:
            risk_profile = self.get_risk_profile(user_id)
            if not risk_profile:
                raise ValueError("用户尚未完成风险评估")
            
            recommendations = []
            
            # 基于风险偏好生成建议
            recommendations.extend(self._generate_risk_based_recommendations(user_id, risk_profile))
            
            # 基于市场环境生成建议
            recommendations.extend(self._generate_market_based_recommendations(user_id, risk_profile))
            
            # 基于组合分析生成建议
            recommendations.extend(self._generate_portfolio_based_recommendations(user_id, risk_profile))
            
            # 保存建议到数据库
            for rec_data in recommendations:
                rec_data.update({
                    'user_id': user_id,
                    'risk_profile_id': risk_profile.id
                })
                recommendation = InvestmentRecommendation(**rec_data)
                self.db.add(recommendation)
            
            self.db.commit()
            
            logger.info(f"生成投资建议成功: {user_id}, {len(recommendations)}条")
            return recommendations
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"生成投资建议失败: {e}")
            raise
    
    def update_recommendation_status(self, recommendation_id: int, user_id: int, 
                                   status: str, is_accepted: bool = None) -> InvestmentRecommendation:
        """更新投资建议状态"""
        try:
            recommendation = self.db.query(InvestmentRecommendation).filter(
                InvestmentRecommendation.id == recommendation_id,
                InvestmentRecommendation.user_id == user_id
            ).first()
            
            if not recommendation:
                raise ValueError("投资建议不存在")
            
            recommendation.status = status
            recommendation.is_read = True
            
            if is_accepted is not None:
                recommendation.is_accepted = is_accepted
            
            if status == 'executed':
                recommendation.executed_at = datetime.now()
            
            recommendation.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(recommendation)
            
            return recommendation
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新投资建议状态失败: {e}")
            raise
    
    # ==================== 风险提醒 ====================
    
    def get_risk_alerts(self, user_id: int, limit: int = 20) -> List[RiskAlert]:
        """获取风险提醒"""
        try:
            return self.db.query(RiskAlert).filter(
                RiskAlert.user_id == user_id,
                RiskAlert.status == 'active'
            ).order_by(
                desc(RiskAlert.severity),
                desc(RiskAlert.created_at)
            ).limit(limit).all()
            
        except Exception as e:
            logger.error(f"获取风险提醒失败: {e}")
            raise
    
    def create_risk_alert(self, user_id: int, alert_data: Dict[str, Any]) -> RiskAlert:
        """创建风险提醒"""
        try:
            alert_data['user_id'] = user_id
            alert = RiskAlert(**alert_data)
            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)
            
            logger.info(f"风险提醒创建成功: {user_id}")
            return alert
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建风险提醒失败: {e}")
            raise
    
    def acknowledge_risk_alert(self, alert_id: int, user_id: int, resolution_note: str = None) -> RiskAlert:
        """确认风险提醒"""
        try:
            alert = self.db.query(RiskAlert).filter(
                RiskAlert.id == alert_id,
                RiskAlert.user_id == user_id
            ).first()
            
            if not alert:
                raise ValueError("风险提醒不存在")
            
            alert.is_acknowledged = True
            alert.acknowledged_at = datetime.now()
            
            if resolution_note:
                alert.resolution_note = resolution_note
                alert.status = 'resolved'
                alert.resolved_at = datetime.now()
            
            alert.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(alert)
            
            return alert
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"确认风险提醒失败: {e}")
            raise
    
    # ==================== 私有辅助方法 ====================
    
    def _calculate_answer_score(self, question: RiskAssessmentQuestion, answer: str) -> float:
        """计算答案得分"""
        try:
            scoring_rules = question.scoring_rules or {}
            
            # 如果有具体的评分规则
            if answer in scoring_rules:
                return float(scoring_rules[answer])
            
            # 默认评分逻辑（基于选项索引）
            options = question.options or []
            for i, option in enumerate(options):
                if option.get('value') == answer:
                    # 假设选项按风险从低到高排列，分数从0到100
                    return (i / max(1, len(options) - 1)) * 100
            
            return 50.0  # 默认中等分数
            
        except Exception as e:
            logger.error(f"计算答案得分失败: {e}")
            return 50.0
    
    def _score_to_risk_tolerance(self, score: int) -> RiskToleranceLevel:
        """根据分数确定风险承受能力等级"""
        if score <= 20:
            return RiskToleranceLevel.CONSERVATIVE
        elif score <= 40:
            return RiskToleranceLevel.MODERATE
        elif score <= 60:
            return RiskToleranceLevel.BALANCED
        elif score <= 80:
            return RiskToleranceLevel.AGGRESSIVE
        else:
            return RiskToleranceLevel.SPECULATIVE
    
    def _infer_investment_objective(self, answers: List[Dict[str, Any]], 
                                  personal_info: Dict[str, Any] = None) -> InvestmentObjective:
        """推断投资目标"""
        # 简化逻辑，实际应该基于具体问题分析
        age = personal_info.get('age', 40) if personal_info else 40
        
        if age < 30:
            return InvestmentObjective.CAPITAL_APPRECIATION
        elif age < 50:
            return InvestmentObjective.BALANCED_GROWTH
        else:
            return InvestmentObjective.INCOME_GENERATION
    
    def _infer_time_horizon(self, answers: List[Dict[str, Any]], 
                          personal_info: Dict[str, Any] = None) -> TimeHorizon:
        """推断投资时间范围"""
        # 简化逻辑，实际应该基于具体问题分析
        age = personal_info.get('age', 40) if personal_info else 40
        
        if age < 35:
            return TimeHorizon.LONG_TERM
        elif age < 55:
            return TimeHorizon.MEDIUM_TERM
        else:
            return TimeHorizon.SHORT_TERM
    
    def _get_default_risk_parameters(self, risk_tolerance: RiskToleranceLevel) -> Dict[str, Any]:
        """获取默认风险参数"""
        risk_params = {
            RiskToleranceLevel.CONSERVATIVE: {
                'max_portfolio_loss_percentage': Decimal('5.0'),
                'max_single_position_percentage': Decimal('10.0'),
                'preferred_asset_classes': ['bonds', 'cash', 'conservative_funds'],
                'excluded_asset_classes': ['crypto', 'options', 'futures']
            },
            RiskToleranceLevel.MODERATE: {
                'max_portfolio_loss_percentage': Decimal('10.0'),
                'max_single_position_percentage': Decimal('15.0'),
                'preferred_asset_classes': ['bonds', 'stocks', 'balanced_funds'],
                'excluded_asset_classes': ['crypto', 'options']
            },
            RiskToleranceLevel.BALANCED: {
                'max_portfolio_loss_percentage': Decimal('15.0'),
                'max_single_position_percentage': Decimal('20.0'),
                'preferred_asset_classes': ['stocks', 'bonds', 'etfs', 'reits'],
                'excluded_asset_classes': ['crypto']
            },
            RiskToleranceLevel.AGGRESSIVE: {
                'max_portfolio_loss_percentage': Decimal('25.0'),
                'max_single_position_percentage': Decimal('30.0'),
                'preferred_asset_classes': ['stocks', 'growth_funds', 'etfs', 'reits'],
                'excluded_asset_classes': []
            },
            RiskToleranceLevel.SPECULATIVE: {
                'max_portfolio_loss_percentage': Decimal('40.0'),
                'max_single_position_percentage': Decimal('50.0'),
                'preferred_asset_classes': ['stocks', 'crypto', 'options', 'futures'],
                'excluded_asset_classes': []
            }
        }
        
        return risk_params.get(risk_tolerance, risk_params[RiskToleranceLevel.BALANCED])
    
    def _create_default_portfolio_config(self, user_id: int, risk_profile_id: int, 
                                       risk_tolerance: RiskToleranceLevel):
        """创建默认投资组合配置"""
        try:
            # 根据风险承受能力设置默认分配
            default_allocations = {
                RiskToleranceLevel.CONSERVATIVE: {
                    'bonds': Decimal('60.0'),
                    'stocks': Decimal('30.0'),
                    'cash': Decimal('10.0')
                },
                RiskToleranceLevel.MODERATE: {
                    'bonds': Decimal('50.0'),
                    'stocks': Decimal('40.0'),
                    'cash': Decimal('10.0')
                },
                RiskToleranceLevel.BALANCED: {
                    'stocks': Decimal('60.0'),
                    'bonds': Decimal('30.0'),
                    'cash': Decimal('10.0')
                },
                RiskToleranceLevel.AGGRESSIVE: {
                    'stocks': Decimal('70.0'),
                    'bonds': Decimal('20.0'),
                    'cash': Decimal('10.0')
                },
                RiskToleranceLevel.SPECULATIVE: {
                    'stocks': Decimal('80.0'),
                    'bonds': Decimal('10.0'),
                    'cash': Decimal('10.0')
                }
            }
            
            allocation = default_allocations.get(risk_tolerance, default_allocations[RiskToleranceLevel.BALANCED])
            
            config_data = {
                'user_id': user_id,
                'risk_profile_id': risk_profile_id,
                'name': '默认配置',
                'description': f'基于{risk_tolerance.value}风险偏好的默认投资组合配置',
                'asset_allocation': allocation,
                'is_default': True,
                'rebalance_threshold': Decimal('5.0'),
                'auto_rebalance': False
            }
            
            config = PortfolioConfiguration(**config_data)
            self.db.add(config)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"创建默认投资组合配置失败: {e}")
    
    def _generate_initial_recommendations(self, user_id: int, risk_profile_id: int):
        """生成初始投资建议"""
        try:
            recommendations = [
                {
                    'title': '完善投资组合配置',
                    'description': '建议根据您的风险偏好调整投资组合分配',
                    'recommendation_type': 'portfolio_optimization',
                    'priority': 'high',
                    'reasoning': '基于您的风险评估结果，建议优化投资组合以获得更好的风险收益比'
                },
                {
                    'title': '定期复评风险偏好',
                    'description': '建议每年重新评估一次风险偏好',
                    'recommendation_type': 'risk_reassessment',
                    'priority': 'medium',
                    'reasoning': '随着年龄和财务状况的变化，风险偏好可能会发生变化'
                }
            ]
            
            for rec_data in recommendations:
                rec_data.update({
                    'user_id': user_id,
                    'risk_profile_id': risk_profile_id,
                    'valid_from': datetime.now(),
                    'valid_until': datetime.now() + timedelta(days=90)
                })
                recommendation = InvestmentRecommendation(**rec_data)
                self.db.add(recommendation)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"生成初始投资建议失败: {e}")
    
    def _validate_asset_allocation(self, allocation: Dict[str, Any]):
        """验证资产分配"""
        total = sum(Decimal(str(v)) for v in allocation.values())
        if abs(total - 100) > Decimal('0.01'):
            raise ValueError(f"资产分配总和必须等于100%，当前为{total}%")
    
    def _record_allocation_history(self, config_id: int, allocation: Dict[str, Any], reason: str):
        """记录分配历史"""
        try:
            history = AllocationHistory(
                portfolio_config_id=config_id,
                allocation_date=datetime.now(),
                allocation_data=allocation,
                change_reason=reason
            )
            self.db.add(history)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"记录分配历史失败: {e}")
    
    def _get_market_data(self) -> Dict[str, Any]:
        """获取市场数据（模拟）"""
        # 这里应该从实际的市场数据源获取数据
        return {
            'expected_returns': {
                'stocks': 0.08,
                'bonds': 0.04,
                'cash': 0.02,
                'reits': 0.06
            },
            'volatilities': {
                'stocks': 0.15,
                'bonds': 0.05,
                'cash': 0.01,
                'reits': 0.12
            },
            'correlations': {
                ('stocks', 'bonds'): 0.1,
                ('stocks', 'cash'): 0.0,
                ('bonds', 'cash'): 0.0
            }
        }
    
    def _mean_variance_optimization(self, market_data: Dict[str, Any], 
                                  risk_profile: RiskProfile, 
                                  params: Dict[str, Any]) -> Dict[str, Decimal]:
        """均值方差优化（简化版本）"""
        # 这里应该实现真正的均值方差优化算法
        # 现在返回基于风险偏好的简化分配
        
        risk_tolerance = risk_profile.risk_tolerance
        
        if risk_tolerance == RiskToleranceLevel.CONSERVATIVE:
            return {'bonds': Decimal('60'), 'stocks': Decimal('30'), 'cash': Decimal('10')}
        elif risk_tolerance == RiskToleranceLevel.MODERATE:
            return {'bonds': Decimal('50'), 'stocks': Decimal('40'), 'cash': Decimal('10')}
        elif risk_tolerance == RiskToleranceLevel.BALANCED:
            return {'stocks': Decimal('60'), 'bonds': Decimal('30'), 'cash': Decimal('10')}
        elif risk_tolerance == RiskToleranceLevel.AGGRESSIVE:
            return {'stocks': Decimal('70'), 'bonds': Decimal('20'), 'cash': Decimal('10')}
        else:  # SPECULATIVE
            return {'stocks': Decimal('80'), 'bonds': Decimal('10'), 'cash': Decimal('10')}
    
    def _calculate_portfolio_metrics(self, allocation: Dict[str, Decimal], 
                                   market_data: Dict[str, Any]) -> Dict[str, Decimal]:
        """计算投资组合指标"""
        expected_returns = market_data['expected_returns']
        volatilities = market_data['volatilities']
        
        # 计算预期收益率
        expected_return = sum(
            float(allocation.get(asset, 0)) / 100 * expected_returns.get(asset, 0)
            for asset in allocation.keys()
        )
        
        # 简化的波动率计算（忽略相关性）
        expected_volatility = sum(
            (float(allocation.get(asset, 0)) / 100) ** 2 * (volatilities.get(asset, 0) ** 2)
            for asset in allocation.keys()
        ) ** 0.5
        
        # 夏普比率（假设无风险利率为2%）
        risk_free_rate = 0.02
        sharpe_ratio = (expected_return - risk_free_rate) / expected_volatility if expected_volatility > 0 else 0
        
        # 优化评分（简化）
        optimization_score = min(100, max(0, sharpe_ratio * 50 + 50))
        
        return {
            'expected_return': Decimal(str(round(expected_return, 4))),
            'expected_volatility': Decimal(str(round(expected_volatility, 4))),
            'sharpe_ratio': Decimal(str(round(sharpe_ratio, 4))),
            'optimization_score': Decimal(str(round(optimization_score, 2)))
        }
    
    def _generate_allocation_suggestions(self, allocation: Dict[str, Decimal], 
                                       risk_profile: RiskProfile) -> List[Dict[str, Any]]:
        """生成分配建议"""
        suggestions = []
        
        for asset, percentage in allocation.items():
            suggestions.append({
                'asset_class': asset,
                'suggested_percentage': percentage,
                'reasoning': f'基于您的{risk_profile.risk_tolerance.value}风险偏好，建议{asset}分配{percentage}%'
            })
        
        return suggestions
    
    def _get_current_positions(self, user_id: int) -> Dict[str, Decimal]:
        """获取当前持仓（模拟）"""
        # 这里应该从实际的持仓数据获取
        return {
            'stocks': Decimal('65.0'),
            'bonds': Decimal('25.0'),
            'cash': Decimal('10.0')
        }
    
    def _calculate_rebalance_actions(self, current_positions: Dict[str, Decimal], 
                                   target_allocation: Dict[str, Decimal], 
                                   threshold: Decimal) -> List[Dict[str, Any]]:
        """计算再平衡操作"""
        actions = []
        
        for asset, target_pct in target_allocation.items():
            current_pct = current_positions.get(asset, Decimal('0'))
            difference = target_pct - current_pct
            
            if abs(difference) > threshold:
                action_type = 'buy' if difference > 0 else 'sell'
                actions.append({
                    'asset': asset,
                    'action': action_type,
                    'current_percentage': float(current_pct),
                    'target_percentage': float(target_pct),
                    'difference': float(difference),
                    'amount_percentage': float(abs(difference))
                })
        
        return actions
    
    def _calculate_next_rebalance_date(self, frequency: str) -> datetime:
        """计算下次再平衡日期"""
        now = datetime.now()
        
        if frequency == 'weekly':
            return now + timedelta(weeks=1)
        elif frequency == 'monthly':
            return now + timedelta(days=30)
        elif frequency == 'quarterly':
            return now + timedelta(days=90)
        elif frequency == 'yearly':
            return now + timedelta(days=365)
        else:
            return now + timedelta(days=30)  # 默认月度
    
    def _generate_risk_based_recommendations(self, user_id: int, risk_profile: RiskProfile) -> List[Dict[str, Any]]:
        """基于风险偏好生成建议"""
        recommendations = []
        
        # 根据风险承受能力生成相应建议
        if risk_profile.risk_tolerance == RiskToleranceLevel.CONSERVATIVE:
            recommendations.append({
                'title': '增加债券配置',
                'description': '考虑增加高等级债券的配置以降低组合风险',
                'recommendation_type': 'asset_allocation',
                'priority': 'medium',
                'target_symbol': 'bonds',
                'reasoning': '基于您的保守型风险偏好，建议增加债券配置'
            })
        
        return recommendations
    
    def _generate_market_based_recommendations(self, user_id: int, risk_profile: RiskProfile) -> List[Dict[str, Any]]:
        """基于市场环境生成建议"""
        recommendations = []
        
        # 获取当前市场环境
        current_regime = self.db.query(MarketRegime).filter(
            MarketRegime.is_current == True
        ).first()
        
        if current_regime and current_regime.recommended_allocations:
            recommendations.append({
                'title': f'适应{current_regime.regime_name}市场环境',
                'description': f'当前市场环境为{current_regime.regime_name}，建议调整投资组合',
                'recommendation_type': 'market_adaptation',
                'priority': 'high',
                'reasoning': current_regime.description
            })
        
        return recommendations
    
    def _generate_portfolio_based_recommendations(self, user_id: int, risk_profile: RiskProfile) -> List[Dict[str, Any]]:
        """基于组合分析生成建议"""
        recommendations = []
        
        # 获取用户当前配置
        configs = self.get_portfolio_configurations(user_id)
        
        if not configs:
            recommendations.append({
                'title': '创建投资组合配置',
                'description': '建议创建您的第一个投资组合配置',
                'recommendation_type': 'portfolio_creation',
                'priority': 'high',
                'reasoning': '您还没有创建任何投资组合配置'
            })
        
        return recommendations