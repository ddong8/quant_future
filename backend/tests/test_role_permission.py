"""
角色权限系统测试
"""
import pytest
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.role import Role, Permission, PermissionConstants, RoleConstants
from app.services.role_service import RoleService
from app.schemas.role import RoleCreate, PermissionCreate, UserRoleAssignmentCreate
from app.core.security import get_password_hash

class TestRolePermissionSystem:
    """角色权限系统测试类"""
    
    def test_create_permission(self, db: Session):
        """测试创建权限"""
        role_service = RoleService(db)
        
        permission_data = PermissionCreate(
            name="test:permission",
            display_name="测试权限",
            description="这是一个测试权限",
            category="测试",
            resource="test",
            action="permission"
        )
        
        permission = role_service.create_permission(permission_data)
        
        assert permission.name == "test:permission"
        assert permission.display_name == "测试权限"
        assert permission.category == "测试"
        assert permission.resource == "test"
        assert permission.action == "permission"
        assert permission.is_active == True
    
    def test_create_role(self, db: Session):
        """测试创建角色"""
        role_service = RoleService(db)
        
        # 先创建一个权限
        permission_data = PermissionCreate(
            name="test:view",
            display_name="测试查看",
            category="测试",
            resource="test",
            action="view"
        )
        permission = role_service.create_permission(permission_data)
        
        # 创建用户作为创建者
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=get_password_hash("password"),
            full_name="Test User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建角色
        role_data = RoleCreate(
            name="test_role",
            display_name="测试角色",
            description="这是一个测试角色",
            permissions=["test:view"]
        )
        
        role = role_service.create_role(role_data, user.id)
        
        assert role.name == "test_role"
        assert role.display_name == "测试角色"
        assert "test:view" in role.permissions
        assert role.created_by == user.id
    
    def test_assign_role_to_user(self, db: Session):
        """测试为用户分配角色"""
        role_service = RoleService(db)
        
        # 创建用户
        user = User(
            username="testuser2",
            email="test2@example.com",
            password_hash=get_password_hash("password"),
            full_name="Test User 2"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建角色
        role_data = RoleCreate(
            name="test_role2",
            display_name="测试角色2",
            permissions=[]
        )
        role = role_service.create_role(role_data, user.id)
        
        # 分配角色
        assignment_data = UserRoleAssignmentCreate(
            user_id=user.id,
            role_id=role.id,
            reason="测试分配"
        )
        
        assignment = role_service.assign_role_to_user(
            user.id, role.id, assignment_data, user.id
        )
        
        assert assignment.user_id == user.id
        assert assignment.role_id == role.id
        assert assignment.reason == "测试分配"
        assert assignment.is_active == True
    
    def test_user_permission_check(self, db: Session):
        """测试用户权限检查"""
        role_service = RoleService(db)
        
        # 创建权限
        permission_data = PermissionCreate(
            name="test:manage",
            display_name="测试管理",
            category="测试",
            resource="test",
            action="manage"
        )
        permission = role_service.create_permission(permission_data)
        
        # 创建用户
        user = User(
            username="testuser3",
            email="test3@example.com",
            password_hash=get_password_hash("password"),
            full_name="Test User 3"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建角色并分配权限
        role_data = RoleCreate(
            name="test_role3",
            display_name="测试角色3",
            permissions=["test:manage"]
        )
        role = role_service.create_role(role_data, user.id)
        
        # 为用户分配角色
        assignment_data = UserRoleAssignmentCreate(
            user_id=user.id,
            role_id=role.id
        )
        role_service.assign_role_to_user(user.id, role.id, assignment_data, user.id)
        
        # 刷新用户数据
        db.refresh(user)
        
        # 检查权限
        assert user.has_permission("test:manage") == True
        assert user.has_permission("test:nonexistent") == False
        assert user.has_role("test_role3") == True
        assert user.has_role("nonexistent_role") == False
    
    def test_permission_wildcard(self, db: Session):
        """测试通配符权限"""
        role_service = RoleService(db)
        
        # 创建用户
        user = User(
            username="testuser4",
            email="test4@example.com",
            password_hash=get_password_hash("password"),
            full_name="Test User 4"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建具有通配符权限的角色
        role_data = RoleCreate(
            name="admin_role",
            display_name="管理员角色",
            permissions=["admin:*"]
        )
        role = role_service.create_role(role_data, user.id)
        
        # 为用户分配角色
        assignment_data = UserRoleAssignmentCreate(
            user_id=user.id,
            role_id=role.id
        )
        role_service.assign_role_to_user(user.id, role.id, assignment_data, user.id)
        
        # 刷新用户数据
        db.refresh(user)
        
        # 检查通配符权限
        assert user.has_permission("admin:view") == True
        assert user.has_permission("admin:create") == True
        assert user.has_permission("admin:delete") == True
        assert user.has_permission("user:view") == False  # 不匹配通配符
    
    def test_role_priority(self, db: Session):
        """测试角色优先级"""
        role_service = RoleService(db)
        
        # 创建用户
        user = User(
            username="testuser5",
            email="test5@example.com",
            password_hash=get_password_hash("password"),
            full_name="Test User 5"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建高优先级角色
        high_priority_role = role_service.create_role(
            RoleCreate(
                name="high_priority",
                display_name="高优先级角色",
                priority=100
            ),
            user.id
        )
        
        # 创建低优先级角色
        low_priority_role = role_service.create_role(
            RoleCreate(
                name="low_priority",
                display_name="低优先级角色",
                priority=10
            ),
            user.id
        )
        
        # 为用户分配两个角色
        for role in [high_priority_role, low_priority_role]:
            assignment_data = UserRoleAssignmentCreate(
                user_id=user.id,
                role_id=role.id
            )
            role_service.assign_role_to_user(user.id, role.id, assignment_data, user.id)
        
        # 获取用户角色（应该按优先级排序）
        user_roles = role_service.get_user_roles(user.id)
        
        assert len(user_roles) == 2
        assert user_roles[0].priority >= user_roles[1].priority  # 按优先级降序排列
    
    def test_batch_role_assignment(self, db: Session):
        """测试批量角色分配"""
        role_service = RoleService(db)
        
        # 创建多个用户
        users = []
        for i in range(3):
            user = User(
                username=f"batchuser{i}",
                email=f"batch{i}@example.com",
                password_hash=get_password_hash("password"),
                full_name=f"Batch User {i}"
            )
            db.add(user)
            users.append(user)
        
        db.commit()
        
        # 创建角色
        role_data = RoleCreate(
            name="batch_role",
            display_name="批量角色"
        )
        role = role_service.create_role(role_data, users[0].id)
        
        # 批量分配角色
        from app.schemas.role import UserRoleBatch
        batch_data = UserRoleBatch(
            user_ids=[user.id for user in users],
            role_ids=[role.id],
            action="assign",
            reason="批量测试"
        )
        
        results = role_service.batch_assign_roles(batch_data, users[0].id)
        
        assert len(results['success']) == 3
        assert len(results['failed']) == 0
        
        # 验证所有用户都有该角色
        for user in users:
            user_roles = role_service.get_user_roles(user.id)
            assert len(user_roles) == 1
            assert user_roles[0].id == role.id

@pytest.fixture
def db():
    """数据库会话fixture"""
    from app.core.database import SessionLocal, engine
    from app.models import Base
    
    # 创建测试数据库表
    Base.metadata.create_all(bind=engine)
    
    # 创建会话
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # 清理测试数据
        Base.metadata.drop_all(bind=engine)