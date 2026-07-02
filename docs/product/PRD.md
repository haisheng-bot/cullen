# OpenStock AI 产品需求文档（PRD）

**Document Version：** v0.3
**Project Name：** OpenStock AI
**Author：** Cullen
**Status：** Official

---

## 1. 项目概述（Project Overview）

### 1.1 项目背景

随着大语言模型（LLM）、Agent、量化投资及金融数据分析技术的发展，传统股票软件已经无法满足现代投资者的需求。

OpenStock AI 的目标不是开发一个普通的股票软件，而是打造一个基于 AI Agent 的智能投资研究平台（AI Investment Research Platform）。

平台将帮助用户从研究单只股票，升级到研究整个投资组合（Portfolio），最终实现 AI 自动辅助投资分析。

OpenStock AI 的第一阶段产品目标，是先逐步进化成 Cullen 的个人股票研究生产力工具，为每日美股筛选、单股研究、Portfolio 跟踪、策略回测、AI 解释和研究报告归档提供技术支持；在个人研究流程稳定之后，再逐步开放为通用 AI 投资研究平台。

本系统仅用于投资研究辅助，不构成任何投资建议。

## 2. 产品定位（Product Position）

OpenStock AI 不是：

* 股票交易软件
* 行情软件
* 券商交易终端

而是：

> AI Investment Research Platform

长期演进目标：

> AI Portfolio Operating System

平台将通过 Workflow Engine 编排 Universe、Portfolio、Factor、Strategy、Constraint、Backtesting、Risk、AI Research、Recommendation、Report 和 Rebalance，使 OpenStock AI 从单点股票分析工具逐步演进成持续可用的投资组合研究生产力系统。

核心能力包括：

* 股票研究
* 投资组合管理
* AI 投资分析
* 策略回测
* 风险分析
* AI 自动研究报告

## 2.1 个人生产力目标（Personal Productivity Goal）

OpenStock AI 首先服务 Cullen 的日常股票研究流程。

核心工作流：

```text
每日股票池扫描
  -> 候选股排序
  -> 单股深度研究
  -> Portfolio 跟踪
  -> 策略回测
  -> AI 解释
  -> 研究报告归档
  -> 次日复盘
```

该目标的详细标准见：

* `docs/product/PERSONAL_PRODUCTIVITY_GOAL.md`

## 3. 产品目标（Product Goals）

OpenStock AI 主要解决以下问题。

### 3.1 股票筛选（Stock Screener）

根据不同策略快速构建股票池，例如：

* AI
* Semiconductor
* Momentum
* Growth
* Dividend
* Healthcare
* Energy
* Defense
* Crypto
* Most Active

支持自定义股票池。

### 3.2 股票研究（Stock Research）

针对单只股票进行全面分析：

* 实时价格
* K 线图
* 成交量
* 财务数据
* 财报分析
* 新闻摘要
* AI 自动评分
* AI 风险提示
* 行业分析
* 技术指标

最终生成 AI Research Report。

### 3.3 投资组合（Portfolio）

支持用户建立多个投资组合。

例如 AI Portfolio：

* NVDA
* AAPL
* MSFT
* META
* TSM
* GOOGL

支持：

* 创建
* 删除
* 编辑
* 导入
* 导出
* 对比多个组合

### 3.4 AI 智能分析（AI Analysis）

利用大语言模型自动完成：

* 股票分析
* 财务分析
* 新闻总结
* 风险解释
* 买卖原因分析
* 组合优化建议

所有分析均可生成自然语言报告。

### 3.5 投资策略（Strategy）

平台支持多种策略组合。

基础策略：

* Equal Weight
* Market Cap
* Dividend
* Growth
* Value
* Momentum

高级策略：

* Mean Variance Optimization
* Black-Litterman
* Risk Parity
* Hierarchical Risk Parity
* Minimum Variance
* Equal Risk Contribution

AI 策略：

* AI Score Strategy
* AI Ranking Strategy
* AI Dynamic Allocation
* AI News Driven Strategy

### 3.6 回测（Backtesting）

支持：

* 1 年
* 3 年
* 5 年
* 10 年
* 自定义时间

输出：

* CAGR
* Annual Return
* Max Drawdown
* Sharpe Ratio
* Sortino Ratio
* Alpha
* Beta
* Win Rate
* Information Ratio

### 3.7 风险分析（Risk Analysis）

支持：

* 波动率
* Beta
* VaR
* CVaR
* 最大回撤
* 行业集中度
* 持仓集中度
* 风险贡献分析
* Stress Test
* Monte Carlo Simulation（后续版本）

## 4. 核心业务流程（Workflow）

用户使用流程：

```text
股票池
  ↓
选择股票
  ↓
建立 Portfolio
  ↓
选择策略
  ↓
配置约束条件
  ↓
运行优化
  ↓
回测
  ↓
AI 自动解释
  ↓
生成投资报告
  ↓
形成投资建议
```

## 5. 系统功能模块

### Module 1：Stock Screener

功能：

* 股票筛选
* 股票分类
* 热门股票
* AI 推荐股票

### Module 2：Stock Research

功能：

* 实时行情
* 财务分析
* 新闻分析
* AI 总结
* 技术指标

### Module 3：Portfolio

功能：

* Portfolio 管理
* 权重管理
* 收益统计
* 风险统计

### Module 4：Strategy Engine

负责：

* 策略配置
* 参数管理
* 权重计算
* Constraint

### Module 5：Portfolio Optimizer

负责：

* 最优权重计算
* 风险收益优化
* Constraint Solver

### Module 6：Risk Engine

负责：

* 风险计算
* 风险暴露
* VaR
* Beta
* Drawdown

### Module 7：Backtesting Engine

负责：

* 回测
* Benchmark
* Performance

### Module 8：AI Research

负责：

* 新闻总结
* 财报总结
* 风险解释
* 策略解释
* 投资建议

### Module 9：AI Report

自动生成：

* PDF
* Markdown
* HTML
* Dashboard

## 6. 技术架构（High Level Architecture）

```text
Infrastructure
  ↓
Data Layer
  ↓
Model Layer
  ↓
Algorithm Layer
  ↓
Workflow Engine
  ↓
AI Agent Layer
  ↓
Strategy Layer
  ↓
Portfolio Layer
  ↓
Application Layer
```

## 7. AI Agent 规划

平台包含多个 AI Agent：

* Research Agent：负责股票研究。
* News Agent：负责新闻分析。
* Financial Agent：负责财报分析。
* Risk Agent：负责风险分析。
* Strategy Agent：负责策略推荐。
* Portfolio Agent：负责组合优化。
* Report Agent：负责自动生成报告。

## 8. 数据来源（Data Source）

第一阶段：

* Yahoo Finance
* SEC EDGAR

第二阶段：

* Finnhub
* Polygon
* Alpha Vantage
* FRED

第三阶段：

* Bloomberg
* Reuters
* Morningstar

## 9. 模型支持（Model Layer）

平台支持统一模型接口。

兼容：

* GPT
* Claude
* Gemini
* DeepSeek
* Qwen
* Llama
* Ollama

通过 LiteLLM 统一调用。

## 10. MVP 范围

第一阶段交付：

* 股票研究
* 股票池
* Portfolio
* Strategy Workflow
* Workflow Engine 状态机与节点观测
* Portfolio Research Workflow
* Backtesting
* AI Summary
* AI Report

不包含：

* 自动交易
* 高频交易
* 期权策略
* 多资产配置

当前需求与实际开发差距见：

* `docs/product/PROJECT_PLAN_PROGRESS.md`
* `docs/product/IMPLEMENTATION_GAP_ANALYSIS.md`

## 11. 后续 Roadmap

### Phase 1

完成基础 MVP：

* Dashboard
* Chart
* Universe
* Strategy Library v0.1
* Portfolio 基础管理
* AI Score
* Workflow Engine v0.1
* Backtesting v0.2
* Risk Engine v0.1
* Portfolio Optimizer v0.1
* Portfolio Research Module v0.1
* Scoring Profiles / 模型权重模块 v0.1
* Research Run History API v0.1

### Phase 2

当前优先收口：

* 数据源健康检查
* 数据质量标记
* Portfolio Manager v0.2
* Strategy Library v0.2
* Stock Research 独立页

### Phase 3

增加：

* Strategy Library v0.2
* Portfolio Manager v0.2
* Risk Engine v0.2
* Portfolio Optimizer v0.2
* Monte Carlo
* Stress Test
* Factor Analysis

### Phase 4

增加：

* Model Center 基础版
* Agent Center 基础版
* AI Agent Workflow
* 自动生成每日投资报告

### Phase 5

打造 OpenStock AI Strategy Marketplace。

允许用户共享：

* 策略
* Agent
* Workflow
* 因子模型
* Portfolio 模板

形成开放式 AI 投资研究平台。

## 12. 项目成功标准（Success Metrics）

产品上线后重点关注：

功能指标：

* 股票池管理
* Portfolio 创建成功率
* 回测成功率
* AI 报告生成速度

AI 指标：

* AI 分析准确率
* AI 推荐一致性
* 新闻总结质量

用户指标：

* Portfolio 数量
* 活跃用户
* 每日研究次数
* AI 报告生成次数

技术指标：

* API 响应时间
* 回测耗时
* Agent 执行成功率
* 模型调用成功率
