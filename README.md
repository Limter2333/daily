# 📰 每日早报晚报系统

一个自动获取财经、科技、半导体、AI等重点新闻，并生成早报晚报的智能系统。

## ✨ 功能特点

- 🌐 **多源新闻聚合**: 从东方财富、36氪、机器之心等多个来源自动采集新闻
- 🤖 **AI 智能分析**: 自动分类新闻、生成摘要、评估重要性
- 📊 **六大新闻类别**: 财经、科技、半导体、AI/机器人、消费、其他
- 📱 **PC/手机双端**: 响应式 Web 界面，随时随地查看
- ⏰ **定时推送**: 每天自动生成早报/晚报
- 📧 **多渠道推送**: 支持邮件、企业微信、钉钉推送
- 💾 **本地存储**: SQLite 数据库，数据安全私有

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- npm 或 yarn

### 1. 克隆项目

```bash
cd daily
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填入你的 AI API Key：

```bash
cp .env.example .env
# 编辑 .env 文件，填入 AI_API_KEY
```

**API 配置示例：**

```bash
# 小米 API (OpenAI 兼容协议)
AI_API_KEY=sk-xxxxx
AI_MODEL=gpt-4o
AI_BASE_URL=https://api.xiaomimimo.com/v1

# 小米 API (Anthropic 兼容协议)
AI_PROVIDER=anthropic
AI_API_KEY=sk-xxxxx
AI_MODEL=claude-sonnet-4-20250514
AI_BASE_URL=https://api.xiaomimimo.com/anthropic
```

### 3. 启动系统

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

### 4. 访问系统

- 📱 前端地址: http://localhost:5173
- 🔧 后端地址: http://localhost:8000
- 📚 API 文档: http://localhost:8000/docs

## 📁 项目结构

```
daily/
├── backend/                 # Python 后端
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # SQLite 数据库
│   ├── models.py            # 数据模型
│   ├── services/            # 业务服务
│   │   ├── ai_analyzer.py       # AI 分析服务
│   │   ├── news_aggregator.py   # 新闻聚合服务
│   │   ├── briefing_generator.py # 早报/晚报生成
│   │   ├── email_sender.py      # 邮件发送
│   │   ├── push_notifier.py     # 推送通知
│   │   └── scheduler.py         # 定时任务
│   └── sources/             # 新闻源
│       ├── finance.py           # 财经新闻源
│       ├── tech.py              # 科技新闻源
│       ├── ai_robotics.py       # AI/机器人新闻源
│       └── general.py           # 综合新闻源
├── frontend/                # React 前端
│   ├── src/
│   │   ├── components/      # React 组件
│   │   ├── services/        # API 服务
│   │   ├── types/           # TypeScript 类型
│   │   └── styles/          # 样式文件
│   └── package.json
├── data/                    # 数据目录
├── config.yaml              # 配置文件
├── requirements.txt         # Python 依赖
├── start.sh                 # Linux/Mac 启动脚本
├── start.bat                # Windows 启动脚本
└── README.md
```

## 📰 新闻源

| 类别 | 来源 | 说明 |
|------|------|------|
| 💰 财经 | 东方财富、新浪财经、华尔街见闻 | 财经快讯、市场动态 |
| 💻 科技 | 36氪、少数派 | 科技新闻、产品发布 |
| 🤖 AI/机器人 | 机器之心、量子位 | AI 技术、行业应用 |
| 📰 综合 | 知乎、今日头条、V2EX、Hacker News | 热门话题、技术社区 |

## ⚙️ 配置说明

### config.yaml

```yaml
scheduler:
  morning_time: "07:30"    # 早报时间
  evening_time: "20:00"    # 晚报时间
  aggregate_interval: 30   # 新闻聚合间隔（分钟）

ai:
  provider: "openai"       # AI 提供商
  model: "gpt-3.5-turbo"   # AI 模型

email:
  enabled: false           # 是否启用邮件
  smtp_server: "smtp.gmail.com"
  smtp_port: 587

push:
  enabled: false           # 是否启用推送
  platform: "wechat"       # 推送平台：wechat/dingtalk
```

### .env 文件

```bash
# AI API 配置（必需）
AI_API_KEY=sk-your-api-key
AI_MODEL=gpt-3.5-turbo

# 可选：自定义 API 地址
# AI_BASE_URL=https://api.openai.com/v1
```

## 📖 使用指南

### 查看新闻

1. 打开 http://localhost:5173
2. 首页显示最新新闻，按重要性排序
3. 点击分类标签筛选特定类别
4. 点击"阅读原文"查看完整文章

### 生成早报/晚报

1. 点击"早报晚报"导航
2. 选择"早报"或"晚报"标签
3. 点击"立即生成"按钮
4. 系统自动聚合新闻并生成报告

### 发送推送

1. 在"设置"页面配置邮件或 Webhook
2. 在"早报晚报"页面点击"发送推送"
3. 系统将通过配置的渠道发送

### 定时任务

系统默认配置：
- 每 30 分钟自动聚合新闻
- 每天 07:30 生成并发送早报
- 每天 20:00 生成并发送晚报

可在"设置"页面修改时间。

## 🔧 API 接口

### 新闻接口

- `GET /api/news` - 获取新闻列表
- `GET /api/news/latest` - 获取最新新闻
- `GET /api/news/{id}` - 获取新闻详情
- `GET /api/news/categories/summary` - 获取分类统计

### 早报/晚报接口

- `GET /api/briefings` - 获取早报/晚报列表
- `GET /api/briefings/latest` - 获取最新早报/晚报
- `POST /api/briefings/generate/{type}` - 生成早报/晚报

### 操作接口

- `POST /api/aggregate` - 手动触发新闻聚合
- `POST /api/send/{type}` - 手动触发发送

### 设置接口

- `GET /api/settings` - 获取设置
- `PUT /api/settings` - 更新设置

完整 API 文档请访问: http://localhost:8000/docs

## 🛠️ 开发指南

### 后端开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端开发

```bash
# 安装依赖
cd frontend
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 📝 注意事项

1. **AI API Key**: 使用 AI 分析功能需要配置 OpenAI 或兼容的 API Key
2. **新闻源稳定性**: 部分新闻源 API 可能不稳定，系统会自动降级处理
3. **数据存储**: 所有数据存储在本地 `data/daily.db` 文件中
4. **邮件配置**: 使用 Gmail 需要开启"应用专用密码"
5. **推送配置**: 企业微信和钉钉需要创建 Webhook 机器人

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
