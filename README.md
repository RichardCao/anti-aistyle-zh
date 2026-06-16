# anti-aistyle-zh

面向中文写作场景的去 AI 味 skill 仓库。当前核心产物是 [anti-aistyle-zh](./anti-aistyle-zh)：一个用于短文、公众号文章、评论、随笔、小说正文、长篇原稿、总纲、卷规划和章节规划的统一入口 Codex skill。

项目目标不是“骗过检测器”，也不是把文本改得更随机、更口语或更碎。目标是在保留原意、事实、体裁、声纹和任务边界的前提下，压掉解释腔、总结腔、汇报腔、规划感、模板化推进和过度成熟的统一人格，让中文成稿更像自然写出来的文本。

## 当前版本重点

- 统一入口：不再按文章、小说、提纲拆成多个 skill。
- 场景化默认强度：创作、公众号、评论、随笔、小说、提纲默认 `偏强`；通知、FAQ、客服口径、口播、社媒脚本默认 `平衡`；政策、法律、医疗、技术、学术、法规、新闻事实说明默认 `保守`。
- 内部执行链：`场景判定 -> 强度映射 -> 诊断 -> 初改 -> 残留簇二扫 -> 必要二改 -> 体裁 / 事实校验 -> 最终成稿`。
- 二层残留热点：新增 [residual_hotlist.md](./anti-aistyle-zh/references/residual_hotlist.md)，专门处理第一轮去味后常残留的 `不是...而是...`、`往往...真正...`、工程复盘腔、小标题排比和结尾升华。
- 回归覆盖：新增历史追改 suite、长文未知题材样本和短规划配额样本。
- 检测器边界：外部检测或风险观察只作为回归辅助，不作为最终质量目标。

## 目录结构

```text
.
├── anti-aistyle-zh/                 # 正式 skill 包
│   ├── SKILL.md                     # 主执行合同
│   ├── agents/openai.yaml           # Codex UI / agent 入口提示
│   ├── references/                  # 按需读取的规则、清单和专项参考
│   ├── assets/                      # 回归夹具
│   └── scripts/                     # 回归渲染和批量检查脚本
├── docs/                            # 仓库级维护说明
└── CHANGELOG.md                     # 仓库级变更记录
```

正式 skill 目录遵循 Codex skill 的最小结构原则，不放 `README.md`、`CHANGELOG.md`、安装指南等辅助文档。仓库说明和变更记录放在仓库根目录。

## 安装

开发机上建议用软链安装，避免维护两份副本：

```bash
ln -sfn "$PWD/anti-aistyle-zh" "${CODEX_HOME:-$HOME/.codex}/skills/anti-aistyle-zh"
```

安装后开启新会话，确认可用 skill 列表中出现 `anti-aistyle-zh`。

## 使用

最小调用只需要目标文本：

```text
请用 $anti-aistyle-zh 处理下面中文文本。
<目标文本>
```

可选控制项只有四类：

- `voice_sample / 样文`
- `改写强度`
- `目标读感`
- `输出模式`

默认输出只有 `最终成稿`。`诊断`、`manifest`、`审计`、`执行回执` 默认属于内部过程；只有用户要求、验证、审计或回归场景，才允许放在最终成稿之后。

## 关键文件

- [anti-aistyle-zh/SKILL.md](./anti-aistyle-zh/SKILL.md)：主合同、默认行为、决策树、输出边界。
- [references/control_modes.md](./anti-aistyle-zh/references/control_modes.md)：控制项、场景化强度、`voice_sample` 声纹锚点。
- [references/residual_hotlist.md](./anti-aistyle-zh/references/residual_hotlist.md)：二层残留热点清单。
- [references/audit_checklist.md](./anti-aistyle-zh/references/audit_checklist.md)：改后审计和强制二改阈值。
- [references/rewrite_principles.md](./anti-aistyle-zh/references/rewrite_principles.md)：通用改写原则和多 pass。
- [references/longform_validation_rules.md](./anti-aistyle-zh/references/longform_validation_rules.md)：长文、强体裁和压缩回潮。
- [references/novel_longform_rules.md](./anti-aistyle-zh/references/novel_longform_rules.md)：小说章节、scene、长篇正文。
- [references/plot_outline_rules.md](./anti-aistyle-zh/references/plot_outline_rules.md)：总纲、卷表、章节规划和 hard fail。
- [references/validation_matrix.md](./anti-aistyle-zh/references/validation_matrix.md)：验证覆盖面和最小回归流程。
- [scripts/render_regression_suite.py](./anti-aistyle-zh/scripts/render_regression_suite.py)：回归夹具渲染、fixture lint、单输出断言。
- [scripts/check_regression_suite_batch.py](./anti-aistyle-zh/scripts/check_regression_suite_batch.py)：批量检查真实输出，支持 `--hotlist-scan`。
- [docs/smoke-commands.md](./docs/smoke-commands.md)：维护者常用校验命令。

## 回归与校验

基础 skill 校验：

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" \
  "$PWD/anti-aistyle-zh"
```

`quick_validate.py` 依赖 `PyYAML`；维护者环境可在虚拟环境中使用 `requirements-dev.txt` 安装，避免污染系统 Python。

查看全部 suite：

```bash
python3 anti-aistyle-zh/scripts/render_regression_suite.py --summary
```

检查 fixture 设计：

```bash
python3 anti-aistyle-zh/scripts/render_regression_suite.py --lint-fixtures
```

核心 smoke：

```bash
python3 anti-aistyle-zh/scripts/render_regression_suite.py --suite anti-aistyle-zh-local-regression --group core_smoke
python3 anti-aistyle-zh/scripts/render_regression_suite.py --suite anti-aistyle-zh-focused-regression --group focused_residuals
python3 anti-aistyle-zh/scripts/render_regression_suite.py --suite anti-aistyle-zh-user-followup-regression --group core_smoke
```

检查真实输出批次：

```bash
python3 anti-aistyle-zh/scripts/check_regression_suite_batch.py --manifest <manifest.json> --hotlist-scan
```

`--hotlist-scan` 只报告热点残留，不单独决定成稿是否合格。

## 维护原则

- `SKILL.md` 只保留核心执行合同，不把热点清单和题材专项完整展开。
- 新增强规则时，优先同时新增 fixture；不能配 fixture 的经验先放临时 notes，不直接进主合同。
- 所有频率判断先和原文比，再和同体裁、同长度、同运行方式的真人常态比。
- 不把检测器分数或风险观察指标作为最终目标；人工读感、事实保真和体裁保真优先级更高。
- 当前权威始终是根目录下的 `anti-aistyle-zh/`。
