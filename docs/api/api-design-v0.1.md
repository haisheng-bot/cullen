# API 设计 v0.1

## 1. REST API

第一阶段 API：

```text
GET /stocks/{symbol}
GET /stocks/{symbol}/financials
GET /stocks/{symbol}/news
GET /stocks/{symbol}/score
GET /stocks/{symbol}/trend
POST /reports/generate
POST /backtests/run
```

## 2. 实时走势 API

```text
GET /stocks/{symbol}/trend?range=1d&interval=1m
```

用途：

* 接入美股走势 API
* 返回实时或近实时价格序列
* 支撑前端趋势图

第一阶段数据源：

* Yahoo Finance chart API

请求参数：

```text
symbol    美股代码，例如 AAPL
range     范围：1d, 5d, 1mo, 3mo, 6mo, 1y
interval  间隔：1m, 2m, 5m, 15m, 30m, 60m, 1d
```

响应示例：

```json
{
  "symbol": "AAPL",
  "range": "1d",
  "interval": "1m",
  "currency": "USD",
  "exchange_name": "NMS",
  "regular_market_price": 210.5,
  "previous_close": 209.1,
  "points": [
    {
      "timestamp": "2026-06-25T13:30:00+00:00",
      "close": 210.1,
      "volume": 1200
    }
  ],
  "source": "Yahoo Finance chart API",
  "analysis_time": "2026-06-25T13:31:00+00:00",
  "risk_disclaimer": "本系统仅用于投资研究辅助，不构成任何投资建议。"
}
```

## 3. 响应要求

所有 AI 分析接口必须返回：

* 数据来源
* 分析时间
* 使用模型
* 输入数据摘要
* 生成结论
* 风险提示

统一风险提示：

> 本系统仅用于投资研究辅助，不构成任何投资建议。
