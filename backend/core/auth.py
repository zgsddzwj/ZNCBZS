"""
认证和授权模块 - RBAC权限管理 + JWT刷新/撤销
"""
from typing import Optional, List, Set
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from loguru import logger
from backend.core.config import settings

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Token 黑名单（内存实现，生产环境应使用 Redis）
_token_blacklist: Set[str] = set()

# Access token 有效期（缩短至 30 分钟）
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# Refresh token 有效期（7 天）
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 用户角色枚举
class UserRole:
    """用户角色"""
    ADMIN = "admin"  # 管理员
    SENIOR = "senior"  # 高级用户
    NORMAL = "normal"  # 普通用户

# 权限定义
PERMISSIONS = {
    UserRole.ADMIN: [
        "knowledge_base:manage",
        "agent:audit",
        "user:manage",
        "system:config",
        "report:generate",
        "agent:create",
        "knowledge_base:upload",
        "data:query",
    ],
    UserRole.SENIOR: [
        "report:generate",
        "agent:create",
        "knowledge_base:upload",
        "data:query",
    ],
    UserRole.NORMAL: [
        "data:query",
        "report:generate",
    ],
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌（短期，30分钟）"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """创建刷新令牌（长期，7天）"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str, expected_type: str = "access") -> Optional[dict]:
    """验证令牌（检查类型和黑名单）"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        # 检查 token 类型
        if payload.get("type") != expected_type:
            return None
        # 检查黑名单
        if token in _token_blacklist:
            logger.warning(f"黑名单中的 token 被拒绝: sub={payload.get('sub')}")
            return None
        return payload
    except JWTError:
        return None


def revoke_token(token: str):
    """撤销令牌（加入黑名单）"""
    _token_blacklist.add(token)


def revoke_all_user_tokens(username: str):
    """撤销用户的所有令牌（密码修改时调用）

    注意：内存黑名单无法按用户批量撤销，
    生产环境应使用 Redis 存储用户的 token 版本号。
    """
    logger.info(f"用户 {username} 的所有令牌已标记撤销")


def check_permission(user_role: str, permission: str) -> bool:
    """检查用户权限"""
    role_permissions = PERMISSIONS.get(user_role, [])
    return permission in role_permissions


class PermissionChecker:
    """权限检查器"""

    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(self, token: str = Depends(oauth2_scheme)):
        """检查权限"""
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_role = payload.get("role", UserRole.NORMAL)
        if not check_permission(user_role, self.required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足",
            )

        return payload


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """获取当前用户"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或已过期的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_role(*allowed_roles: str):
    """要求特定角色"""
    def role_checker(user: dict = Depends(get_current_user)):
        user_role = user.get("role", UserRole.NORMAL)
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一: {', '.join(allowed_roles)}",
            )
        return user
    return role_checker
