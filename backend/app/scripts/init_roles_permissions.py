"""
初始化系统角色和权限脚本
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.role import Role, Permission, PermissionConstants, RoleConstants
from app.models.user import User
from app.services.role_service import RoleService

def init_permissions(db: Session):
    """初始化系统权限"""
    permissions_data = [
        # 用户管理权限
        {
            'name': PermissionConstants.USER_VIEW,
            'display_name': '查看用户',
            'description': '查看用户信息和列表',
            'category': '用户管理',
            'resource': 'user',
            'action': 'view'
        },
        {
            'name': PermissionConstants.USER_CREATE,
            'display_name': '创建用户',
            'description': '创建新用户账户',
            'category': '用户管理',
            'resource': 'user',
            'action': 'create'
        },
        {
            'name': PermissionConstants.USER_UPDATE,
            'display_name': '更新用户',
            'description': '更新用户信息',
            'category': '用户管理',
            'resource': 'user',
            'action': 'update'
        },
        {
            'name': PermissionConstants.USER_DELETE,
            'display_name': '删除用户',
            'description': '删除用户账户',
            'category': '用户管理',
            'resource': 'user',
            'action': 'delete'
        },
        {
            'name': PermissionConstants.USER_MANAGE_ROLES,
            'display_name': '管理用户角色',
            'description': '为用户分配和撤销角色',
            'category': '用户管理',
            'resource': 'user',
            'action': 'manage_roles'
        },
        
        # 策略管理权限
        {
            'name': PermissionConstants.STRATEGY_VIEW,
            'display_name': '查看策略',
            'description': '查看策略信息和列表',
            'category': '策略管理',
            'resource': 'strategy',
            'action': 'view'
        },
        {
            'name': PermissionConstants.STRATEGY_CREATE,
            'display_name': '创建策略',
            'description': '创建新的交易策略',
            'category': '策略管理',
            'resource': 'strategy',
            'action': 'create'
        },
        {
            'name': PermissionConstants.STRATEGY_UPDATE,
            'display_name': '更新策略',
            'description': '修改策略代码和配置',
            'category': '策略管理',
            'resource': 'strategy',
            'action': 'update'
        },
        {
            'name': PermissionConstants.STRATEGY_DELETE,
            'display_name': '删除策略',
            'description': '删除交易策略',
            'category': '策略管理',
            'resource': 'strategy',
            'action': 'delete'
        },
        {
            'name': PermissionConstants.STRATEGY_PUBLISH,
            'display_name': '发布策略',
            'description': '发布策略供他人使用',
            'category': '策略管理',
            'resource': 'strategy',
            'action': 'publish'
        },
        {
            'name': PermissionConstants.STRATEGY_EXECUTE,
            'display_name': '执行策略',
            'description': '运行交易策略',
            'category': '策略管理',
            'resource': 'strategy',
            'action': 'execute'
        },
        
        # 回测管理权限
        {
            'name': PermissionConstants.BACKTEST_VIEW,
            'display_name': '查看回测',
            'description': '查看回测任务和结果',
            'category': '回测管理',
            'resource': 'backtest',
            'action': 'view'
        },
        {
            'name': PermissionConstants.BACKTEST_CREATE,
            'display_name': '创建回测',
            'description': '创建新的回测任务',
            'category': '回测管理',
            'resource': 'backtest',
            'action': 'create'
        },
        {
            'name': PermissionConstants.BACKTEST_UPDATE,
            'display_name': '更新回测',
            'description': '修改回测配置',
            'category': '回测管理',
            'resource': 'backtest',
            'action': 'update'
        },
        {
            'name': PermissionConstants.BACKTEST_DELETE,
            'display_name': '删除回测',
            'description': '删除回测任务',
            'category': '回测管理',
            'resource': 'backtest',
            'action': 'delete'
        },
        {
            'name': PermissionConstants.BACKTEST_EXECUTE,
            'display_name': '执行回测',
            'description': '运行回测任务',
            'category': '回测管理',
            'resource': 'backtest',
            'action': 'execute'
        },
        
        # 订单管理权限
        {
            'name': PermissionConstants.ORDER_VIEW,
            'display_name': '查看订单',
            'description': '查看订单信息和历史',
            'category': '订单管理',
            'resource': 'order',
            'action': 'view'
        },
        {
            'name': PermissionConstants.ORDER_CREATE,
            'display_name': '创建订单',
            'description': '创建新的交易订单',
            'category': '订单管理',
            'resource': 'order',
            'action': 'create'
        },
        {
            'name': PermissionConstants.ORDER_UPDATE,
            'display_name': '更新订单',
            'description': '修改订单信息',
            'category': '订单管理',
            'resource': 'order',
            'action': 'update'
        },
        {
            'name': PermissionConstants.ORDER_DELETE,
            'display_name': '删除订单',
            'description': '删除订单',
            'category': '订单管理',
            'resource': 'order',
            'action': 'delete'
        },
        {
            'name': PermissionConstants.ORDER_EXECUTE,
            'display_name': '执行订单',
            'description': '执行交易订单',
            'category': '订单管理',
            'resource': 'order',
            'action': 'execute'
        },
        {
            'name': PermissionConstants.ORDER_CANCEL,
            'display_name': '取消订单',
            'description': '取消未成交订单',
            'category': '订单管理',
            'resource': 'order',
            'action': 'cancel'
        },
        
        # 持仓管理权限
        {
            'name': PermissionConstants.POSITION_VIEW,
            'display_name': '查看持仓',
            'description': '查看持仓信息',
            'category': '持仓管理',
            'resource': 'position',
            'action': 'view'
        },
        {
            'name': PermissionConstants.POSITION_MANAGE,
            'display_name': '管理持仓',
            'description': '管理持仓操作',
            'category': '持仓管理',
            'resource': 'position',
            'action': 'manage'
        },
        
        # 账户管理权限
        {
            'name': PermissionConstants.ACCOUNT_VIEW,
            'display_name': '查看账户',
            'description': '查看账户信息和资金',
            'category': '账户管理',
            'resource': 'account',
            'action': 'view'
        },
        {
            'name': PermissionConstants.ACCOUNT_MANAGE,
            'display_name': '管理账户',
            'description': '管理账户设置',
            'category': '账户管理',
            'resource': 'account',
            'action': 'manage'
        },
        
        # 风险管理权限
        {
            'name': PermissionConstants.RISK_VIEW,
            'display_name': '查看风险',
            'description': '查看风险指标和报告',
            'category': '风险管理',
            'resource': 'risk',
            'action': 'view'
        },
        {
            'name': PermissionConstants.RISK_MANAGE,
            'display_name': '管理风险',
            'description': '设置风险规则和限制',
            'category': '风险管理',
            'resource': 'risk',
            'action': 'manage'
        },
        {
            'name': PermissionConstants.RISK_OVERRIDE,
            'display_name': '风险覆盖',
            'description': '覆盖风险限制',
            'category': '风险管理',
            'resource': 'risk',
            'action': 'override'
        },
        
        # 系统管理权限
        {
            'name': PermissionConstants.SYSTEM_VIEW,
            'display_name': '查看系统',
            'description': '查看系统状态和信息',
            'category': '系统管理',
            'resource': 'system',
            'action': 'view'
        },
        {
            'name': PermissionConstants.SYSTEM_MANAGE,
            'display_name': '管理系统',
            'description': '管理系统设置',
            'category': '系统管理',
            'resource': 'system',
            'action': 'manage'
        },
        {
            'name': PermissionConstants.SYSTEM_CONFIG,
            'display_name': '系统配置',
            'description': '修改系统配置',
            'category': '系统管理',
            'resource': 'system',
            'action': 'config'
        },
        
        # 数据管理权限
        {
            'name': PermissionConstants.DATA_VIEW,
            'display_name': '查看数据',
            'description': '查看市场数据和历史数据',
            'category': '数据管理',
            'resource': 'data',
            'action': 'view'
        },
        {
            'name': PermissionConstants.DATA_MANAGE,
            'display_name': '管理数据',
            'description': '管理数据源和数据质量',
            'category': '数据管理',
            'resource': 'data',
            'action': 'manage'
        },
        {
            'name': PermissionConstants.DATA_EXPORT,
            'display_name': '导出数据',
            'description': '导出数据到外部系统',
            'category': '数据管理',
            'resource': 'data',
            'action': 'export'
        },
        
        # 报告权限
        {
            'name': PermissionConstants.REPORT_VIEW,
            'display_name': '查看报告',
            'description': '查看各类报告',
            'category': '报告管理',
            'resource': 'report',
            'action': 'view'
        },
        {
            'name': PermissionConstants.REPORT_CREATE,
            'display_name': '创建报告',
            'description': '创建自定义报告',
            'category': '报告管理',
            'resource': 'report',
            'action': 'create'
        },
        {
            'name': PermissionConstants.REPORT_EXPORT,
            'display_name': '导出报告',
            'description': '导出报告文件',
            'category': '报告管理',
            'resource': 'report',
            'action': 'export'
        },
        
        # 管理员权限
        {
            'name': PermissionConstants.ADMIN_ALL,
            'display_name': '管理员权限',
            'description': '拥有所有系统权限',
            'category': '系统管理',
            'resource': 'admin',
            'action': '*'
        }
    ]
    
    created_count = 0
    for perm_data in permissions_data:
        existing = db.query(Permission).filter(Permission.name == perm_data['name']).first()
        if not existing:
            permission = Permission(
                **perm_data,
                is_system=True,
                is_active=True
            )
            db.add(permission)
            created_count += 1
    
    db.commit()
    print(f"创建了 {created_count} 个系统权限")

def init_roles(db: Session):
    """初始化系统角色"""
    roles_data = [
        {
            'name': RoleConstants.SUPER_ADMIN,
            'display_name': '超级管理员',
            'description': '拥有所有权限的超级管理员，可以管理整个系统',
            'permissions': [PermissionConstants.ADMIN_ALL],
            'priority': 1000,
            'config': {
                'can_modify_system_roles': True,
                'can_access_all_data': True
            }
        },
        {
            'name': RoleConstants.ADMIN,
            'display_name': '管理员',
            'description': '系统管理员，拥有大部分管理权限',
            'permissions': [
                PermissionConstants.USER_VIEW, PermissionConstants.USER_CREATE,
                PermissionConstants.USER_UPDATE, PermissionConstants.USER_MANAGE_ROLES,
                PermissionConstants.STRATEGY_VIEW, PermissionConstants.STRATEGY_CREATE,
                PermissionConstants.STRATEGY_UPDATE, PermissionConstants.STRATEGY_PUBLISH,
                PermissionConstants.BACKTEST_VIEW, PermissionConstants.BACKTEST_CREATE,
                PermissionConstants.BACKTEST_EXECUTE,
                PermissionConstants.ORDER_VIEW, PermissionConstants.ORDER_CREATE,
                PermissionConstants.ORDER_UPDATE, PermissionConstants.ORDER_CANCEL,
                PermissionConstants.POSITION_VIEW, PermissionConstants.POSITION_MANAGE,
                PermissionConstants.ACCOUNT_VIEW, PermissionConstants.ACCOUNT_MANAGE,
                PermissionConstants.RISK_VIEW, PermissionConstants.RISK_MANAGE,
                PermissionConstants.SYSTEM_VIEW, PermissionConstants.SYSTEM_MANAGE,
                PermissionConstants.DATA_VIEW, PermissionConstants.DATA_MANAGE,
                PermissionConstants.REPORT_VIEW, PermissionConstants.REPORT_CREATE,
                PermissionConstants.REPORT_EXPORT
            ],
            'priority': 900
        },
        {
            'name': RoleConstants.TRADER,
            'display_name': '交易员',
            'description': '专业交易员，拥有交易相关权限',
            'permissions': [
                PermissionConstants.STRATEGY_VIEW, PermissionConstants.STRATEGY_EXECUTE,
                PermissionConstants.BACKTEST_VIEW, PermissionConstants.BACKTEST_CREATE,
                PermissionConstants.BACKTEST_EXECUTE,
                PermissionConstants.ORDER_VIEW, PermissionConstants.ORDER_CREATE,
                PermissionConstants.ORDER_UPDATE, PermissionConstants.ORDER_CANCEL,
                PermissionConstants.ORDER_EXECUTE,
                PermissionConstants.POSITION_VIEW,
                PermissionConstants.ACCOUNT_VIEW,
                PermissionConstants.RISK_VIEW,
                PermissionConstants.DATA_VIEW,
                PermissionConstants.REPORT_VIEW
            ],
            'priority': 700
        },
        {
            'name': RoleConstants.ANALYST,
            'display_name': '分析师',
            'description': '数据分析师，专注于数据分析和报告',
            'permissions': [
                PermissionConstants.STRATEGY_VIEW,
                PermissionConstants.BACKTEST_VIEW, PermissionConstants.BACKTEST_CREATE,
                PermissionConstants.BACKTEST_EXECUTE,
                PermissionConstants.ORDER_VIEW,
                PermissionConstants.POSITION_VIEW,
                PermissionConstants.ACCOUNT_VIEW,
                PermissionConstants.RISK_VIEW,
                PermissionConstants.DATA_VIEW, PermissionConstants.DATA_EXPORT,
                PermissionConstants.REPORT_VIEW, PermissionConstants.REPORT_CREATE,
                PermissionConstants.REPORT_EXPORT
            ],
            'priority': 600
        },
        {
            'name': RoleConstants.STRATEGY_DEVELOPER,
            'display_name': '策略开发者',
            'description': '策略开发人员，专注于策略开发和回测',
            'permissions': [
                PermissionConstants.STRATEGY_VIEW, PermissionConstants.STRATEGY_CREATE,
                PermissionConstants.STRATEGY_UPDATE, PermissionConstants.STRATEGY_DELETE,
                PermissionConstants.BACKTEST_VIEW, PermissionConstants.BACKTEST_CREATE,
                PermissionConstants.BACKTEST_UPDATE, PermissionConstants.BACKTEST_DELETE,
                PermissionConstants.BACKTEST_EXECUTE,
                PermissionConstants.DATA_VIEW,
                PermissionConstants.REPORT_VIEW
            ],
            'priority': 600
        },
        {
            'name': RoleConstants.RISK_MANAGER,
            'display_name': '风险管理员',
            'description': '风险管理专员，负责风险控制和监控',
            'permissions': [
                PermissionConstants.STRATEGY_VIEW,
                PermissionConstants.BACKTEST_VIEW,
                PermissionConstants.ORDER_VIEW, PermissionConstants.ORDER_CANCEL,
                PermissionConstants.POSITION_VIEW, PermissionConstants.POSITION_MANAGE,
                PermissionConstants.ACCOUNT_VIEW,
                PermissionConstants.RISK_VIEW, PermissionConstants.RISK_MANAGE,
                PermissionConstants.RISK_OVERRIDE,
                PermissionConstants.DATA_VIEW,
                PermissionConstants.REPORT_VIEW, PermissionConstants.REPORT_CREATE
            ],
            'priority': 800
        },
        {
            'name': RoleConstants.VIEWER,
            'display_name': '只读用户',
            'description': '只读权限用户，只能查看数据',
            'permissions': [
                PermissionConstants.STRATEGY_VIEW,
                PermissionConstants.BACKTEST_VIEW,
                PermissionConstants.ORDER_VIEW,
                PermissionConstants.POSITION_VIEW,
                PermissionConstants.ACCOUNT_VIEW,
                PermissionConstants.RISK_VIEW,
                PermissionConstants.DATA_VIEW,
                PermissionConstants.REPORT_VIEW
            ],
            'priority': 100
        },
        {
            'name': RoleConstants.USER,
            'display_name': '普通用户',
            'description': '普通用户，拥有基本功能权限',
            'permissions': [
                PermissionConstants.STRATEGY_VIEW, PermissionConstants.STRATEGY_CREATE,
                PermissionConstants.BACKTEST_VIEW, PermissionConstants.BACKTEST_CREATE,
                PermissionConstants.BACKTEST_EXECUTE,
                PermissionConstants.ORDER_VIEW,
                PermissionConstants.POSITION_VIEW,
                PermissionConstants.ACCOUNT_VIEW,
                PermissionConstants.DATA_VIEW,
                PermissionConstants.REPORT_VIEW
            ],
            'priority': 200
        }
    ]
    
    created_count = 0
    for role_data in roles_data:
        existing = db.query(Role).filter(Role.name == role_data['name']).first()
        if not existing:
            role = Role(
                **role_data,
                is_system=True,
                is_active=True
            )
            db.add(role)
            created_count += 1
    
    db.commit()
    print(f"创建了 {created_count} 个系统角色")

def create_admin_user(db: Session):
    """创建默认管理员用户"""
    from app.core.security import get_password_hash
    
    # 检查是否已存在管理员用户
    admin_user = db.query(User).filter(User.username == "admin").first()
    if admin_user:
        print("管理员用户已存在")
        return admin_user
    
    # 创建管理员用户
    admin_user = User(
        username="admin",
        email="admin@trading-platform.com",
        full_name="系统管理员",
        password_hash=get_password_hash("admin123"),
        is_active=True,
        is_verified=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    # 为管理员分配超级管理员角色
    super_admin_role = db.query(Role).filter(Role.name == RoleConstants.SUPER_ADMIN).first()
    if super_admin_role:
        from app.models.role import user_roles
        # 检查是否已经分配了角色
        existing_assignment = db.execute(
            user_roles.select().where(
                user_roles.c.user_id == admin_user.id,
                user_roles.c.role_id == super_admin_role.id
            )
        ).first()
        
        if not existing_assignment:
            db.execute(
                user_roles.insert().values(
                    user_id=admin_user.id,
                    role_id=super_admin_role.id,
                    assigned_by=admin_user.id
                )
            )
            db.commit()
            print("为管理员用户分配了超级管理员角色")
    
    print(f"创建了管理员用户: {admin_user.username}")
    print("默认密码: admin123")
    return admin_user

def main():
    """主函数"""
    print("开始初始化系统角色和权限...")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 初始化权限
        print("\n1. 初始化系统权限...")
        init_permissions(db)
        
        # 初始化角色
        print("\n2. 初始化系统角色...")
        init_roles(db)
        
        # 创建管理员用户
        print("\n3. 创建默认管理员用户...")
        create_admin_user(db)
        
        print("\n✅ 系统角色和权限初始化完成！")
        print("\n默认管理员账户:")
        print("用户名: admin")
        print("密码: admin123")
        print("请登录后立即修改默认密码！")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()