# OpenStock AI

OpenStock AI 是一个开源 AI 美股分析与推荐系统，核心能力是 AI 选股、股票分析、股票评分、研究报告生成、模拟交易与回测。

项目目标不是直接替用户做投资决策，而是为美股研究提供可追溯、可审计、可扩展的 AI 辅助分析系统。

> 本系统仅用于投资研究辅助，不构成任何投资建议。

## 当前阶段

当前项目处于 `0.1.0` 开发阶段。按 [MVP 路线图](docs/product/mvp-roadmap.md) 的里程碑，目前进度：

* **M0 项目重建**：完成。项目标准、需求分析、架构设计、GitHub 协作配置、基础测试已建立。
* **M1 后端基础**：完成。FastAPI、统一配置管理、数据库连接（默认本地 SQLite，可切换 Postgres）、`audit_logs` 表、Docker Compose、数据库初始化脚本均可用。
* **M2 数据源**：完成。yfinance 风格历史日线、SEC EDGAR 财报申报、FRED 宏观数据（需自备免费 Key）、Yahoo 实时走势均已接入并有测试覆盖。
* **M3 AI 分析**：部分完成。Model Layer 统一接口、Output Validator、Agent 基类和 SEC Filing Agent 已落地并端到端联调；News Agent / Report Agent 尚未开发。
* **M4 评分与报告**：部分完成。独立 Algorithm Layer 提供可解释的规则化推荐评分（`algorithm-v0.2.1`，已接入 SEC 真实财务数据和真实技术指标：基本面/成长性/估值/技术面（RSI/均线金死叉/动量）/风险五因子），并通过新增的 Workflow Layer（`stocks/screening`）实现批量选股排序；基于大模型的 AI Scoring Agent、研究报告生成尚未开发（`packages/scoring` 仍为空）。
* **M5 前端展示**：部分完成。美股操作工作台（关注列表、搜索、报价、走势、候选池、推荐评分）已可用，独立的股票深度分析页和研究报告页尚未开发。
* 尚未开始：模拟交易与回测（`packages/backtesting`、`packages/brokers` 仍为空）。

额外完成的扩展能力（超出原始路线图，但已落地并有测试）：

* Universe Layer：每日扫描美股最活跃 Top 100 候选池（`packages/universe_layer`）
* News / Policy Layer：最近新闻、SEC 披露、政策和内部任免线索（`packages/news_layer`）
* Algorithm Layer：独立于 Model Layer 的可解释推荐算法（`packages/algorithm_layer`）

## 文档入口

* [项目标准文档 v0.1](docs/standards/project-standard-v0.1.md)
* [Universe Layer 标准](docs/standards/UNIVERSE_STANDARD.md)
* [News / Policy Layer 标准](docs/standards/NEWS_POLICY_STANDARD.md)
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
* 最近新闻、政策、SEC 披露和 3 年查询入口
* 项目开发界面，展示版本、架构层和当前状态
* 常用分析维度解读，包括成交量、相对成交量、P/E、RSI、均线、波动率等
* 风险提示和研究辅助边界

主要接口：

```text
GET http://127.0.0.1:8000/stocks/popular
GET http://127.0.0.1:8000/stocks/search?q=AAPL
GET http://127.0.0.1:8000/stocks/universe/most-active?limit=100
GET http://127.0.0.1:8000/stocks/screening?limit=20
GET http://127.0.0.1:8000/stocks/AAPL/quote
GET http://127.0.0.1:8000/stocks/AAPL/recommendation
GET http://127.0.0.1:8000/stocks/AAPL/news?years=3&limit=30
GET http://127.0.0.1:8000/stocks/AAPL/trend?range=1d&interval=1m
GET http://127.0.0.1:8000/stocks/AAPL/history?range=10y&interval=1d
GET http://127.0.0.1:8000/stocks/AAPL/filings?forms=10-K,10-Q,8-K&limit=10
GET http://127.0.0.1:8000/stocks/AAPL/sec-summary
GET http://127.0.0.1:8000/macro/FEDFUNDS/observations?limit=10
```

FRED 接口需要先在 `.env` 设置免费的 `FRED_API_KEY`（注册地址：https://fred.stlouisfed.org/docs/api/api_key.html），否则返回 503。

## 模型层基础

Model Layer 采用 LiteLLM-compatible 设计。真实模型供应商只允许通过：

```text
packages/model_layer/providers/litellm_provider.py
```

Agent、Workflow、Algorithm Layer 和 API 不得直接调用模型 SDK。

未配置任何模型 API Key 时，`packages/model_layer/factory.py` 的 `build_default_router()` 自动 fallback 到 `mock` provider；配置 `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` 等任意一个后自动切换为 `litellm` provider，无需改代码。

每次模型调用在返回前都会经过 `packages/model_layer/validator.py` 的 Output Validator：检查风险提示、数据来源（citations）、模型信息是否齐全，以及输出是否包含"必买/保证上涨/无风险/稳赚"等禁止词，不合规直接抛出 `OutputValidationError`。

## AI Agent Layer（M3）

第一个落地的 Agent：

```text
GET http://127.0.0.1:8000/stocks/AAPL/sec-summary
```

`SECFilingAgent`（`packages/ai_agents/sec_filing_agent.py`）走完整流水线：Policy Guard → Data Context Builder（拉取 SEC EDGAR 申报）→ Workflow Executor → Model Layer（含 Output Validator）→ Audit Logger（写入 `audit_logs`）。已用真实 SEC 数据（AAPL）做过端到端联调。

Agent 基类见 `packages/ai_agents/base.py`，后续 News Agent、Report Agent 复用同一流水线。

## AI 选股 Workflow（M4）

```text
GET http://127.0.0.1:8000/stocks/screening?limit=20
```

`StockScreeningWorkflow`（`packages/workflow_layer/stock_screening.py`）把 Universe Layer 的候选池（Most Active Top 100）逐个用 Algorithm Layer v0.2.1 打分，并发请求（最多 8 个并发）后按总分排序返回。这是"自己选股"场景的核心入口：不指定单一股票，直接看候选池里排序靠前的标的。已用真实数据端到端联调（20 只股票全部评分成功，约 56 秒）。

每次调用都会把候选评分写入 `stock_scores` 表（`packages/db/stock_scores.py`），通过 `GET /stocks/{symbol}/score-history` 可以读出某只股票历次评分，方便对比"这只股票最近几次扫描分数是涨是跌"——这是把 AI 选股从一次性即时计算变成有历史记录的个人工具的关键一步。

### 技术面因子（algorithm-v0.2.1）

`technical` 因子不再是粗略的区间涨跌幅估算，而是基于近 1 年日线收盘价（`packages/data_sources/price_history.py`）计算的真实技术指标（`packages/algorithm_layer/technical_indicators.py`）：10 日动量（40%）、RSI-14（30%）、均线 5/20 金叉死叉状态（30%）。日线数据不足（如新上市股票）时自动退化为旧的区间走势粗估，并在 `explanation` 中说明。计算出的 RSI 数值和均线状态通过 `factors[].explanation` 字段暴露，可用于替换前端面板上现有的占位 RSI/均线标签。

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
