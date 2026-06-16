# Release commands

这份文档只记录公开发布命令。正式 skill 包仍只放 `SKILL.md`、`agents/`、`references/`、`assets/` 和 `scripts/`。

## 前置检查

确认只公开 skill，不公开实验工具、临时目录或本机缓存：

```bash
cd /Users/create/anti-aistyle-publish
git status --short --untracked-files=all
find anti-aistyle-zh -maxdepth 1 -type f -print
git ls-tree -r --name-only HEAD | grep -E '^(tmp/|release/|rewrite-risk-proxy-zh/|research/|experiments/|\.venv/|\.DS_Store|.*__pycache__/|.*\.pyc$|.*auth\.json$)' || true
```

`find` 应只输出：

```text
anti-aistyle-zh/SKILL.md
```

最后一条命令应没有输出。

## 最小校验

```bash
python3 anti-aistyle-zh/scripts/render_regression_suite.py --summary
python3 anti-aistyle-zh/scripts/render_regression_suite.py --lint-fixtures
python3 anti-aistyle-zh/scripts/render_regression_suite.py --suite anti-aistyle-zh-local-regression --group core_smoke
python3 anti-aistyle-zh/scripts/render_regression_suite.py --suite anti-aistyle-zh-focused-regression --group focused_residuals
python3 anti-aistyle-zh/scripts/render_regression_suite.py --suite anti-aistyle-zh-user-followup-regression --group core_smoke
python3 anti-aistyle-zh/scripts/render_regression_suite.py --suite anti-aistyle-zh-technical-method-regression --group core_smoke
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" "$PWD/anti-aistyle-zh"
```

## 发布

如果当前 `HEAD` 就是要发布的提交：

```bash
git push origin HEAD:main
```

如果保留使用发布分支名：

```bash
git push origin publish-v2:main
```

发布后确认：

```bash
git fetch origin main
git log --oneline --decorate --max-count=3 origin/main
git ls-remote origin refs/heads/main
```
