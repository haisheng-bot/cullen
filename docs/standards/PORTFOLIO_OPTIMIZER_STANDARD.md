# OpenStock AI Portfolio Optimizer 标准 v0.1

## 1. 定位

Portfolio Optimizer 位于 `packages/portfolio_optimizer`，负责根据股票池、历史价格、约束和方法生成目标权重。

本系统仅用于投资研究辅助，不构成任何投资建议。

## 2. v0.1 方法

MVP 支持：

* Equal Weight
* Market Cap
* Minimum Variance
* Risk Parity

## 3. 边界

Portfolio Optimizer 不负责：

* 自动交易
* 券商下单
* 承诺收益
* 直接调用模型供应商 SDK
* 复杂协方差矩阵求解器或 Black-Litterman 完整模型

## 4. API

```text
POST /optimizer/portfolio
```

请求包含：

* symbols
* method
* max_position_weight
* min_cash_weight

响应包含：

* method
* target_weights
* cash_weight
* expected_risk_percent
* notes
* source
* generated_at
* risk_disclaimer

## 5. v0.1 近似说明

* `minimum_variance` 使用逆方差权重近似。
* `risk_parity` 使用逆波动率权重近似。
* `market_cap` 使用最新可得价格和股数估算市值。
* 所有方法均应用单票上限和现金比例约束。
