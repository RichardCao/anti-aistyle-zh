# anti-aistyle-zh smoke commands

这些命令用于维护者在修改 skill 后做最小可重复检查。它们不是 skill 执行合同，不放进 `anti-aistyle-zh/SKILL.md`。

## 安装到 Codex 可发现目录

```bash
ln -sfn "$PWD/anti-aistyle-zh" "${CODEX_HOME:-$HOME/.codex}/skills/anti-aistyle-zh"
```

## 基础 skill 校验

先创建虚拟环境并安装维护脚本依赖：

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

再运行基础校验：

```bash
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" \
  "$PWD/anti-aistyle-zh"
```

## fixture 结构检查

```bash
python3 anti-aistyle-zh/scripts/render_regression_suite.py --summary
python3 anti-aistyle-zh/scripts/render_regression_suite.py --lint-fixtures
```

## 核心 smoke

```bash
python3 anti-aistyle-zh/scripts/render_regression_suite.py --suite anti-aistyle-zh-local-regression --group core_smoke
python3 anti-aistyle-zh/scripts/render_regression_suite.py --suite anti-aistyle-zh-focused-regression --group focused_residuals
python3 anti-aistyle-zh/scripts/render_regression_suite.py --suite anti-aistyle-zh-user-followup-regression --group core_smoke
python3 anti-aistyle-zh/scripts/render_regression_suite.py --suite anti-aistyle-zh-technical-method-regression --group core_smoke
```

## 有真实输出文件时

```bash
python3 anti-aistyle-zh/scripts/check_regression_suite_batch.py --manifest <manifest.json> --hotlist-scan
```

`--hotlist-scan` 默认只报告热点残留，不单独决定成稿是否通过。
