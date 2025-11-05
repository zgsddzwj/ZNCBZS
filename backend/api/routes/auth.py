"""
认证和授权API
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta
from backend.core.auth import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_current_user,
    UserRole,
)
from backend.core.config import settings
from backend.core.security import get_client_ip, log_operation
from fastapi import Request

router = APIRouter()


class UserRegister(BaseModel):
    """用户注册"""
    username: str
    email: EmailStr
    password: str
    role: str = UserRole.NORMAL


class UserLogin(BaseModel):
    """用户登录"""
    username: str
    password: str
    verification_code: Optional[str] = None  # 短信验证码（双因素认证）


class UserInfo(BaseModel):
    """用户信息"""
    id: str
    username: str
    email: str
    role: str
    permissions: list


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# 临时用户数据库（实际应该用数据库）
_users_db: dict = {
    "admin": {
        "id": "1",
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": get_password_hash("admin123"),
        "role": UserRole.ADMIN,
    },
    "user": {
        "id": "2",
        "username": "user",
        "email": "user@example.com",
        "hashed_password": get_password_hash("user123"),
        "role": UserRole.NORMAL,
    },
}


@router.post("/register", response_model=UserInfo)
async def register(user: UserRegister, request: Request):
    """用户注册（仅管理员可创建其他用户）"""
    # 检查用户名是否已存在
    if user.username in _users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 创建用户
    user_id = str(len(_users_db) + 1)
    _users_db[user.username] = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "hashed_password": get_password_hash(user.password),
        "role": user.role,
    }
    
    log_operation(
        operation="register",
        resource="/api/v1/auth/register",
        user_id=user_id,
        username=user.username,
        ip=get_client_ip(request),
    )
    
    return UserInfo(
        id=user_id,
        username=user.username,
        email=user.email,
        role=user.role,
        permissions=[],
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
):
    """
    用户登录（支持双因素认证）
    
    实际实现中应该：
    1. 验证用户名密码
    2. 如果启用双因素认证，发送短信验证码
    3. 验证验证码
    4. 生成token
    """
    user = _users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        log_operation(
            operation="login",
            resource="/api/v1/auth/login",
            username=form_data.username,
            ip=get_client_ip(request) if request else None,
            success=False,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成token
    access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    access_token = create_access_token(
        data={
            "sub": user["username"],
            "id": user["id"],
            "role": user["role"],
        },
        expires_delta=access_token_expires,
    )
    
    log_operation(
        operation="login",
        resource="/api/v1/auth/login",
        user_id=user["id"],
        username=user["username"],
        ip=get_client_ip(request) if request else None,
        success=True,
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
    )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    username = current_user.get("sub")
    user = _users_db.get(username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserInfo(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        role=user["role"],
        permissions=[],
    )

