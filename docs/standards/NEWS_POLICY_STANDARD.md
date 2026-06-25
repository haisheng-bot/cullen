# OpenStock AI News / Policy Layer 标准 v0.1

## 1. 定位

News / Policy Layer 负责为每只股票提供新闻、政策、监管披露和公司治理事件。

本层独立于 Agent、Model Layer、Algorithm Layer 和前端页面。前端只展示结果，API 只调用本层。

本系统仅用于投资研究辅助，不构成任何投资建议。

## 2. 第一阶段范围

第一阶段实现：

* 最近公司新闻
* 最近监管披露
* SEC 8-K / 10-K / 10-Q 查询
* 3 年窗口查询参数
* 内部任免相关披露线索
* 新闻来源和发布时间

## 3. 3 年新闻要求

目标能力：

```text
GET /stocks/{symbol}/news?years=3
```

第一阶段说明：

* Yahoo Finance RSS 用于最近新闻。
* SEC EDGAR 用于 3 年内监管披露和公司治理事件。
* “完整 3 年所有新闻”通常需要接入付费或归档新闻源，例如 Polygon、Finnhub、Alpha Vantage、Benzinga、Dow Jones、FactSet、RavenPack 等。
* 当前必须保留接口和数据结构，便于后续替换数据源。

## 4. 内容分类

输出条目必须标记类型：

```text
company_news
market_news
policy
sec_filing
management_change
governance
macro
```

## 5. 输出标准

每条内容至少包含：

* title
* summary
* url
* source
* published_at
* category
* symbols

响应必须包含：

* symbol
* years
* items
* sources
* generated_at
* coverage_note
* risk_disclaimer

## 6. 内部任免

美国上市公司高管任免通常通过 SEC 8-K 披露，常见为 Item 5.02。

第一阶段通过 SEC filings 中的 8-K 和相关描述标记 `management_change` 候选。

## 7. 开发要求

News / Policy Layer 必须：

* 可独立测试
* 不依赖前端
* 不依赖模型
* 不硬编码 API Key
* 保留来源
* 保留时间
* 清楚标记覆盖范围限制

