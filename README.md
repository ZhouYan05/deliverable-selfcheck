# deliverable-selfcheck

> 提交前 30 秒自检：交付物齐不齐、文件名会不会被平台漏判、提交字段会不会被敏感信息过滤拦下。

**零依赖 · 纯 Python 标准库 · 判定确定性 · 退出码可进 CI**

- 仓库地址：https://github.com/ZhouYan05/deliverable-selfcheck
- 许可证：[MIT](LICENSE)
- 适用场景：任何「按关键字检查交付物是否齐全」的提交场景（作业、比赛、内部交付），不绑定某个具体平台。

---

## 它解决什么问题

这不是一个「通用文件检查器」。它是把两个**真实踩过的坑**固化成了可复跑的工具。

### 坑 1：关键字是「文件名字面子串」匹配，不是模糊匹配

平台校验交付物时，拿关键字去文件名里找**连续出现的字面片段**。于是：

| 关键字 | 文件名 | 结果 |
| --- | --- | --- |
| `*AI日志*` | `AI日志.md` | ✅ 命中 |
| `*AI日志*` | `AI_工作日志与AAR.md` | ❌ **不命中**（下划线把「AI」和「日志」劈开了） |
| `*AI日志*` | `AI_LOG.md` | ❌ 不命中（英文名不含中文四字） |

真实代价：交付物齐全，但因为一个下划线被判「缺件」，触发 red flag，交付物完整性直接掉到 5/15 上限。

### 坑 2：提交字段里的「英文冒号 + 空格」会被当成密钥形态

提交标题/简介时，敏感信息过滤器会把 `word: word` 读成 key/value 形态并整单拒收，**即使 value 只是中文项目名**：

```text
字段「projectTitle」提交内容疑似包含敏感信息（密钥/Token（sk- 或 api key 形态））。请脱敏后重新提交。
```

真实的被拒标题形态（把冒号换成破折号即可通过）：

```text
C4 技能分享与传播: deliverable-selfcheck 交付物自检器
```

---

## 安装

```bash
# 方式一 · 装成命令行工具（推荐）
python -m pip install -e .      # 开发 / 自用：可编辑安装
# 或
pipx install .                  # 想在任意目录直接敲 deliverable-selfcheck
```

装好后：

```bash
deliverable-selfcheck --dir . --required "README.md,*AI日志*"
```

---

也可以**不安装**直接跑。本包是 `src/` 布局（`pyproject.toml` 里 `where = ["src"]`），
所以不安装时**必须把 `src` 加进模块搜索路径**，否则会报 `No module named deliverable_selfcheck`：

```bash
# macOS / Linux
PYTHONPATH=src python -m deliverable_selfcheck --dir . --required "README.md"

# Windows PowerShell
$env:PYTHONPATH="src"; python -m deliverable_selfcheck --dir . --required "README.md"

# Windows CMD
set PYTHONPATH=src && python -m deliverable_selfcheck --dir . --required "README.md"
```

连环境变量也不想设？那就跑测试——`tests/test_checker.py` 会自己把 `src` 插进 `sys.path`：

```bash
python -m unittest discover -s tests -v
```

要求：Python **3.9+**，无第三方依赖，不需要联网。

---

## 快速开始

```bash
# 1) 只查交付物是否齐全（关键字逗号分隔）
deliverable-selfcheck --dir ./repo --required "README.md,*repo链接*,*AI日志*,*拿来说明*"

# 2) 从文件读清单，输出 JSON 给 CI 消费
deliverable-selfcheck --dir . --required-file examples/required_c5.txt --json

# 3) 提交前顺手查一眼标题/简介会不会被敏感信息过滤拦下
deliverable-selfcheck --dir . --required "README.md" \
  --title "C5 GitHub Repository - deliverable-selfcheck" \
  --summary "把提交校验的两个真实坑固化成一个零依赖自检器。"

# 4) 复现本仓库自带的 before/after 对照
deliverable-selfcheck --dir examples/before --required "README.md,*repo链接*,*AI日志*,*拿来说明*"
deliverable-selfcheck --dir examples/after  --required "README.md,*repo链接*,*AI日志*,*拿来说明*"
```

`examples/before` 的真实输出（缺件 + 近似命名告警）：

```text
- 结论：**BLOCKED**
| 缺失的交付物 | 说明 |
| `README.md` | 未找到任何文件名**字面包含**该关键字 |
...
## 2. 近似命名告警（改了就能过）
- `AI_工作日志与AAR.md` 看起来想满足 `*AI日志*`，但关键字被多余字符拆开，无法字面命中。
```

`examples/after` 的真实输出：

```text
- 结论：**READY**
全部交付物已命中。
```

---

## 退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | READY：交付物全部命中，且没有阻塞级内容告警 |
| `1` | BLOCKED：有交付物缺失，或发现会被平台拦截的内容 |
| `2` | 参数错误（例如没有给任何 `--required`） |

`--strict` 会让「近似命名告警」也返回 1。

---

## 规则作用域（设计的核心取舍）

规则不是一把梭地扫全仓库，而是按「平台真正会检查什么」分层的：

| 扫描对象 | 启用的规则 | 为什么 |
| --- | --- | --- |
| 仓库**文件内容**（`.md/.txt/.yaml/.toml/...`） | 只有真凭据：`sk-` 风格密钥、GitHub Token、AWS Key、私钥块、明文凭据赋值 | 平台做敏感信息过滤的是**提交字段**，不是仓库正文。无差别扫正文会把 YAML 的 `runs-on: ubuntu-latest`、文档里的 `Note: xxx` 全部误报成阻塞，工具立刻失去可信度 |
| **提交字段**（`--title` / `--summary`） | 真凭据 + 「冒号 + 空格」key-value 形态 | 误判就发生在这里，中文键同样中招 |
| `--strict` 下的文件内容 | 额外启用「冒号 + 空格」规则 | 给「想把整段文本当提交字段来审」的场景留的口子，默认关闭，因为误报多 |

这条取舍是被测试钉住的：`tests/test_checker.py` 里既有一条「中文标题带冒号必须 BLOCKED」，也有一条「正文里的 `Note: xxx` 不许误报」。

---

## 项目结构

```text
deliverable-selfcheck/
├── src/deliverable_selfcheck/
│   ├── rules.py       # 关键字匹配、近似命名判定、文本规则（按作用域分组）
│   ├── checker.py     # 目录扫描 + 报告对象（Markdown / JSON 两种输出）
│   ├── cli.py         # 命令行入口与退出码契约
│   └── __main__.py    # python -m deliverable_selfcheck
├── tests/test_checker.py   # 24 条回归测试，标准库 unittest，零依赖
├── examples/          # before/after 对照样本 + 清单样例
├── docs/USAGE.md      # 详细用法、CI 集成、FAQ
└── .github/workflows/ci.yml
```

---

## 测试

```bash
python -m unittest discover -s tests -v
```

当前：**24 条测试全部通过**（Python 3.12，耗时 0.03s）。不依赖 pytest，任何 3.9+ 环境可直接复跑。

测试覆盖：字面匹配与反例、大小写开关、近似命名、三个退出码、JSON 契约、内容规则作用域、提交字段规则、忽略 `.git`/`__pycache__`。

---

## 诚实边界

- 本工具是平台校验的**近似实现**，不是替代品。最终以平台返回为准。
- 「字面子串」与「冒号 + 空格」两条规则来自作者在真实提交中的**实测**，不是官方规范的全部。
- 内容扫描有 256KB / 后缀白名单限制，二进制文件不扫。
- 不做网络请求，不上传任何内容，不做评分。

---

## 贡献 / 许可 / 致谢

- 贡献指南见 [CONTRIBUTING.md](CONTRIBUTING.md)，变更记录见 [CHANGELOG.md](CHANGELOG.md)。
- 代码以 [MIT](LICENSE) 许可发布。
- 借鉴与引用说明见 [拿来说明.md](拿来说明.md)（英文版 [ATTRIBUTION.md](ATTRIBUTION.md)）。
- AI 使用过程日志见 [AI日志.md](AI日志.md)（英文摘要 [AI_LOG.md](AI_LOG.md)）。

### 关于文件名

仓库里 `AI日志.md` / `AI_LOG.md`、`拿来说明.md` / `ATTRIBUTION.md` 是**中英各一份**：中文名满足平台交付物关键字（`*AI日志*`、`*拿来说明*`）的字面匹配，英文名对应课程模板里的 `AI_LOG.md` / `ATTRIBUTION.md`。这正是本工具要防的那类命名问题，所以在这里显式说明。
