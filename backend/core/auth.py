"""
认证和授权模块 - RBAC权限管理
"""
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.core.config import settings

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# 用户角色枚举
class UserRole:
    """用户角色"""
    ADMIN = "admin"  # 管理员
    SENIOR = "senior"  # 高级用户
    NORMAL = "normal"  # 普通用户

# 权限定义
PERMISSIONS = {
    UserRole.ADMIN: [
        "knowledge_base:manage",  # 知识库管理
        "agent:audit",  # 智能体审核
        "user:manage",  # 用户权限分配
        "system:config",  # 系统参数配置
        "report:generate",  # 报告生成
        "agent:create",  # 创建智能体
        "knowledge_base:upload",  # 上传知识库
        "data:query",  # 数据查询
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
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """验证令牌"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


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
            detail="无效的认证令牌",
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

