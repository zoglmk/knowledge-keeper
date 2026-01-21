#!/bin/bash

# Knowledge Keeper 启动脚本
# 同时启动后端和前端服务

echo "🚀 启动 Knowledge Keeper..."

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 停止可能已运行的服务
echo "📦 停止旧服务..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null
sleep 1

# 启动后端
echo "🔧 启动后端服务 (port 8000)..."
cd "$PROJECT_DIR/backend"
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
BACKEND_PID=$!
echo "   后端 PID: $BACKEND_PID"

# 等待后端启动
sleep 3

# 检查后端是否启动成功
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ 后端启动成功!"
else
    echo "   ❌ 后端启动失败，请检查 backend/server.log"
fi

# 启动前端
echo "🎨 启动前端服务 (port 5173)..."
cd "$PROJECT_DIR/frontend"
nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   前端 PID: $FRONTEND_PID"

# 等待前端启动
sleep 3

echo ""
echo "=========================================="
echo "🎉 Knowledge Keeper 启动完成!"
echo "=========================================="
echo ""
echo "📱 前端应用: http://localhost:5173/"
echo "🔌 后端 API: http://localhost:8000/docs"
echo ""
echo "💡 提示:"
echo "   - 后端日志: backend/server.log"
echo "   - 前端日志: frontend/frontend.log"
echo "   - 停止服务: ./stop.sh"
echo ""
