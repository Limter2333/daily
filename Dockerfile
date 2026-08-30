# ============================================
# Stage 1: 构建前端
# ============================================
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# 先复制依赖文件，利用 Docker 缓存层
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# 复制源码并构建
COPY frontend/ ./
RUN npm run build

# ============================================
# Stage 2: 运行时
# ============================================
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（lxml 需要 libxml2/libxslt）
RUN apt-get update && \
    apt-get install -y --no-install-recommends libxml2-dev libxslt1-dev && \
    rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖（利用 Docker 缓存层）
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/
COPY config.yaml ./

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# 创建数据和日志目录
RUN mkdir -p data logs/backend

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
