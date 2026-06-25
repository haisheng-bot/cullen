# 第一阶段 MVP 路线图 v0.1

## 1. MVP 范围

第一阶段只做：

* 股票代码查询
* 美股基础数据
* 实时走势图
* 美股操作界面
* SEC 财报读取
* AI 财报总结
* 新闻摘要
* 股票评分
* 研究报告生成
* 本地数据库保存

## 2. 暂不做

* 自动交易
* 实盘下单
* 期权策略
* 杠杆交易
* 高频交易

## 3. 里程碑

### M0 项目重建

* 标准文档 [released]
* 需求分析 [released]
* 架构设计 [released]
* GitHub 协作配置 [released]
* 基础测试 [released]

### M1 后端基础

* FastAPI 初始化 [usable]
* 配置管理（`packages/config.py`，环境变量 + `.env`） [verified]
* 数据库连接（`packages/db/session.py`，SQLAlchemy，默认回退本地 SQLite） [verified]
* audit_logs 表（`packages/db/models.py` + `packages/db/audit.py`） [verified]
* Docker Compose 本地 Postgres + Redis（`docker/docker-compose.yml`） [usable]
* 数据库初始化脚本（`scripts/init_db.py`） [usable]

### M2 数据源

* yfinance（近 10 年免费历史日 / 周 / 月线，`packages/data_sources/price_history.py`） [verified]
* SEC EDGAR（按代码解析 CIK，读取 10-K / 10-Q / 8-K 列表，`packages/data_sources/sec_filings.py`） [verified]
* FRED（`packages/data_sources/fred.py`，需用户自备免费 Key，目前仅 mock payload 测试，未做真实联调） [usable]
* 实时走势 API 接入 [usable]

### M3 AI 分析

* 模型统一接口（`packages/model_layer`，mock provider + LiteLLM-compatible provider，无 Key 自动 fallback mock，有 Key 自动切换 litellm） [verified]
* Output Validator（`packages/model_layer/validator.py`，已接入 ModelRouter，强制检查风险提示/数据来源/禁止词） [verified]
* Agent 基类（`packages/ai_agents/base.py`，Policy Guard → Data Context Builder → Workflow Executor → Model Layer → Output Validator → Audit Logger） [verified]
* SEC Filing Agent（`packages/ai_agents/sec_filing_agent.py`，接入 `/stocks/{symbol}/sec-summary`，已用真实 SEC 数据端到端联调） [verified]
* News Agent（消费 `packages/news_layer` 原始数据 + 情绪分析，待接 FinBERT 或 LLM） [planned]
* Report Agent [planned]

### M4 评分与报告

* 规则化推荐评分（Algorithm Layer，`algorithm-v0.2.1`，已接入真实 SEC 财务数据和真实技术指标：基本面/成长性/估值/技术面（RSI/均线金死叉/动量）/风险五因子） [verified]
* AI 选股批量排序（Workflow Layer，`packages/workflow_layer/stock_screening.py`，并发扫描候选池并按分排序，`/stocks/screening`） [verified]
* 选股结果落库存历史（`stock_scores` 表 + `/stocks/{symbol}/score-history`，支持按时间对比同一只股票的评分变化） [verified]
* Scoring Agent（基于 Model Layer 的 AI 评分，区别于上面的规则算法） [planned]
* 研究报告生成 [planned]

### M5 前端展示

* 美股操作工作台（关注列表、搜索、报价、走势、候选池、推荐评分、项目状态面板） [usable]
* 实时走势图页面 [usable]
* 股票分析页面（独立深度分析页，区别于操作工作台） [planned]
* 研究报告页面 [planned]

### 额外扩展（超出原路线图）

* Universe Layer：每日扫描美股最活跃 Top 100 候选池（`packages/universe_layer`） [verified]
* Algorithm Layer：独立于 Model Layer 的可解释推荐算法（`packages/algorithm_layer`） [verified]
* News / Policy Layer：原始新闻、监管披露和公司治理事件抓取（`packages/news_layer`，区别于 News Agent 的 AI 分析） [verified]
* 一键启动脚本 `open-app.command` [usable]
* 项目开发界面：展示版本、架构层和当前状态 [usable]
