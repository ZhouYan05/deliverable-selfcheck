"""deliverable-selfcheck 的回归测试。

零依赖：只用 Python 标准库 unittest，因此任何 Python 3.9+ 机器都能直接复跑。

    python -m unittest discover -s tests -v

（如果用 pytest，`pytest -q` 同样可运行，本文件不依赖 pytest 特有特性。）
"""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deliverable_selfcheck import rules  # noqa: E402
from deliverable_selfcheck.checker import scan  # noqa: E402
from deliverable_selfcheck.cli import main as cli_main  # noqa: E402


class MatchRequirementTest(unittest.TestCase):
    """规则 1：必需交付物按『文件名字面子串』匹配。"""

    def test_literal_hits(self):
        cases = [
            ("*AI日志*", "ZhouYan05_C5_AI日志.md", True),
            ("README.md", "README.md", True),
            ("*demo*", "my_demo.py", True),
            ("*拿来说明*", "ZhouYan05_C5_拿来说明.md", True),
            ("*repo链接*", "ZhouYan05_C5_repo链接.md", True),
        ]
        for token, name, expected in cases:
            with self.subTest(token=token, name=name):
                self.assertIs(rules.match_requirement(token, name), expected)

    def test_underscore_splits_keyword(self):
        # 关键反例：AI_工作日志 不字面包含「AI日志」
        self.assertIs(rules.match_requirement("*AI日志*", "AI_工作日志.md"), False)
        self.assertIs(rules.match_requirement("*AI日志*", "AI_LOG.md"), False)

    def test_case_sensitivity_switch(self):
        self.assertIs(rules.match_requirement("*demo*", "DEMO.md"), True)
        self.assertIs(rules.match_requirement("*demo*", "DEMO.md", case_sensitive=True), False)
        self.assertIs(rules.match_requirement("*DEMO*", "DEMO.md", case_sensitive=True), True)

    def test_near_miss(self):
        self.assertIs(rules.near_miss("*AI日志*", "AI_工作日志.md"), True)
        self.assertIs(rules.near_miss("*AI日志*", "AI_LOG.md"), False)
        self.assertIs(rules.near_miss("*AI日志*", "ZhouYan05_C5_AI日志.md"), False)


class SensitiveScanTest(unittest.TestCase):
    """规则 2：文本字段的敏感信息误判预警。"""

    def test_colon_space_is_flagged_in_metadata(self):
        # 平台真正做敏感信息过滤的是提交字段；中文键 + 冒号 + 空格同样会被判成 key/value
        codes = [h[0] for h in rules.scan_metadata("项目名: 我的自检工具")]
        self.assertIn("keyvalue_colon_space", codes)

    def test_real_rejected_title_from_c4_is_flagged(self):
        # C4 实测被平台拒单的标题形态，必须能被拦住
        codes = [
            h[0]
            for h in rules.scan_metadata("C4 技能分享与传播: deliverable-selfcheck 交付物自检器")
        ]
        self.assertIn("keyvalue_colon_space", codes)

    def test_fullwidth_colon_and_dash_are_safe(self):
        self.assertEqual(rules.scan_metadata("项目名：我的自检工具"), [])
        self.assertEqual(rules.scan_metadata("项目名 - 我的自检工具"), [])

    def test_content_scan_does_not_flag_innocent_colon(self):
        # 故意的作用域设计：正文里的 `Note: xxx`、YAML 的 `runs-on: x` 不该被误报成阻塞，
        # 否则工具会把每个正常仓库都判成 BLOCKED，自检结果就不可信了。
        self.assertEqual(rules.scan_text("Note: 这是一个普通提示"), [])
        self.assertEqual(rules.scan_text("runs-on: ubuntu-latest"), [])
        codes = [h[0] for h in rules.scan_text("Note: 这是一个普通提示", strict=True)]
        self.assertIn("keyvalue_colon_space", codes)

    def test_real_secrets_are_flagged(self):
        self.assertTrue(any(h[0] == "openai_key" for h in rules.scan_text("k = sk-abcdefghijklmnop1234")))
        self.assertTrue(any(h[0] == "github_token" for h in rules.scan_text("t=ghp_" + "a" * 30)))
        self.assertTrue(any(h[0] == "private_key_block" for h in rules.scan_text("-----BEGIN RSA PRIVATE KEY-----")))
        # 真凭据在提交字段上同样必须被拦
        self.assertTrue(any(h[0] == "openai_key" for h in rules.scan_metadata("key: sk-abcdefghijklmnop1234")))


class ScanTest(unittest.TestCase):
    """scan() 端到端。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def make(self, *names: str) -> None:
        for name in names:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("ok\n", encoding="utf-8")

    def test_ready_when_all_present(self):
        self.make("README.md", "ZhouYan05_C5_AI日志.md")
        report = scan(str(self.root), ["README.md", "*AI日志*"])
        self.assertEqual(report.status, "READY")
        self.assertEqual(report.exit_code, 0)
        self.assertEqual(report.missing, [])

    def test_blocked_when_missing(self):
        self.make("README.md")
        report = scan(str(self.root), ["README.md", "*拿来说明*"])
        self.assertEqual(report.status, "BLOCKED")
        self.assertEqual(report.exit_code, 1)
        self.assertEqual(report.missing, ["*拿来说明*"])

    def test_reports_near_miss_name(self):
        self.make("AI_工作日志与AAR.md")
        report = scan(str(self.root), ["*AI日志*"])
        self.assertEqual(report.missing, ["*AI日志*"])
        self.assertTrue(report.name_issues)
        self.assertEqual(report.name_issues[0].filename, "AI_工作日志与AAR.md")

    def test_blocks_on_real_secret_in_content(self):
        (self.root / "notes.md").write_text("key = sk-abcdefghijklmnop1234", encoding="utf-8")
        report = scan(str(self.root), ["*notes*"])
        self.assertEqual(report.status, "BLOCKED")
        self.assertTrue(report.content_issues)

    def test_colon_space_only_blocks_content_in_strict_mode(self):
        (self.root / "notes.md").write_text("标题: 演示", encoding="utf-8")
        self.assertEqual(scan(str(self.root), ["*notes*"]).status, "READY")
        self.assertEqual(scan(str(self.root), ["*notes*"], strict=True).status, "BLOCKED")

    def test_metadata_field_uses_metadata_rules(self):
        self.make("README.md")
        report = scan(
            str(self.root),
            ["README.md"],
            metadata_fields={"title#1": "C5 GitHub Repository: 自检器"},
        )
        self.assertEqual(report.status, "BLOCKED")
        self.assertEqual(len(report.metadata_issues), 1)
        self.assertEqual(report.metadata_issues[0].filename, "title#1")
        self.assertEqual(report.metadata_issues[0].rule_id, "keyvalue_colon_space")
        self.assertIn("metadata_issues", report.to_dict()["summary"])

    def test_safe_metadata_field_keeps_ready(self):
        self.make("README.md")
        report = scan(
            str(self.root),
            ["README.md"],
            metadata_fields={"title#1": "C5 GitHub Repository - 自检器", "summary#1": "把坑固化成工具。"},
        )
        self.assertEqual(report.status, "READY")
        self.assertEqual(report.metadata_issues, [])

    def test_ignores_git_and_cache_dirs(self):
        self.make(".git/README.md", "__pycache__/README.md")
        report = scan(str(self.root), ["README.md"])
        self.assertEqual(report.missing, ["README.md"])

    def test_json_output_shape(self):
        self.make("README.md")
        report = scan(str(self.root), ["README.md"])
        payload = report.to_dict()
        self.assertEqual(payload["summary"]["files"], 1)
        self.assertIn('"status": "READY"', report.to_json())


class CliTest(unittest.TestCase):
    """CLI 契约：退出码 0=READY / 1=BLOCKED / 2=参数错误。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        (self.root / "README.md").write_text("ok\n", encoding="utf-8")

    def run_cli(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli_main(argv)
        return code, buf.getvalue()

    def test_exit_codes_and_markdown(self):
        code, out = self.run_cli(["--dir", str(self.root), "--required", "README.md"])
        self.assertEqual(code, 0)
        self.assertIn("READY", out)

        code, out = self.run_cli(["--dir", str(self.root), "--required", "*AI日志*"])
        self.assertEqual(code, 1)
        self.assertIn("BLOCKED", out)

    def test_json_mode(self):
        code, out = self.run_cli(["--dir", str(self.root), "--required", "README.md", "--json"])
        self.assertEqual(code, 0)
        self.assertTrue(out.lstrip().startswith("{"))

    def test_unsafe_title_field_is_blocked(self):
        code, out = self.run_cli(
            [
                "--dir",
                str(self.root),
                "--required",
                "README.md",
                "--title",
                "C5 GitHub Repository: 自检器",
            ]
        )
        self.assertEqual(code, 1)
        self.assertIn("BLOCKED", out)
        self.assertIn("提交字段", out)

    def test_safe_title_field_passes(self):
        code, _ = self.run_cli(
            [
                "--dir",
                str(self.root),
                "--required",
                "README.md",
                "--title",
                "C5 GitHub Repository - 自检器",
            ]
        )
        self.assertEqual(code, 0)

    def test_strict_mode_flags_colon_in_content(self):
        (self.root / "notes.md").write_text("标题: 演示", encoding="utf-8")
        code, _ = self.run_cli(
            ["--dir", str(self.root), "--required", "*notes*", "--strict"]
        )
        self.assertEqual(code, 1)

    def test_missing_required_is_arg_error(self):
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli(["--dir", str(self.root)])
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
