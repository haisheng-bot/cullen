# Changelog

## [0.1.0] - Unreleased

### Added

* 重建 project5 为 OpenStock AI
* 项目标准文档 v0.1
* 需求分析 v0.1
* 系统设计框架
* AI 开发架构标准
* GitHub 协作标准
* 版本管理标准
* 敏捷迭代与即开发即使用标准
* 基础 CI 和治理测试
* 实时走势 API 和前端趋势图 MVP
* 独立 Model Layer 标准、目录和 mock provider
* AI 开发工具协作标准，支持 Codex、Claude Code、Cursor 混用开发
* 美股操作界面 MVP，包含热门美股、搜索、报价和实时走势
* 双击启动脚本 `open-app.command`
* 独立 Algorithm Layer 和趋势型推荐算法，并接入操作界面
* LiteLLM-compatible Model Layer provider 和标准
* 项目开发界面，展示版本、架构层和当前可用状态
* Universe Layer，用于每日扫描美股最活跃 Top 100 候选池
* 操作界面增加常用分析维度解读区域
* News / Policy Layer，展示最近新闻和 3 年 SEC 披露线索
* 走势图升级为券商式滑动界面，支持十字坐标、成交量和成交额读数
* 常用分析维度升级为可用数据面板，展示成交量、Rel Vol、RSI、均线、52 周位置等实时指标
* 实时行情坐标分析增加估算换手率、买量和卖量展示
* 操作界面增加美国概念板块预览，按 Most Active Top 100 聚合 AI、半导体、EV、Crypto 等概念热度
* 后端基础：统一配置管理、数据库连接层、audit_logs 表，以及 Docker Compose（Postgres + Redis）和数据库初始化脚本
* yfinance 风格免费历史日线数据源（近 10 年日 / 周 / 月线 OHLCV），接入 `/stocks/{symbol}/history`
* SEC EDGAR 财报申报读取（免费，按代码解析 CIK，列出 10-K / 10-Q / 8-K 原文链接），接入 `/stocks/{symbol}/filings`
* FRED 宏观数据源（需用户自备免费 API Key），接入 `/macro/{series_id}/observations`
* Model Layer Output Validator：返回前强制检查风险提示、数据来源、模型信息和禁止词，已接入 ModelRouter
* Agent 基类（`packages/ai_agents/base.py`）落地 Policy Guard → Data Context Builder → Workflow Executor → Model Layer → Output Validator → Audit Logger 流水线
* SEC Filing Agent（M3 第一个 Agent），接入 `/stocks/{symbol}/sec-summary`，已用真实 SEC EDGAR 数据端到端联调并验证 audit_logs 落库
* Model Layer 路由工厂 `build_default_router()`：无 Key 时 fallback 到 mock provider，配置任意模型 Key 后自动切换 litellm provider
* SEC EDGAR XBRL 财务数据源（`packages/data_sources/sec_financials.py`），免费读取营收/净利润/EPS/股东权益等真实财报数据
* Algorithm Layer 升级到 `algorithm-v0.2`：加入基本面、成长性、估值三个真实数据因子，与原技术面/风险因子合并为五维度评分，`/stocks/{symbol}/recommendation` 已接入真实 SEC 财务数据并端到端联调
* Workflow Layer 和 AI 选股批量排序：`packages/workflow_layer/stock_screening.py` 把候选池逐个用 Algorithm Layer 并发评分排序，接入 `/stocks/screening`，已端到端联调
