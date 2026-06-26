# OpenStock AI 系统设计框架 v0.1

## 1. 总体架构

```text
Application Layer
        |
Agent Layer
        |
Workflow Engine
        |
Universe Layer
        |
Algorithm Layer
        |
Model Layer
        |
News / Policy Layer
        |
Knowledge Layer
        |
Data Layer
```

## 2. 后端

后端使用 Python、FastAPI、SQLAlchemy、Pydantic、PostgreSQL、Redis 和 Celery / APScheduler。

后端职责：

* REST API
* 参数校验
* 美股搜索和报价接口
* 每日候选池扫描
* 新闻、政策和披露查询
* 数据源调用
* 实时走势 API
* Agent 编排
* 评分计算
* 推荐算法调用
* 研究报告生成
* audit_logs 写入

## 3. 前端

前端使用 Next.js、TypeScript、Tailwind CSS、ECharts / Recharts。

前端职责：

* 股票查询
* 美股操作工作台
* 实时走势图
* AI 选股列表
* 股票分析页
* 评分展示
* 研究报告展示
* 回测结果展示
* 风险提示展示

## 4. 数据源层

所有外部数据源必须封装在 `packages/data_sources`。

第一阶段数据源：

* yfinance
* SEC EDGAR
* FRED
* Tiger OpenAPI（可选，只读，需用户自行配置 OpenAPI 凭证，支持 quote 与最多近 3 年 K 线参考数据）
* Alpha Vantage
* Finnhub
* Polygon

Tiger OpenAPI 不得通过抓取或自动操作老虎 App 接入；只能通过官方 OpenAPI 和 `packages/data_sources/tiger_openapi.py` 读取授权数据。第一阶段的历史行情边界是 K 线/OHLCV/成交额参考数据，不作为逐笔 tick 全量数据源。

## 5. Workflow Engine

Workflow Engine 位于 `packages/workflow_layer`，是 OpenStock AI 的业务编排层。

Workflow Engine 负责：

* Universe Builder
* Portfolio Builder
* Factor Engine
* Strategy Engine
* Constraint Engine
* Portfolio Optimizer
* Backtesting Engine
* Risk Engine
* AI Research Agent 调度
* Recommendation Engine
* Report Engine
* Rebalance Engine
* 节点状态、trace_id、输入输出摘要、耗时和失败记录

Workflow Engine 不负责：

* 具体因子计算
* 直接模型供应商 SDK 调用
* 直接券商下单
* 硬编码外部 API Key

统一状态机：

```text
Created -> Configured -> Waiting -> Running -> Completed
  -> AI Reviewing -> Recommendation Ready -> Archived
```

详细标准见：

* `docs/standards/WORKFLOW_ENGINE_STANDARD.md`

## 6. Universe Layer

候选池层位于 `packages/universe_layer`，用于每日扫描美股交易最活跃的 100 只股票。

Universe Layer 负责：

* Most Active Top 100
* 市场常见筛选维度
* 每日候选池
* 候选股票标签
* 给 Algorithm Layer 和 Agent Layer 提供输入

详细标准见：

* `docs/standards/UNIVERSE_STANDARD.md`

## 7. Algorithm Layer

算法层位于 `packages/algorithm_layer`，独立于 API、前端、Agent 和 Model Layer。

Algorithm Layer 负责：

* 推荐算法
* 股票评分
* 因子计算
* 推荐等级
* 风险因子
* 候选股排序

详细标准见：

* `docs/standards/ALGORITHM_STANDARD.md`

## 8. Model Layer

模型层位于 `packages/model_layer`，是独立于 Agent 的核心层。

Model Layer 负责：

* OpenAI / Claude / Gemini / DeepSeek / Qwen / Llama / 本地模型适配
* 模型统一请求和响应
* 模型路由
* fallback
* token 和成本统计
* 输出校验
* 模型审计字段

Agent、Workflow、API 和 Data Source 不得直接调用具体模型 SDK。

详细标准见：

* `docs/standards/MODEL_STANDARD.md`

## 9. News / Policy Layer

新闻政策层位于 `packages/news_layer`，负责公司新闻、SEC 披露、政策和治理事件。

第一阶段接入：

* Yahoo Finance RSS
* SEC EDGAR
* 3 年查询窗口
* 内部任免披露候选

详细标准见：

* `docs/standards/NEWS_POLICY_STANDARD.md`

## 10. AI Agent 层

Agent 位于 `packages/ai_agents`，至少包括：

* Market Data Agent
* SEC Filing Agent
* News Agent
* Scoring Agent
* Report Agent

Agent 只负责任务定义和业务推理目标，不负责模型供应商适配。

## 11. 审计日志

所有 AI 输出必须写入 `audit_logs`。

每条记录至少包含：

* 数据来源
* 分析时间
* 使用模型
* 输入数据摘要
* 生成结论
* 风险提示

本系统仅用于投资研究辅助，不构成任何投资建议。
