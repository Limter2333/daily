# Self-Multi-Loop 使用指南

## 简介

Self-Multi-Loop 是一个支持多需求顺序执行的工作流技能。它允许你输入多个需求，按顺序实现每个功能，每个功能完成后自动提交代码。

## 快速开始

### 1. 命令行多需求

```bash
/self-multi-loop 添加用户认证; 优化数据库查询; 添加缓存支持
```

### 2. 从文件读取

```bash
/self-multi-loop @requirements.txt
```

### 3. 交互式输入

```bash
/self-multi-loop
```

## 需求文件格式

创建一个文本文件，每行一个需求：

```txt
# 用户管理功能
添加用户注册功能
添加用户登录功能
添加用户权限管理

# 性能优化
优化数据库查询性能
添加 Redis 缓存支持
```

- 空行会被忽略
- `#` 开头的行为注释
- 每行一个需求描述

## 使用 parse_requirements.py 脚本

### 基本用法

```bash
# 从字符串解析
python scripts/parse_requirements.py "需求1; 需求2; 需求3"

# 从文件解析
python scripts/parse_requirements.py "@requirements.txt"

# 交互式输入
python scripts/parse_requirements.py --interactive
```

### 输出格式

```bash
# 文本格式（默认）
python scripts/parse_requirements.py "需求1; 需求2" --format text

# JSON 格式
python scripts/parse_requirements.py "需求1; 需求2" --format json

# Markdown 格式
python scripts/parse_requirements.py "需求1; 需求2" --format markdown
```

## 执行流程

1. **解析需求** — 将输入解析为需求列表
2. **顺序执行** — 对每个需求执行实现循环
3. **自动提交** — 每个需求完成后自动提交代码
4. **生成报告** — 所有需求完成后生成执行报告

## 示例场景

### 场景 1: 新功能开发

```bash
/self-multi-loop 添加用户认证; 添加权限管理; 添加日志记录
```

### 场景 2: 性能优化

```bash
/self-multi-loop 优化数据库查询; 添加缓存支持; 优化 API 响应
```

### 场景 3: 从项目待办列表

1. 先运行 self-discover 生成待办列表
2. 将待办列表保存到 requirements.txt
3. 执行 `/self-multi-loop @requirements.txt`

## 执行报告

执行完成后会生成报告，保存在 `memory/multi-loop-report.md`：

```markdown
# Self-Multi-Loop 执行报告

## 执行摘要
- 总需求数: 3
- 成功: 2
- 失败: 1

## 详细结果
### ✅ 需求 1/3: 添加用户认证
- 状态: 成功
- 变更文件: backend/services/auth.py
- 测试: 15 通过

### ❌ 需求 2/3: 优化数据库查询
- 状态: 失败
- 错误: 数据库连接失败
```

## 错误处理

- 单个需求失败会跳过提交，继续下一个需求
- 每个需求最多尝试 3 次修复
- 超时（15分钟/需求）会自动跳过

## 最佳实践

1. **需求描述要清晰** — 明确要实现什么功能
2. **每个需求要独立** — 避免需求之间有依赖关系
3. **需求不要太复杂** — 复杂需求拆分为多个小需求
4. **先测试再执行** — 使用小需求测试工作流

## 与现有技能的关系

- **self-loop**: 单个需求的实现循环
- **self-multi-loop**: 多需求顺序执行
- **self-discover**: 发现待处理问题
- **self-implement**: 实现阶段的核心
- **self-test**: 测试阶段的核心
- **self-fix**: 修复阶段的核心

## 常见问题

### Q: 需求之间有依赖怎么办？
A: 将依赖关系明确写在需求描述中，或者将有依赖的需求合并为一个需求。

### Q: 某个需求失败了怎么办？
A: 失败的需求会被跳过，继续执行下一个需求。执行报告会记录失败原因。

### Q: 如何重新执行失败的需求？
A: 将失败的需求单独提取出来，重新执行 `/self-multi-loop 失败的需求`。

### Q: 执行时间太长怎么办？
A: 每个需求有 15 分钟超时限制。如果需求太复杂，建议拆分为更小的需求。
