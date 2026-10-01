# 使用说明 · deliverable-selfcheck

> 面向"马上要交作业、只想少踩一个坑"的同学。**30 秒版本在下面第一节**，细节在后面的章节。
> 完整规则设计动机见 [`../references/rulebook.md`](../references/rulebook.md)；本文只讲"怎么用"。

---

## 1. 30 秒上手

```bash
# 零依赖：只用 Python 标准库，不需要联网，Python >= 3.9

# 路线 A：装一次（推荐）
pip install -e .
python -m deliverable_selfcheck --dir . --required "README.md,*AI日志*"

# 路线 B：不安装，把 src 加进模块搜索路径即可（本包是 src/ 布局）
PYTHONPATH=src python -m deliverable_selfcheck --dir . --required "README.md,*AI日志*"
```

输出示例（Markdown，默认）：

```text
# 交付物自检报告

- 目录：`/home/you/my-project`
- 结论：**BLOCKED**
- 退出码：`1`

## 1. 缺件

- [BLOCK] 缺失必需文件：`*AI日志*`（按文件名字面子串匹配）
...
```

**只看两行就够了**：结论（READY / BLOCKED）和退出码（0 / 1 / 2）。

装好后，`deliverable-selfcheck` 与 `python -m deliverable_selfcheck` **完全等价**：

```bash
pip install -e .
deliverable-selfcheck --dir . --required-file examples/required_examples.txt
```

> ⚠️ 若跳过安装，下文所有 `python -m deliverable_selfcheck` 都必须带上 `PYTHONPATH=src`，
> 否则会报 `No module named deliverable_selfcheck`（PowerShell 写法：`$env:PYTHONPATH="src"; python -m ...`）。
> 只跑测试则不需要：`python -m unittest discover -s tests -v` 可直接用。

---

## 2. 三种典型用法

> 下列命令统一写成 `python -m deliverable_selfcheck`（等价于装好后的 `deliverable-selfcheck`）。
> **未安装**时请在前面加 `PYTHONPATH=src`。

### 用法 A · 交挑战前自检（最常见）

把平台的交付物关键字抄进参数。**括号里的 `*` 会由工具自动剥离**，它不是通配符语法：

```bash
# C5 GitHub Repository
python -m deliverable_selfcheck --dir . \
  --required "README.md,*repo链接*,*AI日志*,*拿来说明*"
```

关键字太长就用清单文件，一行一组（见 `examples/required_examples.txt`）：

```bash
python -m deliverable_selfcheck --dir . --required-file examples/required_examples.txt
```

### 用法 B · 想在 CI 里挡住缺件

`--json` 输出机读结果，退出码可直接驱动流水线：

```bash
python -m deliverable_selfcheck --dir . --required "README.md,*AI日志*" --json > report.json
echo "exit=$?"   # 0 = READY，1 = BLOCKED，2 = 参数错误
```

### 用法 C · 提交前审一遍标题 / 简介（**这条最容易救命**）

平台会过滤提交字段里的敏感信息形态。把标题和简介传进来，提前发现：

```bash
python -m deliverable_selfcheck --dir . \
  --required "README.md,*AI日志*" \
  --title "C5 GitHub Repository - deliverable-selfcheck 交付物自检器" \
  --summary "把平台提交校验的两个真实坑固化为离线自检器。"
```

如果标题写成 `C5 GitHub Repository: deliverable-selfcheck`（**英文冒号 + 空格**），工具会报：

```text
## 4. 提交字段告警（标题 / 简介）

- [BLOCK] title#1：疑似 key-value / 密钥形态：`C5 GitHub Repository: deliverable-selfcheck`
```

这不是工具"太严" —— 这是**实测会发生的事**：这种写法会被平台判为"疑似包含敏感信息（密钥/Token 形态）"而整单拒绝，且报错不指位置。**把冒号换成破折号或全角冒号即可通过。**

---

## 3. 参数表

| 参数 | 说明 |
| --- | --- |
| `--dir <路径>` | 要检查的目录，默认 `.` |
| `--required <关键字,...>` | 必需交付物关键字，可重复；英文逗号分隔多值 |
| `--required-file <路径>` | 从文件读关键字，每行一组，`#` 开头为注释 |
| `--title <文本>` | 待审的提交标题，可重复（对应 `title#1`、`title#2`…） |
| `--summary <文本>` | 待审的提交简介，可重复（对应 `summary#1`…） |
| `--json` | 输出 JSON（给脚本 / CI 用） |
| `--md` | 输出 Markdown（默认） |
| `--no-content-check` | 跳过正文内容规则，只查缺件与命名 |
| `--case-sensitive` | 文件名匹配区分大小写（默认不区分） |
| `--strict` | 额外用"冒号 + 空格"规则扫仓库正文（**误报较多，默认关闭**） |
| `--version` | 打印版本 |

---

## 4. 退出码约定

| 退出码 | 含义 | 怎么处理 |
| --- | --- | --- |
| `0` | **READY** —— 没发现阻断问题 | 可以提交 |
| `1` | **BLOCKED** —— 有缺件或阻断级告警 | 按报告逐条修，再跑一次 |
| `2` | 参数错误（例如给了不存在的目录） | 修命令行 |

`--strict` 下若只存在命名类告警，退出码同样为 `1`（因为那是"阻断级"）。CI 里判断用 `$?` / `%ERRORLEVEL%` 即可。

---

## 5. 报告怎么读

Markdown 报告分四节，**从第 1 节往下看，遇到第一条 [BLOCK] 就停下先修它**：

| 节 | 含义 | 典型问题 |
| --- | --- | --- |
| 1. 缺件 | 必需关键字一个都没命中的文件 | `*AI日志*` 没找到（文件名少一个词） |
| 2. 命名告警 | 命中了但文件名可疑 | 同族文件命名不一致 |
| 3. 正文告警 | 仓库正文里的真凭据形态 | 误把 `sk-` 风格串提交进仓库 |
| 4. 提交字段告警 | `--title` / `--summary` 的问题 | **冒号 + 空格被判密钥形态** |

`--json` 的字段结构与上面四节一一对应，键名见 `to_dict()` 输出。

## 6. 常见坑（都是实测撞过的）

### 坑 1 · 文件名差一点就被判缺件

交付物关键字是**文件名字面子串**匹配，不是通配符。也就是说：

| 关键字 | 文件名 | 结果 | 为什么 |
| --- | --- | --- | --- |
| `*AI日志*` | `AI日志.md` | ✅ | 字面包含 `AI日志` |
| `*AI日志*` | `AI_工作日志与AAR.md` | ❌ | 下划线把"AI"和"日志"断开了，字面不含 `AI日志` |
| `*AAR*` | `AI_工作日志与AAR.md` | ✅ | 字面包含 `AAR` |

**结论**：一个文件想同时满足两类交付物，文件名必须**同时字面包含**两个关键词 —— 例如 `AI日志与AAR.md`。

### 坑 2 · 提交字段里的冒号 + 空格

见第 2 节用法 C。报错长这样（平台返回，不含位置）：

```text
字段「projectTitle」提交内容疑似包含敏感信息（密钥/Token（sk- 或 api key 形态））。请脱敏后重新提交。
```

本地排查顺序：**先怀疑标题/简介里的 `词: 词` 模式，再怀疑真密钥**。因为工具里 `sk-` / `token` / `key` 全无命中的情况下，仍然会被这个模式拒掉。

> ⚠️ 注意：`runs-on: ubuntu-latest`、`Note: xxx` 这类**仓库正文**里的冒号是正常的，本工具默认不扫正文（只有 `--strict` 才扫），也不会误报。

### 坑 3 · 交付物没齐就提交

缺件会直接触发 red flag，artifactCompleteness 一维封顶 5 分。**提交前先跑一次本工具**（或平台的 `check-deliverables`）。

---

## 7. 自检 vs 平台校验：边界在哪

| 层面 | 本工具 | 平台 |
| --- | --- | --- |
| 交付物文件名 | ✅ 近似检查（字面子串） | ✅ 权威判定 |
| 提交字段敏感词 | ✅ 近似检查（形态匹配） | ✅ 权威判定（且拒单） |
| 内容质量 / rubric 评分 | ❌ 不做 | ✅ 有 |
| 是否需要联网 | ❌ 完全离线 | ✅ 需要 |

**最终以平台返回为准。** 本工具的价值是"把一次被拒的往返省掉"，不是替代校验。

---

## 8. 复现示例（评审可直接跑）

```bash
git clone https://github.com/ZhouYan05/deliverable-selfcheck
cd deliverable-selfcheck

# 1) 跑测试（零依赖，标准库 unittest；tests 会自己把 src 插进 sys.path，无需安装）
python -m unittest discover -s tests -v

# 接下来的命令行用法需要包可被导入，二选一：
python -m pip install -e .     # 安装（推荐）
export PYTHONPATH=src          # 或：不安装，仅当前会话有效（PowerShell: $env:PYTHONPATH="src"）

# 2) before：故意缺件 + 故意带冒号标题 → 应为 BLOCKED（退出码 1）
python -m deliverable_selfcheck --dir examples/before \
  --required "README.md,*AI日志*" \
  --title "示例项目: 交付物自检"

# 3) after：修好 → 应为 READY（退出码 0）
python -m deliverable_selfcheck --dir examples/after \
  --required "README.md,*AI日志*" \
  --title "示例项目 - 交付物自检"
```

---

## 9. 许可与致谢

- 许可：[MIT](../LICENSE) —— 随便用，出事不负责。
- 拿来清单与边界：[`../拿来说明.md`](../拿来说明.md) / [`../ATTRIBUTION.md`](../ATTRIBUTION.md)。
- 规则设计动机与证据：[`../references/rulebook.md`](../references/rulebook.md)。
- 变更记录：[`../CHANGELOG.md`](../CHANGELOG.md)；想一起改：[`../CONTRIBUTING.md`](../CONTRIBUTING.md)。
