#!/bin/bash

# Knowledge Keeper 停止脚本

echo "🛑 停止 Knowledge Keeper..."

# 停止后端 (port 8000)
echo "   停止后端服务..."
lsof -ti:8000 | xargs kill -9 2>/dev/null

# 停止前端 (port 5173)
echo "   停止前端服务..."
lsof -ti:5173 | xargs kill -9 2>/dev/null

echo "✅ 所有服务已停止"
