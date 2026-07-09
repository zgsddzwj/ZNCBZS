"""
速率限制模块
使用 slowapi 实现基于 IP 的请求速率限制。
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# 全局限速器实例（基于客户端 IP）
limiter = Limiter(key_func=get_remote_address)
