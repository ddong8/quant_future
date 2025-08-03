"""
风险报告和分析服务
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from enum import Enum
import pandas as pd
import numpy as np
from decimal import Decimal

from app.models.risk import RiskEvent, RiskRule, RiskMetrics, RiskLimit
from app.models.position import Position
from app.models.order import Order
from app.models.account import Account
from app.models.user import User
from app.schemas.risk import RiskReportRequest, RiskReport, RiskAnalysis
from app.services.notification_service import NotificationService
from app.utils.risk_calculator import RiskCalculator
from app.core.logging import get_logger

logger = get_logger(__name__)


class ReportType(str, Enum):
    """报告类型枚举"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class RiskReportService:
    """风险报告和分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
        self.risk_calculator = RiskCalculator()
    
    async def generate_risk_report(self, user_id: int, report_type: ReportType, 
                                 start_date: datetime, end_date: datetime,
                                 custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成风险报告"""
        try:
            logger.info(f"生成风险报告 - 用户: {user_id}, 类型: {report_type}")
            
            # 获取基础数据
            base_data = await self._collect_base_data(user_id, start_date, end_date)
            
            # 生成报告各个部分
            report = {
                "report_id": f"risk_report_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "user_id": user_id,
                "report_type": report_type.value,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "generated_at": datetime.utcnow().isoformat(),
                
                # 执行摘要
                "executive_summary": await self._generate_executive_summary(base_data),
                
                # 风险指标分析
                "risk_metrics": await self._analyze_risk_metrics(base_data),
                
                # 风险事件分析
                "risk_events": await self._analyze_risk_events(base_data),
                
                # 持仓风险分析
                "position_analysis": await self._analyze_position_risk(base_data),
                
                # 风险归因分析
                "risk_attribution": await self._perform_risk_attribution(base_data),
                
                # 趋势分析
                "trend_analysis": await self._analyze_risk_trends(base_data),
                
                # 改进建议
                "recommendations": await self._generate_recommendations(base_data),
                
                # 图表数据
                "charts_data": await self._generate_charts_data(base_data)
            }
            
            # 保存报告
            await self._save_report(report)
            
            return report
            
        except Exception as e:
            logger.error(f"生成风险报告失败: {str(e)}")
            raise
    
    async def _collect_base_data(self, user_id: int, start_date: datetime, 
                               end_date: datetime) -> Dict[str, Any]:
        """收集基础数据"""
        try:
            # 获取用户信息
            user = self.db.query(User).filter(User.id == user_id).first()
            account = self.db.query(Account).filter(Account.user_id == user_id).first()
            
            # 获取时间范围内的风险事件
            risk_events = self.db.query(RiskEvent).filter(
                and_(
                    RiskEvent.user_id == user_id,
                    RiskEvent.created_at >= start_date,
                    RiskEvent.created_at <= end_date
                )
            ).all()
            
            # 获取风险指标
            risk_metrics = self.db.query(RiskMetrics).filter(
                and_(
                    RiskMetrics.user_id == user_id,
                    RiskMetrics.date >= start_date.date(),
                    RiskMetrics.date <= end_date.date()
                )
            ).order_by(RiskMetrics.date).all()
            
            # 获取持仓数据
            positions = self.db.query(Position).filter(
                and_(
                    Position.user_id == user_id,
                    Position.created_at <= end_date
                )
            ).all()
            
            # 获取订单数据
            orders = self.db.query(Order).filter(
                and_(
                    Order.user_id == user_id,
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                )
            ).all()
            
            # 获取风险规则
            risk_rules = self.db.query(RiskRule).filter(
                RiskRule.user_id == user_id
            ).all()
            
            # 获取风险限额
            risk_limits = self.db.query(RiskLimit).filter(
                RiskLimit.user_id == user_id
            ).all()
            
            return {
                "user": user,
                "account": account,
                "risk_events": risk_events,
                "risk_metrics": risk_metrics,
                "positions": positions,
                "orders": orders,
                "risk_rules": risk_rules,
                "risk_limits": risk_limits,
                "period": {"start": start_date, "end": end_date}
            }
            
        except Exception as e:
            logger.error(f"收集基础数据失败: {str(e)}")
            raise 
   
    async def _generate_executive_summary(self, base_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成执行摘要"""
        try:
            risk_events = base_data["risk_events"]
            risk_metrics = base_data["risk_metrics"]
            account = base_data["account"]
            
            # 计算关键指标
            total_events = len(risk_events)
            critical_events = len([e for e in risk_events if e.severity == "critical"])
            high_events = len([e for e in risk_events if e.severity == "high"])
            
            # 计算风险评分
            risk_score = await self._calculate_risk_score(base_data)
            
            # 获取最新风险指标
            latest_metrics = risk_metrics[-1] if risk_metrics else None
            
            return {
                "risk_score": risk_score,
                "risk_level": self._get_risk_level(risk_score),
                "total_events": total_events,
                "critical_events": critical_events,
                "high_events": high_events,
                "portfolio_value": float(account.total_balance) if account else 0,
                "max_drawdown": float(latest_metrics.max_drawdown) if latest_metrics and latest_metrics.max_drawdown else 0,
                "var_95": float(latest_metrics.var_95) if latest_metrics and latest_metrics.var_95 else 0,
                "key_findings": await self._extract_key_findings(base_data)
            }
            
        except Exception as e:
            logger.error(f"生成执行摘要失败: {str(e)}")
            return {}
    
    async def _analyze_risk_metrics(self, base_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析风险指标"""
        try:
            risk_metrics = base_data["risk_metrics"]
            
            if not risk_metrics:
                return {"message": "无风险指标数据"}
            
            # 转换为DataFrame进行分析
            df = pd.DataFrame([{
                "date": m.date,
                "portfolio_value": float(m.portfolio_value) if m.portfolio_value else 0,
                "daily_return": float(m.daily_return) if m.daily_return else 0,
                "volatility": float(m.volatility) if m.volatility else 0,
                "max_drawdown": float(m.max_drawdown) if m.max_drawdown else 0,
                "var_95": float(m.var_95) if m.var_95 else 0,
                "sharpe_ratio": float(m.sharpe_ratio) if m.sharpe_ratio else 0,
                "leverage_ratio": float(m.leverage_ratio) if m.leverage_ratio else 0
            } for m in risk_metrics])
            
            # 计算统计指标
            analysis = {
                "period_return": df["daily_return"].sum(),
                "avg_daily_return": df["daily_return"].mean(),
                "return_volatility": df["daily_return"].std(),
                "max_drawdown": df["max_drawdown"].max(),
                "avg_var_95": df["var_95"].mean(),
                "max_var_95": df["var_95"].max(),
                "avg_sharpe_ratio": df["sharpe_ratio"].mean(),
                "max_leverage": df["leverage_ratio"].max(),
                "avg_leverage": df["leverage_ratio"].mean(),
                
                # 风险调整收益指标
                "risk_adjusted_return": df["daily_return"].mean() / df["daily_return"].std() if df["daily_return"].std() > 0 else 0,
                
                # 趋势分析
                "return_trend": "上升" if df["daily_return"].iloc[-5:].mean() > df["daily_return"].iloc[:5].mean() else "下降",
                "volatility_trend": "上升" if df["volatility"].iloc[-5:].mean() > df["volatility"].iloc[:5].mean() else "下降",
                
                # 时间序列数据
                "time_series": {
                    "dates": df["date"].dt.strftime("%Y-%m-%d").tolist(),
                    "portfolio_values": df["portfolio_value"].tolist(),
                    "daily_returns": df["daily_return"].tolist(),
                    "volatilities": df["volatility"].tolist(),
                    "drawdowns": df["max_drawdown"].tolist(),
                    "var_values": df["var_95"].tolist()
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析风险指标失败: {str(e)}")
            return {}
    
    async def _analyze_risk_events(self, base_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析风险事件"""
        try:
            risk_events = base_data["risk_events"]
            
            if not risk_events:
                return {"message": "无风险事件"}
            
            # 按严重程度分类
            severity_counts = {}
            for event in risk_events:
                severity = event.severity
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # 按事件类型分类
            type_counts = {}
            for event in risk_events:
                event_type = event.event_type
                type_counts[event_type] = type_counts.get(event_type, 0) + 1
            
            # 按时间分布
            daily_counts = {}
            for event in risk_events:
                date_str = event.created_at.date().strftime("%Y-%m-%d")
                daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
            
            # 最频繁的事件
            most_common_events = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # 最近的关键事件
            critical_events = [
                {
                    "id": event.id,
                    "type": event.event_type,
                    "severity": event.severity,
                    "title": event.title,
                    "message": event.message,
                    "created_at": event.created_at.isoformat()
                }
                for event in sorted(risk_events, key=lambda x: x.created_at, reverse=True)[:10]
                if event.severity in ["critical", "high"]
            ]
            
            return {
                "total_events": len(risk_events),
                "severity_distribution": severity_counts,
                "type_distribution": type_counts,
                "daily_distribution": daily_counts,
                "most_common_events": most_common_events,
                "recent_critical_events": critical_events,
                "event_frequency": len(risk_events) / max(1, (base_data["period"]["end"] - base_data["period"]["start"]).days)
            }
            
        except Exception as e:
            logger.error(f"分析风险事件失败: {str(e)}")
            return {}
    
    async def _analyze_position_risk(self, base_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析持仓风险"""
        try:
            positions = base_data["positions"]
            account = base_data["account"]
            
            if not positions:
                return {"message": "无持仓数据"}
            
            total_value = float(account.total_balance) if account else 1
            
            # 持仓分析
            position_analysis = []
            total_exposure = 0
            
            for position in positions:
                if position.quantity != 0:
                    market_value = abs(position.quantity * position.current_price) if position.current_price else 0
                    concentration = market_value / total_value if total_value > 0 else 0
                    
                    position_analysis.append({
                        "symbol": position.symbol,
                        "quantity": float(position.quantity),
                        "market_value": market_value,
                        "concentration": concentration,
                        "unrealized_pnl": float(position.unrealized_pnl) if position.unrealized_pnl else 0,
                        "pnl_ratio": float(position.unrealized_pnl) / market_value if market_value > 0 and position.unrealized_pnl else 0
                    })
                    
                    total_exposure += market_value
            
            # 排序并获取前10大持仓
            position_analysis.sort(key=lambda x: x["market_value"], reverse=True)
            top_positions = position_analysis[:10]
            
            # 计算集中度指标
            top_5_concentration = sum(p["concentration"] for p in position_analysis[:5])
            top_10_concentration = sum(p["concentration"] for p in position_analysis[:10])
            
            # 行业/板块分析（这里简化处理）
            sector_exposure = {}
            for pos in position_analysis:
                # 简化的行业分类，实际应该从市场数据获取
                sector = self._get_sector_by_symbol(pos["symbol"])
                sector_exposure[sector] = sector_exposure.get(sector, 0) + pos["market_value"]
            
            return {
                "total_positions": len([p for p in positions if p.quantity != 0]),
                "total_exposure": total_exposure,
                "exposure_ratio": total_exposure / total_value if total_value > 0 else 0,
                "top_positions": top_positions,
                "top_5_concentration": top_5_concentration,
                "top_10_concentration": top_10_concentration,
                "sector_exposure": sector_exposure,
                "long_positions": len([p for p in positions if p.quantity > 0]),
                "short_positions": len([p for p in positions if p.quantity < 0]),
                "total_unrealized_pnl": sum(float(p.unrealized_pnl) for p in positions if p.unrealized_pnl)
            }
            
        except Exception as e:
            logger.error(f"分析持仓风险失败: {str(e)}")
            return {}
    
    async def _perform_risk_attribution(self, base_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行风险归因分析"""
        try:
            positions = base_data["positions"]
            risk_metrics = base_data["risk_metrics"]
            
            if not positions or not risk_metrics:
                return {"message": "数据不足，无法进行风险归因分析"}
            
            # 计算各持仓对总风险的贡献
            risk_contributions = []
            total_var = 0
            
            for position in positions:
                if position.quantity != 0:
                    # 简化的风险贡献计算
                    position_var = self._calculate_position_var(position)
                    correlation = self._get_correlation_with_portfolio(position)
                    
                    risk_contribution = position_var * correlation
                    risk_contributions.append({
                        "symbol": position.symbol,
                        "var_contribution": risk_contribution,
                        "weight": abs(position.quantity * position.current_price) if position.current_price else 0
                    })
                    
                    total_var += risk_contribution
            
            # 按风险贡献排序
            risk_contributions.sort(key=lambda x: abs(x["var_contribution"]), reverse=True)
            
            # 计算风险因子贡献
            factor_contributions = {
                "market_risk": 0.6,  # 市场风险贡献
                "specific_risk": 0.3,  # 个股风险贡献
                "currency_risk": 0.05,  # 汇率风险贡献
                "liquidity_risk": 0.05  # 流动性风险贡献
            }
            
            return {
                "total_var": total_var,
                "position_contributions": risk_contributions[:10],
                "factor_contributions": factor_contributions,
                "concentration_risk": self._calculate_concentration_risk(positions),
                "correlation_risk": self._calculate_correlation_risk(positions)
            }
            
        except Exception as e:
            logger.error(f"风险归因分析失败: {str(e)}")
            return {}
    
    async def _analyze_risk_trends(self, base_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析风险趋势"""
        try:
            risk_metrics = base_data["risk_metrics"]
            risk_events = base_data["risk_events"]
            
            if not risk_metrics:
                return {"message": "无足够数据进行趋势分析"}
            
            # 转换为时间序列
            df = pd.DataFrame([{
                "date": m.date,
                "var_95": float(m.var_95) if m.var_95 else 0,
                "volatility": float(m.volatility) if m.volatility else 0,
                "max_drawdown": float(m.max_drawdown) if m.max_drawdown else 0,
                "leverage_ratio": float(m.leverage_ratio) if m.leverage_ratio else 0
            } for m in risk_metrics])
            
            # 计算趋势
            trends = {}
            for column in ["var_95", "volatility", "max_drawdown", "leverage_ratio"]:
                if len(df) >= 5:
                    recent_avg = df[column].tail(5).mean()
                    earlier_avg = df[column].head(5).mean()
                    trend_direction = "上升" if recent_avg > earlier_avg else "下降"
                    trend_magnitude = abs(recent_avg - earlier_avg) / earlier_avg if earlier_avg != 0 else 0
                    
                    trends[column] = {
                        "direction": trend_direction,
                        "magnitude": trend_magnitude,
                        "current_value": df[column].iloc[-1],
                        "period_change": (df[column].iloc[-1] - df[column].iloc[0]) / df[column].iloc[0] if df[column].iloc[0] != 0 else 0
                    }
            
            # 事件频率趋势
            event_trend = self._analyze_event_frequency_trend(risk_events)
            
            # 预测未来风险水平
            risk_forecast = self._forecast_risk_levels(df)
            
            return {
                "metric_trends": trends,
                "event_frequency_trend": event_trend,
                "risk_forecast": risk_forecast,
                "trend_summary": self._summarize_trends(trends)
            }
            
        except Exception as e:
            logger.error(f"分析风险趋势失败: {str(e)}")
            return {}
    
    async def _generate_recommendations(self, base_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成改进建议"""
        try:
            recommendations = []
            
            # 基于风险事件的建议
            risk_events = base_data["risk_events"]
            critical_events = [e for e in risk_events if e.severity == "critical"]
            
            if len(critical_events) > 5:
                recommendations.append({
                    "category": "风险控制",
                    "priority": "高",
                    "title": "加强风险控制措施",
                    "description": f"检测到{len(critical_events)}个严重风险事件，建议检查并加强风险控制规则",
                    "action_items": [
                        "审查现有风险规则的有效性",
                        "考虑降低风险阈值",
                        "增加实时监控频率"
                    ]
                })
            
            # 基于持仓集中度的建议
            position_analysis = await self._analyze_position_risk(base_data)
            if position_analysis.get("top_5_concentration", 0) > 0.5:
                recommendations.append({
                    "category": "投资组合",
                    "priority": "中",
                    "title": "降低持仓集中度",
                    "description": f"前5大持仓占比{position_analysis['top_5_concentration']:.1%}，建议分散投资",
                    "action_items": [
                        "考虑减少大额持仓",
                        "增加投资标的多样性",
                        "设置单一持仓限额"
                    ]
                })
            
            # 基于风险指标的建议
            risk_metrics = base_data["risk_metrics"]
            if risk_metrics:
                latest_metrics = risk_metrics[-1]
                if latest_metrics.max_drawdown and float(latest_metrics.max_drawdown) > 0.1:
                    recommendations.append({
                        "category": "风险管理",
                        "priority": "高",
                        "title": "控制回撤风险",
                        "description": f"最大回撤达到{float(latest_metrics.max_drawdown):.1%}，需要加强风险控制",
                        "action_items": [
                            "设置止损规则",
                            "降低杠杆比例",
                            "增加对冲策略"
                        ]
                    })
            
            # 基于趋势分析的建议
            trend_analysis = await self._analyze_risk_trends(base_data)
            if trend_analysis.get("metric_trends", {}).get("volatility", {}).get("direction") == "上升":
                recommendations.append({
                    "category": "市场风险",
                    "priority": "中",
                    "title": "应对波动率上升",
                    "description": "检测到波动率上升趋势，建议调整投资策略",
                    "action_items": [
                        "减少高波动性资产配置",
                        "增加现金或低风险资产比例",
                        "考虑使用波动率对冲工具"
                    ]
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"生成改进建议失败: {str(e)}")
            return []    

    async def _generate_charts_data(self, base_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成图表数据"""
        try:
            risk_metrics = base_data["risk_metrics"]
            risk_events = base_data["risk_events"]
            positions = base_data["positions"]
            
            charts_data = {}
            
            # 风险指标时间序列图表
            if risk_metrics:
                dates = [m.date.strftime("%Y-%m-%d") for m in risk_metrics]
                charts_data["risk_metrics_timeline"] = {
                    "dates": dates,
                    "var_95": [float(m.var_95) if m.var_95 else 0 for m in risk_metrics],
                    "volatility": [float(m.volatility) if m.volatility else 0 for m in risk_metrics],
                    "max_drawdown": [float(m.max_drawdown) if m.max_drawdown else 0 for m in risk_metrics],
                    "portfolio_value": [float(m.portfolio_value) if m.portfolio_value else 0 for m in risk_metrics]
                }
            
            # 风险事件分布饼图
            if risk_events:
                severity_counts = {}
                for event in risk_events:
                    severity = event.severity
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                charts_data["risk_events_distribution"] = {
                    "labels": list(severity_counts.keys()),
                    "values": list(severity_counts.values())
                }
            
            # 持仓集中度图表
            if positions:
                position_data = []
                for pos in positions:
                    if pos.quantity != 0 and pos.current_price:
                        market_value = abs(pos.quantity * pos.current_price)
                        position_data.append({
                            "symbol": pos.symbol,
                            "value": market_value
                        })
                
                position_data.sort(key=lambda x: x["value"], reverse=True)
                top_10 = position_data[:10]
                
                charts_data["position_concentration"] = {
                    "symbols": [p["symbol"] for p in top_10],
                    "values": [p["value"] for p in top_10]
                }
            
            return charts_data
            
        except Exception as e:
            logger.error(f"生成图表数据失败: {str(e)}")
            return {}
    
    async def _calculate_risk_score(self, base_data: Dict[str, Any]) -> float:
        """计算风险评分"""
        try:
            score = 0.0
            
            # 基于风险事件的评分
            risk_events = base_data["risk_events"]
            critical_events = len([e for e in risk_events if e.severity == "critical"])
            high_events = len([e for e in risk_events if e.severity == "high"])
            
            event_score = min(100, critical_events * 20 + high_events * 10)
            score += event_score * 0.3
            
            # 基于风险指标的评分
            risk_metrics = base_data["risk_metrics"]
            if risk_metrics:
                latest = risk_metrics[-1]
                
                # VaR评分
                var_score = min(100, float(latest.var_95) / 1000 * 100) if latest.var_95 else 0
                score += var_score * 0.25
                
                # 波动率评分
                vol_score = min(100, float(latest.volatility) * 1000) if latest.volatility else 0
                score += vol_score * 0.2
                
                # 回撤评分
                dd_score = min(100, float(latest.max_drawdown) * 500) if latest.max_drawdown else 0
                score += dd_score * 0.25
            
            return min(100, score)
            
        except Exception as e:
            logger.error(f"计算风险评分失败: {str(e)}")
            return 0.0
    
    def _get_risk_level(self, risk_score: float) -> str:
        """根据风险评分获取风险等级"""
        if risk_score >= 80:
            return "极高"
        elif risk_score >= 60:
            return "高"
        elif risk_score >= 40:
            return "中"
        elif risk_score >= 20:
            return "低"
        else:
            return "极低"
    
    async def _extract_key_findings(self, base_data: Dict[str, Any]) -> List[str]:
        """提取关键发现"""
        findings = []
        
        try:
            # 分析风险事件
            risk_events = base_data["risk_events"]
            if len(risk_events) > 10:
                findings.append(f"报告期内发生{len(risk_events)}个风险事件，需要关注")
            
            # 分析持仓集中度
            positions = base_data["positions"]
            if positions:
                active_positions = [p for p in positions if p.quantity != 0]
                if len(active_positions) < 5:
                    findings.append("持仓过于集中，建议增加投资多样性")
            
            # 分析风险指标趋势
            risk_metrics = base_data["risk_metrics"]
            if len(risk_metrics) >= 5:
                recent_var = [float(m.var_95) for m in risk_metrics[-5:] if m.var_95]
                earlier_var = [float(m.var_95) for m in risk_metrics[:5] if m.var_95]
                
                if recent_var and earlier_var and np.mean(recent_var) > np.mean(earlier_var) * 1.2:
                    findings.append("VaR指标呈上升趋势，风险水平增加")
            
            return findings
            
        except Exception as e:
            logger.error(f"提取关键发现失败: {str(e)}")
            return []
    
    def _get_sector_by_symbol(self, symbol: str) -> str:
        """根据标的代码获取行业分类（简化实现）"""
        # 这里应该从市场数据服务获取真实的行业分类
        tech_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        finance_symbols = ["JPM", "BAC", "WFC", "GS", "MS"]
        
        if symbol in tech_symbols:
            return "科技"
        elif symbol in finance_symbols:
            return "金融"
        else:
            return "其他"
    
    def _calculate_position_var(self, position) -> float:
        """计算单个持仓的VaR（简化实现）"""
        if not position.current_price or position.quantity == 0:
            return 0.0
        
        market_value = abs(position.quantity * position.current_price)
        # 简化的VaR计算，实际应该基于历史波动率
        volatility = 0.02  # 假设2%的日波动率
        confidence_level = 1.645  # 95%置信度
        
        return market_value * volatility * confidence_level
    
    def _get_correlation_with_portfolio(self, position) -> float:
        """获取与组合的相关性（简化实现）"""
        # 这里应该基于历史数据计算真实相关性
        return 0.7  # 假设70%的相关性
    
    def _calculate_concentration_risk(self, positions) -> float:
        """计算集中度风险"""
        if not positions:
            return 0.0
        
        total_value = sum(abs(p.quantity * p.current_price) for p in positions if p.current_price and p.quantity != 0)
        if total_value == 0:
            return 0.0
        
        # 计算赫芬达尔指数
        hhi = sum((abs(p.quantity * p.current_price) / total_value) ** 2 for p in positions if p.current_price and p.quantity != 0)
        return hhi
    
    def _calculate_correlation_risk(self, positions) -> float:
        """计算相关性风险（简化实现）"""
        # 这里应该基于历史数据计算持仓间的相关性
        return 0.5  # 假设50%的平均相关性
    
    def _analyze_event_frequency_trend(self, risk_events) -> Dict[str, Any]:
        """分析事件频率趋势"""
        if len(risk_events) < 10:
            return {"trend": "数据不足", "frequency": 0}
        
        # 按日期分组
        daily_counts = {}
        for event in risk_events:
            date_str = event.created_at.date().strftime("%Y-%m-%d")
            daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
        
        # 计算趋势
        dates = sorted(daily_counts.keys())
        if len(dates) >= 7:
            recent_avg = np.mean([daily_counts.get(d, 0) for d in dates[-7:]])
            earlier_avg = np.mean([daily_counts.get(d, 0) for d in dates[:7]])
            
            trend = "上升" if recent_avg > earlier_avg else "下降"
            return {
                "trend": trend,
                "recent_frequency": recent_avg,
                "earlier_frequency": earlier_avg,
                "change_rate": (recent_avg - earlier_avg) / earlier_avg if earlier_avg > 0 else 0
            }
        
        return {"trend": "稳定", "frequency": len(risk_events) / len(dates) if dates else 0}
    
    def _forecast_risk_levels(self, df) -> Dict[str, Any]:
        """预测未来风险水平（简化实现）"""
        if len(df) < 5:
            return {"forecast": "数据不足"}
        
        # 简单的线性趋势预测
        recent_var = df["var_95"].tail(5).mean()
        earlier_var = df["var_95"].head(5).mean()
        
        trend_rate = (recent_var - earlier_var) / len(df) if len(df) > 0 else 0
        
        # 预测未来7天的VaR
        forecast_days = 7
        forecasted_var = recent_var + trend_rate * forecast_days
        
        return {
            "forecast_period": f"{forecast_days}天",
            "current_var": recent_var,
            "forecasted_var": forecasted_var,
            "trend_direction": "上升" if trend_rate > 0 else "下降",
            "confidence": "低"  # 简化模型的置信度较低
        }
    
    def _summarize_trends(self, trends) -> str:
        """总结趋势"""
        if not trends:
            return "无足够数据进行趋势分析"
        
        rising_metrics = [k for k, v in trends.items() if v.get("direction") == "上升"]
        falling_metrics = [k for k, v in trends.items() if v.get("direction") == "下降"]
        
        if len(rising_metrics) > len(falling_metrics):
            return f"风险指标整体呈上升趋势，主要体现在{', '.join(rising_metrics)}"
        elif len(falling_metrics) > len(rising_metrics):
            return f"风险指标整体呈下降趋势，主要体现在{', '.join(falling_metrics)}"
        else:
            return "风险指标趋势混合，需要持续关注"
    
    async def _save_report(self, report: Dict[str, Any]) -> None:
        """保存报告"""
        try:
            # 这里可以将报告保存到数据库或文件系统
            logger.info(f"保存风险报告: {report['report_id']}")
            # 实际实现中应该保存到数据库
        except Exception as e:
            logger.error(f"保存报告失败: {str(e)}")
    
    async def schedule_periodic_reports(self) -> None:
        """调度定期报告"""
        try:
            # 获取需要生成报告的用户
            users = self.db.query(User).filter(User.is_active == True).all()
            
            for user in users:
                # 生成日报
                end_date = datetime.now()
                start_date = end_date - timedelta(days=1)
                
                daily_report = await self.generate_risk_report(
                    user.id, ReportType.DAILY, start_date, end_date
                )
                
                # 发送报告通知
                await self._send_report_notification(user.id, daily_report)
                
        except Exception as e:
            logger.error(f"调度定期报告失败: {str(e)}")
    
    async def _send_report_notification(self, user_id: int, report: Dict[str, Any]) -> None:
        """发送报告通知"""
        try:
            await self.notification_service.send_notification(
                user_id=user_id,
                title=f"风险报告 - {report['report_type']}",
                content=f"您的{report['report_type']}风险报告已生成，风险评分：{report['executive_summary']['risk_score']:.1f}",
                notification_type="risk_report",
                priority="medium"
            )
        except Exception as e:
            logger.error(f"发送报告通知失败: {str(e)}")