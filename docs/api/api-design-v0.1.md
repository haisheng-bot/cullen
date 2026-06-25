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
GET /stocks/{symbol}/financials
GET /stocks/{symbol}/news
GET /stocks/{symbol}/score
GET /stocks/{symbol}/trend
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

### 2.4 实时走势

```text
GET /stocks/{symbol}/trend?range=1d&interval=1m
```

### 2.5 推荐算法

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
