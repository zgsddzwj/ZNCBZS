"""
数据库连接和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from typing import Generator
from loguru import logger
from backend.core.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 需要
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类"""
    pass


def init_db():
    """创建所有数据库表"""
    # 确保模型被导入，以便 Base.metadata 包含所有表定义
    from backend.models.user import User  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("数据库表初始化完成")


def get_db() -> Generator:
    """依赖注入：提供数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
