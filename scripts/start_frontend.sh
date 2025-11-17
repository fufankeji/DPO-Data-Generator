#!/bin/bash
# 启动前端开发服务器

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../frontend"

echo "========================================="
echo "  AutoToolDPO Frontend Dev Server"
echo "========================================="

# 检查Node.js环境
if ! command -v npm &> /dev/null; then
    echo "错误: 未找到 npm"
    exit 1
fi

# 安装依赖（首次运行）
if [ ! -d "node_modules" ]; then
    echo "安装依赖..."
    npm install
fi

# 创建.env文件（如果不存在）
if [ ! -f ".env" ]; then
    echo "创建 .env 配置文件..."
    cp .env.example .env
fi

# 启动开发服务器
echo "启动前端服务器 (http://localhost:3000)..."
npm run dev
