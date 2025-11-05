#!/bin/bash

# 智能财报助手启动脚本

echo "🚀 启动智能财报助手..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python版本: $python_version"

# 检查依赖
if [ ! -f "requirements.txt" ]; then
    echo "❌ 未找到 requirements.txt"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖..."
pip install -q -r requirements.txt

# 检查环境变量
if [ ! -f ".env" ]; then
    echo "⚙️  创建环境变量文件..."
    cp config/env_template.txt .env
    echo "⚠️  请编辑 .env 文件，填入你的API密钥"
fi

# 创建必要的目录
mkdir -p data/uploads
mkdir -p data/reports
mkdir -p logs
mkdir -p templates

# 启动后端服务
echo "🔧 启动后端服务..."
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"
echo "📖 API文档: http://localhost:8000/docs"
echo "🏥 健康检查: http://localhost:8000/health"
echo ""
echo "按 Ctrl+C 停止服务"

# 等待中断信号
trap "kill $BACKEND_PID; exit" INT TERM
wait $BACKEND_PID

