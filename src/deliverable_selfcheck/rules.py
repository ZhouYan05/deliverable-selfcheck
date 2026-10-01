"""Rule definitions for deliverable-selfcheck.

Two rule families live here.  Both were reverse-engineered from the *real*
behaviour observed while submitting challenges on the EduSeed platform.

1. ``normalize_requirement`` / ``match_requirement`` reproduce how a
   ``requiredDeliverables`` token is matched against a file name.

   The platform does **not** do fuzzy matching.  A token such as ``*AI日志*``
   has its surrounding ``*`` stripped and is then matched as a *literal
   substring* of the file name.  ``AI_工作日志.md`` therefore FAILS the token
   ``*AI日志*``: the underscore physically separates the two characters, so the
   literal byte sequence "AI日志" never appears in the name.

2. ``scan_text`` flags content that the platform's sensitive-information
   filter rejects.  The interesting case is ``word: word`` inside a title or a
   summary: the filter reads an ASCII colon followed by a space as a
   key / value pair and refuses the whole submission, even when the value is a
   perfectly innocent Chinese project description.

Nothing here is a substitute for the platform's own validation -- it is a fast,
deterministic approximation you can run locally before you submit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# --------------------------------------------------------------------------
# Rule family 1 -- deliverable name matching
# --------------------------------------------------------------------------


def normalize_requirement(token: str) -> str:
    """Return the literal needle a ``requiredDeliverables`` token matches on.

    >>> normalize_requirement("*AI日志*")
    'AI日志'
    >>> normalize_requirement("README.md")
    'README.md'
    """
    return token.strip().strip("*").strip()


def match_requirement(token: str, filename: str, case_sensitive: bool = False) -> bool:
    """True when ``filename`` satisfies the requirement ``token``."""
    needle = normalize_requirement(token)
    if not needle:
        return False
    if case_sensitive:
        return needle in filename
    return needle.casefold() in filename.casefold()


def near_miss(token: str, filename: str) -> bool:
    """Detect the ``AI_日志`` trap.

    Returns True when a file name contains every character of the needle, in
    order, but with extra characters inserted between them -- the classic
    "looks right, fails the literal match" mistake.
    """
    needle = normalize_requirement(token)
    if len(needle) < 2:
        return False
    if match_requirement(token, filename):
        return False
    pos = 0
    for ch in filename:
        if pos < len(needle) and ch == needle[pos]:
            pos += 1
    return pos == len(needle)


# --------------------------------------------------------------------------
# Rule family 2 -- sensitive-information scan
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class TextRule:
    """One pattern the platform's sensitive-information filter rejects."""

    rule_id: str
    pattern: re.Pattern[str]
    severity: str  # "block" | "warn"
    hint: str


#: 真凭据：无论扫哪里都必须拦截。
SECRET_RULES: tuple[TextRule, ...] = (
    TextRule(
        "openai_key",
        re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}"),
        "block",
        "疑似 OpenAI 风格密钥（sk- 开头），必须移除或改成占位符。",
    ),
    TextRule(
        "github_token",
        re.compile(r"\b(ghp_|gho_|ghs_|github_pat_)[A-Za-z0-9_]{20,}"),
        "block",
        "疑似 GitHub Token，必须移除；泄露后请到 GitHub 设置里作废。",
    ),
    TextRule(
        "aws_key",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "block",
        "疑似 AWS Access Key ID，必须移除。",
    ),
    TextRule(
        "private_key_block",
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        "block",
        "疑似私钥文件内容，绝对不能提交。",
    ),
    TextRule(
        "generic_secret_assign",
        re.compile(
            r"\b(api[_-]?key|access[_-]?token|secret|password|passwd)\b\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{8,}",
            re.IGNORECASE,
        ),
        "block",
        "疑似明文凭据赋值，必须换成占位符（如 <YOUR_API_KEY>）。",
    ),
)

#: `word: word` 陷阱：平台把「英文冒号 + 空格」读成 key/value 形态，
#: 即使 value 是中文项目名，整单也会被拒。
#: 注意关键字**不限于**英文字母键：实测 `C4 技能分享与传播: deliverable-...`
#: 这种「中文 + 冒号 + 空格」同样会被拦，所以这里用宽匹配。
COLON_SPACE_RULES: tuple[TextRule, ...] = (
    TextRule(
        "keyvalue_colon_space",
        re.compile(r"\S:\s+\S"),
        "block",
        "「冒号 + 空格」会被平台误判为「密钥/key-value」形态，整单会被拒。"
        "把英文冒号换成破折号「-」或全角冒号「：」即可通过。",
    ),
)

#: 扫描仓库**文件内容**时使用的规则：只拦真凭据。
#: 理由：平台真正做敏感信息过滤的是提交字段，不是仓库正文；
#: 无差别扫正文会把 YAML 的 `runs-on: ubuntu-latest`、文档里的 `Note: xxx`
#: 全部误报成阻塞，反而让工具失去可信度。
CONTENT_RULES: tuple[TextRule, ...] = SECRET_RULES

#: `--strict` 下的内容规则：额外启用「冒号 + 空格」规则（误报较多，按需开启）。
STRICT_CONTENT_RULES: tuple[TextRule, ...] = COLON_SPACE_RULES + SECRET_RULES

#: 扫描**提交字段**（标题 / 简介）：这两组规则同时生效。
METADATA_RULES: tuple[TextRule, ...] = COLON_SPACE_RULES + SECRET_RULES


def _scan(text: str, active: tuple[TextRule, ...]) -> list[tuple[str, str, str]]:
    hits: list[tuple[str, str, str]] = []
    for rule in active:
        if rule.pattern.search(text):
            hits.append((rule.rule_id, rule.severity, rule.hint))
    return hits


def scan_text(text: str, strict: bool = False) -> list[tuple[str, str, str]]:
    """扫描**文件内容**。

    默认只拦真凭据（``CONTENT_RULES``）；``strict=True`` 时额外启用
    「冒号 + 空格」规则。Same input -> same output；无网络、无模型、无随机。
    """
    return _scan(text, STRICT_CONTENT_RULES if strict else CONTENT_RULES)


def scan_metadata(text: str) -> list[tuple[str, str, str]]:
    """扫描**提交字段**（标题 / 简介），两组规则同时生效。

    这是最贴近平台真实行为的一次检查：平台的误判就发生在这些字段上。
    """
    return _scan(text, METADATA_RULES)
