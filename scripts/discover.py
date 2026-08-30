#!/usr/bin/env python3
"""
Self-Discover 自动扫描脚本
自动发现项目中的待办事项、技术债务、缺失测试等
"""

import os
import re
import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

# 设置标准输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class Priority(Enum):
    """优先级枚举"""
    HIGH = "🔴 高"
    MEDIUM = "🟡 中"
    LOW = "🟢 低"


class Category(Enum):
    """类别枚举"""
    SECURITY = "安全"
    TEST = "测试"
    QUALITY = "质量"
    DOC = "文档"
    PERF = "优化"
    STYLE = "风格"


@dataclass
class Issue:
    """问题数据类"""
    priority: Priority
    category: Category
    file: str
    line: int
    description: str
    impact: str
    fix: str


class ProjectScanner:
    """项目扫描器"""

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.issues: List[Issue] = []
        self.stats = {
            "total_py_files": 0,
            "total_ts_files": 0,
            "todo_count": 0,
            "security_issues": 0,
            "test_coverage": {},
        }

    def scan_all(self) -> List[Issue]:
        """执行完整扫描"""
        print("🔍 开始项目扫描...")

        self._scan_structure()
        self._scan_code_quality()
        self._scan_tests()
        self._scan_security()
        self._scan_dependencies()

        # 按优先级排序
        priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        self.issues.sort(key=lambda x: priority_order[x.priority])

        return self.issues

    def _scan_structure(self):
        """扫描项目结构"""
        print("📁 扫描项目结构...")

        # 统计文件
        for root, dirs, files in os.walk(self.root_dir):
            # 跳过不需要的目录
            if any(skip in root for skip in ['node_modules', '__pycache__', '.git', 'htmlcov']):
                continue

            for file in files:
                if file.endswith('.py'):
                    self.stats["total_py_files"] += 1
                elif file.endswith(('.ts', '.tsx')):
                    self.stats["total_ts_files"] += 1

        # 检查目录结构
        required_dirs = [
            ("backend/tests", "后端测试目录"),
            ("frontend/src/test", "前端测试目录"),
            ("memory", "记忆目录"),
        ]

        for dir_path, desc in required_dirs:
            if not (self.root_dir / dir_path).exists():
                self.issues.append(Issue(
                    priority=Priority.MEDIUM,
                    category=Category.QUALITY,
                    file=dir_path,
                    line=0,
                    description=f"缺少{desc}",
                    impact="项目结构不完整",
                    fix=f"创建目录: mkdir -p {dir_path}"
                ))

    def _scan_code_quality(self):
        """扫描代码质量"""
        print("🔍 扫描代码质量...")

        # 扫描 TODO/FIXME
        todo_pattern = re.compile(r'TODO|FIXME|HACK|XXX', re.IGNORECASE)
        empty_except_pattern = re.compile(r'except\s*:')
        broad_except_pattern = re.compile(r'except\s+Exception')

        for root, dirs, files in os.walk(self.root_dir):
            if any(skip in root for skip in ['node_modules', '__pycache__', '.git', 'htmlcov']):
                continue

            for file in files:
                if not file.endswith('.py'):
                    continue

                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    for i, line in enumerate(lines, 1):
                        stripped_line = line.strip()

                        # 跳过注释行和字符串中的内容
                        if stripped_line.startswith('#') or stripped_line.startswith('"') or stripped_line.startswith("'"):
                            continue

                        # 跳过测试文件中的 TODO
                        if 'test' in filepath.lower():
                            continue

                        # TODO/FIXME - 只匹配真正的注释
                        if todo_pattern.search(line) and '#' in line:
                            # 提取注释部分
                            comment_part = line.split('#')[1] if '#' in line else ''
                            if todo_pattern.search(comment_part):
                                self.stats["todo_count"] += 1
                                self.issues.append(Issue(
                                    priority=Priority.LOW,
                                    category=Category.QUALITY,
                                    file=filepath,
                                    line=i,
                                    description=f"TODO/FIXME 注释: {comment_part.strip()[:60]}",
                                    impact="待办事项未完成",
                                    fix="完成待办事项或移除注释"
                                ))

                        # 空 except - 只匹配真正的空 except 块
                        if empty_except_pattern.search(line):
                            # 检查下一行是否也是空的或只有 pass
                            if i < len(lines):
                                next_line = lines[i].strip() if i < len(lines) else ''
                                if next_line == 'pass' or next_line == '' or next_line.startswith('#'):
                                    self.issues.append(Issue(
                                        priority=Priority.HIGH,
                                        category=Category.QUALITY,
                                        file=filepath,
                                        line=i,
                                        description="空的 except 块",
                                        impact="错误被静默吞掉，难以调试",
                                        fix="添加具体的异常类型和日志记录"
                                    ))

                        # 过于宽泛的异常捕获 - 排除合理的使用场景
                        if broad_except_pattern.search(line):
                            # 检查是否在合理的位置（如顶层错误处理）
                            if 'main' in filepath or 'app' in filepath.lower():
                                # 在主程序或应用入口的异常捕获可能是合理的
                                pass
                            else:
                                self.issues.append(Issue(
                                    priority=Priority.MEDIUM,
                                    category=Category.QUALITY,
                                    file=filepath,
                                    line=i,
                                    description="捕获过于宽泛的 Exception",
                                    impact="可能隐藏其他错误",
                                    fix="捕获具体的异常类型"
                                ))

                except Exception as e:
                    print(f"  ⚠️ 无法读取 {filepath}: {e}")

    def _scan_tests(self):
        """扫描测试覆盖"""
        print("🧪 扫描测试覆盖...")

        # 检查后端服务测试
        services_dir = self.root_dir / "backend" / "services"
        tests_dir = self.root_dir / "backend" / "tests" / "unit"

        if services_dir.exists():
            for service_file in services_dir.glob("*.py"):
                if service_file.name == "__init__.py":
                    continue

                test_file = tests_dir / f"test_{service_file.name}"
                if not test_file.exists():
                    self.issues.append(Issue(
                        priority=Priority.HIGH,
                        category=Category.TEST,
                        file=str(service_file),
                        line=0,
                        description=f"缺少单元测试: {service_file.name}",
                        impact="代码变更无法自动验证",
                        fix=f"创建测试文件: {test_file}"
                    ))

        # 检查前端组件测试
        components_dir = self.root_dir / "frontend" / "src" / "components"
        component_tests_dir = components_dir / "__tests__"

        if components_dir.exists():
            for component_file in components_dir.glob("*.tsx"):
                test_file = component_tests_dir / f"{component_file.stem}.test.tsx"
                if not test_file.exists():
                    self.issues.append(Issue(
                        priority=Priority.MEDIUM,
                        category=Category.TEST,
                        file=str(component_file),
                        line=0,
                        description=f"缺少组件测试: {component_file.name}",
                        impact="UI 组件行为未验证",
                        fix=f"创建测试文件: {test_file}"
                    ))

        # 尝运行覆盖率
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "backend/tests/", "--cov=backend", "--cov-report=json"],
                capture_output=True,
                text=True,
                cwd=self.root_dir,
                timeout=60
            )

            if result.returncode == 0:
                # 解析覆盖率报告
                coverage_file = self.root_dir / "coverage.json"
                if coverage_file.exists():
                    with open(coverage_file) as f:
                        cov_data = json.load(f)

                    for file_path, data in cov_data.get("files", {}).items():
                        pct = data.get("summary", {}).get("percent_covered", 0)
                        if pct < 80 and "test" not in file_path and "__init__" not in file_path:
                            self.stats["test_coverage"][file_path] = pct
                            self.issues.append(Issue(
                                priority=Priority.MEDIUM,
                                category=Category.TEST,
                                file=file_path,
                                line=0,
                                description=f"测试覆盖率低: {pct:.1f}%",
                                impact="代码未充分测试",
                                fix="补充单元测试提高覆盖率"
                            ))
        except Exception as e:
            print(f"  ⚠️ 无法运行覆盖率分析: {e}")

    def _scan_security(self):
        """扫描安全问题"""
        print("🔒 扫描安全问题...")

        # 硬编码密钥模式
        secret_patterns = [
            (re.compile(r'password\s*=\s*["\'][^"\']+["\']'), "硬编码密码"),
            (re.compile(r'api_key\s*=\s*["\'][^"\']+["\']'), "硬编码 API Key"),
            (re.compile(r'secret\s*=\s*["\'][^"\']+["\']'), "硬编码 Secret"),
            (re.compile(r'token\s*=\s*["\'][^"\']+["\']'), "硬编码 Token"),
        ]

        # 不安全的函数
        unsafe_patterns = [
            (re.compile(r'eval\s*\('), "使用 eval() 函数"),
            (re.compile(r'exec\s*\('), "使用 exec() 函数"),
            (re.compile(r'os\.system\s*\('), "使用 os.system() 函数"),
        ]

        for root, dirs, files in os.walk(self.root_dir):
            if any(skip in root for skip in ['node_modules', '__pycache__', '.git', 'htmlcov']):
                continue

            for file in files:
                if not file.endswith(('.py', '.ts', '.tsx')):
                    continue

                filepath = os.path.join(root, file)

                # 跳过测试文件、示例文件和脚本文件
                if 'test' in filepath or '.example' in filepath or 'scripts' in filepath:
                    continue

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    for i, line in enumerate(lines, 1):
                        # 跳过注释
                        if line.strip().startswith('#'):
                            continue

                        # 检查硬编码密钥
                        for pattern, desc in secret_patterns:
                            if pattern.search(line):
                                self.stats["security_issues"] += 1
                                self.issues.append(Issue(
                                    priority=Priority.HIGH,
                                    category=Category.SECURITY,
                                    file=filepath,
                                    line=i,
                                    description=f"{desc}: {line.strip()[:60]}",
                                    impact="敏感信息泄露风险",
                                    fix="使用环境变量或配置文件"
                                ))

                        # 检查不安全的函数
                        for pattern, desc in unsafe_patterns:
                            if pattern.search(line):
                                self.issues.append(Issue(
                                    priority=Priority.HIGH,
                                    category=Category.SECURITY,
                                    file=filepath,
                                    line=i,
                                    description=f"{desc}",
                                    impact="代码注入风险",
                                    fix="使用更安全的替代方案"
                                ))

                except Exception as e:
                    print(f"  ⚠️ 无法读取 {filepath}: {e}")

    def _scan_dependencies(self):
        """扫描依赖"""
        print("📦 扫描依赖...")

        # 检查 requirements.txt
        req_file = self.root_dir / "requirements.txt"
        if req_file.exists():
            try:
                result = subprocess.run(
                    ["pip", "list", "--outdated", "--format=json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    outdated = json.loads(result.stdout)
                    for pkg in outdated[:5]:  # 只报告前5个
                        self.issues.append(Issue(
                            priority=Priority.LOW,
                            category=Category.PERF,
                            file="requirements.txt",
                            line=0,
                            description=f"过时的依赖: {pkg['name']} ({pkg['version']} -> {pkg['latest_version']})",
                            impact="可能缺少安全更新或新功能",
                            fix=f"pip install --upgrade {pkg['name']}"
                        ))
            except Exception as e:
                print(f"  ⚠️ 无法检查依赖: {e}")

    def generate_report(self) -> str:
        """生成 Markdown 报告"""
        report = []
        report.append(f"# 项目待办事项 — {datetime.now().strftime('%Y-%m-%d')}")
        report.append("")

        # 项目概览
        report.append("## 📊 项目概览")
        report.append(f"- **Python 文件**: {self.stats['total_py_files']} 个")
        report.append(f"- **TypeScript 文件**: {self.stats['total_ts_files']} 个")
        report.append(f"- **TODO/FIXME**: {self.stats['todo_count']} 个")
        report.append(f"- **安全问题**: {self.stats['security_issues']} 个")
        report.append("")

        # 按优先级分组
        high_issues = [i for i in self.issues if i.priority == Priority.HIGH]
        medium_issues = [i for i in self.issues if i.priority == Priority.MEDIUM]
        low_issues = [i for i in self.issues if i.priority == Priority.LOW]

        # 高优先级
        if high_issues:
            report.append("## 🔴 高优先级 (必须修复)")
            report.append("")
            for i, issue in enumerate(high_issues, 1):
                report.append(f"### {i}. [{issue.category.value}] {issue.file}:{issue.line}")
                report.append(f"- **问题**: {issue.description}")
                report.append(f"- **影响**: {issue.impact}")
                report.append(f"- **修复**: {issue.fix}")
                report.append("")

        # 中优先级
        if medium_issues:
            report.append("## 🟡 中优先级 (建议修复)")
            report.append("")
            for i, issue in enumerate(medium_issues, 1):
                report.append(f"### {i}. [{issue.category.value}] {issue.file}:{issue.line}")
                report.append(f"- **问题**: {issue.description}")
                report.append(f"- **影响**: {issue.impact}")
                report.append(f"- **修复**: {issue.fix}")
                report.append("")

        # 低优先级
        if low_issues:
            report.append("## 🟢 低优先级 (可选优化)")
            report.append("")
            for i, issue in enumerate(low_issues, 1):
                report.append(f"### {i}. [{issue.category.value}] {issue.file}:{issue.line}")
                report.append(f"- **问题**: {issue.description}")
                report.append(f"- **影响**: {issue.impact}")
                report.append(f"- **修复**: {issue.fix}")
                report.append("")

        # 统计
        report.append("## 📈 问题统计")
        report.append(f"- 高优先级: {len(high_issues)} 个")
        report.append(f"- 中优先级: {len(medium_issues)} 个")
        report.append(f"- 低优先级: {len(low_issues)} 个")
        report.append(f"- 总计: {len(self.issues)} 个")
        report.append("")

        return "\n".join(report)


def main():
    """主函数"""
    scanner = ProjectScanner()
    issues = scanner.scan_all()

    # 生成报告
    report = scanner.generate_report()

    # 写入文件
    output_file = Path("memory/backlog.md")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✅ 扫描完成！发现 {len(issues)} 个问题")
    print(f"📄 报告已写入: {output_file}")

    # 打印摘要
    high_count = len([i for i in issues if i.priority == Priority.HIGH])
    medium_count = len([i for i in issues if i.priority == Priority.MEDIUM])
    low_count = len([i for i in issues if i.priority == Priority.LOW])

    print(f"\n📊 问题摘要:")
    print(f"  🔴 高优先级: {high_count}")
    print(f"  🟡 中优先级: {medium_count}")
    print(f"  🟢 低优先级: {low_count}")


if __name__ == "__main__":
    main()
