# API 设计 v0.1

## 1. REST API

第一阶段 API：

```text
GET /stocks/{symbol}
GET /stocks/popular
GET /stocks/search
GET /stocks/universe/most-active
GET /stocks/{symbol}/quote
GET /stocks/{symbol}/recommendation
GET /stocks/{symbol}/history
GET /stocks/{symbol}/filings
GET /stocks/{symbol}/financials
GET /stocks/{symbol}/news
GET /stocks/{symbol}/score
GET /stocks/{symbol}/trend
GET /macro/{series_id}/observations
POST /reports/generate
POST /backtests/run
```

## 2. 实时走势 API

### 2.1 美股列表

```text
GET /stocks/popular
GET /stocks/search?q=AAPL
```

用途：

* 提供美股操作界面的默认关注列表
* 支持按股票代码、公司名、行业搜索
* 第一阶段使用内置热门美股列表，后续接入证券主数据服务

### 2.2 单股报价

```text
GET /stocks/{symbol}/quote
```

用途：

* 返回美股当前报价
* 返回涨跌额和涨跌幅
* 支撑操作台顶部报价区

数据来源：

* Yahoo Finance chart API

### 2.3 每日候选池

```text
GET /stocks/universe/most-active?limit=100
```

用途：

* 扫描美股交易最活跃的 100 只股票
* 作为每日筛选股票的第一层候选池
* 输出市场常见分析维度和标签
* 为 Algorithm Layer、Agent Layer 和操作界面提供输入

第一阶段维度：

* 成交量
* 相对成交量
* 成交额
* 涨跌幅
* 市值
* P/E
* EPS / 收入增长
* RSI / 均线
* 波动率
* 52 周位置
* 行业
* 分析师评级

### 2.4 历史日线（yfinance，免费）

```text
GET /stocks/{symbol}/history?range=10y&interval=1d
```

用途：

* 提供近 10 年的免费历史日 / 周 / 月线（开高低收量）
* 用于长周期回测和趋势研究，区别于 2.6 节的分钟级实时走势

数据来源：

* Yahoo Finance chart API（yfinance 同源公开接口）

请求参数：

```text
symbol    美股代码，例如 AAPL
range     范围：1y, 2y, 5y, 10y, max
interval  间隔：1d, 1wk, 1mo
```

响应示例：

```json
{
  "symbol": "AAPL",
  "range": "10y",
  "interval": "1mo",
  "currency": "USD",
  "exchange_name": "NMS",
  "points": [
    {
      "date": "2016-07-01",
      "open": 23.8725,
      "high": 26.1375,
      "low": 23.5925,
      "close": 26.0525,
      "volume": 2743118400
    }
  ],
  "source": "Yahoo Finance chart API (yfinance-compatible)",
  "analysis_time": "2026-06-25T13:31:00+00:00",
  "risk_disclaimer": "本系统仅用于投资研究辅助，不构成任何投资建议。"
}
```

### 2.5 SEC 财报读取（SEC EDGAR，免费）

```text
GET /stocks/{symbol}/filings?forms=10-K,10-Q,8-K&limit=10
```

用途：

* 按股票代码解析 SEC CIK，并读取最近的 10-K / 10-Q / 8-K 等申报文件列表
* 提供官方文档原文链接，供 AI 财报总结（M3 SEC Filing Agent）和人工核查使用
* 免费、无需 API Key，但请求需带描述性 User-Agent（SEC 公平访问要求）

数据来源：

* SEC EDGAR（`www.sec.gov` 股票代码映射 + `data.sec.gov` 申报记录接口）

请求参数：

```text
symbol    美股代码，例如 AAPL
forms     逗号分隔的表单类型，默认 10-K,10-Q,8-K
limit     返回条数上限，默认 10，最大 50
```

响应示例：

```json
{
  "symbol": "AAPL",
  "cik": "0000320193",
  "company_name": "Apple Inc.",
  "filings": [
    {
      "form": "10-Q",
      "filing_date": "2026-05-01",
      "report_date": "2026-03-28",
      "accession_number": "0000320193-26-000013",
      "primary_document": "aapl-20260328.htm",
      "document_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm"
    }
  ],
  "source": "SEC EDGAR",
  "analysis_time": "2026-06-25T13:31:00+00:00",
  "risk_disclaimer": "本系统仅用于投资研究辅助，不构成任何投资建议。"
}
```

### 2.6 实时走势

```text
GET /stocks/{symbol}/trend?range=1d&interval=1m
```

### 2.7 推荐算法

```text
GET /stocks/{symbol}/recommendation
```

用途：

* 调用独立 Algorithm Layer
* 返回股票评分和推荐等级
* 展示因子分、推荐理由和风险

第一阶段算法：

* `algorithm-v0.1`
* 基于实时走势、前收盘、波动和成交量活跃度

说明：

推荐算法仅用于研究关注优先级，不构成买卖建议。

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

### 2.8 FRED 宏观数据（需免费 API Key）

```text
GET /macro/{series_id}/observations?start_date=&end_date=&limit=100
```

用途：

* 读取美联储 FRED 宏观经济序列（如 `FEDFUNDS` 联邦基金利率、`CPIAUCSL` CPI、`UNRATE` 失业率）
* 为后续宏观新闻、估值分析提供背景数据

数据来源：

* FRED（St. Louis Fed），需在 `.env` 设置 `FRED_API_KEY`（免费注册：https://fred.stlouisfed.org/docs/api/api_key.html）
* 未配置 Key 时返回 503，并提示如何申请，不会使用任何内置默认 Key

请求参数：

```text
series_id     FRED 序列代码，例如 FEDFUNDS
start_date    起始日期 YYYY-MM-DD，可选
end_date      结束日期 YYYY-MM-DD，可选
limit         返回条数上限，默认 100，最大 1000
```

响应示例：

```json
{
  "series_id": "FEDFUNDS",
  "observations": [
    {"date": "2026-05-01", "value": 5.33},
    {"date": "2026-04-01", "value": null}
  ],
  "source": "FRED (Federal Reserve Economic Data)",
  "analysis_time": "2026-06-25T13:31:00+00:00",
  "risk_disclaimer": "本系统仅用于投资研究辅助，不构成任何投资建议。"
}
```

说明：本接口尚未接入真实 FRED Key 做过线上联调，仅通过 mock payload 完成单元测试覆盖；接入真实 Key 后请重新做一次实际请求验证。

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
