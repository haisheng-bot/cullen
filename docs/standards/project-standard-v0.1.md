# OpenStock AI 项目标准文档 v0.1

## 1. 项目定位

OpenStock AI 是一个开源 AI 美股分析与推荐系统。

项目目标不是直接替用户做投资决策，而是提供：

* 美股数据采集
* 财报分析
* 新闻分析
* 股票评分
* 投资组合分析
* AI 研究报告
* 模拟交易与回测
* 未来可接入券商 API

系统输出仅作为研究辅助，不构成投资建议。

---

## 2. 核心原则

### 2.1 合规优先

系统不得承诺收益，不得诱导用户买卖股票。

所有推荐结果必须带有风险提示：

> 本系统仅用于投资研究辅助，不构成任何投资建议。

### 2.2 数据可追溯

所有分析结果必须能够追溯到数据来源。

每一个 AI 结论至少应包含：

* 数据来源
* 分析时间
* 使用模型
* 输入数据摘要
* 生成结论
* 风险提示

### 2.3 人工确认

系统可以生成推荐，但不得默认自动下单。

第一阶段只允许：

* 分析
* 推荐
* 评分
* 模拟交易
* 人工确认后交易

### 2.4 模块化设计

系统必须支持模块替换。

包括：

* 数据源可替换
* 大模型可替换
* 券商接口可替换
* 评分模型可替换
* 前端展示可替换

---

## 3. 技术架构标准

### 3.1 后端

推荐技术栈：

* Python
* FastAPI
* PostgreSQL
* Redis
* Celery / APScheduler
* SQLAlchemy
* Pydantic
* LangGraph

### 3.2 前端

推荐技术栈：

* Next.js
* TypeScript
* Tailwind CSS
* ECharts / Recharts

### 3.3 AI 模型层

系统不得绑定单一模型。

模型设计不得放在 AI Agent 内部，必须建立独立 Model Layer。

必须支持：

* OpenAI
* Claude
* Gemini
* DeepSeek
* Qwen
* Llama
* 本地模型

通过统一接口调用。

### 3.4 数据源

第一阶段优先支持：

* Yahoo Finance / yfinance
* SEC EDGAR
* FRED
* Alpha Vantage
* Finnhub
* Polygon

数据源必须抽象为独立模块。

---

## 4. 项目目录规范

```text
openstock-ai/
├── apps/
│   ├── api/
│   └── web/
├── packages/
│   ├── data_sources/
│   ├── ai_agents/
│   ├── algorithm_layer/
│   ├── model_layer/
│   ├── scoring/
│   ├── backtesting/
│   └── brokers/
├── docs/
│   ├── standards/
│   ├── architecture/
│   ├── api/
│   └── product/
├── tests/
├── scripts/
├── docker/
├── README.md
└── pyproject.toml
```

---

## 5. Agent 设计标准

系统至少包含以下 Agent：

### 5.1 Market Data Agent

负责获取：

* 股票价格
* 成交量
* 市值
* PE / PB
* 财务指标

### 5.2 SEC Filing Agent

负责读取：

* 10-K
* 10-Q
* 8-K
* 财报 XBRL 数据

### 5.3 News Agent

负责分析：

* 公司新闻
* 行业新闻
* 宏观新闻
* 情绪倾向

### 5.4 Scoring Agent

负责生成股票评分。

评分维度包括：

* 基本面
* 成长性
* 估值
* 技术面
* 新闻情绪
* 风险

### 5.5 Report Agent

负责输出自然语言研究报告。

报告必须包含：

* 公司概况
* 核心财务数据
* 利好因素
* 风险因素
* AI 评分
* 结论
* 免责声明

---

## 6. 股票评分标准

初版评分模型：

```text
总分 = 基本面 30%
     + 成长性 20%
     + 估值 20%
     + 技术面 10%
     + 新闻情绪 10%
     + 风险控制 10%
```

评分输出：

```text
85-100：强关注
70-84：观察
50-69：中性
0-49：回避
```

禁止直接输出：

* 必买
* 保证上涨
* 无风险
* 稳赚

---

## 7. 数据库标准

核心表包括：

* stocks
* stock_prices
* financial_statements
* sec_filings
* news_articles
* ai_reports
* stock_scores
* portfolios
* backtest_results
* audit_logs

所有 AI 输出必须写入 audit_logs。

---

## 8. API 设计标准

API 必须遵守 REST 风格。

示例：

```text
GET /stocks/{symbol}
GET /stocks/{symbol}/financials
GET /stocks/{symbol}/news
GET /stocks/{symbol}/score
POST /reports/generate
POST /backtests/run
```

所有接口必须有：

* 请求参数校验
* 错误码
* 日志记录
* 测试用例

---

## 9. Git 规范

### 9.1 分支

```text
main        稳定版本
develop     开发版本
feature/*   新功能
fix/*       修复
docs/*      文档
```

### 9.2 Commit 规范

```text
feat: add stock scoring module
fix: correct SEC parser error
docs: update architecture standard
test: add unit tests for scoring
refactor: simplify data source interface
```

---

## 10. AI 开发工具约束

Codex / Claude Code / Cursor 必须遵守：

1. 不得直接修改 main 分支。
2. 每次修改前必须说明修改范围。
3. 每次修改后必须生成测试。
4. 不得删除已有核心文档。
5. 不得绕过类型检查。
6. 不得硬编码 API Key。
7. 不得把真实账户信息写入代码。
8. 所有外部 API 调用必须封装。
9. 所有投资结论必须带风险提示。
10. 所有新增模块必须更新 docs。

---

## 11. 安全标准

禁止提交：

* API Key
* Token
* 券商账户
* 身份证信息
* 银行卡信息
* 真实交易记录

必须使用：

```text
.env
.env.example
```

敏感信息只允许放在本地环境变量中。

---

## 12. 第一阶段 MVP 范围

第一阶段只做：

* 股票代码查询
* 美股基础数据
* SEC 财报读取
* AI 财报总结
* 新闻摘要
* 股票评分
* 研究报告生成
* 本地数据库保存

暂不做：

* 自动交易
* 实盘下单
* 期权策略
* 杠杆交易
* 高频交易

---

## 13. 项目免责声明

OpenStock AI 是一个开源投资研究辅助工具。

本项目不提供任何形式的投资顾问服务，不构成证券买卖建议。用户应自行判断投资风险，并对自己的投资行为负责。
