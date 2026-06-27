# OpenStock AI Portfolio Strategy 标准 v0.1

## 1. 定位

Portfolio Strategy Engine 是 OpenStock AI 的组合投资策略模块，负责对一组股票在指定时间区间内进行仓位分配、买卖规则执行、风险控制、回测评估和结果解释。这个模块可以作为 OpenStock AI 的第二核心，仅次于 Model Layer。

该模块只用于投资研究辅助，不构成任何投资建议。

## 2. 标准流程

```text
股票池（Universe）
        |
选择策略（Strategy Library）
        |
配置约束（收益目标、最大回撤、仓位限制）
        |
运行回测（Backtest）
        |
AI 自动分析结果（收益、风险、原因）
        |
生成投资组合建议（Portfolio Recommendation）
```

## 3. 架构边界

Portfolio Strategy 不应写在前端页面或 Agent 内部。

职责分层：

* Application Layer：展示组合、约束（含基础/高级两级配置和提交前字段校验）、回测结果（指标卡片、净值曲线图、交易明细表）和免责声明；6 步流程状态随组合/配置/运行进度动态更新。
* Workflow Layer：编排 Universe、Strategy、Backtest、Model Analysis。
* Algorithm / Backtesting Layer：执行仓位分配、信号规则、风险控制和回测指标计算。
* Model Layer：后续负责对回测结果做自然语言解释和审计，不直接计算收益。
* Data Layer：提供历史价格、行情、行业和后续财报/新闻数据。

代码落地在 `packages/backtesting/`（与 `algorithm_layer/`、`workflow_layer/` 同级的顶层包，对应文档里的 Algorithm / Backtesting Layer）：

```text
packages/backtesting/
├── schemas.py      策略配置、规则、回测结果等数据结构（含 signal_mode/min_ai_score/max_ai_score）
├── signals.py       Signal Engine：技术指标（复用 algorithm_layer/technical_indicators.py）+
│                    ai_score（复用 algorithm_layer/financial_factors.py）+
│                    select_financials_as_of（按披露日期过滤，回测核心防穿越函数）
├── allocation.py    Position Sizing：等权 / 低波动 / 技术评分(或 ai_score) / 市值加权 + 仓位上限与现金底线
├── risk.py          Risk Engine：止损、组合最大回撤熔断、行业暴露检查
├── engine.py        Strategy Engine + Backtest Engine：PortfolioBacktestEngine.run()
└── performance.py   Performance Evaluator：收益、回撤、Sharpe、胜率、Alpha/Beta
```

`packages/data_sources/sec_financials.py` 的 `parse_companyfacts_series` / `SECFinancialsClient.fetch_annual_series` 提供按披露日期标注的历史财报系列；`packages/db/financial_facts_cache.py` 缓存该系列（24 小时 TTL，与价格缓存同构）。

## 4. 阶段范围

**第一阶段（`backtesting-v0.1`）为什么只用技术面信号，不直接用 `/stocks/{symbol}/recommendation` 的完整 AI 评分：**

旧版 `packages/data_sources/sec_financials.py` 只暴露最新 1-2 个财年数据，没有保留每条 XBRL 财务事实的实际披露日期（`filed` 字段）。如果直接把这套评分接入回测，会在历史调仓日"看到"当时还没披露的财报数据，即未来数据穿越（lookahead bias），回测结果会失真且无法被信任。

价格 / 技术指标（动量、RSI、均线金死叉）天然不存在这个问题——它们是某个历史日期之前收盘价序列的纯函数，只要截到调仓日为止取数即可保证不穿越。因此第一阶段的买卖规则和仓位评分只使用技术面信号，命名为 `technical_score` 而非 `ai_score`，避免被误读为验证了完整的 5 维 AI 评分。

**第二阶段（`backtesting-v0.2`）：按披露日期重建历史财报快照，新增 `signal_mode="ai_score"`。**

`packages/data_sources/sec_financials.py` 的 `parse_companyfacts_series` 现在保留每个财年最早的 `filed` 日期（`AnnualFinancials.filed_date`），`packages/backtesting/signals.py` 的 `select_financials_as_of(series, as_of_date)` 只返回 `filed_date <= as_of_date` 的财年——这是修复未来数据穿越的关键函数，有专门的回归测试（一个财年的数据在其 `filed_date` 之前必须不可见）。

`ai_score` 是 algorithm-v0.3 的基本面(0.30)/成长(0.20)/估值(0.20)/技术(0.10)/新闻情绪(0.10)/波动风险(0.10) 六因子去掉新闻情绪后，剩余权重按比例放大到合计 1.0：基本面 1/3、成长 2/9、估值 2/9、技术 1/9、波动风险 1/9（见 `packages/backtesting/signals.py` 的 `AI_SCORE_WEIGHTS`）。**新闻情绪因子被排除**：`packages/news_layer/news_policy.py` 的 Yahoo Finance RSS 新闻源只能拿到"当前"最新新闻，没有历史新闻归档（模块自带的 `COVERAGE_NOTE` 也写明"完整 3 年新闻归档需要专门的归档新闻源"），无法在历史回测里保证不穿越，因此第二阶段也无法把它纳入 `ai_score`。

`StrategyConfig.signal_mode`（`"technical"` 默认 / `"ai_score"`）控制买卖规则和仓位评分用哪套分数；`min_technical_score`/`max_technical_score` 两种模式下含义不变（始终是技术分阈值），新增的 `min_ai_score`/`max_ai_score` 只在 `signal_mode="ai_score"` 时生效——一个字段名永远只代表一种分数，不会被静默重新定义。

第一阶段实现：

* 使用 Most Active Top 100 作为候选股票池。
* 支持人工选择股票组合。
* 支持策略库选择：
  * 等权组合
  * 技术评分加权
  * 低波动加权
  * 市值加权
* 支持约束配置：
  * 收益目标
  * 最大回撤
  * 单只股票最大仓位
  * 最低现金比例
  * 回测年限
  * 初始资金
  * 高级设置（默认折叠）：信号模式（`technical`/`ai_score`）、再平衡频率、基准代码、止损 %
* 调用 `POST /backtests/run` 执行历史回测。
* 输出收益、年化收益、最大回撤、Sharpe、Alpha、贡献股票、风险提示，以及净值曲线图（组合 vs 基准）和完整交易明细表。

第一阶段不做（第二阶段已完成）：

* ~~使用未来数据的回测~~ → 第二阶段已通过按披露日期重建历史财报快照修复（`ai_score` 模式）。

第二阶段仍不做：

* 自动实盘下单
* 保证收益
* 无人工确认的交易
* 新闻情绪因子的历史回测（无历史新闻归档数据源，见上文）

## 5. API 标准

组合策略前端面板调用的是 Workflow Layer 入口：

```text
POST /workflows/portfolio-research
GET /workflows/portfolio-research/{trace_id}
POST /risk/portfolio
POST /optimizer/portfolio
POST /portfolio-research/run
```

请求必须包含：

* portfolio_name
* universe_limit
* selected_symbols（可选，省略时回退到 `backtest.symbols`）
* backtest（嵌套对象，字段同下方 `POST /backtests/run` 的请求体）：
  * strategy_name
  * symbols
  * start_date
  * end_date
  * initial_cash
  * benchmark_symbol
  * signal_mode（`"technical"` 或 `"ai_score"`）
  * allocation
  * entry_rules
  * exit_rules
  * risk
  * sector_map

响应必须包含：

* trace_id
* state（`"Recommendation Ready"` 或 `"Failed"`）
* node_results（每个节点的 name/module/state/duration_ms/error）
* backtest（嵌套对象，等同 `POST /backtests/run` 的响应体：total_return_percent、annualized_return_percent、max_drawdown_percent、sharpe_ratio、benchmark_total_return_percent、alpha_percent、beta、contributions、trades、equity_curve、suggestions、risks、source、algorithm_version、generated_at）
* ai_summary（conclusion、key_findings，模板生成，非实时模型推理）
* portfolio_recommendation（action、reasons、suggestions、risks、risk_disclaimer）
* risk_disclaimer

每次 `POST /workflows/portfolio-research` 都必须把完整可序列化响应写入 `workflow_runs`，并支持通过 `GET /workflows/portfolio-research/{trace_id}` 复盘同一次 workflow 的节点状态、回测结果、AI Summary 和 Portfolio Recommendation。

组合风险摘要通过 `POST /risk/portfolio` 调用独立 Risk Engine v0.1，输出 Volatility、Beta、Max Drawdown、Average Correlation、Concentration 和 Sector Exposure。

目标权重建议通过 `POST /optimizer/portfolio` 调用独立 Portfolio Optimizer v0.1，支持 Equal Weight、Market Cap、Minimum Variance 和 Risk Parity 初版。

前端 Portfolio Research Workbench 应优先调用 `POST /portfolio-research/run` 作为统一体验入口；上面的 Workflow、Risk、Optimizer API 保留为底层模块接口和调试入口。

底层单次回测仍可直接调用：

```text
POST /backtests/run
```

请求/响应字段与上面 `backtest` 嵌套对象一致；该端点保留供测试、脚本和未来其他调用方使用，前端组合策略面板不再直接调用它。

### 5.1 策略库（Strategy Library）

策略与组合（Portfolio，即一组股票）完全解耦：组合只管"有哪些股票"，策略只管"用什么参数测试"，任意已保存的策略可以套用在任意组合上。

```text
GET /strategies
PUT /strategies/{name}
DELETE /strategies/{name}
```

* `GET /strategies` 返回全部已保存策略：`items: [{name, preferences, constraints, updated_at}]`。
* `PUT /strategies/{name}` 新增或更新（按名字 upsert）：
  * `preferences`：`scoring_mode`、`backtest_mode`（`"technical"` 或 `"ai_score"`）、`optimizer_method`（`equal_weight`/`market_cap`/`minimum_variance`/`risk_parity`）、`rebalance_frequency`（`weekly`/`monthly`/`quarterly`）。
  * `constraints`：`max_position_weight`、`min_cash_weight`、`max_drawdown`、`benchmark_symbol`、`backtest_years`。
  * 这组字段直接对应 Portfolio Research Workbench 表单当前值（`packages/portfolio_research/schemas.py` 的 `StrategyPreferences`/`ResearchConstraints`），不是另一套独立定义。
* `DELETE /strategies/{name}` 删除一个已保存策略，不存在时返回 404。

前端「策略库 Strategy Library」面板（左边栏）提供新增/应用/更新/删除：应用会把已保存策略的参数写回表单（不自动运行），调整后可以「更新」覆盖保存，或用新名字「新增策略」存成一个克隆变体；运行回测时仍然是表单当前值通过 `POST /portfolio-research/run` 提交，策略库只负责参数的保存与复用，不参与运行时编排。

## 6. 版本管理

代码中的实际版本号是 `BacktestResult.algorithm_version`（`packages/backtesting/engine.py` 的 `ALGORITHM_VERSION` 常量），与下表一一对应：

```text
portfolio-strategy-v0.1  组合策略工作流与技术面回测界面 [released]
backtesting-v0.1  技术面组合回测与约束配置（仅 technical_score，无基本面因子） [released]
backtesting-v0.2  按披露日期重建历史财报快照，新增 signal_mode="ai_score"（不含新闻情绪因子） [released]
backtesting-v0.3  加入 Model Layer 回测结果自然语言解释 [planned]
backtesting-v1.0  稳定组合策略工作流 [planned]
```

版本号必须出现在文档、API 结果或界面说明中，便于回溯。

## 7. 合规要求

所有组合建议必须显示：

```text
本系统仅用于投资研究辅助，不构成任何投资建议。
```

禁止输出：

* 必买
* 保证收益
* 无风险
* 稳赚
* 自动下单

## 8. 测试要求

新增组合策略能力必须至少覆盖：

* 策略配置结构测试
* 风险约束测试
* 回测指标测试
* API 请求/响应测试
* 前端是否调用 `POST /workflows/portfolio-research` 的治理测试
* 策略库 CRUD（`GET/PUT/DELETE /strategies`）的数据层和 API 测试
