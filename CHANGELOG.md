# Changelog

## 2026-06-16

### Added

- 新增 `references/residual_hotlist.md`，集中处理第一轮去味后常残留的二层热点：负向平行、总结锚点、无证泛化、工程复盘腔、安全补丁、小标题排比、结尾升华和伪具体。
- 新增 `references/technical_method_article_rules.md`，吸收技术方法文 / 内部工程分享稿的词频驱动二扫、用户点名词强审、prompt 示例低介入、正向约束改写和硬信息保真规则。
- 新增 `assets/user_followup_regression_fixtures.json`，把历史追改中反复出现的 `不是...而是...`、`往往...真正...`、正反两面解释、公众号模板和工程复盘腔外溢转成回归 suite。
- 新增 `assets/technical_method_regression_fixtures.json`，覆盖含 prompt / checklist / 路径 / 函数名 / 命令的技术方法文，以及用户点名 `不` 后的二扫场景。
- 新增长文覆盖样本 `L16`、`L17`，补访谈实录和学术摘要等未知 / 强边界题材。
- 新增提纲覆盖样本 `O08`，补短规划单块“平均配额”问题。
- 新增 `scripts/check_regression_suite_batch.py --hotlist-scan`，用于真实输出批次的热点残留扫描。
- 新增 `docs/smoke-commands.md`，记录安装、校验和核心 smoke 命令。
- 新增 `requirements-dev.txt`，声明维护校验脚本所需的 `PyYAML` 依赖。

### Changed

- `SKILL.md` 默认强度从单一 `平衡` 改为场景化映射：创作、公众号、评论、随笔、复盘、小说、提纲默认 `偏强`；通知、FAQ、客服口径、口播、社媒脚本默认 `平衡`；政策、法律、医疗、技术、学术、法规、新闻事实说明默认 `保守`。
- 内部执行顺序调整为 `场景判定 -> 强度映射 -> 诊断 -> 初改 -> 残留簇二扫 -> 必要二改 -> 体裁 / 事实校验 -> 最终成稿`。
- `control_modes.md` 新增 `偏强` 档、场景化强度映射、`voice_sample` 声纹锚点和 `绝对避免项`。
- `audit_checklist.md` 新增残留簇二扫卡和强制二改阈值。
- `rewrite_principles.md` 新增多 pass：姿态、骨架、节奏、词簇、体裁、事实；小说增加 `scene 运行 pass`，提纲增加 `不公平配额 pass`。
- `SKILL.md` 新增技术方法文路由、点名词强审入口和工具性结构保真边界。
- `audit_checklist.md` 新增技术方法文 / 内部经验分享卡，区分功能词残留和 prompt / checklist / 专业术语必要用法。
- `rewrite_principles.md` 新增技术方法文的 `工具性结构 pass`。
- `longform_validation_rules.md`、`novel_longform_rules.md`、`plot_outline_rules.md` 同步新增专项 pass 路由。
- `validation_matrix.md` 更新当前重点补样、历史追改 suite 和 `--hotlist-scan` 流程。
- `agents/openai.yaml` 同步场景化默认强度，不再写 `Default to balanced`。
- 根 `README.md` 重写为仓库级说明，补安装、使用、关键文件、回归校验、维护原则和发布边界。

### Verified

- `python3 anti-aistyle-zh/scripts/render_regression_suite.py --summary`
- `python3 anti-aistyle-zh/scripts/render_regression_suite.py --lint-fixtures`
- `python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" "$PWD/anti-aistyle-zh"`，在已安装 `requirements-dev.txt` 依赖的虚拟环境中执行。
- `python3 anti-aistyle-zh/scripts/render_regression_suite.py --suite anti-aistyle-zh-user-followup-regression --group core_smoke`
- `python3 anti-aistyle-zh/scripts/render_regression_suite.py --suite anti-aistyle-zh-technical-method-regression --group core_smoke`
