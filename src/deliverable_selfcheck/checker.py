"""Directory scanning and report building for deliverable-selfcheck."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from . import rules

IGNORED_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".idea"}

#: Files whose *content* is scanned for sensitive-information patterns.
SCANNABLE_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg"}

MAX_BYTES = 256 * 1024


@dataclass
class NameIssue:
    """A file that looks like it should satisfy a requirement but does not."""

    filename: str
    requirement: str
    reason: str


@dataclass
class ContentIssue:
    """A sensitive-information pattern found in a file."""

    filename: str
    rule_id: str
    severity: str
    hint: str


@dataclass
class Report:
    directory: str
    requirements: list[str]
    files: list[str] = field(default_factory=list)
    found: dict[str, list[str]] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    name_issues: list[NameIssue] = field(default_factory=list)
    content_issues: list[ContentIssue] = field(default_factory=list)
    #: 提交字段（标题 / 简介）上的告警；`filename` 位置放字段名，如 `title#1`。
    metadata_issues: list[ContentIssue] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        """READY only when nothing is missing and no blocking issue was found."""
        if self.missing:
            return False
        if any(i.severity == "block" for i in self.content_issues):
            return False
        return not any(i.severity == "block" for i in self.metadata_issues)

    @property
    def exit_code(self) -> int:
        return 0 if self.ready else 1

    @property
    def status(self) -> str:
        return "READY" if self.ready else "BLOCKED"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "directory": self.directory,
            "requirements": self.requirements,
            "summary": {
                "files": len(self.files),
                "found": len(self.found),
                "missing": len(self.missing),
                "name_issues": len(self.name_issues),
                "content_issues": len(self.content_issues),
                "metadata_issues": len(self.metadata_issues),
            },
            "found": self.found,
            "missing": self.missing,
            "name_issues": [i.__dict__ for i in self.name_issues],
            "content_issues": [i.__dict__ for i in self.content_issues],
            "metadata_issues": [i.__dict__ for i in self.metadata_issues],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        lines = [
            "# 交付物自检报告",
            "",
            f"- 目录：`{self.directory}`",
            f"- 结论：**{self.status}**",
            f"- 扫描文件：{len(self.files)} 个",
            "",
            "## 1. 交付物匹配",
            "",
        ]
        if self.missing:
            lines.append("| 缺失的交付物 | 说明 |")
            lines.append("| --- | --- |")
            for req in self.missing:
                lines.append(f"| `{req}` | 未找到任何文件名**字面包含**该关键字 |")
            lines.append("")
        else:
            lines.append("全部交付物已命中。")
            lines.append("")
        if self.found:
            lines.append("| 交付物 | 命中文件 |")
            lines.append("| --- | --- |")
            for req in self.requirements:
                hits = self.found.get(req)
                if hits:
                    lines.append(f"| `{req}` | {', '.join('`' + h + '`' for h in hits)} |")
            lines.append("")

        if self.name_issues:
            lines.append("## 2. 近似命名告警（改了就能过）")
            lines.append("")
            for issue in self.name_issues:
                lines.append(
                    f"- `{issue.filename}` 看起来想满足 `{issue.requirement}`，但{issue.reason}"
                )
            lines.append("")

        if self.content_issues:
            lines.append("## 3. 敏感信息告警")
            lines.append("")
            for issue in self.content_issues:
                tag = "阻塞" if issue.severity == "block" else "提示"
                lines.append(f"- **[{tag}]** `{issue.filename}` — {issue.hint}")
            lines.append("")
        else:
            lines.append("## 3. 敏感信息告警")
            lines.append("")
            lines.append("未发现会被平台过滤拦截的内容。")
            lines.append("")

        if self.metadata_issues:
            lines.append("## 4. 提交字段告警（标题 / 简介）")
            lines.append("")
            for issue in self.metadata_issues:
                tag = "阻塞" if issue.severity == "block" else "提示"
                lines.append(f"- **[{tag}]** `{issue.filename}` — {issue.hint}")
            lines.append("")
            lines.append(
                "> 这类告警发生在**提交字段**上，平台会做敏感信息过滤；"
                "文件名里的同类写法不受影响。"
            )
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("本报告是平台校验的近似实现，最终以平台返回为准。")
        return "\n".join(lines)


def collect_files(directory: Path) -> list[str]:
    """Return every file name under ``directory``, relative, POSIX-style."""
    out: list[str] = []
    for root, dirs, filenames in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for name in filenames:
            full = Path(root) / name
            out.append(full.relative_to(directory).as_posix())
    return sorted(out)


def scan(
    directory: str,
    requirements: list[str],
    case_sensitive: bool = False,
    check_content: bool = True,
    strict: bool = False,
    metadata_fields: dict[str, str] | None = None,
) -> Report:
    """Run every rule against ``directory`` and return a :class:`Report`.

    ``strict`` 会额外启用「冒号 + 空格」内容规则；
    ``metadata_fields`` 是标题 / 简介这类提交字段，按平台的过滤规则检查。
    """
    base = Path(directory).resolve()
    report = Report(directory=str(base), requirements=list(requirements))
    if not base.is_dir():
        report.missing = list(requirements)
        return report

    report.files = collect_files(base)
    basenames = [(f, Path(f).name) for f in report.files]

    for req in requirements:
        hits = [
            rel
            for rel, name in basenames
            if rules.match_requirement(req, name, case_sensitive=case_sensitive)
        ]
        if hits:
            report.found[req] = hits
        else:
            report.missing.append(req)
            for rel, name in basenames:
                if rules.near_miss(req, name):
                    report.name_issues.append(
                        NameIssue(
                            filename=rel,
                            requirement=req,
                            reason="关键字被多余字符拆开，无法字面命中。"
                            "去掉中间的下划线/空格即可。",
                        )
                    )

    if check_content:
        for rel, name in basenames:
            if Path(name).suffix.lower() not in SCANNABLE_SUFFIXES:
                continue
            full = base / rel
            try:
                if full.stat().st_size > MAX_BYTES:
                    continue
                text = full.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for rule_id, severity, hint in rules.scan_text(text, strict=strict):
                report.content_issues.append(
                    ContentIssue(filename=rel, rule_id=rule_id, severity=severity, hint=hint)
                )

    for field_name, value in (metadata_fields or {}).items():
        for rule_id, severity, hint in rules.scan_metadata(value):
            report.metadata_issues.append(
                ContentIssue(
                    filename=field_name, rule_id=rule_id, severity=severity, hint=hint
                )
            )
    return report
