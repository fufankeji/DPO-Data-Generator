#!/bin/bash
# 一键安装脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "========================================="
echo "  AutoToolDPO 环境安装"
echo "========================================="

# 1. 创建目录结构
echo "创建目录结构..."
mkdir -p logs data/raw data/processed data/exports

# 2. 安装后端依赖
echo ""
echo "安装后端依赖..."
if command -v python3 &> /dev/null; then
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -r backend/requirements.txt
    echo "✓ 后端依赖安装完成"
else
    echo "✗ 未找到 python3，跳过后端安装"
fi

# 3. 安装前端依赖
echo ""
echo "安装前端依赖..."
if command -v npm &> /dev/null; then
    cd frontend
    npm install
    echo "✓ 前端依赖安装完成"
    cd ..
else
    echo "✗ 未找到 npm，跳过前端安装"
fi

# 4. 复制配置文件
echo ""
echo "配置环境变量..."
if [ ! -f "frontend/.env" ]; then
    cp frontend/.env.example frontend/.env
    echo "✓ .env 配置文件已创建"
fi

# 5. 设置脚本可执行权限
echo ""
echo "设置脚本权限..."
chmod +x scripts/*.sh
echo "✓ 脚本权限已设置"

echo ""
echo "========================================="
echo "  安装完成！"
echo "========================================="
echo ""
echo "启动方式："
echo "  后端: ./scripts/start_backend.sh"
echo "  前端: ./scripts/start_frontend.sh"
echo ""
echo "或使用命令行："
echo "  python backend/main.py --help"
echo ""
