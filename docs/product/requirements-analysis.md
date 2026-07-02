# OpenStock AI 需求分析 v0.1

## 1. 项目定位

OpenStock AI 是一个 AI Investment Research Platform。

长期目标是演进为 AI Portfolio Operating System，由 Workflow Engine 编排 Universe、Portfolio、Factor、Strategy、Constraint、Backtesting、Risk、AI Research、Recommendation、Report 和 Rebalance。

系统不是股票交易软件、行情软件或券商终端，而是面向美股研究、投资组合管理、策略回测、风险分析和 AI 自动研究报告的智能投资研究平台。

系统面向美股市场，通过行情、财报、新闻、宏观数据、评分模型、策略引擎、回测引擎和 AI Agent，帮助用户从研究单只股票升级到研究整个 Portfolio，并生成可追溯的研究结论。

OpenStock AI 的第一阶段重点，是逐步成为 Cullen 的个人股票研究生产力工具，为每日股票筛选、单股技术支持、Portfolio 跟踪、策略回测、AI 解释、研究报告归档和次日复盘提供稳定工作台。

本系统仅用于投资研究辅助，不构成任何投资建议。

## 2. 核心需求

系统需要提供：

* Personal Productivity Workflow：每日股票池扫描、候选股排序、Portfolio 跟踪、策略回测、AI 解释和研究报告归档
* Workflow Engine：统一编排 Universe、Portfolio、Strategy、Backtesting、Risk、AI Agent、Report 和 Rebalance，并记录节点状态、trace_id、输入输出摘要和耗时
* Stock Screener：股票池、热门股票、主题股票、自定义股票池
* Stock Research：单股行情、K 线、财务、财报、新闻、技术指标、AI 评分
* Portfolio：多个组合创建、编辑、删除、导入、导出、对比
* Strategy Engine：策略配置、参数管理、权重计算、约束管理
* Portfolio Optimizer：最优权重、风险收益优化、约束求解
* Risk Engine：波动率、Beta、VaR、CVaR、最大回撤、行业集中度、持仓集中度
* Backtesting Engine：1 年、3 年、5 年、10 年和自定义时间回测
* AI Research：股票分析、财务分析、新闻总结、风险解释、策略解释
* AI Report：PDF、Markdown、HTML、Dashboard 报告
* 本地数据库保存和审计追踪

## 3. 目标用户

* Cullen：把 OpenStock AI 作为个人美股研究生产力工具，完成每日筛选、研究、回测、报告和复盘
* 个人投资者：快速筛选和理解美股标的及组合风险
* 股票研究者：整理行情、财报、新闻和策略结果，形成研究结论
* 组合研究者：建立 Portfolio、配置策略、运行回测和风险分析
* 内容创作者：生成美股分析、组合复盘和 AI 研究报告
* 开发者：扩展数据源、评分模型、Agent、策略、优化器和回测模块

## 4. 核心场景

### 4.0 个人每日研究闭环

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

该场景是第一阶段最高优先级，详细标准见 `docs/product/PERSONAL_PRODUCTIVITY_GOAL.md`。

### 4.1 股票筛选

用户根据主题、策略或市场活跃度生成股票池。

股票池示例：

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

输出必须包含：

* 股票代码
* 公司名称
* 主题或行业标签
* 成交量和成交额
* 涨跌幅
* 数据来源
* 风险提示

### 4.2 单股研究

用户输入股票代码，系统输出：

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
* AI Research Report

### 4.3 Portfolio 管理

用户可以建立多个投资组合，例如 AI Portfolio：

* NVDA
* AAPL
* MSFT
* META
* TSM
* GOOGL

Portfolio 必须支持：

* 创建
* 删除
* 编辑
* 导入
* 导出
* 权重管理
* 收益统计
* 风险统计
* 多组合对比

### 4.4 Strategy Workflow

用户从股票池选择股票并建立 Portfolio 后，可以选择策略并配置约束。

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

### 4.5 回测与风险分析

回测周期：

* 1 年
* 3 年
* 5 年
* 10 年
* 自定义时间

回测输出：

* CAGR
* Annual Return
* Max Drawdown
* Sharpe Ratio
* Sortino Ratio
* Alpha
* Beta
* Win Rate
* Information Ratio

风险输出：

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

### 4.6 AI 报告生成

AI Report 必须支持：

* 新闻总结
* 财报总结
* 风险解释
* 策略解释
* 投资组合建议
* PDF
* Markdown
* HTML
* Dashboard

## 5. 核心业务流程

```text
股票池
  -> 选择股票
  -> 建立 Portfolio
  -> 选择策略
  -> 配置约束条件
  -> 运行优化
  -> 回测
  -> AI 自动解释
  -> 生成投资报告
  -> 形成投资建议
```

## 6. AI Agent 规划

平台包含多个 AI Agent：

* Research Agent：负责股票研究
* News Agent：负责新闻分析
* Financial Agent：负责财报分析
* Risk Agent：负责风险分析
* Strategy Agent：负责策略推荐
* Portfolio Agent：负责组合优化
* Report Agent：负责自动生成报告

## 7. 推荐边界

允许输出：

* 强关注
* 观察
* 中性
* 回避
* 候选标的
* 研究关注名单
* 组合优化建议
* 风险复核建议

禁止输出：

* 必买
* 保证上涨
* 无风险
* 稳赚
* 诱导用户立即买入或卖出
* 默认自动交易

## 8. MVP 范围

第一阶段交付：

* 股票研究
* 股票池
* Portfolio
* Strategy Workflow
* Portfolio Research Workflow
* Backtesting
* AI Summary
* AI Report

第一阶段不包含：

* 自动交易
* 高频交易
* 期权策略
* 多资产配置

当前需求与实际开发差距见：

* `docs/product/PROJECT_PLAN_PROGRESS.md`
* `docs/product/IMPLEMENTATION_GAP_ANALYSIS.md`

下一阶段优先收口：

```text
1. 数据源健康检查
2. 数据质量标记
3. Portfolio Manager v0.2
4. Strategy Library v0.2
5. Stock Research 独立页
```

已完成并从下一阶段移除：

```text
PRD v0.3 / Roadmap 对齐
Scoring Profiles / 模型权重模块 v0.1
Research Run History API
trace_id 完整复盘页
Report Archive v0.1
每日研究首页
```

## 9. 成功标准

功能指标：

* 股票池管理可用
* Portfolio 创建成功率可观测
* 回测成功率可观测
* AI 报告生成速度可观测

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
