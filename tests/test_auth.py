"""
认证模块单元测试
"""
import pytest
from datetime import timedelta
from backend.core.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_password,
    get_password_hash,
    check_permission,
    UserRole,
    PERMISSIONS,
)


class TestPasswordHashing:
    """密码哈希测试"""

    def test_hash_password(self):
        """测试密码哈希生成"""
        hashed = get_password_hash("testpassword123")
        assert hashed != "testpassword123"
        assert len(hashed) > 0

    def test_verify_correct_password(self):
        """测试正确密码验证"""
        hashed = get_password_hash("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self):
        """测试错误密码验证"""
        hashed = get_password_hash("mypassword")
        assert verify_password("wrongpassword", hashed) is False


class TestJWT:
    """JWT 令牌测试"""

    def test_create_and_verify_access_token(self):
        """测试 access token 创建和验证"""
        data = {"sub": "testuser", "id": 1, "role": "admin"}
        token = create_access_token(data)
        payload = verify_token(token, expected_type="access")
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["type"] == "access"

    def test_create_and_verify_refresh_token(self):
        """测试 refresh token 创建和验证"""
        data = {"sub": "testuser", "id": 1, "role": "admin"}
        token = create_refresh_token(data)
        payload = verify_token(token, expected_type="refresh")
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["type"] == "refresh"

    def test_access_token_rejected_as_refresh(self):
        """测试 access token 不能用作 refresh token"""
        data = {"sub": "testuser", "id": 1, "role": "admin"}
        token = create_access_token(data)
        payload = verify_token(token, expected_type="refresh")
        assert payload is None

    def test_invalid_token(self):
        """测试无效 token"""
        payload = verify_token("invalid.token.here")
        assert payload is None


class TestPermissions:
    """权限测试"""

    def test_admin_has_all_permissions(self):
        """测试管理员拥有所有权限"""
        for perm in PERMISSIONS[UserRole.ADMIN]:
            assert check_permission(UserRole.ADMIN, perm) is True

    def test_normal_user_limited_permissions(self):
        """测试普通用户权限受限"""
        assert check_permission(UserRole.NORMAL, "data:query") is True
        assert check_permission(UserRole.NORMAL, "user:manage") is False

    def test_senior_user_permissions(self):
        """测试高级用户权限"""
        assert check_permission(UserRole.SENIOR, "report:generate") is True
        assert check_permission(UserRole.SENIOR, "user:manage") is False
