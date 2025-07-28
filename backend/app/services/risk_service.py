"""
风险管理服务
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging

from ..models import Order, Position, Account, Strategy, User
from ..models.enums import OrderDirection, OrderOffset, OrderStatus
from ..core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class RiskService:
    """风险管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # 默认风险参数
        self.default_risk_params = {
            'max_position_ratio': 0.3,  # 单个品种最大持仓比例
            'max_daily_loss': 0.05,     # 日最大亏损比例
            'max_order_value': 1000000, # 单笔订单最大金额
            'max_orders_per_minute': 10, # 每分钟最大订单数
            'min_account_balance': 10000, # 最小账户余额
        }
    
    def check_order_risk(self, order_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """检查订单风险"""
        try:
            risk_result = {
                'passed': True,
                'reason': '',
                'warnings': [],
                'checks': {}
            }
            
            # 1. 检查账户资金
            account_check = self._check_account_balance(order_data, user_id)
            risk_result['checks']['account_balance'] = account_check
            if not account_check['passed']:
                risk_result['passed'] = False
                risk_result['reason'] = account_check['reason']
                return risk_result
            
            # 2. 检查持仓比例
            position_check = self._check_position_ratio(order_data, user_id)
            risk_result['checks']['position_ratio'] = position_check
            if not position_check['passed']:
                risk_result['passed'] = False
                risk_result['reason'] = position_check['reason']
                return risk_result
            
            # 3. 检查订单金额
            order_value_check = self._check_order_value(order_data)
            risk_result['checks']['order_value'] = order_value_check
            if not order_value_check['passed']:
                risk_result['passed'] = False
                risk_result['reason'] = order_value_check['reason']
                return risk_result
            
            # 4. 检查交易频率
            frequency_check = self._check_trading_frequency(order_data, user_id)
            risk_result['checks']['trading_frequency'] = frequency_check
            if not frequency_check['passed']:
                risk_result['passed'] = False
                risk_result['reason'] = frequency_check['reason']
                return risk_result
            
            # 5. 检查日亏损限制
            daily_loss_check = self._check_daily_loss_limit(order_data, user_id)
            risk_result['checks']['daily_loss'] = daily_loss_check
            if not daily_loss_check['passed']:
                risk_result['warnings'].append(daily_loss_check['reason'])
            
            return risk_result
            
        except Exception as e:
            logger.error(f"风险检查失败: {e}")
            return {
                'passed': False,
                'reason': f'风险检查系统错误: {str(e)}',
                'warnings': [],
                'checks': {}
            }
    
    def _check_account_balance(self, order_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """检查账户余额"""
        try:
            # 获取用户账户信息
            account = self.db.query(Account).filter(Account.user_id == user_id).first()
            
            if not account:
                return {
                    'passed': False,
                    'reason': '未找到账户信息'
                }
            
            # 计算订单所需资金
            order_value = order_data['volume'] * order_data['price']
            margin_required = order_value * 0.1  # 假设保证金率10%
            
            # 检查可用资金
            if account.available < margin_required:
                return {
                    'passed': False,
                    'reason': f'可用资金不足，需要 {margin_required:.2f}，可用 {account.available:.2f}'
                }
            
            # 检查最小余额
            if account.balance < self.default_risk_params['min_account_balance']:
                return {
                    'passed': False,
                    'reason': f'账户余额低于最小要求 {self.default_risk_params["min_account_balance"]}'
                }
            
            return {
                'passed': True,
                'reason': '账户资金检查通过',
                'available_balance': account.available,
                'required_margin': margin_required
            }
            
        except Exception as e:
            logger.error(f"账户余额检查失败: {e}")
            return {
                'passed': False,
                'reason': f'账户检查错误: {str(e)}'
            }
    
    def _check_position_ratio(self, order_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """检查持仓比例"""
        try:
            symbol = order_data['symbol']
            strategy_id = order_data['strategy_id']
            
            # 获取当前持仓
            current_position = self.db.query(Position).filter(
                and_(
                    Position.strategy_id == strategy_id,
                    Position.symbol == symbol
                )
            ).first()
            
            # 获取账户总价值
            account = self.db.query(Account).filter(Account.user_id == user_id).first()
            if not account:
                return {
                    'passed': False,
                    'reason': '未找到账户信息'
                }
            
            total_value = account.balance + account.unrealized_pnl
            
            # 计算新订单后的持仓价值
            order_value = order_data['volume'] * order_data['price']
            current_position_value = 0
            
            if current_position:
                current_position_value = current_position.volume * order_data['price']
            
            # 根据订单类型计算新的持仓价值
            if order_data['offset'] == OrderOffset.OPEN:
                new_position_value = current_position_value + order_value
            else:
                new_position_value = max(0, current_position_value - order_value)
            
            # 检查持仓比例
            position_ratio = new_position_value / total_value if total_value > 0 else 0
            max_ratio = self.default_risk_params['max_position_ratio']
            
            if position_ratio > max_ratio:
                return {
                    'passed': False,
                    'reason': f'持仓比例超限，当前 {position_ratio:.2%}，最大允许 {max_ratio:.2%}'
                }
            
            return {
                'passed': True,
                'reason': '持仓比例检查通过',
                'current_ratio': position_ratio,
                'max_ratio': max_ratio
            }
            
        except Exception as e:
            logger.error(f"持仓比例检查失败: {e}")
            return {
                'passed': False,
                'reason': f'持仓检查错误: {str(e)}'
            }
    
    def _check_order_value(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查订单金额"""
        try:
            order_value = order_data['volume'] * order_data['price']
            max_value = self.default_risk_params['max_order_value']
            
            if order_value > max_value:
                return {
                    'passed': False,
                    'reason': f'订单金额超限，当前 {order_value:.2f}，最大允许 {max_value:.2f}'
                }
            
            return {
                'passed': True,
                'reason': '订单金额检查通过',
                'order_value': order_value,
                'max_value': max_value
            }
            
        except Exception as e:
            logger.error(f"订单金额检查失败: {e}")
            return {
                'passed': False,
                'reason': f'订单金额检查错误: {str(e)}'
            }
    
    def _check_trading_frequency(self, order_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """检查交易频率"""
        try:
            strategy_id = order_data['strategy_id']
            
            # 检查最近1分钟的订单数量
            one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
            
            recent_orders_count = self.db.query(Order).join(Strategy).filter(
                and_(
                    Strategy.user_id == user_id,
                    Order.strategy_id == strategy_id,
                    Order.created_at >= one_minute_ago
                )
            ).count()
            
            max_orders = self.default_risk_params['max_orders_per_minute']
            
            if recent_orders_count >= max_orders:
                return {
                    'passed': False,
                    'reason': f'交易频率过高，1分钟内已下单 {recent_orders_count} 次，最大允许 {max_orders} 次'
                }
            
            return {
                'passed': True,
                'reason': '交易频率检查通过',
                'recent_orders': recent_orders_count,
                'max_orders': max_orders
            }
            
        except Exception as e:
            logger.error(f"交易频率检查失败: {e}")
            return {
                'passed': False,
                'reason': f'交易频率检查错误: {str(e)}'
            }
    
    def _check_daily_loss_limit(self, order_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """检查日亏损限制"""
        try:
            # 获取今日已实现盈亏
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            account = self.db.query(Account).filter(Account.user_id == user_id).first()
            if not account:
                return {
                    'passed': False,
                    'reason': '未找到账户信息'
                }
            
            # 计算今日盈亏（简化计算）
            today_pnl = account.realized_pnl  # 这里应该是今日的实现盈亏
            
            # 检查是否超过日亏损限制
            max_daily_loss = account.balance * self.default_risk_params['max_daily_loss']
            
            if today_pnl < -max_daily_loss:
                return {
                    'passed': False,
                    'reason': f'今日亏损已达限制，当前亏损 {abs(today_pnl):.2f}，限制 {max_daily_loss:.2f}'
                }
            
            return {
                'passed': True,
                'reason': '日亏损检查通过',
                'today_pnl': today_pnl,
                'max_loss': max_daily_loss
            }
            
        except Exception as e:
            logger.error(f"日亏损检查失败: {e}")
            return {
                'passed': True,  # 检查失败时不阻止交易，只记录警告
                'reason': f'日亏损检查错误: {str(e)}'
            }
    
    def get_risk_summary(self, user_id: int) -> Dict[str, Any]:
        """获取风险摘要"""
        try:
            account = self.db.query(Account).filter(Account.user_id == user_id).first()
            if not account:
                return {'error': '未找到账户信息'}
            
            # 计算各项风险指标
            total_value = account.balance + account.unrealized_pnl
            
            # 持仓风险
            positions = self.db.query(Position).join(Strategy).filter(
                Strategy.user_id == user_id
            ).all()
            
            position_risks = []
            total_position_value = 0
            
            for position in positions:
                position_value = position.volume * position.avg_price  # 简化计算
                position_ratio = position_value / total_value if total_value > 0 else 0
                total_position_value += position_value
                
                position_risks.append({
                    'symbol': position.symbol,
                    'value': position_value,
                    'ratio': position_ratio,
                    'risk_level': 'high' if position_ratio > 0.2 else 'medium' if position_ratio > 0.1 else 'low'
                })
            
            # 整体风险度
            overall_risk_ratio = total_position_value / total_value if total_value > 0 else 0
            
            # 资金使用率
            fund_usage_ratio = account.margin / account.balance if account.balance > 0 else 0
            
            return {
                'account_balance': account.balance,
                'available_funds': account.available,
                'total_value': total_value,
                'margin_used': account.margin,
                'fund_usage_ratio': fund_usage_ratio,
                'overall_risk_ratio': overall_risk_ratio,
                'position_risks': position_risks,
                'risk_level': self._calculate_risk_level(overall_risk_ratio, fund_usage_ratio),
                'daily_pnl': account.realized_pnl + account.unrealized_pnl,
                'risk_warnings': self._generate_risk_warnings(account, overall_risk_ratio, fund_usage_ratio)
            }
            
        except Exception as e:
            logger.error(f"获取风险摘要失败: {e}")
            return {'error': f'风险摘要计算错误: {str(e)}'}
    
    def _calculate_risk_level(self, position_ratio: float, fund_usage_ratio: float) -> str:
        """计算风险等级"""
        if position_ratio > 0.5 or fund_usage_ratio > 0.8:
            return 'high'
        elif position_ratio > 0.3 or fund_usage_ratio > 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _generate_risk_warnings(self, account: Account, position_ratio: float, fund_usage_ratio: float) -> List[str]:
        """生成风险警告"""
        warnings = []
        
        if position_ratio > 0.4:
            warnings.append(f"持仓比例过高 ({position_ratio:.1%})，建议降低仓位")
        
        if fund_usage_ratio > 0.7:
            warnings.append(f"资金使用率过高 ({fund_usage_ratio:.1%})，建议增加保证金")
        
        if account.available < account.balance * 0.2:
            warnings.append("可用资金不足，建议减少持仓或增加资金")
        
        if account.unrealized_pnl < -account.balance * 0.1:
            warnings.append("未实现亏损较大，建议检查持仓风险")
        
        return warnings
    
    def update_risk_parameters(self, user_id: int, risk_params: Dict[str, Any]) -> Dict[str, Any]:
        """更新风险参数"""
        try:
            # 这里应该将风险参数存储到数据库中
            # 为简化，暂时只更新内存中的参数
            
            allowed_params = [
                'max_position_ratio', 'max_daily_loss', 'max_order_value',
                'max_orders_per_minute', 'min_account_balance'
            ]
            
            updated_params = {}
            for param, value in risk_params.items():
                if param in allowed_params:
                    self.default_risk_params[param] = value
                    updated_params[param] = value
            
            logger.info(f"用户 {user_id} 风险参数更新: {updated_params}")
            
            return {
                'success': True,
                'updated_params': updated_params,
                'current_params': self.default_risk_params
            }
            
        except Exception as e:
            logger.error(f"更新风险参数失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }