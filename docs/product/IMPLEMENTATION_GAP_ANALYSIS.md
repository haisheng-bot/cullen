# OpenStock AI 需求与实际开发差距分析 v0.1

## 1. 当前判断

OpenStock AI 已经从概念文档进入可运行 MVP 骨架阶段。

项目计划、实际进度、差异和下一步行动的总表见：

* `docs/product/PROJECT_PLAN_PROGRESS.md`

按当前代码和测试覆盖判断：

```text
MVP 架构骨架完成度：约 65% - 70%
个人股票研究生产力工具完成度：约 50% - 60%
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
| Algorithm Layer | 部分完成 | 五/六因子规则评分、技术指标、财务因子、新闻规则情绪已接入 |
| Backtesting | 部分完成 | 技术面回测和 AI-score 回测已可用 |
| Portfolio Research Workflow | 初版完成 | `POST /workflows/portfolio-research` 已接入 v0.1 |
| Portfolio | 初版完成 | 基础组合保存、增删股票已可用 |
| Report Agent | 初版完成 | 单股研究报告 Agent 已接入 |
| Tiger OpenAPI | 骨架完成 | 只读 quote/history 接口边界已定义，真实 SDK adapter 仍待完善 |

## 3. 主要差距

### 3.1 Portfolio Optimizer 尚未实现

需求中包含：

* Mean Variance Optimization
* Black-Litterman
* Risk Parity
* Hierarchical Risk Parity
* Minimum Variance
* Equal Risk Contribution

当前状态：

* 只有回测中的仓位分配方法
* 还没有独立 Portfolio Optimizer 模块
* 还没有协方差矩阵、目标收益、优化约束求解器

差距级别：高。

### 3.2 Risk Engine 不完整

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

* 已有回测里的止损、最大回撤、部分风险控制
* 尚未形成独立 `packages/risk_engine`
* 风险报告还不是单独产品能力

差距级别：高。

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

### 3.4 前端尚未完全 Workflow 化

当前状态：

* 页面已有工作台、行情、候选池、组合策略工作流、报告入口
* 新的 `POST /workflows/portfolio-research` 后端已接入
* 前端尚未完全切换为 Workflow Engine 驱动

目标状态：

```text
页面操作
  -> Workflow API
  -> 节点状态展示
  -> 回测结果
  -> AI 解释
  -> 组合建议
  -> 历史归档
```

差距级别：中高。

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

### 3.7 Git / 发布状态仍需整理

当前状态：

* `develop` 上存在多项未提交改动
* 多个功能已经本地测试通过，但未拆分 commit

建议：

* 按功能拆分提交
* 每个提交对应文档和测试
* 避免把 UI、Tiger、Workflow、Report Agent 混在同一个 commit

差距级别：中。

## 4. 下一阶段收口方向

不要继续扩很多新概念，下一阶段应优先把现有能力收口为可日常使用的闭环。

建议顺序：

```text
1. 前端接入 Portfolio Research Workflow
2. Portfolio 权重管理
3. Risk Engine v0.1
4. Portfolio Optimizer v0.1
5. AI Report 归档
```

## 5. 近期优先级

### P0：Workflow 前端化

目标：

* 操作界面调用 `POST /workflows/portfolio-research`
* 展示每个节点状态
* 展示 `trace_id`
* 展示 AI Summary 和 Portfolio Recommendation

### P1：Portfolio 权重管理

目标：

* 每个组合支持目标权重
* 支持现金比例
* 支持保存策略配置
* 支持组合导入 / 导出

### P2：Risk Engine v0.1

目标：

* Volatility
* Beta
* Max Drawdown
* Correlation
* Position Concentration
* Sector Exposure

### P3：Portfolio Optimizer v0.1

目标：

* Equal Weight
* Market Cap Weight
* Minimum Variance
* Risk Parity 初版

### P4：Report Archive

目标：

* 保存 AI Report
* 保存 Workflow Run
* 支持按日期复盘
* 支持 Markdown / HTML 输出

## 6. 当前真实状态一句话

当前项目已经具备：

```text
架构骨架 + 核心 API + 初版页面 + 初版算法 + 初版回测 + 初版 workflow
```

但距离完整生产力系统仍缺：

```text
稳定数据体系 + 完整风险引擎 + 组合优化器 + 多 Agent 自动研究 + 正式报告系统 + 前端完整 workflow 化
```
