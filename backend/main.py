"""
智能财报助手 - 主应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import uvicorn
from loguru import logger

from backend.api import router
from backend.core.config import settings
from backend.core.logging import setup_logging
from backend.core.middleware import GlobalExceptionHandler, RequestLoggingMiddleware
from backend.core.auth import get_password_hash, UserRole
from backend.core.rate_limit import limiter
from backend.data.storage import init_storage
from backend.data.database import init_db, SessionLocal
from backend.models.user import User
from sqlalchemy import select


def _create_initial_admin():
    """首次启动时从环境变量创建初始管理员账户"""
    if not settings.INITIAL_ADMIN_PASSWORD:
        logger.warning("未配置 INITIAL_ADMIN_PASSWORD，跳过初始管理员创建。请在 .env 中设置。")
        return

    db = SessionLocal()
    try:
        existing = db.execute(
            select(User).where(User.username == settings.INITIAL_ADMIN_USERNAME)
        ).scalar_one_or_none()
        if existing:
            return

        admin = User(
            username=settings.INITIAL_ADMIN_USERNAME,
            email=settings.INITIAL_ADMIN_EMAIL,
            hashed_password=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.commit()
        logger.info(f"初始管理员账户已创建: {settings.INITIAL_ADMIN_USERNAME}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    setup_logging()
    logger.info("应用启动中...")

    # 初始化数据库表
    init_db()

    # 首次启动时创建初始管理员账户
    _create_initial_admin()

    await init_storage()
    
    # 启动数据调度器
    from backend.services.scheduler import scheduler
    await scheduler.start()
    
    yield
    
    # 关闭时清理
    logger.info("应用关闭中...")
    from backend.services.scheduler import scheduler
    await scheduler.stop()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于大模型 + 知识增强的财务分析工具",
    lifespan=lifespan,
)

# 速率限制
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# 中间件注册（注意顺序：最后注册的最先执行）
app.add_middleware(GlobalExceptionHandler)
app.add_middleware(RequestLoggingMiddleware)

# CORS配置（中间件栈中最后注册的先执行，CORS应最先执行）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    # 生产环境安全断言
    env = os.getenv("APP_ENV", "development")
    if env == "production" and settings.DEBUG:
        raise RuntimeError("DEBUG must be False in production (APP_ENV=production)")

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )

