# 第一阶段 MVP 路线图 v0.1

## 1. MVP 范围

第一阶段产品目标：OpenStock AI 先成为 Cullen 的个人股票研究生产力工具，支撑每日股票池扫描、候选股排序、单股研究、Portfolio 跟踪、策略回测、AI 解释、研究报告归档和次日复盘。

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
* 个人研究记录沉淀
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
* Tiger OpenAPI 只读接入边界（配置状态、quote、最多近 3 年历史 K 线参考数据，真实官方 SDK adapter 待完善） [usable]

### M3 AI 分析

* 模型统一接口（`packages/model_layer`，mock provider + LiteLLM-compatible provider，无 Key 自动 fallback mock，有 Key 自动切换 litellm） [verified]
* Output Validator（`packages/model_layer/validator.py`，已接入 ModelRouter，强制检查风险提示/数据来源/禁止词） [verified]
* Agent 基类（`packages/ai_agents/base.py`，Policy Guard → Data Context Builder → Workflow Executor → Model Layer → Output Validator → Audit Logger） [verified]
* SEC Filing Agent（`packages/ai_agents/sec_filing_agent.py`，接入 `/stocks/{symbol}/sec-summary`，已用真实 SEC 数据端到端联调） [verified]
* Report Agent（`packages/ai_agents/report_agent.py`，接入 `/stocks/{symbol}/report`，复用算法层五因子评分 + News/Policy Layer 近期信号生成研究结论，已用真实数据端到端联调并接入工作台「生成研究报告」按钮） [verified]
* News Agent（消费 `packages/news_layer` 原始数据 + 情绪分析，待接 FinBERT 或 LLM） [planned]

### M4 评分与报告

* 规则化推荐评分（Algorithm Layer，`algorithm-v0.3`，已接入真实 SEC 财务数据、真实技术指标和规则化新闻情绪：基本面（净利润率+ROC）/成长性/估值（P/E+EV/EBIT）/技术面（RSI/均线金死叉/动量）/新闻情绪/风险六因子） [verified]
* Scoring Profiles 模型权重模块（`packages/scoring_profiles`，把上述六因子权重从硬编码抽成 Balanced/Growth/Value/Defensive/Momentum 5 个内置只读权重组，接入 `/stocks/{symbol}/recommendation`、`/stocks/screening`、`/backtests/run`、`/portfolio-research/run` 的 `scoring_profile` 参数） [verified]
* AI 选股批量排序（Workflow Layer，`packages/workflow_layer/stock_screening.py`，并发扫描候选池并按分排序，`/stocks/screening`） [verified]
* 选股结果落库存历史（`stock_scores` 表 + `/stocks/{symbol}/score-history`，支持按时间对比同一只股票的评分变化） [verified]
* Scoring Agent（基于 Model Layer 的 AI 评分，区别于上面的规则算法） [planned]
* 研究报告生成（Report Agent，见 M3，`/stocks/{symbol}/report`） [verified]

### M5 前端展示

* 美股操作工作台（关注列表、搜索、报价、走势、候选池、推荐评分、项目状态面板） [usable]
* 实时走势图页面 [usable]
* 股票分析页面（独立深度分析页，区别于操作工作台） [planned]
* 研究报告面板（工作台右侧「生成研究报告」按钮，接入 `/stocks/{symbol}/report`） [verified]，独立的研究报告页面仍为 [planned]

### M6 Portfolio Strategy / Backtesting

* Portfolio Strategy Engine（`packages/backtesting`，`backtesting-v0.1`：仓位分配、技术面信号买卖规则、风险熔断、回测指标）[verified]
* `POST /backtests/run` + 前端组合策略工作流（Universe → Strategy Library → Constraints → Backtest → Recommendation） [usable]
* Portfolio Strategy Engine 升级到 `backtesting-v0.2`：按披露日期重建历史财报快照（`parse_companyfacts_series`），新增 `signal_mode="ai_score"` 复用基本面/成长/估值/技术/波动风险五因子回测（新闻情绪因子因无历史新闻归档暂不支持） [verified]
* 组合策略工作流前端体验改造：高级设置（信号模式/再平衡频率/基准/止损）、净值曲线图、交易明细表、提交前字段校验、加载态、6步流程动态状态 [verified]
* 新闻情绪因子的历史回测：依赖接入有历史归档的新闻数据源 [planned]
* 券商接口 `packages/brokers` [planned]

### M7 Workflow Engine / Portfolio Research

* Workflow Engine 通用状态机（Created → Configured → Waiting → Running → Completed → AI Reviewing → Recommendation Ready → Archived）[verified]
* Workflow 节点观测（trace_id、节点输入摘要、输出摘要、耗时、失败记录）[verified]
* Portfolio Research Workflow v0.1（Universe Builder → Portfolio Builder → Strategy Selector → Constraint Config → Backtest Runner → AI Summary → Portfolio Recommendation）[verified]
* `POST /workflows/portfolio-research` API [verified]
* 前端完整接入 Portfolio Research Workflow，并展示节点状态和 trace_id [verified]
* Workflow Run 持久化与按 trace_id 查询复盘 [verified]
* Research Run History API（`packages/research_history`、`GET /research-runs`，按时间/组合/策略库存档名查询历史运行列表，复用既有 `workflow_runs` 表） [verified]
* 完整 Workflow / Report 复盘页（前端历史列表/详情页，消费 `GET /research-runs`） [planned]
* Portfolio Research Module v0.1（一个入口整合 Workflow、Backtesting、Risk、Optimizer、AI Summary、Recommendation）[verified]
* `POST /portfolio-research/run` 和 `GET /portfolio-research/{trace_id}` [verified]
* 前端 Portfolio Research Workbench 调用统一入口 [verified]

### M8 Portfolio / Risk MVP

* Portfolio 权重管理（`PUT /portfolios/{name}/config`，保存 target_weights、cash_weight；策略参数已收敛到独立的策略库，不再重复保存在这里）[verified]
* Risk Engine v0.1（`packages/risk_engine`，输出 Volatility、Beta、Max Drawdown、Average Correlation、Concentration、Sector Exposure）[verified]
* `POST /risk/portfolio` API [verified]
* 前端组合策略面板保存权重并展示 Risk Engine 摘要 [verified]
* Portfolio Optimizer v0.1（`packages/portfolio_optimizer`，支持 Equal Weight、Market Cap、Minimum Variance、Risk Parity 初版）[verified]
* `POST /optimizer/portfolio` API [verified]
* 前端组合策略面板展示 Optimizer 目标权重摘要 [verified]
* 策略库 Strategy Library（`packages/db/strategies.py`，策略与 Portfolio 解耦的独立可复用实体）[verified]
* `GET/PUT/DELETE /strategies` API [verified]
* 前端「策略库」面板支持新增/应用/更新/删除已保存策略，选股加入组合的动作改为跟随当前查看的股票（右边栏），不再绑定在左边栏的桶选择上 [verified]

### 额外扩展（超出原路线图）

* Universe Layer：每日扫描美股最活跃 Top 100 候选池（`packages/universe_layer`） [verified]
* Algorithm Layer：独立于 Model Layer 的可解释推荐算法（`packages/algorithm_layer`） [verified]
* News / Policy Layer：原始新闻、监管披露和公司治理事件抓取（`packages/news_layer`，区别于 News Agent 的 AI 分析） [verified]
* 一键启动脚本 `open-app.command` [usable]
* 项目开发界面：展示版本、架构层和当前状态 [usable]

## 4. 当前差距

详细文档见：

* `docs/product/PROJECT_PLAN_PROGRESS.md`
* `docs/product/IMPLEMENTATION_GAP_ANALYSIS.md`

当前已经完成：

```text
架构骨架 + 核心 API + 初版页面 + 初版算法 + 初版回测 + 初版 workflow
```

仍需补齐：

```text
Trace 复盘页 + Report Archive + 稳定数据体系 + 多 Agent 自动研究
```

下一阶段优先级：

```text
1. trace_id 完整复盘页
2. Report Archive v0.1
3. 数据源健康检查
4. Strategy Library v0.2
5. Portfolio Manager v0.2
```

已完成并从下一阶段移除：

```text
PRD v0.3 / Roadmap 对齐
Scoring Profiles / 模型权重模块 v0.1
Research Run History API
前端接入 Portfolio Research Workflow
Portfolio 权重管理
Risk Engine v0.1
Portfolio Optimizer v0.1
Strategy Library v0.1
Portfolio Research Module v0.1
```
