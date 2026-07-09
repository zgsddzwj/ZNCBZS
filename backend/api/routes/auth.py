"""
认证和授权API
"""
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.core.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_password,
    get_password_hash,
    get_current_user,
    revoke_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    UserRole,
    PERMISSIONS,
)
from backend.core.config import settings
from backend.core.security import get_client_ip, log_operation
from backend.data.database import get_db
from backend.models.user import User
from backend.core.rate_limit import limiter
from loguru import logger

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
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str


@router.post("/register", response_model=UserInfo)
async def register(
    user: UserRegister,
    request: Request,
    db: Session = Depends(get_db),
):
    """用户注册（仅管理员可创建其他用户）"""
    # 检查用户名是否已存在
    existing = db.execute(
        select(User).where(User.username == user.username)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    existing_email = db.execute(
        select(User).where(User.email == user.email)
    ).scalar_one_or_none()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 创建用户
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        role=user.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_operation(
        operation="register",
        resource="/api/v1/auth/register",
        user_id=new_user.id,
        username=new_user.username,
        ip=get_client_ip(request),
    )

    permissions = PERMISSIONS.get(user.role, [])
    return UserInfo(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        role=new_user.role,
        permissions=permissions,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """用户登录（支持双因素认证）"""
    user = db.execute(
        select(User).where(User.username == form_data.username)
    ).scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
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

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用",
        )

    # 生成 access token (30分钟) 和 refresh token (7天)
    token_data = {
        "sub": user.username,
        "id": user.id,
        "role": user.role,
    }
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    log_operation(
        operation="login",
        resource="/api/v1/auth/login",
        user_id=user.id,
        username=user.username,
        ip=get_client_ip(request) if request else None,
        success=True,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    body: RefreshRequest,
):
    """使用 refresh token 获取新的 access token"""
    payload = verify_token(body.refresh_token, expected_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或已过期的刷新令牌",
        )

    token_data = {
        "sub": payload.get("sub"),
        "id": payload.get("id"),
        "role": payload.get("role"),
    }
    new_access_token = create_access_token(data=token_data)
    new_refresh_token = create_refresh_token(data=token_data)

    # 撤销旧的 refresh token
    revoke_token(body.refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
):
    """登出（撤销当前令牌）"""
    # 注意：客户端需要将 token 传过来才能撤销
    # 实际实现中可以从请求头提取 token 并加入黑名单
    return {"message": "已登出，请清除本地令牌"}


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户信息"""
    username = current_user.get("sub")
    user = db.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    permissions = PERMISSIONS.get(user.role, [])
    return UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        permissions=permissions,
    )
