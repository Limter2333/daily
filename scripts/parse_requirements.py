#!/usr/bin/env python3
"""
需求解析脚本 - 解析多需求输入
"""

import sys
import argparse
from typing import List
from pathlib import Path


def parse_requirements_from_string(input_str: str) -> List[str]:
    """从字符串解析需求列表"""
    # 按分号分割
    requirements = []
    for line in input_str.split(';'):
        line = line.strip()
        if line:
            requirements.append(line)
    return requirements


def parse_requirements_from_file(file_path: str) -> List[str]:
    """从文件解析需求列表"""
    path = Path(file_path)
    if not path.exists():
        print(f"错误: 文件不存在: {file_path}")
        return []

    requirements = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释
            if line and not line.startswith('#'):
                requirements.append(line)
    return requirements


def parse_requirements_interactive() -> List[str]:
    """交互式解析需求列表"""
    print("请输入需求列表（每行一个，输入空行结束）:")
    requirements = []
    while True:
        try:
            line = input("> ").strip()
            if not line:
                break
            requirements.append(line)
        except EOFError:
            break
    return requirements


def format_requirements(requirements: List[str]) -> str:
    """格式化需求列表"""
    if not requirements:
        return "无需求"

    lines = []
    for i, req in enumerate(requirements, 1):
        lines.append(f"{i}. {req}")
    return "\n".join(lines)


def generate_report(requirements: List[str], results: List[dict]) -> str:
    """生成执行报告"""
    report = []
    report.append("# Self-Multi-Loop 执行报告")
    report.append("")

    # 统计
    success_count = sum(1 for r in results if r.get('success', False))
    fail_count = len(results) - success_count

    report.append("## 执行摘要")
    report.append(f"- **总需求数**: {len(requirements)}")
    report.append(f"- **成功**: {success_count}")
    report.append(f"- **失败**: {fail_count}")
    report.append("")

    # 详细结果
    report.append("## 详细结果")
    report.append("")

    for i, (req, result) in enumerate(zip(requirements, results), 1):
        status = "✅" if result.get('success', False) else "❌"
        report.append(f"### {status} 需求 {i}/{len(requirements)}: {req}")
        report.append(f"- **状态**: {'成功' if result.get('success', False) else '失败'}")

        if result.get('error'):
            report.append(f"- **错误**: {result['error']}")

        if result.get('files'):
            report.append(f"- **变更文件**: {', '.join(result['files'])}")

        if result.get('tests_passed'):
            report.append(f"- **测试**: {result['tests_passed']} 通过")

        if result.get('commit'):
            report.append(f"- **提交**: {result['commit']}")

        report.append("")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description='解析多需求输入')
    parser.add_argument('input', nargs='?', help='需求输入（字符串或@文件路径）')
    parser.add_argument('--interactive', '-i', action='store_true', help='交互式输入')
    parser.add_argument('--format', '-f', choices=['text', 'json', 'markdown'], default='text', help='输出格式')

    args = parser.parse_args()

    # 解析需求
    requirements = []

    if args.interactive:
        requirements = parse_requirements_interactive()
    elif args.input:
        if args.input.startswith('@'):
            # 从文件读取
            file_path = args.input[1:]
            requirements = parse_requirements_from_file(file_path)
        else:
            # 从字符串解析
            requirements = parse_requirements_from_string(args.input)
    else:
        # 默认交互式
        requirements = parse_requirements_interactive()

    # 输出结果
    if args.format == 'json':
        import json
        print(json.dumps(requirements, ensure_ascii=False, indent=2))
    elif args.format == 'markdown':
        print("## 需求列表")
        print()
        for i, req in enumerate(requirements, 1):
            print(f"{i}. {req}")
    else:
        print(format_requirements(requirements))


if __name__ == '__main__':
    main()
