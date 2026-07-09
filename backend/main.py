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
from backend.core.middleware import GlobalExceptionHandler, RequestLoggingMiddleware, RequestBodySizeLimitMiddleware, SecurityHeadersMiddleware
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
    description="基于大模型 + 知识增强的财务分析工具\n\n## 版本说明\n- v1: 当前版本，提供财报分析、对话查询、智能体等功能\n- v2: 规划中，将支持多租户和自定义分析模型",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# 速率限制
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# 中间件注册（注意顺序：最后注册的最先执行）
from starlette.middleware.trustedhost import TrustedHostMiddleware

# TrustedHost 中间件（生产环境必须配置）
if not settings.DEBUG:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

app.add_middleware(GlobalExceptionHandler)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestBodySizeLimitMiddleware)

# CORS配置（仅允许实际使用的方法和头部）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
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


@app.get("/health/deep")
async def deep_health_check():
    """深度健康检查 - 检查所有依赖服务状态"""
    checks = {"status": "healthy", "services": {}}

    # 检查数据库
    try:
        from backend.data.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["services"]["database"] = "healthy"
    except Exception as e:
        checks["services"]["database"] = f"unhealthy: {str(e)[:50]}"
        checks["status"] = "degraded"

    # 检查 Redis
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        r.ping()
        checks["services"]["redis"] = "healthy"
    except Exception as e:
        checks["services"]["redis"] = f"unhealthy: {str(e)[:50]}"
        checks["status"] = "degraded"

    # 检查调度器
    try:
        from backend.services.scheduler import scheduler
        checks["services"]["scheduler"] = "running" if scheduler.running else "stopped"
    except Exception:
        checks["services"]["scheduler"] = "unknown"

    return checks


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

