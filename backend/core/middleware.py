"""
全局中间件 - 异常处理、请求日志、耗时统计、安全响应头、请求体限制
"""
import time
import traceback
import re
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from loguru import logger

# 默认最大请求体大小 (10MB，文件上传端点可单独配置)
DEFAULT_MAX_BODY_SIZE = 10 * 1024 * 1024

# 敏感字段模式（日志中会被脱敏）
_SENSITIVE_PATTERNS = [
    re.compile(r'(token|password|secret|key|authorization)=[^&\s]+', re.IGNORECASE),
    re.compile(r'Bearer\s+[\w\-]+\.[\w\-]+\.[\w\-]+', re.IGNORECASE),
]


class GlobalExceptionHandler(BaseHTTPMiddleware):
    """
    全局异常处理中间件
    
    统一捕获所有未处理异常，返回标准化的错误响应格式，
    避免敏感信息泄露（如完整堆栈对外暴露）。
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
            return response
        except StarletteHTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "error": {
                        "code": e.status_code,
                        "message": str(e.detail),
                        "type": "http_error",
                    },
                },
            )
        except Exception as e:
            # 记录完整的异常堆栈到日志
            logger.error(f"未处理的异常: {request.method} {request.url.path}\n{traceback.format_exc()}")
            # 返回安全的错误信息给客户端
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": 500,
                        "message": "服务器内部错误，请稍后重试",
                        "type": "internal_error",
                    },
                },
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    
    记录每个请求的方法、路径、状态码、耗时等信息，
    便于生产环境问题排查和性能监控。
    """

    # 不记录日志的路径前缀（静态资源、健康检查等）
    SKIP_PATH_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/health", "/")

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        # 跳过静态资源和健康检查的日志
        if any(request.url.path.startswith(prefix) for prefix in self.SKIP_PATH_PREFIXES):
            return await call_next(request)

        # 记录请求信息（脱敏处理，不记录完整 URL 中的查询参数）
        client_ip = request.client.host if request.client else "unknown"
        logger.info(
            f"📥 请求开始 | {client_ip} | {request.method} {request.url.path}"
        )

        # 执行请求
        response = await call_next(request)

        # 计算耗时
        process_time = time.time() - start_time
        status_code = response.status_code

        # 根据状态码选择日志级别
        log_level = logger.warning if status_code >= 400 else logger.info
        log_level(
            f"📤 请求完成 | {status_code} | "
            f"{request.method} {request.url.path} | "
            f"耗时 {process_time:.3f}s"
        )




        # 在响应头中添加耗时信息（方便调试）
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        return response


class RequestBodySizeLimitMiddleware(BaseHTTPMiddleware):
    """
    请求体大小限制中间件
    
    防止超大请求体导致内存耗尽，默认限制 10MB。
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > DEFAULT_MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={
                    "success": False,
                    "error": {
                        "code": 413,
                        "message": "请求体过大",
                        "type": "payload_too_large",
                    },
                },
            )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全响应头中间件
    
    添加标准安全响应头，增强应用安全性。
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response
