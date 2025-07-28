"""
认证API集成测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import verify_password


class TestAuthAPI:
    """认证API测试类"""
    
    def test_register_user(self, client: TestClient, db_session: Session):
        """测试用户注册"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "id" in data
        
        # 验证用户已创建
        user = db_session.query(User).filter(User.email == user_data["email"]).first()
        assert user is not None
        assert user.username == user_data["username"]
        assert verify_password(user_data["password"], user.hashed_password)
    
    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """测试重复邮箱注册"""
        user_data = {
            "username": "anotheruser",
            "email": test_user.email,
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_register_duplicate_username(self, client: TestClient, test_user: User):
        """测试重复用户名注册"""
        user_data = {
            "username": test_user.username,
            "email": "another@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "already taken" in response.json()["detail"]
    
    def test_login_success(self, client: TestClient, test_user: User):
        """测试成功登录"""
        login_data = {
            "username": test_user.username,
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == test_user.username
    
    def test_login_invalid_credentials(self, client: TestClient, test_user: User):
        """测试无效凭据登录"""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client: TestClient):
        """测试不存在用户登录"""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_refresh_token(self, client: TestClient, test_user: User):
        """测试刷新令牌"""
        # 先登录获取令牌
        login_data = {
            "username": test_user.username,
            "password": "testpass123"
        }
        
        login_response = client.post("/api/v1/auth/login", data=login_data)
        refresh_token = login_response.json()["refresh_token"]
        
        # 使用刷新令牌获取新的访问令牌
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_refresh_invalid_token(self, client: TestClient):
        """测试无效刷新令牌"""
        refresh_data = {"refresh_token": "invalid_token"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]
    
    def test_logout(self, client: TestClient, auth_headers: dict):
        """测试登出"""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
    
    def test_logout_without_auth(self, client: TestClient):
        """测试未认证登出"""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401
    
    def test_get_current_user(self, client: TestClient, auth_headers: dict, test_user: User):
        """测试获取当前用户信息"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert data["id"] == str(test_user.id)
    
    def test_get_current_user_without_auth(self, client: TestClient):
        """测试未认证获取用户信息"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    def test_change_password(self, client: TestClient, auth_headers: dict, test_user: User, db_session: Session):
        """测试修改密码"""
        password_data = {
            "current_password": "testpass123",
            "new_password": "newpass123"
        }
        
        response = client.post("/api/v1/auth/change-password", json=password_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"
        
        # 验证密码已更改
        db_session.refresh(test_user)
        assert verify_password("newpass123", test_user.hashed_password)
    
    def test_change_password_wrong_current(self, client: TestClient, auth_headers: dict):
        """测试错误当前密码修改"""
        password_data = {
            "current_password": "wrongpass",
            "new_password": "newpass123"
        }
        
        response = client.post("/api/v1/auth/change-password", json=password_data, headers=auth_headers)
        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]
    
    def test_reset_password_request(self, client: TestClient, test_user: User):
        """测试密码重置请求"""
        reset_data = {"email": test_user.email}
        
        response = client.post("/api/v1/auth/reset-password-request", json=reset_data)
        assert response.status_code == 200
        assert "Password reset email sent" in response.json()["message"]
    
    def test_reset_password_nonexistent_email(self, client: TestClient):
        """测试不存在邮箱的密码重置"""
        reset_data = {"email": "nonexistent@example.com"}
        
        response = client.post("/api/v1/auth/reset-password-request", json=reset_data)
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_protected_endpoint_without_token(self, client: TestClient):
        """测试未认证访问受保护端点"""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_invalid_token(self, client: TestClient):
        """测试无效令牌访问受保护端点"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401
    
    def test_admin_endpoint_with_regular_user(self, client: TestClient, auth_headers: dict):
        """测试普通用户访问管理员端点"""
        response = client.get("/api/v1/users/", headers=auth_headers)
        assert response.status_code == 403
    
    def test_admin_endpoint_with_admin_user(self, client: TestClient, admin_headers: dict):
        """测试管理员访问管理员端点"""
        response = client.get("/api/v1/users/", headers=admin_headers)
        assert response.status_code == 200


class TestAuthFlow:
    """认证流程测试"""
    
    def test_complete_auth_flow(self, client: TestClient, db_session: Session):
        """测试完整认证流程"""
        # 1. 注册用户
        register_data = {
            "username": "flowuser",
            "email": "flow@example.com",
            "password": "flowpass123"
        }
        
        register_response = client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == 201
        
        # 2. 登录
        login_data = {
            "username": "flowuser",
            "password": "flowpass123"
        }
        
        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        
        # 3. 访问受保护资源
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "flowuser"
        
        # 4. 刷新令牌
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = client.post("/api/v1/auth/refresh", json=refresh_data)
        assert refresh_response.status_code == 200
        
        new_access_token = refresh_response.json()["access_token"]
        
        # 5. 使用新令牌访问资源
        new_headers = {"Authorization": f"Bearer {new_access_token}"}
        me_response2 = client.get("/api/v1/auth/me", headers=new_headers)
        assert me_response2.status_code == 200
        
        # 6. 修改密码
        password_data = {
            "current_password": "flowpass123",
            "new_password": "newflowpass123"
        }
        
        change_response = client.post("/api/v1/auth/change-password", json=password_data, headers=new_headers)
        assert change_response.status_code == 200
        
        # 7. 使用新密码登录
        new_login_data = {
            "username": "flowuser",
            "password": "newflowpass123"
        }
        
        new_login_response = client.post("/api/v1/auth/login", data=new_login_data)
        assert new_login_response.status_code == 200
        
        # 8. 登出
        final_headers = {"Authorization": f"Bearer {new_login_response.json()['access_token']}"}
        logout_response = client.post("/api/v1/auth/logout", headers=final_headers)
        assert logout_response.status_code == 200