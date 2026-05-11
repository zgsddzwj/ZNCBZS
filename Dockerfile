FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖 + uv
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    libtesseract-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# 复制项目配置
COPY pyproject.toml .
COPY backend ./backend

# 用 uv 安装依赖
RUN uv sync --no-dev

# 暴露端口
EXPOSE 8000

# 启动命令（使用 uv run 运行）
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
