#!/bin/bash
# 停止后端API服务器

echo "========================================="
echo "  停止 AutoToolDPO Backend"
echo "========================================="

# 查找并停止uvicorn进程
echo "查找运行中的后端进程..."
PIDS=$(ps aux | grep "[u]vicorn api.app:app" | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "✓ 没有运行中的后端进程"
else
    echo "找到进程: $PIDS"
    for PID in $PIDS; do
        echo "停止进程 $PID..."
        kill -15 $PID 2>/dev/null
    done

    # 等待进程结束
    sleep 2

    # 强制杀死仍在运行的进程
    REMAINING=$(ps aux | grep "[u]vicorn api.app:app" | awk '{print $2}')
    if [ ! -z "$REMAINING" ]; then
        echo "强制停止残留进程..."
        kill -9 $REMAINING 2>/dev/null
    fi

    echo "✓ 后端进程已停止"
fi

echo ""
echo "后端已完全停止"
