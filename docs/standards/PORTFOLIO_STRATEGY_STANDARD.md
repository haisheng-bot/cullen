# OpenStock AI Portfolio Strategy 标准 v0.1

## 1. 定位

Portfolio Strategy 是 OpenStock AI 的组合策略工作流，负责把每日股票池、策略库、约束条件和回测结果串成可复核的组合建议。

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

## 4. 第一阶段范围

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

```text
portfolio-strategy-v0.1  技术面组合回测与约束配置 [released]
portfolio-strategy-v0.2  加入 Model Layer 回测解释 [planned]
portfolio-strategy-v0.3  加入财报、估值、新闻情绪组合约束 [planned]
portfolio-strategy-v1.0  稳定组合策略工作流 [planned]
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

