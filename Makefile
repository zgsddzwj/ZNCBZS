.PHONY: help install dev test clean docker-up docker-down

help:
	@echo "智能财报助手 - 开发命令"
	@echo ""
	@echo "  make install    - 安装Python依赖"
	@echo "  make dev        - 启动开发服务器"
	@echo "  make test       - 运行测试"
	@echo "  make docker-up  - 启动Docker服务"
	@echo "  make docker-down - 停止Docker服务"
	@echo "  make clean      - 清理临时文件"

install:
	pip install -r requirements.txt

dev:
	cd backend && uvicorn main:app --reload

test:
	pytest backend/tests/

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache

