# OpenStock AI

OpenStock AI 是一个开源 AI Investment Research Platform，核心能力是 AI 选股、股票研究、投资组合管理、策略回测、风险分析和 AI 自动研究报告。

长期目标是演进为 **AI Portfolio Operating System**：由 Workflow Engine 编排 Universe、Portfolio、Factor、Strategy、Constraint、Backtesting、Risk、AI Research、Recommendation、Report 和 Rebalance，让平台逐步成为 Cullen 的股票研究生产力工具。

项目目标不是直接替用户做投资决策，而是为美股研究提供可追溯、可审计、可扩展的 AI 辅助分析系统。

第一阶段，OpenStock AI 要优先成为 Cullen 的个人股票研究生产力工具：每日扫描候选股、跟踪 Portfolio、运行策略回测、生成 AI 解释和研究报告，并沉淀可复盘的历史记录。

> 本系统仅用于投资研究辅助，不构成任何投资建议。

## 当前阶段

当前项目处于 `0.1.0` 开发阶段。按 [MVP 路线图](docs/product/mvp-roadmap.md) 的里程碑，目前进度：

* **M0 项目重建**：完成。项目标准、需求分析、架构设计、GitHub 协作配置、基础测试已建立。
* **M1 后端基础**：完成。FastAPI、统一配置管理、数据库连接（默认本地 SQLite，可切换 Postgres）、`audit_logs` 表、Docker Compose、数据库初始化脚本均可用。
* **M2 数据源**：完成。yfinance 风格历史日线、SEC EDGAR 财报申报、FRED 宏观数据（需自备免费 Key）、Yahoo 实时走势均已接入并有测试覆盖。
* **M3 AI 分析**：部分完成。Model Layer 统一接口、Output Validator、Agent 基类、SEC Filing Agent 和 Report Agent 已落地并端到端联调；News Agent（独立的 LLM 情绪分析）尚未开发。
* **M4 评分与报告**：部分完成。独立 Algorithm Layer 提供可解释的规则化推荐评分（`algorithm-v0.2.2`，已接入 SEC 真实财务数据和真实技术指标：基本面（净利润率+ROC）/成长性/估值（P/E+EV/EBIT）/技术面（RSI/均线金死叉/动量）/风险五因子），并通过新增的 Workflow Layer（`stocks/screening`）实现批量选股排序；研究报告生成已由 Report Agent 落地，基于大模型的 AI Scoring Agent 尚未开发（`packages/scoring` 仍为空）。
* **M5 前端展示**：部分完成。前端已从单文件 `apps/web/index.html` 迁移为 React + Vite + React Router 的 7 页应用（`apps/web-react/`，HashRouter）：Dashboard、Market Scanner、Stock Research（独立的股票深度分析页，含手绘 K 线图）、Portfolio Research（组合策略工作流）、Strategy Library、Reports（独立的研究报告页）、Settings；后端已切换为服务 `apps/web-react/dist/`，`apps/web/index.html` 保留在磁盘上作为回滚参考、未挂载。
* **M6 Portfolio Strategy / Backtesting**：部分完成。`packages/backtesting` 已提供价格技术面回测（`signal_mode="technical"`）和按披露日期重建历史财报快照的 AI 评分回测（`signal_mode="ai_score"`，`backtesting-v0.2`，新闻情绪因子因无历史新闻归档暂不支持）、仓位分配、风险约束和 `/backtests/run` API；`packages/risk_engine` 已提供独立 Risk Engine v0.1；券商接口 `packages/brokers` 尚未开发。

额外完成的扩展能力（超出原始路线图，但已落地并有测试）：

* Universe Layer：每日扫描美股最活跃 Top 100 候选池（`packages/universe_layer`）
* News / Policy Layer：最近新闻、SEC 披露、政策和内部任免线索（`packages/news_layer`）
* Algorithm Layer：独立于 Model Layer 的可解释推荐算法（`packages/algorithm_layer`）
* Portfolio Strategy：Universe → Strategy Library → Constraints → Backtest → AI Analysis → Portfolio Recommendation（`packages/backtesting`）
* Workflow Engine：通用状态机和 `PortfolioResearchWorkflow v0.1`，接入 `POST /workflows/portfolio-research`，并支持按 `trace_id` 查询历史 workflow run
* Portfolio 权重管理：组合配置可保存目标权重、现金比例和策略设置
* Risk Engine v0.1：输出 Volatility、Beta、Max Drawdown、Average Correlation、Concentration、Sector Exposure
* Portfolio Optimizer v0.1：支持 Equal Weight、Market Cap、Minimum Variance、Risk Parity 初版
* Portfolio Research Module v0.1：统一入口整合 Workflow、Backtesting、Risk、Optimizer、AI Summary 和 Recommendation
* 策略库（Strategy Library）：策略与 Portfolio（股票桶）解耦的独立可复用实体（`packages/db/strategies.py`、`GET/PUT/DELETE /strategies`），前端「策略库」面板支持新增/应用/更新/删除已保存策略
* Scoring Profiles 模型权重模块：把 Algorithm Layer 评分权重从硬编码抽成独立模块（`packages/scoring_profiles`），内置 Balanced/Growth/Value/Defensive/Momentum 5 个只读权重组，接入推荐、选股、回测、Portfolio Research 四个入口的 `scoring_profile` 参数
* Research Run History API：`GET /research-runs`（`packages/research_history`），复用既有 `workflow_runs` 表按时间/组合/策略库存档名查询历史研究运行列表；前端「应用策略」会带上 `strategy_library_name` 一并提交
* Report Archive v0.1：`report_archives` 表和 `/reports` API，可从 Portfolio Research `trace_id` 生成 Markdown/HTML 报告，前端 Report Archive 面板支持生成、刷新、查看报告详情
* 每日研究首页：前端首屏聚合 Most Active Top 100、Top 20 推荐、最近 5 次 Research Run 和当前组合风险摘要
* 数据源健康检查：`GET /data-sources/health` 和前端 Data Source Health 面板展示 Yahoo/SEC/FRED/Tiger 的配置、可用性、最近错误和 fallback 状态
* 数据质量标记：quote/trend/history/filings/news/macro/Tiger 响应新增 `data_quality`（source/as_of/freshness/missing_fields/fallback），前端报价区展示 source/freshness
* Portfolio Manager v0.2：组合支持 JSON/CSV 导入导出和两两对比
* 异步任务队列 Job Queue v0.1：`packages/job_queue`（APScheduler）+ `job_queue` 表，为 screening 和 Portfolio Research Workflow 提供 `POST /jobs/screening`、`POST /jobs/portfolio-research`、`GET /jobs/{job_id}`、`GET /jobs` 异步提交/轮询入口，同步接口保持不变

## 当前差距

详细差距见 [需求与实际开发差距分析](docs/product/IMPLEMENTATION_GAP_ANALYSIS.md)。

项目计划、实际进度、差异和下一步统一维护在 [项目计划与进度总表](docs/product/PROJECT_PLAN_PROGRESS.md)。

当前真实状态：

```text
已完成：架构骨架 + 核心 API + 初版页面 + 初版算法 + 初版回测 + 初版 workflow + 初版报告归档

未完成：多 Agent 自动研究 + PDF/Dashboard 报告 + 商业数据源覆盖
```

下一阶段优先收口：

```text
1. Strategy Library v0.2
2. Stock Research 独立页
3. News Agent / Risk Agent v0.1
4. PDF/Dashboard 报告
```

已完成：PRD v0.3 / Roadmap 对齐、Scoring Profiles / 模型权重模块 v0.1、Research Run History API、Research Run 复盘页、Report Archive v0.1、每日研究首页、数据源健康检查、数据质量标记、Portfolio Manager v0.2。

## 文档入口

最高优先级规则：

* [Project Constitution](PROJECT_CONSTITUTION.md)
* [AI Development Charter](AI_DEVELOPMENT_CHARTER.md)
* [AI Startup Protocol](.ai/AI_STARTUP_PROTOCOL.md)

* [项目标准文档 v0.1](docs/standards/project-standard-v0.1.md)
* [Universe Layer 标准](docs/standards/UNIVERSE_STANDARD.md)
* [News / Policy Layer 标准](docs/standards/NEWS_POLICY_STANDARD.md)
* [Algorithm Layer 标准](docs/standards/ALGORITHM_STANDARD.md)
* [Model Layer 标准](docs/standards/MODEL_STANDARD.md)
* [Workflow Engine 标准](docs/standards/WORKFLOW_ENGINE_STANDARD.md)
* [Portfolio Research Module 标准](docs/standards/PORTFOLIO_RESEARCH_MODULE_STANDARD.md)
* [Portfolio Strategy 标准](docs/standards/PORTFOLIO_STRATEGY_STANDARD.md)
* [Risk Engine 标准](docs/standards/RISK_ENGINE_STANDARD.md)
* [Portfolio Optimizer 标准](docs/standards/PORTFOLIO_OPTIMIZER_STANDARD.md)
* [Tiger OpenAPI 接入标准](docs/standards/TIGER_OPENAPI_STANDARD.md)
* [产品需求文档 PRD v0.3](docs/product/PRD.md)
* [个人股票研究生产力目标](docs/product/PERSONAL_PRODUCTIVITY_GOAL.md)
* [项目计划与进度总表](docs/product/PROJECT_PLAN_PROGRESS.md)
* [需求与实际开发差距分析](docs/product/IMPLEMENTATION_GAP_ANALYSIS.md)
* [需求分析 v0.1](docs/product/requirements-analysis.md)
* [系统设计框架](docs/architecture/system-design.md)
* [AI 开发架构标准](docs/architecture/ai-development-architecture.md)
* [GitHub 协作标准](docs/standards/github-collaboration.md)
* [版本管理标准](docs/standards/version-management.md)
* [敏捷迭代与即开发即使用标准](docs/standards/agile-iteration.md)
* [AI 开发工具协作标准](docs/standards/AI_TOOL_COLLABORATION.md)
* [API 设计 v0.1](docs/api/api-design-v0.1.md)
* [AI 行为总规范](.ai/AGENTS.md)
* [项目 AI 开发规则](.ai/PROJECT_RULES.md)

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
* 组合策略工作流：选择组合、配置收益目标/最大回撤/仓位限制、运行回测、生成组合建议
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
GET http://127.0.0.1:8000/integrations/tiger/status
GET http://127.0.0.1:8000/stocks/AAPL/tiger/quote
GET http://127.0.0.1:8000/stocks/AAPL/tiger/history?years=3&period=day
PUT http://127.0.0.1:8000/portfolios/Core%20Watch/config
GET http://127.0.0.1:8000/strategies
PUT http://127.0.0.1:8000/strategies/Momentum%20Aggressive
DELETE http://127.0.0.1:8000/strategies/Momentum%20Aggressive
POST http://127.0.0.1:8000/portfolio-research/run
GET http://127.0.0.1:8000/portfolio-research/{trace_id}
POST http://127.0.0.1:8000/risk/portfolio
POST http://127.0.0.1:8000/optimizer/portfolio
POST http://127.0.0.1:8000/backtests/run
POST http://127.0.0.1:8000/workflows/portfolio-research
GET http://127.0.0.1:8000/workflows/portfolio-research/{trace_id}
```

FRED 接口需要先在 `.env` 设置免费的 `FRED_API_KEY`（注册地址：https://fred.stlouisfed.org/docs/api/api_key.html），否则返回 503。

Tiger OpenAPI 是可选只读数据源，需要先在 `.env` 设置 `TIGER_ID`、`TIGER_ACCOUNT`、`TIGER_LICENSE`、`TIGER_PRIVATE_KEY_PATH` 和 `TIGER_ENV`。当前接入边界支持单股 quote 和最多近 3 年 K 线参考数据，不读取或抓取老虎 App，不提供自动交易接口。

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

第二个落地的 Agent：

```text
GET http://127.0.0.1:8000/stocks/AAPL/report
```

`ReportAgent`（`packages/ai_agents/report_agent.py`）走同一条流水线，Data Context Builder 复用 `/stocks/{symbol}/recommendation` 的五因子算法评分（`TrendRecommendationAlgorithm`）和近期新闻/政策信号（`NewsPolicyClient`），由模型把评分和新闻综合成一段研究结论。已用真实数据（AAPL）做过端到端联调，工作台右侧「生成研究报告」按钮已接入。

Agent 基类见 `packages/ai_agents/base.py`，后续 News Agent 复用同一流水线。

## AI 选股 Workflow（M4）

```text
GET http://127.0.0.1:8000/stocks/screening?limit=20
```

`StockScreeningWorkflow`（`packages/workflow_layer/stock_screening.py`）把 Universe Layer 的候选池（Most Active Top 100）逐个用 Algorithm Layer v0.2.2 打分，并发请求（最多 8 个并发）后按总分排序返回。这是"自己选股"场景的核心入口：不指定单一股票，直接看候选池里排序靠前的标的。已用真实数据端到端联调（20 只股票全部评分成功，约 56 秒）。

通用 Workflow Engine 骨架见 `packages/workflow_layer/engine.py`，标准见 `docs/standards/WORKFLOW_ENGINE_STANDARD.md`。它负责节点编排、状态机、trace_id、输入输出摘要、耗时和失败记录；不负责具体算法计算，也不直接调用模型供应商 SDK。

`PortfolioResearchWorkflow`（`packages/workflow_layer/portfolio_research.py`）是第一个组合研究闭环 workflow：

```text
Universe Builder
  -> Portfolio Builder
  -> Strategy Selector
  -> Constraint Config
  -> Backtest Runner
  -> AI Summary
  -> Portfolio Recommendation
```

API 入口为 `POST /workflows/portfolio-research`。v0.1 的 AI Summary 是可审计的规则解释，后续可替换为 Research Agent / Report Agent 节点。每次运行都会写入 `workflow_runs` 表，并可通过 `GET /workflows/portfolio-research/{trace_id}` 复盘节点状态、回测结果、AI Summary 和 Portfolio Recommendation。当前工作台已接入 Research Run 复盘面板，消费 `GET /research-runs` 和 `GET /portfolio-research/{trace_id}`，可按组合、策略、状态和日期打开历史研究详情。

每次调用都会把候选评分写入 `stock_scores` 表（`packages/db/stock_scores.py`），通过 `GET /stocks/{symbol}/score-history` 可以读出某只股票历次评分，方便对比"这只股票最近几次扫描分数是涨是跌"——这是把 AI 选股从一次性即时计算变成有历史记录的个人工具的关键一步。

### 技术面因子（algorithm-v0.2.1）

`technical` 因子不再是粗略的区间涨跌幅估算，而是基于近 1 年日线收盘价（`packages/data_sources/price_history.py`）计算的真实技术指标（`packages/algorithm_layer/technical_indicators.py`）：10 日动量（40%）、RSI-14（30%）、均线 5/20 金叉死叉状态（30%）。日线数据不足（如新上市股票）时自动退化为旧的区间走势粗估，并在 `explanation` 中说明。计算出的 RSI 数值和均线状态通过 `factors[].explanation` 字段暴露，可用于替换前端面板上现有的占位 RSI/均线标签。

### 基本面/估值因子加入 Magic Formula 指标（algorithm-v0.2.2）

`fundamentals` 因子加入 ROC（资本回报率 = 营业利润 / (净营运资本 + 净固定资产)），跟净利润率各占 50%；`valuation` 因子加入 EV/EBIT（企业价值 / 营业利润），跟 P/E 各占 50%。这是 Joel Greenblatt「Magic Formula」选股法用的两个经典指标，衡量原来的净利润率/P/E 漏掉的资本使用效率和负债/现金对真实估值的影响。任一指标缺 SEC 财报数据时自动退化为只用另一半，两者都缺时退化为中性分，详见 `docs/standards/ALGORITHM_STANDARD.md` 第 9.3 节。

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

## GitHub 协作入口

GitHub 协作标准见：

```text
docs/standards/github-collaboration.md
```

提交 Issue 或 Pull Request 前请确认：

* 已选择对应模板
* 已说明修改范围和测试结果
* 已更新相关文档
* 未提交 API Key、Token、券商账户或真实交易记录
* 投资研究相关输出保留风险提示
