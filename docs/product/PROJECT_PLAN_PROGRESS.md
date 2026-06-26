# OpenStock AI 项目计划与进度总表 v0.1

## 1. 文档用途

本文档用于把 OpenStock AI 的产品需求、开发计划、实际进度、进度差异和下一步行动放在同一张表内，作为后续同步进度、同步文档、同步开发计划的主入口。

每次完成一个功能、接口、页面、Agent、Workflow、数据源或测试后，都应同步更新本文档。

本系统仅用于投资研究辅助，不构成任何投资建议。

## 2. 状态定义

| 状态 | 含义 |
|---|---|
| released | 已完成并可作为稳定基础 |
| verified | 已有测试覆盖，行为已验证 |
| usable | 已可使用，但仍需增强稳定性或体验 |
| partial | 已完成核心骨架，但需求未完整覆盖 |
| planned | 已进入计划，尚未开发 |
| blocked | 当前受外部条件或前置能力阻塞 |

## 3. 项目总览

| 项目维度 | 目标 | 当前判断 | 差异 |
|---|---|---|---|
| MVP 架构骨架 | 支撑股票研究、组合、回测、AI 报告和 Workflow | 约 65%-70% | 仍缺风险引擎、优化器、报告归档和前端 workflow 化 |
| 个人股票研究生产力工具 | 支撑 Cullen 每日选股、研究、回测、报告和复盘 | 约 50%-60% | 日常闭环还缺归档、权重管理、前端 workflow 状态和复盘页 |
| AI Portfolio Operating System | Workflow 驱动组合研究、风险、优化、报告和再平衡 | 约 25%-35% | 多 Agent、Risk Engine、Optimizer、Rebalance Engine 尚未成型 |

## 4. 计划与进度总表

| ID | 模块 | 计划目标 | 当前实际进度 | 状态 | 进度差异 | 下一步 | 同步触发 |
|---|---|---|---|---|---|---|---|
| M0 | 项目重建与治理 | 建立标准文档、GitHub 协作、CI、测试规范 | 项目标准、需求、架构、GitHub 模板、治理测试已建立 | released | 基本无 | 保持文档随开发同步 | 新增模块或标准时 |
| M1 | 后端基础 | FastAPI、配置、数据库、audit_logs、Docker 本地服务 | FastAPI、配置、SQLite fallback、Postgres/Redis compose、初始化脚本已可用 | verified | 需要更多运行监控 | 补 API 响应时间和错误统计 | 新增 API 或 DB 表时 |
| M2 | 数据源层 | Yahoo、SEC、FRED、Tiger、Alpha Vantage、Finnhub、Polygon 可替换接入 | Yahoo/SEC/FRED/Tiger 已有不同程度接入；Alpha Vantage/Finnhub/Polygon 未接 | partial | 数据源稳定性和商业源覆盖不足 | 建立数据源健康检查、重试、限流和优先级 | 新增或修改外部数据源时 |
| M3 | Model Layer | OpenAI、Claude、Gemini、DeepSeek、Qwen、Llama、Ollama 统一调用 | LiteLLM-compatible provider、mock provider、router、validator 已完成 | partial | 真实多模型联调不足 | 补多模型配置样例、成本统计、失败 fallback 测试 | 新增模型或 Agent 时 |
| M4 | AI Agent Layer | Research、News、Financial、Risk、Strategy、Portfolio、Macro、Report、Decision Agents | SEC Filing Agent、Report Agent 已落地 | partial | 多数 Agent 未实现，多 Agent workflow 未成型 | 先做 News Agent 和 Risk Agent v0.1 | 新增 Agent 或 AI 输出时 |
| M5 | Universe / Screener | 每日扫描美股最活跃 100 只票，支持主题和自定义股票池 | Most Active Top 100 已可用，概念板块预览已接入页面 | usable | 主题筛选和自定义股票池不完整 | 增加 AI、Semiconductor、Growth、Dividend 等主题 universe | 新增筛选维度时 |
| M6 | Algorithm Layer | 独立推荐算法、评分因子、可解释输出 | algorithm-v0.3 已有财务、估值、技术、新闻规则情绪、风险因子 | verified | 仍偏规则化，非成熟量化模型 | 引入因子归一化、行业相对估值、历史表现校验 | 调整评分权重或因子时 |
| M7 | Stock Research | 单股实时价格、K 线、财务、新闻、评分、报告 | 报价、趋势、历史、SEC、新闻、推荐、报告接口已存在 | usable | 独立深度分析页未完成 | 做独立 Stock Research 页面 | 前端新增研究视图时 |
| M8 | Portfolio | 多组合创建、删除、编辑、导入、导出、权重管理、对比 | 基础组合保存、增删股票已完成 | partial | 缺权重、现金比例、导入导出、多组合对比 | 做 Portfolio 权重管理 v0.1 | 修改组合数据结构时 |
| M9 | Strategy / Backtesting | 策略配置、约束、回测、收益风险指标 | `/backtests/run`、technical / ai_score 回测、交易明细和净值曲线已可用 | verified | 高级策略和历史新闻情绪未接 | 完善策略库和历史新闻归档输入 | 新增策略或回测指标时 |
| M10 | Workflow Engine | 统一编排 Universe、Portfolio、Strategy、Backtesting、AI Summary、Recommendation | 通用 engine + PortfolioResearchWorkflow v0.1 已完成 | verified | 前端未完全调用 workflow，workflow run 未持久化 | 前端接入 `/workflows/portfolio-research` 并保存 run | 新增 workflow 或节点时 |
| M11 | Risk Engine | VaR、CVaR、Beta、波动率、回撤、行业暴露、持仓集中度 | 回测中已有部分止损、最大回撤、风险提示 | partial | 独立 Risk Engine 未形成 | 建 `packages/risk_engine` v0.1 | 新增风险指标时 |
| M12 | Portfolio Optimizer | Mean Variance、Risk Parity、HRP、Minimum Variance、Black-Litterman | 尚未独立实现 | planned | 与需求差距高 | 先做 Minimum Variance 和 Risk Parity 初版 | 新增优化器时 |
| M13 | AI Report / Archive | PDF、Markdown、HTML、Dashboard、报告归档、每日复盘 | 单股 Report Agent 已有，正式报告系统未完成 | partial | 缺归档和正式输出格式 | 做 Report Archive + Markdown/HTML 输出 | 新增报告模板时 |
| M14 | 前端工作台 | 操作界面可完成查询、筛选、组合、回测、报告 | 当前工作台可用，组合策略 UI 已增强 | usable | 新 Portfolio Research Workflow 未完整接入 | 接入 workflow 节点状态、trace_id、AI Summary | 修改页面 workflow 时 |
| M15 | Tiger OpenAPI | 官方只读行情数据接入，不抓 App，不自动交易 | status、quote、history 接口骨架和标准已完成 | usable | 真实 SDK adapter 未完整接通 | 完成官方 SDK adapter 和凭证联调 | 修改 Tiger 接入时 |
| M16 | Broker Layer | 未来可接券商 API，人工确认后交易 | `packages/brokers` 仍为空 | planned | 第一阶段不做交易 | 暂只保留接口边界，不开发自动交易 | 开始券商接口设计时 |
| M17 | 数据可追溯 / 审计 | AI 输出写 audit_logs，结论有数据来源和时间 | Agent 基类和 ModelResponse 审计路径已建立 | partial | Workflow run 和普通算法输出审计还需增强 | 持久化 workflow run 和 report archive | 新增 AI/Workflow 输出时 |
| M18 | Git / 发布管理 | develop 开发、main 稳定、功能拆分提交 | develop 当前有多项未提交改动，测试通过；本地未配置 GitHub remote，暂不能 push | partial | 需要拆分 commit、整理发布记录，并配置 GitHub remote | 先确认 GitHub 仓库地址，再按功能分批 stage/commit/push | 准备 PR 或发布时 |

## 5. 下一阶段执行顺序

| 优先级 | 任务 | 目标结果 | 验收标准 |
|---|---|---|---|
| P0 | 前端接入 Portfolio Research Workflow | 页面直接调用 `POST /workflows/portfolio-research` | 可看到节点状态、trace_id、AI Summary、Portfolio Recommendation |
| P1 | Portfolio 权重管理 | 组合支持权重、现金比例、保存策略配置 | API 和页面均可查看、修改、保存权重 |
| P2 | Risk Engine v0.1 | 独立风险计算模块 | 输出 Volatility、Beta、Max Drawdown、Correlation、Concentration、Sector Exposure |
| P3 | Portfolio Optimizer v0.1 | 独立组合优化模块 | 支持 Equal Weight、Market Cap、Minimum Variance、Risk Parity 初版 |
| P4 | AI Report 归档 | 报告和 workflow 结果可复盘 | 生成 Markdown/HTML，并保存历史记录 |

## 6. 同步规则

每次开发完成后必须同步：

1. 更新本文件对应行的 `当前实际进度`、`状态`、`进度差异` 和 `下一步`。
2. 如果新增模块，更新 `README.md`、`docs/product/mvp-roadmap.md` 和相关标准文档。
3. 如果新增 API，更新 `docs/api/api-design-v0.1.md`。
4. 如果新增 AI 输出，确认风险提示和 audit/log 路径。
5. 如果新增数据源，确认 `.env.example`、安全边界和测试。
6. 运行测试并记录结果。

## 7. 最近一次同步

```text
日期：2026-06-27
测试：196 tests OK
Git 检查：develop 分支存在多项未提交改动；git remote -v 为空，暂不能直接同步到 GitHub。
安全检查：未发现真实 API Key；git diff --check 通过。
状态：新增项目计划与进度总表，并同步 GitHub 发布阻塞点，作为后续同步进度、文档和开发计划的主入口。
```
