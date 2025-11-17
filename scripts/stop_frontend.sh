#!/bin/bash
# 停止前端开发服务器

echo "========================================="
echo "  停止 AutoToolDPO Frontend"
echo "========================================="

# 查找并停止vite/npm进程
echo "查找运行中的前端进程..."
PIDS=$(ps aux | grep "[n]pm run dev" | awk '{print $2}')
VITE_PIDS=$(ps aux | grep "[v]ite" | awk '{print $2}')

ALL_PIDS="$PIDS $VITE_PIDS"

if [ -z "$ALL_PIDS" ]; then
    echo "✓ 没有运行中的前端进程"
else
    echo "找到进程: $ALL_PIDS"
    for PID in $ALL_PIDS; do
        echo "停止进程 $PID..."
        kill -15 $PID 2>/dev/null
    done

    # 等待进程结束
    sleep 2

    # 强制杀死仍在运行的进程
    REMAINING_NPM=$(ps aux | grep "[n]pm run dev" | awk '{print $2}')
    REMAINING_VITE=$(ps aux | grep "[v]ite" | awk '{print $2}')
    REMAINING="$REMAINING_NPM $REMAINING_VITE"

    if [ ! -z "$REMAINING" ]; then
        echo "强制停止残留进程..."
        kill -9 $REMAINING 2>/dev/null
    fi

    echo "✓ 前端进程已停止"
fi

echo ""
echo "前端已完全停止"
