#!/bin/bash
# 基金分析助手启动脚本

PROJECT_DIR="/Users/ternura/Desktop/claude-workplace/金融学习/fund-analyzer"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "🚀 启动基金分析助手..."

# 启动后端
echo "📡 启动后端服务..."
cd "$BACKEND_DIR"
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/fund-backend.log 2>&1 &
echo $! > /tmp/fund-backend.pid
echo "   后端 PID: $(cat /tmp/fund-backend.pid)"

# 启动前端
echo "🌐 启动前端服务..."
cd "$FRONTEND_DIR"
nohup npm run dev > /tmp/fund-frontend.log 2>&1 &
echo $! > /tmp/fund-frontend.pid
echo "   前端 PID: $(cat /tmp/fund-frontend.pid)"

sleep 3
echo ""
echo "✅ 启动完成!"
echo "   前端: http://localhost:3000"
echo "   后端: http://localhost:8000"
echo ""
echo "📋 日志文件:"
echo "   后端: /tmp/fund-backend.log"
echo "   前端: /tmp/fund-frontend.log"
