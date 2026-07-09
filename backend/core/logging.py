"""
日志配置 - 包含敏感信息脱敏过滤器
"""
import sys
import re
from pathlib import Path
from loguru import logger
from backend.core.config import settings

# 敏感信息正则模式
_SENSITIVE_PATTERNS = [
    # Bearer token
    re.compile(r'(Bearer\s+)[\w\-]+\.([\w\-]+\.?[\w\-]*)', re.IGNORECASE),
    # password=xxx, token=xxx, secret=xxx, key=xxx
    re.compile(r'((?:password|passwd|token|secret|api_key|apikey|authorization)=[^&\s]+)', re.IGNORECASE),
    # JWT token (xxx.yyy.zzz)
    re.compile(r'eyJ[\w\-]+\.eyJ[\w\-]+\.[\w\-]+'),
]

_REPLACEMENT = '***REDACTED***'


def sanitize_log_message(message: str) -> str:
    """脱敏日志消息中的敏感信息"""
    if not isinstance(message, str):
        message = str(message)
    for pattern in _SENSITIVE_PATTERNS:
        message = pattern.sub(_REPLACEMENT, message)
    return message


def _sensitive_filter(record):
    """日志记录过滤器：脱敏敏感信息"""
    record["message"] = sanitize_log_message(record["message"])
    return True


def setup_logging():
    """配置日志系统"""
    # 移除默认 handler
    logger.remove()

    # 控制台输出（添加敏感信息过滤）
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True,
        filter=_sensitive_filter,
    )

    # 文件输出（添加敏感信息过滤）
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.LOG_LEVEL,
        rotation="00:00",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        filter=_sensitive_filter,
    )

    logger.info("日志系统初始化完成（已启用敏感信息脱敏）")
