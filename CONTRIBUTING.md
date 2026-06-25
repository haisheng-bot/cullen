# Contributing to OpenStock AI

## 开发流程

1. 从 `develop` 创建分支。
2. 使用 `feature/*`、`fix/*` 或 `docs/*`。
3. 修改前阅读 `docs/standards/project-standard-v0.1.md`。
4. 修改后补充测试。
5. 新增模块必须更新 docs。
6. 提交 Pull Request，并完整填写 `.github/pull_request_template.md`。

## 分支规范

```text
main        稳定版本，不直接开发
develop     日常集成分支
feature/*   新功能
fix/*       修复
docs/*      文档
```

不得直接修改 `main` 分支。所有功能、修复和文档调整都应通过 PR 合并。

## Commit 规范

```text
feat: add portfolio optimizer module
fix: correct backtest drawdown calculation
docs: update PRD and GitHub templates
test: add governance checks for PR template
refactor: simplify data source interface
```

## Pull Request 要求

PR 必须说明：

* 修改范围
* AI 开发工具标识（codex / claude-code / cursor / human / mixed）
* 测试命令和结果
* 文档是否更新
* 是否涉及外部 API
* 是否涉及 AI 输出
* 是否涉及投资研究结论

PR 合并前应通过：

```bash
.venv311/bin/python -m unittest discover -s tests
```

## Issue 要求

提交 GitHub Issue 时必须使用模板：

* Bug report
* Feature request

Feature request 应标明所属模块，例如 Stock Screener、Portfolio、Strategy Engine、Backtesting Engine、AI Report 或 Docs / GitHub。

## 合规要求

所有投资相关输出必须包含：

> 本系统仅用于投资研究辅助，不构成任何投资建议。

禁止提交 API Key、Token、券商账户、真实交易记录和个人敏感信息。

不得提交：

* API Key
* Token
* 券商账户
* 身份证信息
* 银行卡信息
* 真实交易记录

外部 API 调用必须封装在 data source 或独立模块中，不得把 Key 写死在代码里。
