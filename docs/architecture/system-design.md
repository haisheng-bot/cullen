# OpenStock AI 系统设计框架 v0.1

## 1. 总体架构

```text
apps/web
  -> apps/api
  -> packages/ai_agents
  -> packages/data_sources
  -> packages/scoring
  -> PostgreSQL / Redis
```

## 2. 后端

后端使用 Python、FastAPI、SQLAlchemy、Pydantic、PostgreSQL、Redis 和 Celery / APScheduler。

后端职责：

* REST API
* 参数校验
* 数据源调用
* Agent 编排
* 评分计算
* 研究报告生成
* audit_logs 写入

## 3. 前端

前端使用 Next.js、TypeScript、Tailwind CSS、ECharts / Recharts。

前端职责：

* 股票查询
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
* Alpha Vantage
* Finnhub
* Polygon

## 5. AI Agent 层

Agent 位于 `packages/ai_agents`，至少包括：

* Market Data Agent
* SEC Filing Agent
* News Agent
* Scoring Agent
* Report Agent

## 6. 审计日志

所有 AI 输出必须写入 `audit_logs`。

每条记录至少包含：

* 数据来源
* 分析时间
* 使用模型
* 输入数据摘要
* 生成结论
* 风险提示

本系统仅用于投资研究辅助，不构成任何投资建议。

