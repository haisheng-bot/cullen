# API 设计 v0.1

## 1. REST API

第一阶段 API：

```text
GET /stocks/{symbol}
GET /stocks/popular
GET /stocks/search
GET /stocks/universe/most-active
GET /stocks/screening
GET /stocks/{symbol}/quote
GET /stocks/{symbol}/recommendation
GET /stocks/{symbol}/history
GET /stocks/{symbol}/filings
GET /stocks/{symbol}/sec-summary
GET /stocks/{symbol}/financials
GET /stocks/{symbol}/news
GET /stocks/{symbol}/score
GET /stocks/{symbol}/trend
GET /macro/{series_id}/observations
GET /integrations/tiger/status
GET /data-sources/health
GET /stocks/{symbol}/tiger/quote
GET /stocks/{symbol}/tiger/history
GET /workflows/portfolio-research/{trace_id}
GET /portfolio-research/{trace_id}
PUT /portfolios/{name}/config
POST /risk/portfolio
POST /optimizer/portfolio
POST /portfolio-research/run
POST /reports/from-trace/{trace_id}
POST /backtests/run
POST /workflows/portfolio-research
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
GET /stocks/{symbol}/tiger/quote
GET /stocks/{symbol}/tiger/history?years=3&period=day
```

用途：

* 返回美股当前报价
* 返回涨跌额和涨跌幅
* 返回最多近 3 年历史 K 线参考数据
* 支撑操作台顶部报价区
* 可选通过 Tiger OpenAPI 读取用户授权后的官方行情数据

数据来源：

* Yahoo Finance chart API
* Tiger Brokers OpenAPI（可选，只读，需用户自行配置 OpenAPI 凭证）

### 2.2.1 Tiger OpenAPI 状态

```text
GET /integrations/tiger/status
```

用途：

* 检查 Tiger OpenAPI 是否已配置
* 检查官方 SDK 是否可用
* 返回缺失配置字段名称
* 明确 `trading_enabled=false`

说明：

OpenStock AI 不读取、不抓取、不逆向老虎 App。Tiger 数据只能通过官方 OpenAPI 和用户授权凭证接入。第一阶段只做只读研究数据，不提供自动下单。

### 2.2.1.1 数据源健康检查

```text
GET /data-sources/health
```

用途：

* 汇总 Yahoo Market Data、SEC EDGAR、FRED Macro、Tiger Brokers OpenAPI 的配置与可用状态
* 返回每个数据源的 `configured`、`available`、`status`、`capabilities`、`last_error`、`fallback`
* 支撑前端 Data Source Health 面板，帮助判断当前分析是否缺外部配置

响应示例：

```json
{
  "overall_status": "ok",
  "available_count": 2,
  "total_count": 4,
  "items": [
    {
      "name": "FRED Macro",
      "source": "FRED API",
      "configured": false,
      "available": false,
      "status": "not_configured",
      "capabilities": ["macro_series"],
      "requires_config": true,
      "last_error": "FRED_API_KEY is not configured.",
      "fallback": "Macro panel remains unavailable until FRED_API_KEY is configured.",
      "checked_at": "2026-07-02T10:20:30.000000+00:00"
    }
  ],
  "risk_disclaimer": "本系统仅用于投资研究辅助，不构成任何投资建议。",
  "checked_at": "2026-07-02T10:20:30.000000+00:00"
}
```

说明：

* 该接口不返回任何密钥或敏感配置值
* 当前版本是轻量配置/能力健康检查，不在页面加载时发起外部网络探测
* 未配置的 FRED/Tiger 会显示 `not_configured`，系统继续使用 Yahoo/SEC 等可用数据源

### 2.2.2 Tiger 近 3 年历史 K 线

```text
GET /stocks/{symbol}/tiger/history?years=3&period=day
```

用途：

* 读取用户授权范围内的历史 K 线参考数据
* 第一阶段支持 `day`、`week`、`month`
* 第一阶段最多请求近 3 年数据
* 返回 OHLC、成交量、成交额、数据来源、分析时间和风险提示
* 作为算法层、回测层和研究报告的参考数据输入

边界：

* 不是逐笔 tick 全量数据
* 不保证覆盖老虎 App 内所有展示字段
* 不绕过官方 OpenAPI 权限和频率限制
* 不用于自动交易

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

### 2.6 新闻、政策和披露

```text
GET /stocks/{symbol}/news?years=3&limit=30
```

用途：

* 展示最近公司新闻
* 展示政策、监管披露和 SEC 文件线索
* 支持查询 3 年窗口
* 标记内部任免和治理相关披露候选

第一阶段数据源：

* Yahoo Finance RSS：最近新闻
* SEC EDGAR：3 年内监管披露、8-K、10-K、10-Q

说明：

完整 3 年所有新闻需要后续接入归档新闻源或付费数据源。当前接口先提供统一结构和公开源能力。

### 2.7 实时走势

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

### 2.8 推荐算法

```text
GET /stocks/{symbol}/recommendation
```

用途：

* 调用独立 Algorithm Layer
* 返回股票评分和推荐等级
* 展示因子分、推荐理由和风险
* 当前仅输出 1 年推荐，响应字段 `recommendation_horizon` 固定为 `1y`

查询参数：

* `scoring_profile`（可选，默认 `balanced`）：`balanced`/`growth`/`value`/`defensive`/`momentum` 五个内置权重组之一，详见 `docs/standards/SCORING_PROFILES_STANDARD.md`。未知名返回 400。

当前算法：`algorithm-v0.3`，1 年推荐，六个因子（以下权重为 `balanced` 默认值，其余 profile 权重不同）：

* `fundamentals` 基本面（净利润率 50% + ROC 资本回报率 50%，合计 30%）—— 来自 SEC XBRL company facts
* `growth` 成长性（营收同比，20%）—— 来自 SEC XBRL company facts
* `valuation` 估值（P/E 50% + EV/EBIT 50%，合计 20%）—— 结合实时价格、EPS、负债与现金
* `technical` 技术面（动量 10 日 40% + RSI(14) 30% + 均线 5/20 金死叉 30%，权重小计 10%）—— 来自近 1 年日线收盘价，数据不足时退化为区间走势粗估
* `news_sentiment` 新闻情绪（10%）—— 来自 News / Policy Layer 的 Yahoo Finance RSS 新闻与 SEC 披露，v0.3 为规则化估算
* `volatility_risk` 风险（区间波动，10%）

ROC、EV/EBIT 是 Joel Greenblatt「Magic Formula」用的两个经典指标，详见 `docs/standards/ALGORITHM_STANDARD.md` 第 9.3 节。某只股票缺少可用财务或新闻数据时，对应因子退化为中性分（50分），并在 `risks`/`explanation` 中提示。

说明：推荐算法仅用于研究关注优先级，不构成买卖建议。

响应示例：

```json
{
  "symbol": "AAPL",
  "total_score": 59,
  "recommendation": "中性",
  "factors": [
    {"name": "fundamentals", "score": 92, "weight": 0.3, "explanation": "净利润率约 26.9%，资本回报率(ROC)约 413.7%（基于最近年度 SEC 财报）"},
    {"name": "growth", "score": 58, "weight": 0.2, "explanation": "营收同比增长约 6.4%（基于最近两个年度 SEC 财报）"},
    {"name": "valuation", "score": 55, "weight": 0.2, "explanation": "P/E 约 37.5，EV/EBIT 约 31.5（绝对档位估算，非行业相对）"},
    {"name": "technical", "score": 28, "weight": 0.1, "explanation": "动量(10日) -4.07%，RSI(14) 24.6，均线(5/20)状态：空头排列"},
    {"name": "news_sentiment", "score": 54, "weight": 0.1, "explanation": "基于 20 条新闻/SEC 披露信号，正向词 3，负向词 2，治理/政策披露 1 条（规则化估算）"},
    {"name": "volatility_risk", "score": 30, "weight": 0.1, "explanation": "区间波动估算 3.63%"}
  ],
  "reasons": ["区间走势为负，短线动量偏弱。", "当前价格低于或接近前收盘价。", "区间波动较高，需要结合风险承受能力观察。"],
  "risks": ["新闻情绪为规则化初版估算，估值评分为绝对档位启发式，非行业相对。", "短线波动较大，评分可能快速变化。"],
  "source": "Yahoo Finance chart API",
  "algorithm_version": "algorithm-v0.3",
  "analysis_time": "2026-06-25T14:30:46.957647+00:00",
  "recommendation_horizon": "1y",
  "scoring_profile": "balanced",
  "risk_disclaimer": "本系统仅用于投资研究辅助，不构成任何投资建议。"
}
```

已用真实 AAPL 数据（SEC XBRL 财报 + Yahoo 实时走势 + 近 1 年日线技术指标 + News / Policy Layer 新闻披露信号）做过线上联调。

### 2.9 FRED 宏观数据（需免费 API Key）

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

## 3. AI Agent API

第一个落地的 AI Agent，走完整 Policy Guard → Data Context Builder → Workflow Executor → Model Layer → Agent Executor → Output Validator → Audit Logger 流水线（见 `docs/architecture/ai-development-architecture.md` 第 3 节）。

### 3.1 SEC Filing Agent

```text
GET /stocks/{symbol}/sec-summary
```

用途：

* 调用 SEC Filing Agent（`packages/ai_agents/sec_filing_agent.py`）
* 读取最近的 10-K / 10-Q / 8-K 申报（复用 2.5 节的 SEC EDGAR 数据源）
* 经 Model Layer 统一接口生成摘要，返回前必须通过 Output Validator 合规检查（免责声明、数据来源、禁止词）
* 写入 `audit_logs`

数据来源：

* SEC EDGAR
* 使用模型：默认 `mock` provider（未配置任何模型 API Key 时的 fallback）；配置 `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` 等后自动切换为 `litellm` provider，无需改代码

响应示例：

```json
{
  "symbol": "AAPL",
  "task_type": "sec_filing_summary",
  "model": "mock/mock-model-v0",
  "data_source": ["https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm"],
  "input_summary": "Company: Apple Inc. (AAPL, CIK 0000320193)...",
  "conclusion": "Mock response for sec_filing_summary: ...",
  "analysis_time": "2026-06-25T09:18:15.683985+00:00",
  "trace_id": "dbf51cdb-d3ac-4fd3-939c-775c7c3566b6",
  "risk_disclaimer": "本系统仅用于投资研究辅助，不构成任何投资建议。"
}
```

已用真实 SEC EDGAR 数据（AAPL）做过线上联调，并确认 `audit_logs` 落库成功。

## 4. AI 选股 Workflow API

对应 `docs/product/requirements-analysis.md` 第 4.1 节"AI 选股"场景：用户不指定单一标的，系统从候选池里扫描并输出排序后的候选列表。

### 4.1 批量选股排序

```text
GET /stocks/screening?limit=20
```

用途：

* 调用 Workflow Layer（`packages/workflow_layer/stock_screening.py`），编排 Universe Layer（候选池）→ 数据源（实时走势 + SEC 财务数据 + 近 1 年日线）→ Algorithm Layer（评分）
* 对候选池逐个并发评分（最多 8 个并发请求），按 `total_score` 降序排列
* 单只股票数据获取失败时跳过并记录在 `skipped`，不影响其余候选
* 每个候选评分会写入 `stock_scores` 表（见 4.2 节），用于跨天对比同一只股票的分数变化

请求参数：

```text
limit            候选池大小，同时也是评分数量上限，默认 20，最大 50
scoring_profile  可选，默认 balanced；balanced/growth/value/defensive/momentum 之一，未知名返回 400
```

性能说明：每只股票需要额外请求 SEC 财务数据和近 1 年日线，受 Yahoo/SEC 服务端响应速度影响，`limit=20` 时实测约 56 秒完成；这是个人使用工具，未做更激进的并发或缓存优化。

响应示例：

```json
{
  "market": "US",
  "requested_limit": 10,
  "scored_count": 10,
  "candidates": [
    {
      "rank": 1,
      "symbol": "SOFI",
      "name": "SoFi Technologies, Inc.",
      "sector": "",
      "total_score": 69,
      "recommendation": "中性",
      "factors": [
        {"name": "fundamentals", "score": 95, "weight": 0.3, "explanation": "净利润率约 77.7%（基于最近年度 SEC 财报）"},
        {"name": "growth", "score": 78, "weight": 0.2, "explanation": "营收同比增长约 23.1%（基于最近两个年度 SEC 财报）"},
        {"name": "valuation", "score": 40, "weight": 0.2, "explanation": "按最新价格估算 P/E 约 44.4（绝对档位估算，非行业相对）"},
        {"name": "technical", "score": 74, "weight": 0.2, "explanation": "动量(10日) +5.10%，RSI(14) 54.8，均线(5/20)状态：多头排列"},
        {"name": "volatility_risk", "score": 20, "weight": 0.1, "explanation": "区间波动估算 6.76%"}
      ],
      "reasons": ["区间走势为正，短线动量偏强。"],
      "risks": ["新闻情绪为规则化初版估算，估值评分为绝对档位启发式，非行业相对。"],
      "source": "Yahoo Finance chart API",
      "algorithm_version": "algorithm-v0.3"
    }
  ],
  "skipped": [],
  "source": "Yahoo Finance predefined most_actives + Algorithm Layer",
  "generated_at": "2026-06-25T10:04:57.520340+00:00",
  "scoring_profile": "balanced",
  "risk_disclaimer": "本系统仅用于投资研究辅助，不构成任何投资建议。"
}
```

已用真实候选池数据做过线上联调（20 只股票，全部评分成功，按分排序正确）。

### 4.2 选股历史

```text
GET /stocks/{symbol}/score-history?limit=30
```

用途：

* 读取 `stock_scores` 表中某只股票历次 `/stocks/screening` 评分记录，按时间倒序返回
* 用于个人使用场景下对比"这只股票的分数是涨是跌"，而不是每次都是无状态的即时计算

请求参数：

```text
limit  返回条数上限，默认 30，最大 200
```

响应示例：

```json
{
  "symbol": "SOFI",
  "items": [
    {
      "screened_at": "2026-06-25T11:03:12.789243",
      "rank": 1,
      "total_score": 69,
      "recommendation": "中性",
      "factors": [
        {"name": "fundamentals", "score": 95, "weight": 0.3, "explanation": "净利润率约 77.7%（基于最近年度 SEC 财报）"}
      ],
      "reasons": ["区间走势为正，短线动量偏强。"],
      "risks": ["新闻情绪为规则化初版估算，估值评分为绝对档位启发式，非行业相对。"],
      "algorithm_version": "algorithm-v0.3"
    }
  ],
  "risk_disclaimer": "本系统仅用于投资研究辅助，不构成任何投资建议。"
}
```

已用真实数据做过线上联调：调用一次 `/stocks/screening` 后再读取 `/stocks/SOFI/score-history`，记录正确落库并可读出。

### 4.3 Portfolio Strategy 回测

```text
POST /backtests/run
```

用途：

* 承载 Portfolio Strategy 六步流程：Universe → Strategy Library → Constraints → Backtest → AI Analysis → Portfolio Recommendation
* 对人工选择的美股组合进行历史回测
* 返回收益、风险、贡献股票、交易记录、策略建议和风险提示
* 为操作界面的组合策略选择、约束配置和组合建议提供统一接口

请求体必须包含：

```json
{
  "strategy_name": "Core Watch · 技术评分加权",
  "symbols": ["AAPL", "MSFT", "NVDA"],
  "start_date": "2023-06-25",
  "end_date": "2026-06-25",
  "initial_cash": 10000,
  "rebalance_frequency": "monthly",
  "benchmark_symbol": "SPY",
  "signal_mode": "ai_score",
  "scoring_profile": "balanced",
  "allocation": {
    "method": "technical_score_weighted",
    "max_position_weight": 0.25,
    "min_cash_weight": 0.1
  },
  "entry_rules": {
    "min_technical_score": 60,
    "min_momentum_percent": 0,
    "require_ma_cross": null,
    "min_ai_score": 65
  },
  "exit_rules": {
    "max_technical_score": 40,
    "stop_loss_percent": 0.08,
    "require_ma_cross": null,
    "max_ai_score": 35
  },
  "risk": {
    "max_portfolio_drawdown": 0.12,
    "max_sector_exposure": null
  },
  "sector_map": {
    "AAPL": "Technology",
    "MSFT": "Technology",
    "NVDA": "Technology"
  }
}
```

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
* scoring_profile
* generated_at
* risk_disclaimer

`signal_mode` 取值 `"technical"`（默认，仅价格/技术信号）或 `"ai_score"`（`backtesting-v0.2`：基本面/成长/估值/技术/波动风险五因子综合评分，按披露日期重建历史财报快照、不含新闻情绪因子）。`min_technical_score`/`max_technical_score` 两种模式下都生效；`min_ai_score`/`max_ai_score` 只在 `signal_mode="ai_score"` 时生效。

`scoring_profile`（可选，默认 `balanced`）只在 `signal_mode="ai_score"` 时生效，取值 `balanced`/`growth`/`value`/`defensive`/`momentum`，决定基本面/成长/估值/技术/波动风险五因子的相对权重（排除新闻情绪后重新归一化），详见 `docs/standards/SCORING_PROFILES_STANDARD.md`，未知名返回 400。

合规说明：

* 回测结果只代表历史模拟，不代表未来收益。
* `signal_mode="ai_score"` 不含新闻情绪因子（无历史新闻归档数据源），与 `/stocks/{symbol}/recommendation` 实时评分权重不完全相同。
* 组合建议必须人工复核，不允许默认自动下单。
* 本系统仅用于投资研究辅助，不构成任何投资建议。

### 4.4 Portfolio Research Workflow

```text
POST /workflows/portfolio-research
GET /workflows/portfolio-research/{trace_id}
```

用途：

* 编排 Universe Builder、Portfolio Builder、Strategy Selector、Constraint Config、Backtest Runner、AI Summary 和 Portfolio Recommendation
* 将“股票池 -> 组合 -> 策略 -> 约束 -> 回测 -> AI 解释 -> 组合建议”作为一个可观测 workflow 执行
* 返回 workflow 状态、节点结果、trace_id、portfolio、strategy、constraints、backtest、ai_summary 和 portfolio_recommendation
* 将完整 workflow 响应写入 `workflow_runs` 表，支持后续按 `trace_id` 查询复盘
* 回测结果会写入 backtest run 存储路径，便于后续复盘

请求体核心字段：

```json
{
  "portfolio_name": "AI Workflow",
  "strategy_library_name": null,
  "universe_limit": 100,
  "selected_symbols": ["AAPL", "MSFT", "NVDA"],
  "backtest": {
    "strategy_name": "AI Workflow Backtest",
    "symbols": ["AAPL", "MSFT", "NVDA"],
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "rebalance_frequency": "monthly",
    "allocation": {
      "method": "equal_weight",
      "max_position_weight": 0.25,
      "min_cash_weight": 0.10
    }
  }
}
```

说明：

* `selected_symbols` 会覆盖 `backtest.symbols`，用于页面中已经选好的组合
* v0.1 的 `ai_summary` 是确定性的规则解释，不直接调用模型供应商 SDK
* `GET /workflows/portfolio-research/{trace_id}` 返回原始 workflow 响应；未找到时返回 404
* 本接口只生成研究辅助结论，不提供自动交易

### 4.5 Portfolio Research Module

```text
POST /portfolio-research/run
GET /portfolio-research/{trace_id}
```

用途：

* 面向前端工作台的统一组合研究入口
* 一次请求完成 Workflow、Backtesting、Risk Engine、Portfolio Optimizer、AI Summary 和 Recommendation
* 返回一个 trace_id，并支持按 trace_id 复盘完整研究结果

请求体：

```json
{
  "portfolio_name": "Core Watch",
  "symbols": ["AAPL", "MSFT", "NVDA"],
  "research_goal": "balanced_growth",
  "strategy_library_name": null,
  "constraints": {
    "max_position_weight": 0.35,
    "min_cash_weight": 0.1,
    "max_drawdown": 0.2,
    "benchmark_symbol": "SPY",
    "backtest_years": 3
  },
  "strategy_preferences": {
    "scoring_mode": "algorithm_v0.3",
    "scoring_profile": "balanced",
    "backtest_mode": "ai_score",
    "optimizer_method": "minimum_variance",
    "rebalance_frequency": "monthly"
  }
}
```

`strategy_preferences.scoring_profile` 可选，默认 `balanced`；`balanced`/`growth`/`value`/`defensive`/`momentum` 之一（详见 `docs/standards/SCORING_PROFILES_STANDARD.md`），决定 `backtest_mode="ai_score"` 时使用的因子权重，未知名返回 400。

响应包含：

* score_summary
* backtest_summary
* risk_summary
* optimized_weights
* ai_explanation
* recommendation
* warnings
* risk_disclaimer

底层 `/workflows/portfolio-research`、`/risk/portfolio`、`/optimizer/portfolio` 仍保留用于模块调试和测试。

### 4.6 Portfolio 权重管理

```text
PUT /portfolios/{name}/config
```

用途：

* 保存组合目标权重
* 保存现金比例
* 为后续回测、Risk Engine 和 Portfolio Optimizer 提供稳定输入

请求体：

```json
{
  "target_weights": {"AAPL": 0.45, "MSFT": 0.45},
  "cash_weight": 0.10
}
```

策略参数（仓位分配方法、信号模式、再平衡频率、约束）不在这里保存，由解耦的策略库管理，见 4.9。

### 4.7 Risk Engine v0.1

```text
POST /risk/portfolio
```

用途：

* 输出组合波动率、Beta、最大回撤、平均相关性、持仓集中度和行业暴露
* 为组合研究和后续 Optimizer 提供独立风险输入

请求体：

```json
{
  "symbols": ["AAPL", "MSFT"],
  "weights": {"AAPL": 0.5, "MSFT": 0.5},
  "benchmark_symbol": "SPY",
  "sector_map": {"AAPL": "Technology", "MSFT": "Technology"}
}
```

说明：

* 第一阶段使用历史收盘价计算风险指标
* 不生成交易指令，不承诺收益

### 4.8 Portfolio Optimizer v0.1

```text
POST /optimizer/portfolio
```

用途：

* 根据股票池、历史价格、市值估算和约束生成目标权重
* 支持 Equal Weight、Market Cap、Minimum Variance、Risk Parity 初版
* 为组合策略和后续再平衡建议提供研究输入

请求体：

```json
{
  "symbols": ["AAPL", "MSFT"],
  "method": "minimum_variance",
  "max_position_weight": 0.5,
  "min_cash_weight": 0.1
}
```

说明：

* `minimum_variance` 使用逆方差近似
* `risk_parity` 使用逆波动率近似
* `market_cap` 使用最新可得价格和股数估算市值
* 不自动下单，不构成投资建议

### 4.9 策略库 Strategy Library

```text
GET /strategies
PUT /strategies/{name}
DELETE /strategies/{name}
```

用途：

* 策略（仓位分配方法、信号模式、再平衡频率、约束）与 Portfolio（股票桶）完全解耦，任意已保存策略可套用在任意组合上
* 前端「策略库」面板用它实现新增/应用/更新/删除已保存策略

请求体（`PUT /strategies/{name}`）：

```json
{
  "preferences": {
    "scoring_mode": "algorithm_v0.3",
    "backtest_mode": "ai_score",
    "optimizer_method": "minimum_variance",
    "rebalance_frequency": "monthly",
    "scoring_profile": "growth"
  },
  "constraints": {
    "max_position_weight": 0.3,
    "min_cash_weight": 0.1,
    "max_drawdown": 0.15,
    "benchmark_symbol": "SPY",
    "backtest_years": 3
  }
}
```

说明：

* 按 `name` upsert：已存在则更新，不存在则新增
* `optimizer_method`/`backtest_mode`/`rebalance_frequency`/`scoring_profile` 校验落在已知枚举内，否则返回 400（`scoring_profile` 复用 `packages/scoring_profiles/profiles.py::get_profile()`，与推荐、选股、回测、Portfolio Research 四个入口同一套校验）
* `DELETE /strategies/{name}` 不存在时返回 404
* 不参与运行时编排——运行回测仍由前端把当前表单值（可能是刚应用的某个策略）通过 `POST /portfolio-research/run` 提交
* Strategy Library v0.2（P9）：Clone/Save As 和 JSON 导入导出均为前端复用 `PUT /strategies/{name}`（另存为=读现有策略后用新名字 PUT；导出=客户端把 `{name, preferences, constraints}` 序列化成文件下载；导入=解析上传文件后 PUT），未新增接口

### 4.10 Research Run History

```text
GET /research-runs?limit=20&offset=0&workflow_name=&state=&portfolio_name=&strategy_library_name=&start_date=&end_date=
```

用途：

* 复用既有的 `workflow_runs` 表（`/workflows/portfolio-research` 和 `/portfolio-research/run` 两条路径都已写入这张表），不新建表
* 按时间、组合、策略库存档名查询历史研究运行列表，每行带 trace_id、组合、策略、状态、摘要和时间
* 前端 Research Run 复盘面板（P3）已消费这个列表，并用 `GET /portfolio-research/{trace_id}` 打开完整详情

请求参数：

```text
limit                  默认 20，最大 100
offset                 默认 0
workflow_name          可选，"portfolio_research_workflow" 或 "portfolio_research_module"，按 SQL 索引列过滤
state                  可选，按 SQL 索引列过滤；两种 workflow_name 的状态取值词表不同（旧路径是 WorkflowState 枚举值如 "Recommendation Ready"，新路径是 "completed"/"failed"）
portfolio_name         可选，精确匹配
strategy_library_name  可选，精确匹配；只有提交时已应用过 Strategy Library 存档的运行才有值，否则为 null
start_date / end_date  可选，按 started_at 的日期前缀过滤（YYYY-MM-DD）
```

`portfolio_name`/`strategy_library_name`/日期过滤在内存里做（这两个字段存在 `request`/`response` JSON 里，个人工具量级不值得做 SQLite JSON 查询下推），`limit`/`offset` 分页也是在过滤后的内存列表上切片。

响应示例：

```json
{
  "items": [
    {
      "trace_id": "9cfecaf7-2e30-4058-b98d-07f4d001ca4a",
      "workflow_name": "portfolio_research_module",
      "workflow_version": "portfolio-research-module-v0.1",
      "state": "completed",
      "portfolio_name": "Core Watch",
      "symbols": ["AAPL"],
      "strategy_library_name": "市值加权防守型",
      "summary_text": "建议：research_candidate；回测总收益 12.18%",
      "started_at": "2026-06-27T09:53:09.849343+00:00",
      "completed_at": "2026-06-27T09:53:11.624227+00:00"
    }
  ],
  "total_count": 1,
  "limit": 20,
  "offset": 0,
  "risk_disclaimer": "本系统仅用于投资研究辅助，不构成任何投资建议。"
}
```

说明：

* `strategy_library_name` 字段同时新增在 `POST /portfolio-research/run`（4.5 节）和 `POST /workflows/portfolio-research`（4.4 节）的请求体里，可选；前端在「应用」或「新增/更新」某个 Strategy Library 存档后自动带上，不强制和当前表单实际值一致（用户应用后又手动调整表单，这个字段仍是最后应用/保存的存档名，作为标签，不是强校验）
* `GET /research-runs` 只读，不修改任何数据

### 4.11 Report Archive

```text
POST /reports/from-trace/{trace_id}
GET /reports?limit=20&offset=0&portfolio_name=
GET /reports/{trace_id}
```

用途：

* 从已完成的 Portfolio Research `trace_id` 生成 Markdown/HTML 报告，并写入 `report_archives`
* 查询报告归档列表，支持按 `portfolio_name` 过滤
* 读取单份报告详情，用于前端 Report Archive 面板展示

响应示例：

```json
{
  "trace_id": "9cfecaf7-2e30-4058-b98d-07f4d001ca4a",
  "portfolio_name": "Core Watch",
  "title": "Core Watch Research Report",
  "markdown": "# Core Watch Research Report\n\n...",
  "html": "<h1>Core Watch Research Report</h1>\n...",
  "source_summary": {
    "symbols": ["AAPL", "MSFT"],
    "workflow_version": "portfolio-research-module-v0.1",
    "state": "completed"
  },
  "risk_disclaimer": "本系统仅用于投资研究辅助，不构成任何投资建议。",
  "generated_at": "2026-07-02T10:20:30.000000+00:00"
}
```

说明：

* `POST /reports/from-trace/{trace_id}` 是幂等 upsert：同一个 `trace_id` 再次生成会覆盖同一份归档
* 未找到 `trace_id` 返回 404；未找到报告详情返回 404
* HTML 由服务端从受控 Markdown 生成，用于本地工作台展示；后续 PDF/Dashboard 输出另行扩展

### 4.12 异步任务队列 Job Queue

```text
POST /jobs/screening?limit=20&scoring_profile=balanced
POST /jobs/portfolio-research
GET /jobs/{job_id}
GET /jobs?job_type=&status=&limit=20&offset=0
```

用途：

* 为耗时较长的操作（候选池 screening、Portfolio Research Workflow）提供异步入口：提交后立即返回 `job_id`，客户端轮询 `GET /jobs/{job_id}` 获取状态、进度和最终结果
* 同步入口 `/stocks/screening`、`/workflows/portfolio-research` 保持不变，供不需要异步的调用方继续使用；`/jobs/*` 是新增的并行入口，不替换
* 由 `packages/job_queue`（APScheduler `BackgroundScheduler`）在后台线程执行，执行结果与同步入口共享同一套持久化（`stock_scores`/`backtest_runs`/`workflow_runs`），保证两条路径产出一致

请求体（`POST /jobs/portfolio-research`）与 `POST /workflows/portfolio-research` 相同（`PortfolioResearchWorkflowRequest`：`portfolio_name`/`strategy_library_name`/`universe_limit`/`selected_symbols`/`backtest`）。

响应示例（提交）：

```json
{
  "job_id": "8653b3f9-2b89-4048-870e-2134aeabd5ff",
  "job_type": "screening",
  "status": "pending",
  "created_at": "2026-08-01T15:06:05.993139+00:00",
  "message": "Job submitted successfully."
}
```

响应示例（`GET /jobs/{job_id}`）：

```json
{
  "job_id": "8653b3f9-2b89-4048-870e-2134aeabd5ff",
  "job_type": "screening",
  "status": "completed",
  "payload": {"limit": 20, "scoring_profile": "balanced"},
  "result": {"market": "US", "candidates": ["..."]},
  "error_message": null,
  "progress_percent": 100,
  "created_at": "2026-08-01T15:06:05.993139+00:00",
  "started_at": "2026-08-01T15:06:06.010000+00:00",
  "completed_at": "2026-08-01T15:06:07.500000+00:00"
}
```

说明：

* `status` 取值：`pending`/`running`/`completed`/`failed`/`cancelled`；`GET /jobs/{job_id}` 未找到返回 404
* `result` 与对应同步接口的响应体同构（screening 复用 `ScreeningResult.to_dict()`；portfolio-research 复用 `/workflows/portfolio-research` 的响应结构，`trace_id` 即 `job_id`）
* `job_type` 未知时会在提交阶段以 400 拒绝（`scoring_profile` 不合法同理）
* 当前无鉴权、无取消接口、无重试策略；`v0.1` 仅覆盖 screening 和 portfolio-research 两类任务

## 5. 响应要求

所有 AI 分析接口必须返回：

* 数据来源
* 分析时间
* 使用模型
* 输入数据摘要
* 生成结论
* 风险提示

统一风险提示：

> 本系统仅用于投资研究辅助，不构成任何投资建议。

### 5.1 数据质量标记

外部数据源响应必须尽量包含 `data_quality`，当前覆盖：

```text
GET /stocks/{symbol}/quote
GET /stocks/{symbol}/trend
GET /stocks/{symbol}/history
GET /stocks/{symbol}/filings
GET /stocks/{symbol}/news
GET /macro/{series_id}/observations
GET /stocks/{symbol}/tiger/quote
GET /stocks/{symbol}/tiger/history
```

字段：

```json
{
  "data_quality": {
    "source": "Yahoo Finance chart API",
    "as_of": "2026-07-02T10:20:30.000000+00:00",
    "freshness": "fresh",
    "missing_fields": [],
    "fallback": "Use cached price history where available; otherwise show source error."
  }
}
```

说明：

* `freshness` 取值为 `fresh` / `recent` / `stale` / `unknown`
* `missing_fields` 只标记当前响应必需但为空的顶层字段
* `fallback` 描述当前端点数据不可用时的降级策略，不代表已经发生降级
* 前端报价区展示当前 quote 的 `source` 和 `freshness`
