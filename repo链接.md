# 仓库链接与提交说明

本文件是 C5「GitHub Repository」挑战的提交索引，便于评审快速定位每个交付物。

## 1. 仓库地址

- **GitHub 仓库**：https://github.com/ZhouYan05/deliverable-selfcheck
- **可见性**：Public
- **默认分支**：`main`
- **许可证**：MIT（见 `LICENSE`）

## 2. 这个仓库是什么

`deliverable-selfcheck`：一个零依赖的交付物自检命令行工具。

它把作者在真实提交中踩到的两个坑固化成了可复跑的程序：

1. 交付物关键字是**文件名字面子串**匹配 —— 文件名里多一个下划线（`AI_工作日志.md`）就会被判缺件；
2. 提交字段里的**英文冒号 + 空格**会被敏感信息过滤器误判成密钥形态，导致整单被拒。

## 3. 30 秒验证（评审可照抄）

```bash
git clone https://github.com/ZhouYan05/deliverable-selfcheck.git
cd deliverable-selfcheck

# 1) 跑测试：应输出 "Ran 24 tests ... OK"
python -m unittest discover -s tests -v

# 2) 复现「缺件 + 近似命名告警」：应输出 BLOCKED，退出码 1
python -m deliverable_selfcheck --dir examples/before \
  --required "README.md,*repo链接*,*AI日志*,*拿来说明*"
echo $?

# 3) 复现「修好之后」：应输出 READY，退出码 0
python -m deliverable_selfcheck --dir examples/after \
  --required "README.md,*repo链接*,*AI日志*,*拿来说明*"
echo $?

# 4) 复现「标题被敏感信息过滤拦下」
python -m deliverable_selfcheck --dir . --required "README.md" \
  --title "C5 GitHub Repository: deliverable-selfcheck"
```

> Windows PowerShell 下把 `$?` 换成 `$LASTEXITCODE`，`python -m deliverable_selfcheck` 需要先 `$env:PYTHONPATH="src"` 或先执行 `pip install -e .`。

## 4. 交付物对照表

| 平台要求的关键字 | 仓库中的文件 | 说明 |
| --- | --- | --- |
| `README.md` | `README.md` | 项目首页：定位、安装、用法、测试、许可 |
| `*repo链接*` | `repo链接.md` | 本文件，含仓库地址与验证步骤 |
| `*AI日志*` | `AI日志.md` | 完整 AI 使用过程日志 + AAR 复盘（英文摘要：`AI_LOG.md`） |
| `*拿来说明*` | `拿来说明.md` | 借鉴来源、许可兼容性与边界声明（英文版：`ATTRIBUTION.md`） |

课程模板要求的其余文件：`LICENSE`（MIT）、`.gitignore`、使用说明 `docs/USAGE.md`、示例 `examples/`。

## 5. 提交信息

- 提交人：ZhouYan05（学号 2024102310451）
- 挑战：C5 GitHub Repository
- 项目标题：C5 GitHub Repository - deliverable-selfcheck 交付物自检器

> 注：标题中的破折号是刻意的 —— 英文冒号 + 空格会被平台的敏感信息过滤拦下，这一点已写进工具规则库 `src/deliverable_selfcheck/rules.py`。
