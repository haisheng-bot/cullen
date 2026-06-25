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

* Application Layer：展示组合、约束、回测结果和免责声明。
* Workflow Layer：编排 Universe、Strategy、Backtest、Model Analysis。
* Algorithm / Backtesting Layer：执行仓位分配、信号规则、风险控制和回测指标计算。
* Model Layer：后续负责对回测结果做自然语言解释和审计，不直接计算收益。
* Data Layer：提供历史价格、行情、行业和后续财报/新闻数据。

代码落地在 `packages/backtesting/`（与 `algorithm_layer/`、`workflow_layer/` 同级的顶层包，对应文档里的 Algorithm / Backtesting Layer）：

```text
packages/backtesting/
├── schemas.py      策略配置、规则、回测结果等数据结构
├── signals.py       Signal Engine：复用 algorithm_layer/technical_indicators.py 的技术指标
├── allocation.py    Position Sizing：等权 / 低波动 / 技术评分 / 市值加权 + 仓位上限与现金底线
├── risk.py          Risk Engine：止损、组合最大回撤熔断、行业暴露检查
├── engine.py        Strategy Engine + Backtest Engine：PortfolioBacktestEngine.run()
└── performance.py   Performance Evaluator：收益、回撤、Sharpe、胜率、Alpha/Beta
```

## 4. 第一阶段范围

**第一阶段为什么只用技术面信号，不直接用 `/stocks/{symbol}/recommendation` 的完整 AI 评分：**

现有 AI 评分依赖 SEC 年报基本面因子，而 `packages/data_sources/sec_financials.py` 目前只暴露最新 1-2 个财年数据，没有保留每条 XBRL 财务事实的实际披露日期（`filed` 字段）。如果直接把这套评分接入回测，会在历史调仓日"看到"当时还没披露的财报数据，即未来数据穿越（lookahead bias），回测结果会失真且无法被信任。要修复需要新增按披露日期重建历史可见财报快照的能力，而且年报频率对月度调仓也偏稀疏（多数月份没有新数据）。

价格 / 技术指标（动量、RSI、均线金死叉）天然不存在这个问题——它们是某个历史日期之前收盘价序列的纯函数，只要截到调仓日为止取数即可保证不穿越。因此第一阶段（`backtesting-v0.1`）的买卖规则和仓位评分只使用技术面信号，命名为 `technical_score` 而非 `ai_score`，避免被误读为验证了完整的 5 维 AI 评分。基于完整 AI 评分（含基本面）的回测是第二阶段（见第 6 节版本管理），依赖先完成按披露日期重建历史财报快照的工作。

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
* 调用 `POST /backtests/run` 执行历史回测。
* 输出收益、年化收益、最大回撤、Sharpe、Alpha、交易次数、贡献股票、风险提示。

第一阶段不做：

* 自动实盘下单
* 保证收益
* 无人工确认的交易
* 使用未来数据的回测

## 5. API 标准

组合策略回测使用：

```text
POST /backtests/run
```

请求必须包含：

* strategy_name
* symbols
* start_date
* end_date
* initial_cash
* benchmark_symbol
* allocation
* entry_rules
* exit_rules
* risk
* sector_map

响应必须包含：

* total_return_percent
* annualized_return_percent
* max_drawdown_percent
* sharpe_ratio
* benchmark_total_return_percent
* alpha_percent
* beta
* contributions
* trades
* suggestions
* risks
* source
* algorithm_version
* generated_at
* risk_disclaimer

## 6. 版本管理

代码中的实际版本号是 `BacktestResult.algorithm_version`（`packages/backtesting/engine.py` 的 `ALGORITHM_VERSION` 常量），与下表一一对应：

```text
backtesting-v0.1  技术面组合回测与约束配置（仅 technical_score，无基本面因子） [released]
backtesting-v0.2  接入按披露日期重建的历史财报快照，回测规则可使用 ai_score [planned]
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
* 前端是否调用 `POST /backtests/run` 的治理测试

