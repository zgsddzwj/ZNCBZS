"""
Gunicorn 生产环境配置
使用方式: gunicorn -c backend/gunicorn_conf.py backend.main:app
"""
import multiprocessing
import os

# 绑定地址
bind = f"0.0.0.0:{os.getenv('API_PORT', '8000')}"

# Worker 数量（CPU 核心数 * 2 + 1）
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Worker 类型（uvicorn worker 支持 ASGI）
worker_class = "uvicorn.workers.UvicornWorker"

# 超时（秒）- LLM 请求可能较慢
timeout = 120

# 优雅关闭超时
graceful_timeout = 30

# 保持连接超时
keepalive = 5

# 最大请求数（防止内存泄漏，处理完后 worker 重启）
max_requests = 1000
max_requests_jitter = 50

# 预加载应用（减少内存使用，加快启动）
preload_app = True

# 日志
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()

# 进程名
proc_name = "zncbzs"

# 优雅关闭
def on_exit(server):
    """服务器退出时的钩子"""
    server.log.info("Gunicorn 服务器正在关闭...")
