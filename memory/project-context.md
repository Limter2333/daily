# 项目上下文记忆

## 技术栈
- 后端: Python FastAPI + SQLite
- 前端: React + TypeScript + Vite + Tailwind CSS
- AI: OpenAI 兼容 API

## 关键文件
- backend/main.py - FastAPI 入口
- backend/services/ - 核心业务逻辑
- backend/sources/ - 新闻源爬虫
- frontend/src/components/ - React 组件

## 常见任务
1. 添加新新闻源 → 在 backend/sources/ 下新建文件
2. 修改前端页面 → 在 frontend/src/components/ 下修改
3. 添加新 API → 在 backend/main.py 中添加路由
