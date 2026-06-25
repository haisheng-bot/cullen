# OpenStock AI Universe Layer 标准 v0.1

## 1. 定位

Universe Layer 负责生成每日股票候选池。

第一阶段核心任务：

* 扫描美股交易最活跃的 100 只股票
* 用市场常见筛选维度做基础分析
* 输出每日候选池
* 为 Algorithm Layer、Agent Layer 和操作界面提供输入

Universe Layer 不直接给出买卖建议，也不替代推荐算法。

本系统仅用于投资研究辅助，不构成任何投资建议。

## 2. 架构位置

```text
Application Layer
        |
Agent Layer
        |
Workflow Layer
        |
Universe Layer
        |
Algorithm Layer
        |
Model Layer
        |
Knowledge Layer
        |
Data Layer
```

Universe Layer 回答：

```text
今天应该优先看哪些股票？
```

Algorithm Layer 回答：

```text
这些股票如何评分和排序？
```

## 3. 目录规范

Universe Layer 代码必须放在：

```text
packages/universe_layer/
```

建议结构：

```text
packages/universe_layer/
├── __init__.py
├── schemas.py
├── most_active.py
├── dimensions.py
└── scheduler.py
```

## 4. 第一阶段数据源

第一阶段优先使用公开市场数据源：

* Yahoo Finance Most Active
* Yahoo Finance chart API
* 后续可接入 Polygon、Finnhub、Alpha Vantage

如果实时外部接口失败，允许使用静态 fallback 列表保证页面和测试可用，但必须在响应中标记数据来源。

## 5. 市场常见分析维度

参考 Yahoo Finance、Finviz、TradingView、Investing.com 等常见筛选器，第一阶段维度包括：

### 5.1 流动性

* 当前成交量
* 平均成交量
* 相对成交量
* 成交额

### 5.2 价格行为

* 当日涨跌幅
* 区间涨跌幅
* 盘中高低点
* 52 周高低位置

### 5.3 趋势和技术

* 短期动量
* RSI
* 均线位置
* 波动率

### 5.4 基本面和估值

* 市值
* P/E
* Forward P/E
* P/B
* EPS 增长
* 收入增长

### 5.5 风险

* Beta
* 短期波动
* 跌幅
* 过热风险
* 数据缺失风险

### 5.6 行业和主题

* Sector
* Industry
* 热门主题
* 同行业对比

## 6. 输出标准

每日候选池必须包含：

* universe_date
* universe_name
* market
* limit
* source
* generated_at
* items
* analysis_dimensions
* risk_disclaimer

每只股票至少包含：

* rank
* symbol
* name
* sector
* volume
* price
* change_percent
* market_cap
* pe_ratio
* relative_volume
* analysis_tags

## 7. API 标准

第一阶段 API：

```text
GET /stocks/universe/most-active?limit=100
```

返回美股最活跃股票候选池。

## 8. 每日运行标准

每天美股盘前、盘中或盘后可以运行：

```text
Universe Scan
  -> Most Active Top 100
  -> Dimension Enrichment
  -> Algorithm Layer scoring
  -> Watchlist candidates
  -> Audit logs
```

第一阶段可以手动触发，后续接入 APScheduler / Celery。

## 9. 开发要求

Universe Layer 必须可以单独开发和测试：

* 不依赖前端
* 不依赖 Agent
* 不依赖 Model Layer
* 不依赖真实 API Key
* 外部数据失败时有 fallback
* 输出必须带风险提示

