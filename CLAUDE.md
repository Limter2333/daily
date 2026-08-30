# 每日早报晚报系统 - 项目指南

## 项目概述
自动获取财经、科技、半导体、AI等重点新闻，生成早报晚报的智能系统。

## 技术栈
- **后端**: Python 3.9+ / FastAPI / SQLite / APScheduler
- **前端**: React 18 / TypeScript / Vite / Tailwind CSS
- **AI**: OpenAI/Anthropic 兼容 API（用于新闻分析和摘要生成）

## API 配置

支持两种 AI API 协议：

**OpenAI 兼容协议：**
```bash
AI_API_KEY=sk-xxxxx
AI_MODEL=gpt-4o
AI_BASE_URL=https://api.xiaomimimo.com/v1
```

**Anthropic 兼容协议：**
```bash
AI_PROVIDER=anthropic
AI_API_KEY=sk-xxxxx
AI_MODEL=claude-sonnet-4-20250514
AI_BASE_URL=https://api.xiaomimimo.com/anthropic
```

## 项目结构
- `backend/main.py` - FastAPI 应用入口
- `backend/services/` - 核心业务逻辑（AI分析、新闻聚合、早报生成等）
- `backend/sources/` - 新闻源爬虫（按类别分文件）
- `frontend/src/components/` - React 组件
- `frontend/src/services/` - API 调用封装
- `data/` - SQLite 数据库文件

## 开发规范

### 代码风格
- Python: 遵循 PEP8，使用 type hints
- TypeScript: 使用严格模式，所有函数必须有返回类型
- 组件使用函数式组件 + Hooks

### 命名规范
- Python 文件: snake_case
- TypeScript 文件: PascalCase（组件）/ camelCase（工具函数）
- API 路由: /api/xxx 格式

### 提交规范
- feat: 新功能
- fix: 修复 bug
- refactor: 重构
- docs: 文档更新

## 常用命令

### 后端
```bash
cd backend && python -m uvicorn main:app --reload --port 8000
```

### 前端
```bash
cd frontend && npm run dev
```

### 运行测试
```bash
# 后端测试
python -m pytest backend/tests/ -v

# 后端测试（带覆盖率）
python -m pytest backend/tests/ --cov=backend --cov-report=term-missing

# 前端测试
cd frontend && npm test

# 前端测试（监听模式）
cd frontend && npm run test:watch
```

### 项目扫描
```bash
# 自动发现待办事项和技术债务
python scripts/discover.py

# 扫描结果会写入 memory/backlog.md
```

### 自动迭代开发
```bash
# 使用 self-loop 技能进行自动迭代开发
/self-loop

# 使用 self-discover 技能发现待办事项
/self-discover
```

## 测试体系

### 测试文件结构
```
backend/tests/
├── conftest.py              # 测试配置和 fixtures
├── unit/                    # 单元测试
│   ├── test_models.py       # 数据模型测试
│   ├── test_database.py     # 数据库操作测试
│   ├── test_sources.py      # 新闻源测试
│   ├── test_services.py     # AI 分析服务测试
│   ├── test_briefing_generator.py  # 早报生成测试
│   ├── test_news_aggregator.py     # 新闻聚合测试
│   ├── test_scheduler.py    # 定时任务测试
│   ├── test_email_sender.py # 邮件发送测试
│   └── test_push_notifier.py # 推送通知测试
└── integration/             # 集成测试
    └── test_api.py          # API 端点测试

frontend/src/
├── test/                    # 测试工具
│   ├── setup.ts             # 测试环境配置
│   ├── test-utils.tsx       # 测试工具函数
│   └── __mocks__/           # Mock 文件
└── components/
    └── __tests__/           # 组件测试
        └── NewsCard.test.tsx
```

### 测试覆盖率目标
- 核心模块（models, database）: > 95%
- 服务层（services）: > 80%
- API 层（main）: > 75%
- 前端组件: > 70%

## 注意事项
- 新闻源 API 可能不稳定，需要做好错误处理和降级
- AI API 调用需要处理超时和限流
- 数据库操作使用 async/await
- 前端 API 调用统一放在 services/ 目录
- 修改代码后运行测试验证: `python -m pytest backend/tests/ -v`
- 定期运行项目扫描: `python scripts/discover.py`
