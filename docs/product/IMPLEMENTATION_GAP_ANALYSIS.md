# OpenStock AI 需求与实际开发差距分析 v0.1

## 1. 当前判断

OpenStock AI 已经从概念文档进入可运行 MVP 骨架阶段。

项目计划、实际进度、差异和下一步行动的总表见：

* `docs/product/PROJECT_PLAN_PROGRESS.md`

按当前代码和测试覆盖判断：

```text
MVP 架构骨架完成度：约 80% - 85%
个人股票研究生产力工具完成度：约 65% - 75%
AI Portfolio Operating System 完成度：约 25% - 35%
```

本系统仅用于投资研究辅助，不构成任何投资建议。

## 2. 已接近需求的部分

| 模块 | 当前状态 | 说明 |
|---|---|---|
| 项目标准 / GitHub / 版本管理 | 基本完成 | 标准文档、协作规范、CI 和治理测试已建立 |
| Model Layer | 部分完成 | 统一接口、LiteLLM-compatible provider、Mock provider、Router、Validator 已有 |
| Workflow Engine | 部分完成 | 状态机、节点、trace_id、输入输出摘要、耗时、失败记录已落地 |
| Universe Layer | 部分完成 | Most Active Top 100 候选池已可用 |
| Algorithm Layer | 部分完成 | 五/六因子规则评分、技术指标、财务因子、新闻规则情绪已接入；当前算法制作范围收敛为 1 年推荐 |
| Backtesting | 部分完成 | 技术面回测和 AI-score 回测已可用 |
| Portfolio Research Workflow | 已完成 | `POST /workflows/portfolio-research` v0.1，前端已通过统一入口接入 |
| Portfolio Research Module | 已完成 | `packages/portfolio_research`，`POST /portfolio-research/run` 统一整合 Workflow/Risk/Optimizer/AI Summary/Recommendation，支持按 `trace_id` 复盘 |
| Risk Engine v0.1 | 已完成 | `packages/risk_engine`，`POST /risk/portfolio`，输出 Volatility/Beta/Max Drawdown/Correlation/Concentration/Sector Exposure |
| Portfolio Optimizer v0.1 | 已完成 | `packages/portfolio_optimizer`，`POST /optimizer/portfolio`，支持 Equal Weight/Market Cap/Minimum Variance/Risk Parity 初版 |
| 策略库 Strategy Library | 已完成 | `GET/PUT/DELETE /strategies`，策略与 Portfolio 解耦的独立可复用实体，前端支持新增/应用/更新/删除 |
| Portfolio | 已完成 | 基础组合保存、增删股票、目标权重、现金比例已可用 |
| Report Agent | 初版完成 | 单股研究报告 Agent 已接入 |
| Tiger OpenAPI | 骨架完成 | 只读 quote/history 接口边界已定义，真实 SDK adapter 仍待完善 |

## 3. 主要差距

### 3.1 Portfolio Optimizer v0.1 已完成，高级求解器仍缺

需求中包含：

* Mean Variance Optimization
* Black-Litterman
* Risk Parity
* Hierarchical Risk Parity
* Minimum Variance
* Equal Risk Contribution

当前状态：

* `packages/portfolio_optimizer` 已实现 Equal Weight、Market Cap、Minimum Variance（逆方差近似）、Risk Parity（逆波动率近似），接入 `POST /optimizer/portfolio` 和前端摘要
* 仍未实现：完整协方差矩阵求解、Black-Litterman、Hierarchical Risk Parity、Equal Risk Contribution（当前 Minimum Variance/Risk Parity 用的是近似公式，不是完整协方差矩阵优化）

差距级别：中（初版已可用，缺高级求解器）。

### 3.2 Risk Engine v0.1 已完成，VaR/CVaR/压力测试仍缺

需求中包含：

* VaR
* CVaR
* Correlation
* Sector Exposure
* Position Exposure
* Concentration Risk
* Stress Test
* Monte Carlo Simulation

当前状态：

* `packages/risk_engine` 已实现 Volatility、Beta、Max Drawdown、Average Correlation、Concentration、Sector Exposure，接入 `POST /risk/portfolio` 和前端摘要
* 仍未实现：VaR、CVaR、Stress Test、Monte Carlo Simulation

差距级别：中（初版已可用，缺尾部风险指标）。

### 3.3 AI Agent 体系未完整

已完成：

* SEC Filing Agent
* Report Agent

未完成或待深化：

* News Agent
* Financial Agent
* Risk Agent
* Strategy Agent
* Portfolio Agent
* Macro Agent
* Decision Agent

当前状态：

* Agent 基类和模型层边界已明确
* 多 Agent workflow 尚未形成

差距级别：中高。

### 3.4 前端接入 Portfolio Research Workflow 与 Research Run 复盘页已完成，报告归档页仍缺

当前状态：

* 页面已通过统一入口 `POST /portfolio-research/run` 调用 Workflow/Backtesting/Risk/Optimizer/AI Summary/Recommendation，节点状态、AI Summary、Portfolio Recommendation、trace_id 均已展示
* 「策略库 Strategy Library」面板已接入，策略与组合解耦
* Research Run 复盘面板已接入，支持按组合、策略库存档名、状态和日期查询历史 workflow run，并打开 `trace_id` 详情复盘
* 仍缺：Report Archive 正式报告列表、Markdown/HTML 报告详情和报告级归档

目标状态：

```text
页面操作
  -> Portfolio Research Module API
  -> 节点状态展示
  -> 回测结果
  -> AI 解释
  -> 组合建议
  -> 历史运行复盘
  -> 报告归档（仍缺）
```

差距级别：低到中（核心运行复盘已打通，缺报告归档 UI）。

### 3.5 数据源稳定性仍需加强

当前状态：

* Yahoo / SEC / FRED / Tiger 均有不同程度接入
* 已有部分缓存和 best-effort 降级

仍需补齐：

* 统一数据源优先级
* 失败重试
* 限流
* 数据质量标记
* 缺失数据提示
* 数据源健康检查

差距级别：中。

### 3.6 AI Report 尚未成为正式报告系统

当前状态：

* Report Agent 可生成单股研究结论
* 工作台已接入报告按钮

未完成：

* PDF 报告
* Markdown 报告
* HTML 报告
* Dashboard 报告
* 报告归档
* 每日复盘报告
* 多组合对比报告

差距级别：中。

### 3.7 Git / 发布状态：本地提交已拆分，远端推送仍受阻

当前状态：

* `develop` 上此前积累的未提交改动已按模块拆分为独立 commit（Risk Engine、Optimizer、Portfolio 权重管理、Workflow Run 持久化、Portfolio Research Module、前端接入、文档同步分别成提交）
* 远端 `origin` 已配置为 `haisheng-bot/cullen`，但本机缺 HTTPS 凭证和 SSH 公钥，`develop` 尚未推送到远端

差距级别：低（本地提交已整理，仅剩推送凭证待补）。

## 4. 下一阶段收口方向

不要继续扩很多新概念，下一阶段应优先把现有能力收口为可日常使用的闭环。

已完成（原 1-4 项）：

```text
1. ~~前端接入 Portfolio Research Workflow~~ [已完成]
2. ~~Portfolio 权重管理~~ [已完成]
3. ~~Risk Engine v0.1~~ [已完成]
4. ~~Portfolio Optimizer v0.1~~ [已完成]
```

额外完成（超出原计划）：策略库 Strategy Library v0.1（策略与 Portfolio 解耦）、Portfolio Research Module v0.1（统一入口）、workflow run 持久化（按 trace_id 复盘）、Scoring Profiles v0.1、Research Run History API v0.1。

建议顺序（下一批）：

```text
1. AI Report 归档
2. 每日研究首页
3. 数据源健康检查
4. 数据质量标记
5. Portfolio Manager v0.2
6. Strategy Library v0.2
7. Stock Research 独立页
8. 1 年推荐算法打磨
9. Risk/Optimizer 高级能力暂缓
10. Model Center / Agent Center 暂缓
11. Rebalance Engine 仅保留设计
```

## 5. 近期优先级

### P0：Workflow 前端化 [已完成]

目标：

* 操作界面调用 `POST /workflows/portfolio-research`
* 展示每个节点状态
* 展示 `trace_id`
* 展示 AI Summary 和 Portfolio Recommendation

### P1：Portfolio 权重管理 [已完成]

目标：

* 每个组合支持目标权重
* 支持现金比例
* 支持保存策略配置
* 支持组合导入 / 导出（导入/导出仍未做）

### P2：Risk Engine v0.1 [已完成]

目标：

* Volatility
* Beta
* Max Drawdown
* Correlation
* Position Concentration
* Sector Exposure

### P3：Portfolio Optimizer v0.1 [已完成]

目标：

* Equal Weight
* Market Cap Weight
* Minimum Variance
* Risk Parity 初版

### P4：Report Archive

目标：

* 保存 AI Report
* 保存 Workflow Run（已完成，按 `trace_id` 可查）
* 支持按日期复盘（Research Run 复盘页已完成，报告归档仍缺）
* 支持 Markdown / HTML 输出

### P5：策略库导入导出 / Strategy Marketplace 评估

目标：

* 策略库 v0.1（新增/应用/更新/删除）已完成
* 评估是否需要导入导出、分享给其他用户（PRD 里的 Strategy Marketplace 远期方向）

### P6：Scoring Profiles / 模型权重模块 [已完成]

目标：

* 将评分因子权重从 Algorithm Layer 中独立出来
* 内置 Balanced / Growth / Value / Defensive / Momentum 研究风格
* 让单股评分、批量筛选和 Portfolio Research 都支持 `scoring_profile`

### P7：Research History API [已完成]

目标：

* 增加 Research Run 历史列表 API
* 支持按组合、策略库存档名、状态和日期查询历史运行

### P8：Trace 复盘页 [已完成]

目标：

* 前端支持从历史列表打开 trace_id
* 展示 Workflow 节点、回测、Risk、Optimizer、AI Summary、Recommendation

## 6. 当前真实状态一句话

当前项目已经具备：

```text
架构骨架 + 核心 API + 完整页面 + 初版算法 + 初版回测 + 统一 workflow（含 Risk/Optimizer/策略库）
```

但距离完整生产力系统仍缺：

```text
稳定数据体系 + 风险引擎尾部指标（VaR/CVaR） + 优化器高级求解器（HRP/Black-Litterman） + 多 Agent 自动研究 + 正式报告系统
```
