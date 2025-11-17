#!/bin/bash
# 启动后端API服务器

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "========================================="
echo "  AutoToolDPO Backend API Server"
echo "========================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

# 创建必要的目录
mkdir -p logs data/raw data/processed data/exports

# 安装依赖（首次运行）
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "安装依赖..."
    pip install -r backend/requirements.txt
else
    source venv/bin/activate
fi

# 启动API服务器
echo "启动API服务器 (http://localhost:8000)..."
cd backend
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
