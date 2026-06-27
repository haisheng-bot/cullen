# OpenStock AI Risk Engine 标准 v0.1

## 1. 定位

Risk Engine 位于 `packages/risk_engine`，负责把组合价格序列、权重和行业映射转换为可复盘的风险报告。

本系统仅用于投资研究辅助，不构成任何投资建议。

## 2. v0.1 指标

Risk Engine v0.1 必须输出：

* Volatility
* Beta
* Max Drawdown
* Average Correlation
* Position Concentration
* Sector Exposure

## 3. 边界

Risk Engine 不负责：

* 自动交易
* 生成买卖指令
* 直接调用模型供应商 SDK
* 直接读取券商账户
* 承诺收益或暗示低风险

## 4. API

```text
POST /risk/portfolio
```

请求包含：

* symbols
* weights
* benchmark_symbol
* sector_map

响应包含：

* volatility_percent
* beta
* max_drawdown_percent
* average_correlation
* concentration_percent
* sector_exposure
* source
* generated_at
* risk_disclaimer
