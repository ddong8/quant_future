"""
回测配置管理服务
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime, timedelta
import json
import uuid

from ..models.backtest import BacktestTemplate, BacktestType
from ..models.user import User
from ..schemas.backtest import BacktestTemplateCreate, BacktestTemplateUpdate
from ..core.exceptions import ValidationError, NotFoundError, PermissionError

logger = logging.getLogger(__name__)


class BacktestConfigService:
    """回测配置管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_config_template(self, template_data: BacktestTemplateCreate, user_id: int) -> BacktestTemplate:
        """创建回测配置模板"""
        try:
            # 验证配置模板
            self._validate_config_template(template_data.config_template)
            
            template = BacktestTemplate(
                uuid=str(uuid.uuid4()),
                name=template_data.name,
                description=template_data.description,
                category=template_data.category,
                config_template=template_data.config_template,
                default_parameters=template_data.default_parameters,
                tags=template_data.tags,
                author_id=user_id
            )
            
            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)
            
            logger.info(f"创建回测配置模板成功: {template.id} - {template.name}")
            return template
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建回测配置模板失败: {str(e)}")
            raise
    
    def get_config_template(self, template_id: int, user_id: Optional[int] = None) -> BacktestTemplate:
        """获取回测配置模板"""
        query = self.db.query(BacktestTemplate).filter(
            BacktestTemplate.id == template_id,
            BacktestTemplate.is_active == True
        )
        
        # 如果指定用户ID，则只返回该用户的模板或公开模板
        if user_id:
            query = query.filter(
                or_(
                    BacktestTemplate.author_id == user_id,
                    BacktestTemplate.is_official == True
                )
            )
        
        template = query.first()
        if not template:
            raise NotFoundError("回测配置模板不存在")
        
        # 增加使用次数
        template.usage_count += 1
        self.db.commit()
        
        return template
    
    def update_config_template(self, template_id: int, template_data: BacktestTemplateUpdate, user_id: int) -> BacktestTemplate:
        """更新回测配置模板"""
        try:
            template = self.db.query(BacktestTemplate).filter(
                BacktestTemplate.id == template_id,
                BacktestTemplate.author_id == user_id,
                BacktestTemplate.is_active == True
            ).first()
            
            if not template:
                raise NotFoundError("回测配置模板不存在或无权限修改")
            
            # 更新字段
            update_data = template_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field == 'config_template' and value:
                    self._validate_config_template(value)
                setattr(template, field, value)
            
            self.db.commit()
            self.db.refresh(template)
            
            logger.info(f"更新回测配置模板成功: {template.id}")
            return template
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新回测配置模板失败: {str(e)}")
            raise
    
    def delete_config_template(self, template_id: int, user_id: int) -> bool:
        """删除回测配置模板"""
        try:
            template = self.db.query(BacktestTemplate).filter(
                BacktestTemplate.id == template_id,
                BacktestTemplate.author_id == user_id
            ).first()
            
            if not template:
                raise NotFoundError("回测配置模板不存在或无权限删除")
            
            # 软删除
            template.is_active = False
            self.db.commit()
            
            logger.info(f"删除回测配置模板成功: {template_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除回测配置模板失败: {str(e)}")
            raise
    
    def list_config_templates(self, 
                            category: Optional[str] = None,
                            is_official: Optional[bool] = None,
                            user_id: Optional[int] = None,
                            page: int = 1,
                            page_size: int = 20) -> tuple[List[BacktestTemplate], int]:
        """获取回测配置模板列表"""
        query = self.db.query(BacktestTemplate).filter(
            BacktestTemplate.is_active == True
        )
        
        # 分类筛选
        if category:
            query = query.filter(BacktestTemplate.category == category)
        
        # 官方模板筛选
        if is_official is not None:
            query = query.filter(BacktestTemplate.is_official == is_official)
        
        # 用户筛选
        if user_id:
            query = query.filter(
                or_(
                    BacktestTemplate.author_id == user_id,
                    BacktestTemplate.is_official == True
                )
            )
        
        # 获取总数
        total = query.count()
        
        # 分页和排序
        templates = query.order_by(desc(BacktestTemplate.usage_count)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return templates, total
    
    def get_default_config(self, backtest_type: BacktestType = BacktestType.SIMPLE) -> Dict[str, Any]:
        """获取默认回测配置"""
        default_configs = {
            BacktestType.SIMPLE: {
                "basic_settings": {
                    "initial_capital": 100000,
                    "benchmark": "000300.SH",
                    "frequency": "1d"
                },
                "trading_settings": {
                    "commission_rate": 0.001,
                    "slippage_rate": 0.001,
                    "min_commission": 5.0
                },
                "risk_settings": {
                    "max_position_size": 1.0,
                    "stop_loss": None,
                    "take_profit": None
                },
                "data_settings": {
                    "data_source": "default",
                    "symbols": [],
                    "start_date": (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                    "end_date": datetime.now().strftime("%Y-%m-%d")
                }
            },
            BacktestType.WALK_FORWARD: {
                "basic_settings": {
                    "initial_capital": 100000,
                    "benchmark": "000300.SH",
                    "frequency": "1d"
                },
                "trading_settings": {
                    "commission_rate": 0.001,
                    "slippage_rate": 0.001,
                    "min_commission": 5.0
                },
                "risk_settings": {
                    "max_position_size": 1.0,
                    "stop_loss": None,
                    "take_profit": None
                },
                "data_settings": {
                    "data_source": "default",
                    "symbols": [],
                    "start_date": (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d"),
                    "end_date": datetime.now().strftime("%Y-%m-%d")
                },
                "walk_forward_settings": {
                    "training_period": 252,  # 训练期（天）
                    "testing_period": 63,    # 测试期（天）
                    "step_size": 21          # 步长（天）
                }
            },
            BacktestType.MONTE_CARLO: {
                "basic_settings": {
                    "initial_capital": 100000,
                    "benchmark": "000300.SH",
                    "frequency": "1d"
                },
                "trading_settings": {
                    "commission_rate": 0.001,
                    "slippage_rate": 0.001,
                    "min_commission": 5.0
                },
                "risk_settings": {
                    "max_position_size": 1.0,
                    "stop_loss": None,
                    "take_profit": None
                },
                "data_settings": {
                    "data_source": "default",
                    "symbols": [],
                    "start_date": (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                    "end_date": datetime.now().strftime("%Y-%m-%d")
                },
                "monte_carlo_settings": {
                    "simulation_count": 1000,  # 模拟次数
                    "confidence_level": 0.95,  # 置信水平
                    "random_seed": 42          # 随机种子
                }
            }
        }
        
        return default_configs.get(backtest_type, default_configs[BacktestType.SIMPLE])
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证回测配置"""
        errors = []
        
        try:
            # 验证基础设置
            if 'basic_settings' in config:
                basic = config['basic_settings']
                
                # 验证初始资金
                if 'initial_capital' in basic:
                    if not isinstance(basic['initial_capital'], (int, float)) or basic['initial_capital'] <= 0:
                        errors.append("初始资金必须为正数")
                
                # 验证频率
                if 'frequency' in basic:
                    allowed_frequencies = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M']
                    if basic['frequency'] not in allowed_frequencies:
                        errors.append(f"数据频率必须是: {', '.join(allowed_frequencies)}")
            
            # 验证交易设置
            if 'trading_settings' in config:
                trading = config['trading_settings']
                
                # 验证手续费率
                if 'commission_rate' in trading:
                    if not isinstance(trading['commission_rate'], (int, float)) or trading['commission_rate'] < 0:
                        errors.append("手续费率必须为非负数")
                
                # 验证滑点率
                if 'slippage_rate' in trading:
                    if not isinstance(trading['slippage_rate'], (int, float)) or trading['slippage_rate'] < 0:
                        errors.append("滑点率必须为非负数")
            
            # 验证风险设置
            if 'risk_settings' in config:
                risk = config['risk_settings']
                
                # 验证最大持仓比例
                if 'max_position_size' in risk and risk['max_position_size'] is not None:
                    if not isinstance(risk['max_position_size'], (int, float)) or risk['max_position_size'] <= 0 or risk['max_position_size'] > 1:
                        errors.append("最大持仓比例必须在0-1之间")
            
            # 验证数据设置
            if 'data_settings' in config:
                data = config['data_settings']
                
                # 验证日期
                if 'start_date' in data and 'end_date' in data:
                    try:
                        start_date = datetime.strptime(data['start_date'], "%Y-%m-%d")
                        end_date = datetime.strptime(data['end_date'], "%Y-%m-%d")
                        if start_date >= end_date:
                            errors.append("开始日期必须早于结束日期")
                    except ValueError:
                        errors.append("日期格式必须为YYYY-MM-DD")
                
                # 验证交易标的
                if 'symbols' in data:
                    if not isinstance(data['symbols'], list) or len(data['symbols']) == 0:
                        errors.append("至少需要选择一个交易标的")
            
        except Exception as e:
            errors.append(f"配置验证失败: {str(e)}")
        
        return len(errors) == 0, errors
    
    def save_user_config(self, user_id: int, config_name: str, config: Dict[str, Any], description: str = "") -> Dict[str, Any]:
        """保存用户自定义配置"""
        try:
            # 验证配置
            is_valid, errors = self.validate_config(config)
            if not is_valid:
                raise ValidationError(f"配置验证失败: {'; '.join(errors)}")
            
            # 创建配置模板
            template_data = BacktestTemplateCreate(
                name=config_name,
                description=description,
                category="user_custom",
                config_template=config,
                default_parameters={},
                tags=["用户自定义"]
            )
            
            template = self.create_config_template(template_data, user_id)
            
            return {
                "id": template.id,
                "uuid": template.uuid,
                "name": template.name,
                "description": template.description,
                "config": template.config_template,
                "created_at": template.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"保存用户配置失败: {str(e)}")
            raise
    
    def get_user_configs(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户自定义配置列表"""
        templates = self.db.query(BacktestTemplate).filter(
            BacktestTemplate.author_id == user_id,
            BacktestTemplate.is_active == True
        ).order_by(desc(BacktestTemplate.created_at)).all()
        
        return [
            {
                "id": template.id,
                "uuid": template.uuid,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "config": template.config_template,
                "usage_count": template.usage_count,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat()
            }
            for template in templates
        ]
    
    def get_popular_configs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门配置模板"""
        templates = self.db.query(BacktestTemplate).filter(
            BacktestTemplate.is_active == True,
            BacktestTemplate.is_official == True
        ).order_by(desc(BacktestTemplate.usage_count)).limit(limit).all()
        
        return [
            {
                "id": template.id,
                "uuid": template.uuid,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "usage_count": template.usage_count,
                "rating": template.rating
            }
            for template in templates
        ]
    
    def _validate_config_template(self, config_template: Dict[str, Any]):
        """验证配置模板格式"""
        required_sections = ['basic_settings', 'trading_settings', 'data_settings']
        
        for section in required_sections:
            if section not in config_template:
                raise ValidationError(f"配置模板缺少必需部分: {section}")
        
        # 验证配置内容
        is_valid, errors = self.validate_config(config_template)
        if not is_valid:
            raise ValidationError(f"配置模板验证失败: {'; '.join(errors)}")
    
    def get_config_categories(self) -> List[Dict[str, Any]]:
        """获取配置分类列表"""
        categories = [
            {
                "key": "trend_following",
                "name": "趋势跟踪",
                "description": "适用于趋势跟踪策略的回测配置",
                "icon": "trend-up"
            },
            {
                "key": "mean_reversion",
                "name": "均值回归",
                "description": "适用于均值回归策略的回测配置",
                "icon": "trending-flat"
            },
            {
                "key": "arbitrage",
                "name": "套利策略",
                "description": "适用于套利策略的回测配置",
                "icon": "swap-horizontal"
            },
            {
                "key": "market_making",
                "name": "做市策略",
                "description": "适用于做市策略的回测配置",
                "icon": "layers"
            },
            {
                "key": "momentum",
                "name": "动量策略",
                "description": "适用于动量策略的回测配置",
                "icon": "rocket"
            },
            {
                "key": "statistical",
                "name": "统计套利",
                "description": "适用于统计套利策略的回测配置",
                "icon": "bar-chart"
            },
            {
                "key": "user_custom",
                "name": "用户自定义",
                "description": "用户自定义的回测配置",
                "icon": "settings"
            }
        ]
        
        return categories
    
    def create_preset_templates(self):
        """创建预设配置模板"""
        preset_templates = [
            {
                "name": "股票日线回测",
                "description": "适用于股票日线数据的标准回测配置",
                "category": "trend_following",
                "config_template": {
                    "basic_settings": {
                        "initial_capital": 100000,
                        "benchmark": "000300.SH",
                        "frequency": "1d"
                    },
                    "trading_settings": {
                        "commission_rate": 0.0003,
                        "slippage_rate": 0.001,
                        "min_commission": 5.0
                    },
                    "risk_settings": {
                        "max_position_size": 0.2,
                        "stop_loss": 0.1,
                        "take_profit": 0.2
                    },
                    "data_settings": {
                        "data_source": "default",
                        "symbols": [],
                        "start_date": "2020-01-01",
                        "end_date": "2023-12-31"
                    }
                },
                "is_official": True
            },
            {
                "name": "期货高频回测",
                "description": "适用于期货高频交易的回测配置",
                "category": "momentum",
                "config_template": {
                    "basic_settings": {
                        "initial_capital": 500000,
                        "benchmark": "IF00.CFX",
                        "frequency": "1m"
                    },
                    "trading_settings": {
                        "commission_rate": 0.00005,
                        "slippage_rate": 0.0005,
                        "min_commission": 2.0
                    },
                    "risk_settings": {
                        "max_position_size": 0.5,
                        "stop_loss": 0.02,
                        "take_profit": 0.03
                    },
                    "data_settings": {
                        "data_source": "futures",
                        "symbols": [],
                        "start_date": "2023-01-01",
                        "end_date": "2023-12-31"
                    }
                },
                "is_official": True
            },
            {
                "name": "加密货币回测",
                "description": "适用于加密货币交易的回测配置",
                "category": "momentum",
                "config_template": {
                    "basic_settings": {
                        "initial_capital": 10000,
                        "benchmark": "BTC-USDT",
                        "frequency": "1h"
                    },
                    "trading_settings": {
                        "commission_rate": 0.001,
                        "slippage_rate": 0.002,
                        "min_commission": 0.1
                    },
                    "risk_settings": {
                        "max_position_size": 0.3,
                        "stop_loss": 0.05,
                        "take_profit": 0.1
                    },
                    "data_settings": {
                        "data_source": "crypto",
                        "symbols": [],
                        "start_date": "2023-01-01",
                        "end_date": "2023-12-31"
                    }
                },
                "is_official": True
            }
        ]
        
        try:
            for template_data in preset_templates:
                # 检查是否已存在
                existing = self.db.query(BacktestTemplate).filter(
                    BacktestTemplate.name == template_data["name"],
                    BacktestTemplate.is_official == True
                ).first()
                
                if not existing:
                    template = BacktestTemplate(
                        uuid=str(uuid.uuid4()),
                        name=template_data["name"],
                        description=template_data["description"],
                        category=template_data["category"],
                        config_template=template_data["config_template"],
                        default_parameters={},
                        tags=["官方", "预设"],
                        is_official=True,
                        author_id=None
                    )
                    
                    self.db.add(template)
            
            self.db.commit()
            logger.info("预设配置模板创建完成")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建预设配置模板失败: {str(e)}")
            raise