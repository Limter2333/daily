# 项目待办事项 — 2026-08-23

## 📊 项目概览
- **Python 文件**: 36 个
- **TypeScript 文件**: 14 个
- **TODO/FIXME**: 0 个
- **安全问题**: 0 个

## 🔴 高优先级 (必须修复)

### 1. [测试] backend\services\ai_analyzer.py:0 ✅ 已完成
- **问题**: 缺少单元测试: ai_analyzer.py
- **影响**: 代码变更无法自动验证
- **修复**: 创建测试文件: backend\tests\unit\test_ai_analyzer.py
- **状态**: 覆盖率从 64% 提升到 99%，新增 15 个测试

### 2. [安全] .\daily_briefing.py:43
- **问题**: 使用 os.system() 函数
- **影响**: 代码注入风险
- **修复**: 使用更安全的替代方案

## 🟡 中优先级 (建议修复)

### 1. [质量] .\daily_briefing.py:72
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 2. [质量] .\daily_briefing.py:152
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 3. [质量] .\daily_briefing.py:178
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 4. [质量] .\daily_briefing.py:204
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 5. [质量] .\daily_briefing.py:230
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 6. [质量] .\daily_briefing.py:256
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 7. [质量] .\daily_briefing.py:279
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 8. [质量] .\daily_briefing.py:676
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 9. [质量] .\backend\services\ai_analyzer.py:81
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 10. [质量] .\backend\services\ai_analyzer.py:224
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 11. [质量] .\backend\services\email_sender.py:58
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 12. [质量] .\backend\services\push_notifier.py:38
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 13. [质量] .\backend\services\scheduler.py:121
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 14. [质量] .\backend\services\scheduler.py:147
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 15. [质量] .\backend\services\scheduler.py:173
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 16. [质量] .\backend\sources\ai_robotics.py:70
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 17. [质量] .\backend\sources\ai_robotics.py:110
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 18. [质量] .\backend\sources\base.py:41
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 19. [质量] .\backend\sources\base.py:66
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 20. [质量] .\backend\sources\base.py:76
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 21. [质量] .\backend\sources\finance.py:73
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 22. [质量] .\backend\sources\finance.py:112
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 23. [质量] .\backend\sources\finance.py:147
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 24. [质量] .\backend\sources\general.py:68
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 25. [质量] .\backend\sources\general.py:98
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 26. [质量] .\backend\sources\general.py:127
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 27. [质量] .\backend\sources\general.py:160
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 28. [质量] .\backend\sources\tech.py:65
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 29. [质量] .\backend\sources\tech.py:103
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 30. [质量] .\scripts\discover.py:199
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 31. [质量] .\scripts\discover.py:275
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 32. [质量] .\scripts\discover.py:347
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 33. [质量] .\scripts\discover.py:377
- **问题**: 捕获过于宽泛的 Exception
- **影响**: 可能隐藏其他错误
- **修复**: 捕获具体的异常类型

### 34. [测试] frontend\src\components\BriefingView.tsx:0
- **问题**: 缺少组件测试: BriefingView.tsx
- **影响**: UI 组件行为未验证
- **修复**: 创建测试文件: frontend\src\components\__tests__\BriefingView.test.tsx

### 35. [测试] frontend\src\components\Dashboard.tsx:0
- **问题**: 缺少组件测试: Dashboard.tsx
- **影响**: UI 组件行为未验证
- **修复**: 创建测试文件: frontend\src\components\__tests__\Dashboard.test.tsx

### 36. [测试] frontend\src\components\Settings.tsx:0
- **问题**: 缺少组件测试: Settings.tsx
- **影响**: UI 组件行为未验证
- **修复**: 创建测试文件: frontend\src\components\__tests__\Settings.test.tsx

### 37. [测试] backend\main.py:0
- **问题**: 测试覆盖率低: 78.5%
- **影响**: 代码未充分测试
- **修复**: 补充单元测试提高覆盖率

### 38. [测试] backend\services\ai_analyzer.py:0 ✅ 已完成
- **问题**: 测试覆盖率低: 63.5%
- **影响**: 代码未充分测试
- **修复**: 补充单元测试提高覆盖率
- **状态**: 覆盖率提升到 99%，新增 15 个测试

### 39. [测试] backend\sources\ai_robotics.py:0 ✅ 已完成
- **问题**: 测试覆盖率低: 19.4%
- **影响**: 代码未充分测试
- **修复**: 补充单元测试提高覆盖率
- **状态**: 覆盖率提升到 92%，新增 8 个测试

### 40. [测试] backend\sources\finance.py:0 ✅ 已完成
- **问题**: 测试覆盖率低: 16.7%
- **影响**: 代码未充分测试
- **修复**: 补充单元测试提高覆盖率
- **状态**: 覆盖率提升到 91%，新增 8 个测试

### 41. [测试] backend\sources\general.py:0 ✅ 已完成
- **问题**: 测试覆盖率低: 14.9%
- **影响**: 代码未充分测试
- **修复**: 补充单元测试提高覆盖率
- **状态**: 覆盖率提升到 89%，新增 13 个测试

### 42. [测试] backend\sources\tech.py:0 ✅ 已完成
- **问题**: 测试覆盖率低: 21.1%
- **影响**: 代码未充分测试
- **修复**: 补充单元测试提高覆盖率
- **状态**: 覆盖率提升到 93%，新增 7 个测试

## 📈 问题统计
- 高优先级: 2 个 (1 个已完成)
- 中优先级: 42 个 (9 个已完成)
- 低优先级: 0 个
- 总计: 44 个 (10 个已完成)

## ✅ 已完成项目
1. ai_analyzer.py 测试补充 (覆盖率 64% → 99%)
2. sources/ai_robotics.py 测试补充 (覆盖率 19% → 92%)
3. sources/finance.py 测试补充 (覆盖率 17% → 91%)
4. sources/general.py 测试补充 (覆盖率 15% → 89%)
5. sources/tech.py 测试补充 (覆盖率 21% → 93%)
6. AI 分析器 AI 功能测试 (新增 15 个测试)
7. 新闻源集成测试 (新增 40 个测试)
