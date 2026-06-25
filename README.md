# OpenStock AI

OpenStock AI 是一个开源 AI 美股分析与推荐系统，核心能力是 AI 选股、股票分析、股票评分、研究报告生成、模拟交易与回测。

项目目标不是直接替用户做投资决策，而是为美股研究提供可追溯、可审计、可扩展的 AI 辅助分析系统。

> 本系统仅用于投资研究辅助，不构成任何投资建议。

## 当前阶段

当前项目处于 `0.1.0` 框架重建阶段，已建立：

* 项目标准
* 需求分析
* 系统架构设计
* AI 开发架构
* GitHub 协作规范
* 版本管理规范
* 敏捷迭代标准
* 基础 CI
* 项目治理测试

## 文档入口

* [项目标准文档 v0.1](docs/standards/project-standard-v0.1.md)
* [Universe Layer 标准](docs/standards/UNIVERSE_STANDARD.md)
* [Algorithm Layer 标准](docs/standards/ALGORITHM_STANDARD.md)
* [Model Layer 标准](docs/standards/MODEL_STANDARD.md)
* [需求分析 v0.1](docs/product/requirements-analysis.md)
* [系统设计框架](docs/architecture/system-design.md)
* [AI 开发架构标准](docs/architecture/ai-development-architecture.md)
* [GitHub 协作标准](docs/standards/github-collaboration.md)
* [版本管理标准](docs/standards/version-management.md)
* [敏捷迭代与即开发即使用标准](docs/standards/agile-iteration.md)
* [AI 开发工具协作标准](docs/standards/AI_TOOL_COLLABORATION.md)
* [API 设计 v0.1](docs/api/api-design-v0.1.md)

## 本地检查

```bash
python3 -m unittest discover -s tests
```

## 美股操作界面 MVP

双击启动：

```text
open-app.command
```

启动 API：

```bash
.venv311/bin/python -m uvicorn apps.api.main:app --reload
```

打开界面：

```text
http://127.0.0.1:8000/
```

界面内容：

* 美股关注列表、搜索、报价和实时走势
* 每日扫描美股交易最活跃 100 只股票
* 独立 Algorithm Layer 返回的推荐评分
* 项目开发界面，展示版本、架构层和当前状态
* 常用分析维度解读，包括成交量、相对成交量、P/E、RSI、均线、波动率等
* 风险提示和研究辅助边界

主要接口：

```text
GET http://127.0.0.1:8000/stocks/popular
GET http://127.0.0.1:8000/stocks/search?q=AAPL
GET http://127.0.0.1:8000/stocks/universe/most-active?limit=100
GET http://127.0.0.1:8000/stocks/AAPL/quote
GET http://127.0.0.1:8000/stocks/AAPL/recommendation
GET http://127.0.0.1:8000/stocks/AAPL/trend?range=1d&interval=1m
GET http://127.0.0.1:8000/stocks/AAPL/history?range=10y&interval=1d
GET http://127.0.0.1:8000/stocks/AAPL/filings?forms=10-K,10-Q,8-K&limit=10
```

## 模型层基础

Model Layer 采用 LiteLLM-compatible 设计。真实模型供应商只允许通过：

```text
packages/model_layer/providers/litellm_provider.py
```

Agent、Workflow、Algorithm Layer 和 API 不得直接调用模型 SDK。

## 后端基础（配置 / 数据库 / audit_logs）

启动本地 Postgres 和 Redis：

```bash
docker compose -f docker/docker-compose.yml up -d
```

复制环境变量并初始化数据库表：

```bash
cp .env.example .env
.venv311/bin/python scripts/init_db.py
```

验证：

```bash
.venv311/bin/python -m unittest tests.test_db -v
```

```text
GET http://127.0.0.1:8000/health/db
```

未配置数据库时，`DATABASE_URL` 默认回退到本地 SQLite 文件，保证不依赖 Docker 也能跑通测试和基础功能。所有模型调用产生的 `ModelResponse` 都可以通过 `packages/db/audit.py` 中的 `write_audit_log` 写入 `audit_logs` 表。

## Git 分支规范

```text
main        稳定版本
develop     开发版本
feature/*   新功能
fix/*       修复
docs/*      文档
```
