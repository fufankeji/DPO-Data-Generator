#!/bin/bash
# 同时启动前后端服务

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "========================================="
echo "  AutoToolDPO 一键启动"
echo "========================================="

# 检查依赖
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ 错误: 未找到 npm"
    exit 1
fi

# 创建必要的目录
mkdir -p logs data/raw data/processed data/exports

echo ""
echo "1️⃣  启动后端服务..."
echo "========================================="

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "安装后端依赖..."
    pip install -r backend/requirements.txt
else
    source venv/bin/activate
fi

# 后台启动后端
cd backend
nohup python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "✓ 后端已启动 (PID: $BACKEND_PID)"
echo "  - API地址: http://localhost:8000"
echo "  - API文档: http://localhost:8000/docs"
echo "  - 日志文件: logs/backend.log"

# 等待后端启动
echo ""
echo "等待后端服务就绪..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ 后端服务已就绪"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  警告: 后端服务启动超时，但将继续启动前端"
    fi
    sleep 1
done

echo ""
echo "2️⃣  启动前端服务..."
echo "========================================="

cd frontend

# 安装前端依赖（如果需要）
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

# 创建.env文件
if [ ! -f ".env" ]; then
    echo "创建 .env 配置..."
    cp .env.example .env
fi

# 后台启动前端
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

echo "✓ 前端已启动 (PID: $FRONTEND_PID)"
echo "  - 访问地址: http://localhost:3000"
echo "  - 日志文件: logs/frontend.log"

cd ..

echo ""
echo "========================================="
echo "  🎉 启动完成！"
echo "========================================="
echo ""
echo "📝 服务信息:"
echo "  • 后端API:  http://localhost:8000"
echo "  • 前端界面: http://localhost:3000"
echo "  • API文档:  http://localhost:8000/docs"
echo ""
echo "📋 管理命令:"
echo "  • 查看后端日志: tail -f logs/backend.log"
echo "  • 查看前端日志: tail -f logs/frontend.log"
echo "  • 停止所有服务: ./scripts/stop_all.sh"
echo ""
echo "💡 提示: 服务在后台运行，关闭终端不会停止服务"
echo ""
