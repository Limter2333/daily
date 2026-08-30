#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                每日早报晚报系统启动脚本                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 检查 Python
echo "📦 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装 Python3"
    exit 1
fi

# 检查 Node.js
echo "📦 检查 Node.js 环境..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js"
    exit 1
fi

# 安装 Python 依赖
echo "📦 安装 Python 依赖..."
pip install -r requirements.txt

# 安装前端依赖
echo "📦 安装前端依赖..."
cd frontend
npm install
cd ..

# 创建目录
mkdir -p data
mkdir -p logs/backend logs/frontend

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件，正在创建..."
    cat > .env << EOF
# AI API 配置
AI_API_KEY=your-api-key-here
AI_MODEL=gpt-3.5-turbo

# 其他配置请参考 config.yaml
EOF
    echo "✓ 已创建 .env 文件，请编辑填入你的 API Key"
fi

echo ""
echo "🚀 启动系统..."
echo ""

# 停止已有的后端服务（端口 8002）
echo "检查并停止已有的后端服务..."
BACKEND_PID=$(lsof -ti:8002 2>/dev/null)
if [ ! -z "$BACKEND_PID" ]; then
    echo "停止后端进程 $BACKEND_PID..."
    kill $BACKEND_PID 2>/dev/null
    sleep 1
fi

# 停止已有的前端服务（端口 5173）
echo "检查并停止已有的前端服务..."
FRONTEND_PID=$(lsof -ti:5173 2>/dev/null)
if [ ! -z "$FRONTEND_PID" ]; then
    echo "停止前端进程 $FRONTEND_PID..."
    kill $FRONTEND_PID 2>/dev/null
    sleep 1
fi

# 启动后端（后台运行）
echo "🔧 启动后端服务..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8002 --reload &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端
echo "🎨 启动前端服务..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    ✅ 系统已启动！                            ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                              ║"
echo "║  📱 前端地址: http://localhost:5173                          ║"
echo "║  🔧 后端地址: http://localhost:8002                          ║"
echo "║  📚 API 文档: http://localhost:8002/docs                     ║"
echo "║                                                              ║"
echo "║  📁 日志目录:                                                ║"
echo "║     后端: logs/backend/                                      ║"
echo "║     前端: 浏览器控制台                                        ║"
echo "║                                                              ║"
echo "║  按 Ctrl+C 停止系统                                          ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# 捕获退出信号
trap "echo ''; echo '🛑 正在停止系统...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

# 等待
wait
