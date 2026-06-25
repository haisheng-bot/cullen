# OpenStock AI 系统设计框架 v0.1

## 1. 总体架构

```text
Application Layer
        |
Agent Layer
        |
Workflow Layer
        |
Algorithm Layer
        |
Model Layer
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
* Alpha Vantage
* Finnhub
* Polygon

## 5. Algorithm Layer

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

## 6. Model Layer

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

## 7. AI Agent 层

Agent 位于 `packages/ai_agents`，至少包括：

* Market Data Agent
* SEC Filing Agent
* News Agent
* Scoring Agent
* Report Agent

Agent 只负责任务定义和业务推理目标，不负责模型供应商适配。

## 8. 审计日志

所有 AI 输出必须写入 `audit_logs`。

每条记录至少包含：

* 数据来源
* 分析时间
* 使用模型
* 输入数据摘要
* 生成结论
* 风险提示

本系统仅用于投资研究辅助，不构成任何投资建议。
