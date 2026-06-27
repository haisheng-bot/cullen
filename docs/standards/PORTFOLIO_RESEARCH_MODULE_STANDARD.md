# OpenStock AI Portfolio Research Module 标准 v0.1

## 1. 定位

Portfolio Research Module 是面向用户的统一组合研究体验层，位于 `packages/portfolio_research`。

它把 Workflow、Backtesting、Risk Engine、Portfolio Optimizer、AI Summary 和 Recommendation 整合成一个产品入口。

本系统仅用于投资研究辅助，不构成任何投资建议。

## 2. 用户入口

```text
POST /portfolio-research/run
GET /portfolio-research/{trace_id}
```

前端工作台应优先调用 `POST /portfolio-research/run`，而不是直接拼接底层 Workflow、Risk 或 Optimizer API。

## 3. 内部能力

Portfolio Research Module 可调用：

* Portfolio Research Workflow
* Backtesting Engine
* Risk Engine
* Portfolio Optimizer
* Workflow archive

底层接口仍保留用于测试、调试和模块复用：

```text
POST /workflows/portfolio-research
POST /risk/portfolio
POST /optimizer/portfolio
```

## 4. 输出结构

统一响应必须包含：

* trace_id
* state
* portfolio
* score_summary
* backtest_summary
* risk_summary
* optimized_weights
* ai_explanation
* recommendation
* warnings
* risk_disclaimer

## 5. 设计原则

* 底层模块保持分层。
* 用户体验保持一个入口、一个结果、一个 trace_id。
* 投资相关输出必须带风险提示。
* 不提供自动交易。
