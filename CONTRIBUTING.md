# Contributing

感谢你有兴趣改进 `deliverable-selfcheck`。这是一个**零依赖、可离线运行**的
小工具，请帮忙守住这条底线。

## 1. 底线（改动前请先读）

- **不引入第三方运行依赖。** 只用 Python 标准库。
- **不引入第三方测试框架。** 测试用 `unittest`，`python -m unittest` 要能直接跑。
- **不联网。** 工具必须能在完全离线的机器上工作。
- **不加"自动修盘"行为。** 工具只报告，不改动用户文件。
- **不把平台的非公开实现写进来。** 规则必须能追溯到一次可复现的真实观察。

## 2. 开发环境

```bash
git clone https://github.com/ZhouYan05/deliverable-selfcheck
cd deliverable-selfcheck

# 方式 A：不安装，直接跑源码
PYTHONPATH=src python -m deliverable_selfcheck --help

# 方式 B：可编辑安装
python -m pip install -e .
deliverable-selfcheck --help
```

要求 Python >= 3.9。

## 3. 跑测试

```bash
python -m unittest discover -s tests -v
```

当前 24 条用例全部通过。提交 PR 前请确保仍然全绿。

## 4. 改规则的规矩（重要）

本项目最容易出问题的地方就是**规则的作用域**，所以：

1. **新增或修改一条规则，必须同时新增一个测试。** 测试里要写清这条规则
   防的是什么真实场景。
2. **任何"会被误伤"的写法，也要有反例测试。** 例如：CI 配置里的
   `runs-on: ubuntu-latest`、文档里的 `Note: xxx`，都**不应该**被内容扫描拦截。
3. **区分作用域。** 仓库正文规则（`CONTENT_RULES`）与提交字段规则
   （`METADATA_RULES`）是两个集合，不要混用：
   - 平台对**提交字段**做敏感信息过滤 → 规则较严；
   - 平台**不**扫仓库正文 → 正文只拦真凭据，避免误报。
4. **提交字段规则的关键字要能匹配中文键。** 只写 `[A-Za-z]` 开头会漏掉
   `项目名: xxx` 这类真实被拒形态。

## 5. 提交 PR

- 一个 PR 做一件事（新增规则 / 修文档 / 加示例分开提）。
- PR 描述里请写：**动机**（你遇到了什么真实问题）、**改动**、**验证方式**
  （贴命令与输出）。
- 改动输出格式（Markdown 章节、JSON 字段）属于**破坏性变更**，请在
  `CHANGELOG.md` 的 `Unreleased` 下注明。
- 如果改动会影响已有的 24 条测试预期，请在描述里说明为什么。

## 6. 报告问题

开 Issue 时请尽量给出：

- 你的目录结构（脱敏后的文件名即可）；
- 你用的完整命令；
- 实际输出与期望输出的差异；
- 你的 Python 版本与操作系统。

**如果你发现的是"平台行为和本工具规则不一致"，这类 Issue 最有价值 ——
它直接决定下一版规则的走向。**
