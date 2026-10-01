# Changelog

本文件记录 `deliverable-selfcheck` 的可见变更。格式参考
[Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Roadmap（已规划，未实现）

- 把规则集拆到外部数据文件（`rules.json` / `rules.yaml`），改规则不必改代码。
- `--fix` 预览：只提示「哪个文件名改成什么就能命中」，不自动改盘。
- 可选的平台清单拉取（需网络与凭据，默认关闭，保持零依赖离线可用）。

## [1.0.0] - 2026-10-01

首个公开版本。把 C4 里沉淀的两条真实平台坑，做成一个零依赖、可复跑、
IO 明确的提交前自检器。

### Added

- `deliverable-selfcheck` 命令行工具，入口 `deliverable_selfcheck.cli:main`。
- 交付物检查：按**文件名字面子串**匹配关键字，区分 `missing` 与 `near_miss`（近似命名告警）。
- 内容扫描：按后缀白名单扫描仓库正文中的真实凭据形态
  （`sk-` 风格密钥、GitHub Token、AWS Key、私钥块、明文凭据赋值），
  单文件上限 256 KB，二进制与超限文件自动跳过。
- 提交字段检查（`--title` / `--summary`）：额外启用「英文冒号 + 空格」规则，
  用于复现平台把 `word: word` 误判为 key/value 的整单拒收。
- 两种输出：Markdown（默认）与 `--json`；退出码 `0` READY / `1` BLOCKED / `2` 参数错误。
- `--strict`：近似命名告警也视为失败，并把「冒号 + 空格」规则扩展到仓库正文。
- `--case-sensitive`、`--no-content-check`、`--required-file`（支持注释与空行）。
- 示例：`examples/before`（会被 BLOCKED）与 `examples/after`（READY），
  一条命令复现"缺件 → 修好"的全过程。
- 测试：24 条标准库 `unittest` 用例，零依赖。
- 文档：`README.md`、`docs/USAGE.md`、`拿来说明.md` / `ATTRIBUTION.md`、
  `AI日志.md` / `AI_LOG.md`。
- 工程化：`pyproject.toml`（MIT、requires-python >= 3.9）、`LICENSE`、
  `.gitignore`、GitHub Actions CI。

### Known limitations

- 规则集来自作者个人的实测样本，不是平台规范的完整复刻；
  结论对平台版本敏感。
- 只做**文件名**与**文本字段**层面的检查，不解析二进制、不联网、不调用平台接口。
- 不替代平台校验，最终以平台返回为准。
