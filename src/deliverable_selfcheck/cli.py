"""Command line interface for deliverable-selfcheck."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .checker import scan

EPILOG = """\
退出码:
  0  READY    -- 所有交付物命中，且未发现阻塞级问题
  1  BLOCKED  -- 有交付物缺失，或发现会被平台拦截的内容
  2  参数错误

示例:
  # 1) 只查交付物是否齐全
  deliverable-selfcheck --dir ./repo --required "README.md,*repo链接*,*AI日志*,*拿来说明*"

  # 2) 从文件读清单，输出 JSON 给 CI 用
  deliverable-selfcheck --dir . --required-file deliverables.txt --json

  # 3) 提交前顺手查一眼标题 / 简介会不会被敏感信息过滤拦下
  deliverable-selfcheck --dir . --required-file deliverables.txt \\
    --title "C5 GitHub Repository - deliverable-selfcheck" \\
    --summary "把提交校验的两个真实坑固化成一个零依赖自检器。"
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deliverable-selfcheck",
        description="提交前自检：确认交付物齐全、命名不会被平台的「字面子串」规则漏判。",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dir", default=".", help="待检查的目录（默认当前目录）")
    parser.add_argument(
        "--required",
        action="append",
        default=[],
        help="必需交付物关键字，逗号分隔；可重复传入，如 --required 'README.md,*AI日志*'",
    )
    parser.add_argument(
        "--required-file",
        help="从一个文本文件读取必需交付物（每行一个，或整行逗号分隔；# 开头为注释）",
    )
    parser.add_argument("--json", action="store_true", help="以 JSON 输出报告")
    parser.add_argument("--md", action="store_true", help="以 Markdown 输出报告（默认）")
    parser.add_argument(
        "--no-content-check", action="store_true", help="跳过文件内容的敏感信息扫描"
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="按大小写敏感匹配（默认不敏感）",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式：近似命名告警也视为失败，且内容扫描额外启用「冒号 + 空格」规则",
    )
    parser.add_argument(
        "--title",
        action="append",
        default=[],
        help="提交字段：项目标题（可重复）。按平台真实规则检查敏感信息误判。",
    )
    parser.add_argument(
        "--summary",
        action="append",
        default=[],
        help="提交字段：项目简介（可重复）。按平台真实规则检查敏感信息误判。",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def parse_requirements(args: argparse.Namespace) -> list[str]:
    reqs: list[str] = []
    for chunk in args.required:
        reqs.extend(part for part in (p.strip() for p in chunk.split(",")) if part)
    if args.required_file:
        with open(args.required_file, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                reqs.extend(part for part in (p.strip() for p in line.split(",")) if part)
    # de-duplicate, keep first-seen order
    seen: set[str] = set()
    unique: list[str] = []
    for req in reqs:
        if req not in seen:
            seen.add(req)
            unique.append(req)
    return unique


def collect_metadata_fields(args: argparse.Namespace) -> dict[str, str]:
    """标题 / 简介这类提交字段。"""
    fields: dict[str, str] = {}
    for i, value in enumerate(args.title or [], start=1):
        fields[f"title#{i}"] = value
    for i, value in enumerate(args.summary or [], start=1):
        fields[f"summary#{i}"] = value
    return fields


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    requirements = parse_requirements(args)
    if not requirements:
        parser.error("至少需要一个 --required 或 --required-file")

    report = scan(
        args.dir,
        requirements,
        case_sensitive=args.case_sensitive,
        check_content=not args.no_content_check,
        strict=args.strict,
        metadata_fields=collect_metadata_fields(args),
    )

    if args.json:
        print(report.to_json())
    else:
        print(report.to_markdown())

    if report.ready and args.strict and report.name_issues:
        return 1
    return report.exit_code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
