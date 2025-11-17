#!/bin/bash
# 停止所有服务

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================="
echo "  停止 AutoToolDPO 所有服务"
echo "========================================="

# 停止后端
"$SCRIPT_DIR/stop_backend.sh"

echo ""

# 停止前端
"$SCRIPT_DIR/stop_frontend.sh"

echo ""
echo "========================================="
echo "  所有服务已停止"
echo "========================================="
