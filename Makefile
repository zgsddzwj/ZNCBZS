.PHONY: help install dev test clean docker-up docker-down lint format

help:
	@echo "智能财报助手 - 开发命令"
	@echo ""
	@echo "  make install    - 使用 uv 安装 Python 依赖"
	@echo "  make dev        - 启动开发服务器（热重载）"
	@echo "  make test       - 运行测试"
	@echo "  make lint       - 代码检查（ruff + mypy）"
	@echo "  make format     - 代码格式化（black + ruff）"
	@echo "  make docker-up  - 启动 Docker 服务"
	@echo "  make docker-down - 停止 Docker 服务"
	@echo "  make clean      - 清理临时文件"

install:
	uv sync

dev:
	cd backend && uv run uvicorn main:app --reload

test:
	uv run pytest backend/tests/

lint:
	uv run ruff check backend/
	uv run mypy backend/

format:
	uv run black backend/
	uv run ruff check --fix backend/

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
