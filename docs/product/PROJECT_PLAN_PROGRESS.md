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
| MVP 架构骨架 | 支撑股票研究、组合、回测、AI 报告和 Workflow | 约 80%-85% | 仍缺报告归档和完整复盘页 |
| 个人股票研究生产力工具 | 支撑 Cullen 每日选股、研究、回测、报告和复盘 | 约 65%-75% | 日常闭环还缺报告归档和复盘页 |
| AI Portfolio Operating System | Workflow 驱动组合研究、风险、优化、报告和再平衡 | 约 25%-35% | 多 Agent、Risk Engine、Optimizer、Rebalance Engine 尚未成型 |

## 4. 计划与进度总表

| ID | 模块 | 计划目标 | 当前实际进度 | 状态 | 进度差异 | 下一步 | 同步触发 |
|---|---|---|---|---|---|---|---|
| M0 | 项目重建与治理 | 建立标准文档、GitHub 协作、CI、测试规范 | 项目标准、需求、架构、GitHub 模板、治理测试、`.ai/` AI 开发规范、`PROJECT_CONSTITUTION.md`、`AI_DEVELOPMENT_CHARTER.md` 和 `.ai/AI_STARTUP_PROTOCOL.md` 已建立 | released | 基本无 | 保持文档随开发同步；未来开发必须先遵守 Constitution / Charter / Startup Protocol | 新增模块或标准时 |
| M1 | 后端基础 | FastAPI、配置、数据库、audit_logs、Docker 本地服务 | FastAPI、配置、SQLite fallback、Postgres/Redis compose、初始化脚本已可用 | verified | 需要更多运行监控 | 补 API 响应时间和错误统计 | 新增 API 或 DB 表时 |
| M2 | 数据源层 | Yahoo、SEC、FRED、Tiger、Alpha Vantage、Finnhub、Polygon 可替换接入 | Yahoo/SEC/FRED/Tiger 已有不同程度接入；Alpha Vantage/Finnhub/Polygon 未接 | partial | 数据源稳定性和商业源覆盖不足 | 建立数据源健康检查、重试、限流和优先级 | 新增或修改外部数据源时 |
| M3 | Model Layer | OpenAI、Claude、Gemini、DeepSeek、Qwen、Llama、Ollama 统一调用 | LiteLLM-compatible provider、mock provider、router、validator 已完成 | partial | 真实多模型联调不足 | 补多模型配置样例、成本统计、失败 fallback 测试 | 新增模型或 Agent 时 |
| M4 | AI Agent Layer | Research、News、Financial、Risk、Strategy、Portfolio、Macro、Report、Decision Agents | SEC Filing Agent、Report Agent 已落地 | partial | 多数 Agent 未实现，多 Agent workflow 未成型 | 先做 News Agent 和 Risk Agent v0.1 | 新增 Agent 或 AI 输出时 |
| M5 | Universe / Screener | 每日扫描美股最活跃 100 只票，支持主题和自定义股票池 | Most Active Top 100 已可用，概念板块预览已接入页面 | usable | 主题筛选和自定义股票池不完整 | 增加 AI、Semiconductor、Growth、Dividend 等主题 universe | 新增筛选维度时 |
| M6 | Algorithm Layer | 独立推荐算法、评分因子、可解释输出 | algorithm-v0.3 已有财务、估值、技术、新闻规则情绪、风险因子；权重已从硬编码抽成独立的 Scoring Profiles 模块（`packages/scoring_profiles`，Balanced/Growth/Value/Defensive/Momentum 5 个内置只读权重组），接入推荐、选股、回测、Portfolio Research 四个入口的 `scoring_profile` 参数 | verified | 仍偏规则化，非成熟量化模型；Scoring Profiles 暂不支持用户自定义保存 | 引入因子归一化、行业相对估值、历史表现校验；评估 Scoring Profiles 自定义保存需求 | 调整评分权重或因子时 |
| M7 | Stock Research | 单股实时价格、K 线、财务、新闻、评分、报告 | 报价、趋势、历史、SEC、新闻、推荐、报告接口已存在 | usable | 独立深度分析页未完成 | 做独立 Stock Research 页面 | 前端新增研究视图时 |
| M8 | Portfolio | 多组合创建、删除、编辑、导入、导出、权重管理、对比 | 基础组合保存、增删股票、目标权重、现金比例已完成；选股加入组合改为跟随当前查看的股票（右边栏），不再绑定左边栏桶选择；`PortfolioConfig.strategy_config` 旧字段已删除，组合现在只管股票和权重，策略参数全部收敛到策略库 | usable | 缺导入导出、多组合对比 | 做导入导出和多组合对比 | 修改组合数据结构时 |
| M9 | Strategy / Backtesting | 策略配置、约束、回测、收益风险指标 | `/backtests/run`、technical / ai_score 回测、交易明细和净值曲线已可用；策略库 Strategy Library v0.1 已完成（`packages/db/strategies.py`、`GET/PUT/DELETE /strategies`），策略与 Portfolio 完全解耦为独立可复用实体（旧的 `PortfolioConfig.strategy_config` 重叠字段已删除），前端支持新增/应用/更新/删除 | verified | 历史新闻情绪未接；策略库暂无导入导出/分享 | 接入历史新闻归档输入，评估策略市场（导入导出/分享）需求 | 新增策略或回测指标时 |
| M10 | Workflow Engine | 统一编排 Universe、Portfolio、Strategy、Backtesting、AI Summary、Recommendation | 通用 engine + PortfolioResearchWorkflow v0.1 已完成；Portfolio Research Module v0.1 已作为前端统一入口接入 `/portfolio-research/run`；workflow run 支持按 trace_id 查询；新增 `GET /research-runs` 历史列表 API（`packages/research_history`），按时间/组合/策略库存档名查询，前端「应用策略」会带上 `strategy_library_name` | verified | 缺完整复盘页（trace_id 详情前端） | 做 workflow run 列表前端页和复盘页 | 新增 workflow 或节点时 |
| M11 | Risk Engine | VaR、CVaR、Beta、波动率、回撤、行业暴露、持仓集中度 | 独立 `packages/risk_engine` v0.1 已形成，支持 Volatility、Beta、Max Drawdown、Average Correlation、Concentration、Sector Exposure，接入 `POST /risk/portfolio` 和前端摘要 | verified | VaR/CVaR/Stress Test/Monte Carlo 未接 | 后续扩展 VaR、CVaR 和 Stress Test | 新增风险指标时 |
| M12 | Portfolio Optimizer | Mean Variance、Risk Parity、HRP、Minimum Variance、Black-Litterman | 独立 `packages/portfolio_optimizer` v0.1 已完成，支持 Equal Weight、Market Cap、Minimum Variance、Risk Parity 初版，接入 `POST /optimizer/portfolio` 和前端摘要 | verified | HRP、Black-Litterman 和完整协方差求解器未接 | 后续做高级优化器求解器 | 新增优化器时 |
| M13 | AI Report / Archive | PDF、Markdown、HTML、Dashboard、报告归档、每日复盘 | 单股 Report Agent 已有，正式报告系统未完成 | partial | 缺归档和正式输出格式 | 做 Report Archive + Markdown/HTML 输出 | 新增报告模板时 |
| M14 | 前端工作台 | 操作界面可完成查询、筛选、组合、回测、报告 | 当前工作台可用，Portfolio Research Workbench 已调用统一 `/portfolio-research/run`，并展示回测、Risk、Optimizer、AI Summary、Recommendation 和 trace_id 复盘入口；左边栏改造为「策略库 Strategy Library」面板，股票选择移至右边栏 | usable | 暂无历史列表和完整复盘页 | 做 workflow run 历史列表和复盘页 | 修改页面 workflow 时 |
| M15 | Tiger OpenAPI | 官方只读行情数据接入，不抓 App，不自动交易 | status、quote、history 接口骨架和标准已完成 | usable | 真实 SDK adapter 未完整接通 | 完成官方 SDK adapter 和凭证联调 | 修改 Tiger 接入时 |
| M16 | Broker Layer | 未来可接券商 API，人工确认后交易 | `packages/brokers` 仍为空 | planned | 第一阶段不做交易 | 暂只保留接口边界，不开发自动交易 | 开始券商接口设计时 |
| M17 | 数据可追溯 / 审计 | AI 输出写 audit_logs，结论有数据来源和时间 | Agent 基类和 ModelResponse 审计路径已建立，Portfolio Research Workflow run 已按 trace_id 持久化 | partial | 普通算法输出审计和 report archive 还需增强 | 做 report archive 和普通算法输出审计增强 | 新增 AI/Workflow 输出时 |
| M18 | Git / 发布管理 | develop 开发、main 稳定、功能拆分提交 | develop 已完成本地提交 `ea4418b`；origin 已配置为 `haisheng-bot/cullen`；GitHub push 受本机认证阻塞 | partial | 远端 main 是独立初始提交，develop 尚未推送；本机缺 HTTPS 凭证和 SSH 公钥 | 配置 GitHub 凭证后推送 `develop`，再从 develop 发起 PR 合并 main | 准备 PR 或发布时 |

## 5. 下一阶段执行顺序

本节是当前 ToDo list 的主入口。排序原则：先补齐可日常使用闭环，再扩展高级算法和多 Agent。

| 优先级 | 任务 | 目标结果 | 验收标准 |
|---|---|---|---|
| P0 | ~~PRD v0.3 / Roadmap 对齐~~ | ~~把 AI Portfolio Research Platform 的新定位同步到主文档，清理旧的已完成任务~~ | 已完成：`README.md`、`PRD.md`、`mvp-roadmap.md`、本文件已同步新 Roadmap，已完成的 Workflow/Risk/Optimizer 不再作为下一步 |
| P1 | ~~Scoring Profiles / 模型权重模块 v0.1~~ | ~~评分因子权重从 Algorithm Layer 硬编码中独立出来，形成 Balanced/Growth/Value/Defensive/Momentum 等研究风格~~ | 已完成：`packages/scoring_profiles` 存在；`/stocks/{symbol}/recommendation`、`/stocks/screening`、`/backtests/run`、`/portfolio-research/run` 均支持 `scoring_profile` |
| P2 | ~~Research Run History API~~ | ~~用户可以按时间、组合、策略查询历史研究运行~~ | 已完成：`GET /research-runs` 存在，返回 trace_id、组合、策略库存档名、状态、摘要和时间，支持按 workflow_name/state/portfolio_name/strategy_library_name/日期过滤 |
| P3 | Trace 复盘页 | 用户能打开一次研究的完整复盘 | 前端可从历史列表进入 trace_id 详情，展示 Workflow 节点、回测、Risk、Optimizer、AI Summary、Recommendation |
| P4 | Report Archive v0.1 | 每次 Portfolio Research 可生成并保存 Markdown/HTML 报告 | 新增报告归档表和 API；支持从 trace_id 生成报告；前端可查看报告列表和详情 |
| P5 | 数据源健康检查 | Yahoo/SEC/FRED/Tiger 数据状态可观测 | 新增数据源健康 API/页面，展示配置、可用性、最近错误和 fallback 状态 |
| P6 | Strategy Library v0.2 | 策略支持版本、复制、导入导出和分类 | 策略可 Clone/Save As；支持 JSON 导入导出；策略可绑定默认 scoring_profile |
| P7 | Portfolio Manager v0.2 | 组合支持版本、导入导出和组合对比 | 可比较两个组合的持仓、权重、收益、风险和行业暴露 |
| P8 | Risk Engine v0.2 | 风险分析扩展到尾部风险和压力测试 | 输出 Sortino、Calmar、Tracking Error、Information Ratio、VaR、CVaR 和基础 Stress Test |
| P9 | Portfolio Optimizer v0.2 | 优化器输出优化前后对比和高级方法雏形 | 增加 Maximum Sharpe/CVaR Optimization；Black-Litterman 先完成接口和 mock；输出调仓原因 |
| P10 | Model Center 基础版 | 模型供应商、路由、fallback 和成本状态可视化 | 新增 `/models/status`、provider 列表、prompt 模板目录和 token/cost 记录结构 |
| P11 | Agent Center 基础版 | Agent 从散落代码变成注册中心管理 | 建立 Agent Registry，列出 Research/Report/Risk/News/Financial/Strategy Agent 的状态、依赖和入口 |
| P12 | Marketplace 远期评估 | 策略、Agent、Workflow、因子模型具备分享/插件化方向 | 形成设计文档，不在当前 MVP 中实现交易或商业市场 |

已完成并从下一步移除：

```text
1. 前端接入 Portfolio Research Workflow
2. Portfolio 权重管理
3. Risk Engine v0.1
4. Portfolio Optimizer v0.1
5. Strategy Library v0.1
6. Portfolio Research Module v0.1
7. Workflow run 持久化和 trace_id 查询
8. PRD v0.3 / Roadmap 对齐
9. Scoring Profiles / 模型权重模块 v0.1
10. Research Run History API
```

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
测试：236 tests OK（unittest discover，.venv311 / Python 3.11）；`git diff --check` 通过；Playwright 验证：本地打开工作台→点击 `Risk Parity`「推荐组合」→主结果区顶部展示 Recommended Research Portfolio 权重卡片、Portfolio Recommendation 和 Risk Engine；Workbench 桌面布局由三栏改为左侧导航 + 右侧完整工作区，右侧研究/新闻栏下移，不再挤压结果区；截图文件：`.playwright-cli/page-2026-06-27T12-22-46-427Z.png`。
状态：修复策略库选择体验并优化 Portfolio Research Workbench 结果页——前端从浏览器原生 `prompt()` 改为工作台内置策略名称弹层，并进一步把策略名称从手动输入改为 PRD 策略库固定下拉选项；左侧策略库面板持续展示可选策略组合；策略卡片新增「推荐组合」动作；结果区把 Recommended Research Portfolio、Portfolio Recommendation 和 Risk Engine 提前为主结果区，目标权重改为卡片展示，回测图表和交易明细后置并降低高度；桌面布局改为两栏，给 Workbench 更完整的横向空间；提交仍走既有 `PUT /strategies/{name}` 和 `/portfolio-research/run` API，不改变后端接口。
```

```text
日期：2026-06-27
测试：236 tests OK（unittest discover，.venv311 / Python 3.11）；`git diff --check` 通过。
状态：完成文档进度对齐检查后的同步修正——`PRD.md` 版本更新为 v0.3 / Official；`mvp-roadmap.md`、`requirements-analysis.md`、`IMPLEMENTATION_GAP_ANALYSIS.md` 的下一阶段任务移除已完成的 P0/P1/P2，统一从 P3 trace_id 完整复盘页开始；README 文档入口同步为 PRD v0.3。
```

```text
日期：2026-06-27
测试：236 tests OK（unittest discover，.venv311 / Python 3.11）；Playwright 验证：本地起服务→`PUT /strategies/PlaywrightTestStrategy` 建一个策略→前端点击该策略「应用」→点击运行→拦截 `POST /portfolio-research/run` 请求体确认带 `strategy_library_name: "PlaywrightTestStrategy"`→`curl GET /research-runs?portfolio_name=...` 确认该次真实运行可按组合名查到，`strategy_library_name`/`summary_text` 字段值正确；全程无 console error。
状态：完成 P2 Research Run History API——复用既有 `workflow_runs` 表（不新建表），新增 `packages/research_history`（`summarize_run()` 兼容 `portfolio_research_workflow`/`portfolio_research_module` 两种历史 response 形状）+ `packages/db/workflow_runs.py::list_workflow_runs` + `GET /research-runs`（按 workflow_name/state/portfolio_name/strategy_library_name/日期过滤，内存分页）。新增字段 `strategy_library_name`（`PortfolioResearchRunRequest`/`PortfolioResearchWorkflowRequest` 顶层，与 `BacktestRunRequest.strategy_name` 区分开，避免同名不同义冲突）；前端「策略库」应用/新增/更新会记住当前应用的存档名并随提交带上，删除当前应用的存档会清空记忆（仅作标签，不做强校验，手动改表单后不会失效）。同步 `api-design-v0.1.md`（新增 §4.10）、README、mvp-roadmap、CHANGELOG。P2 标记完成，下一步 P3 Trace 复盘页（前端列表/详情页，消费这个新接口）。
```

```text
日期：2026-06-27（上一次）
测试：227 tests OK（unittest discover，.venv311 / Python 3.11）。
状态：完成 P1 Scoring Profiles / 模型权重模块 v0.1——新增 `packages/scoring_profiles`（5 个内置只读权重组：Balanced/Growth/Value/Defensive/Momentum），消除 `packages/algorithm_layer/recommendation.py` 和 `packages/backtesting/signals.py`（原 `AI_SCORE_WEIGHTS` 常量）两处重复硬编码权重，统一为单一权重来源；`/stocks/{symbol}/recommendation`、`/stocks/screening`、`/backtests/run`、`/portfolio-research/run` 四个入口均接入 `scoring_profile` 参数，未知名返回 400。`RecommendationResult`/`BacktestResult`/`ScreeningResult` 响应体新增 `scoring_profile` 字段。新建 `docs/standards/SCORING_PROFILES_STANDARD.md`；同步 `ALGORITHM_STANDARD.md`、`api-design-v0.1.md`、README、mvp-roadmap、CHANGELOG。M6 已知遗留（评分权重硬编码）已清除，P1 标记完成。
```

```text
日期：2026-06-27
测试：待本轮文档治理检查。
状态：新增 `.ai/AI_STARTUP_PROTOCOL.md`，定义 OpenStock AI 开发 Agent 的强制启动顺序：读取 Constitution、Charter、当前模块 PRD、Architecture、Coding Standard，输出理解和计划，涉及架构或接口变更时等待确认，再开发、测试、更新文档和输出变更说明；同步 README、`.ai/AGENTS.md`、`.ai/PROJECT_RULES.md`、CHANGELOG 和治理测试。
```

```text
日期：2026-06-27
测试：待本轮文档治理检查。
状态：新增 `PROJECT_CONSTITUTION.md` 和 `AI_DEVELOPMENT_CHARTER.md`，作为 OpenStock AI 最高优先级开发规则；同步更新 README、`.ai/AGENTS.md`、`.ai/PROJECT_RULES.md`、CHANGELOG 和治理测试入口。未来任何开发任务必须优先读取并遵守这两个文件。
```

```text
日期：2026-06-27
测试：219 tests OK（unittest discover，.venv311 / Python 3.11）。
状态：删除 `PortfolioConfig.strategy_config` 重叠字段——上一次同步记录的"已知遗留"已收敛：组合（Portfolio）现在只管股票和目标权重/现金比例，`PUT /portfolios/{name}/config` 不再接受 `strategy_config`；策略参数唯一归属策略库（`GET/PUT/DELETE /strategies`）。同步改了 `packages/db/models.py`（PortfolioConfig 去掉该列）、`packages/db/portfolios.py`、`apps/api/main.py`、`apps/web/index.html`（Save Weights 按钮不再带策略快照）及对应测试和文档。M8/M9 已知遗留标记已清除。
```

```text
日期：2026-06-27（上一次）
测试：219 tests OK（unittest discover，.venv311 / Python 3.11）；Playwright 验证：新增策略（PUT 请求体字段正确）→列表更新→应用回填表单→更新覆盖→删除生效；右边栏选股加入指定组合桶，左边栏组合列表同步；回测运行路径（`/portfolio-research/run`）不受影响；全程无 console error。
状态：完成策略库 Strategy Library v0.1——新增 `strategies` 表、`packages/db/strategies.py`、`GET/PUT/DELETE /strategies`，策略（仓位分配方法/信号模式/再平衡频率/约束）与 Portfolio（股票桶）解耦为独立可复用实体；左边栏「组合策略选择」改造为「策略库」面板（新增/应用/更新/删除），选股加入组合的动作挪到右边栏跟随当前查看的股票，不再绑定左边栏桶选择。已知遗留：`PortfolioConfig.strategy_config`（旧的按组合存策略字段）与新策略库概念重叠，尚未整合，见 M8/M9。下一步是评估是否收敛旧字段，以及完整复盘页和 Report Archive。
```

```text
日期：2026-06-27（上一次）
测试：210 tests OK（unittest discover，.venv311 / Python 3.11）；`py_compile` 通过；`git diff --check` 通过；本地 API smoke test 通过（`POST /portfolio-research/run` 返回 completed，且 backtest/risk/optimizer 均有结果；同一 `trace_id` 调 `GET /portfolio-research/{trace_id}` 成功读回）。
状态：完成 Portfolio Research Module v0.1 体验整合——新增 `packages/portfolio_research`，新增 `POST /portfolio-research/run` 和 `GET /portfolio-research/{trace_id}`；前端 Portfolio Research Workbench 改为调用统一入口，不再直接拼接 Workflow/Risk/Optimizer API。下一步是完整复盘页和 Report Archive。
```

```text
日期：2026-06-27
测试：207 tests OK（unittest discover，.venv311 / Python 3.11）；`py_compile` 通过；`git diff --check` 通过；本地 API smoke test 通过（`POST /optimizer/portfolio` 返回 minimum_variance 目标权重、cash_weight 和 expected_risk_percent）。
状态：完成 Portfolio Optimizer v0.1——新增 `packages/portfolio_optimizer`、`POST /optimizer/portfolio` 和前端 Optimizer 目标权重摘要；支持 Equal Weight、Market Cap、Minimum Variance、Risk Parity 初版。下一步是 AI Report 归档、Workflow / Report 复盘页和数据源健康检查。
```

```text
日期：2026-06-27
测试：202 tests OK（unittest discover，.venv311 / Python 3.11）；`py_compile` 通过；`git diff --check` 通过；`scripts/init_db.py` 已确认本地 SQLite 包含 `portfolio_configs` 和 `workflow_runs` 表；本地 API smoke test 通过（`PUT /portfolios/Core%20Watch/config` 成功保存权重，`POST /risk/portfolio` 成功返回 Volatility/Beta/Sector Exposure）。
状态：完成 MVP 架构列表 1/2/3 收口——Workflow run 持久化已验证；Portfolio 权重管理 v0.1 完成（`portfolio_configs` + `PUT /portfolios/{name}/config` + 前端 Save Weights）；Risk Engine v0.1 完成（`packages/risk_engine` + `POST /risk/portfolio` + 前端风险摘要）。下一步是 Portfolio Optimizer v0.1、Report Archive 和完整复盘页。
```

```text
日期：2026-06-27
测试：198 tests OK（unittest discover，.venv311 / Python 3.11）；`py_compile` 通过；`scripts/init_db.py` 已确认本地 SQLite 包含 `workflow_runs` 表；本地 API smoke test 通过（`POST /workflows/portfolio-research` 返回 `Recommendation Ready`，再用同一 `trace_id` 调 `GET /workflows/portfolio-research/{trace_id}` 成功读回）。
状态：完成 MVP 收口项——`.ai/` 新开发规范纳入治理入口；Portfolio Research Workflow 每次运行写入 `workflow_runs` 表，新增 `GET /workflows/portfolio-research/{trace_id}` 复盘接口；前端组合策略结果展示 trace_id。下一步是 Portfolio 权重管理、Risk Engine v0.1、Portfolio Optimizer v0.1 和 Report Archive。
```

```text
日期：2026-06-27
测试：196 tests OK（unittest discover，.venv311 / Python 3.11）
Playwright 验证：成功路径（节点全 done、净值曲线/交易表/AI Summary/Recommendation 均渲染）、节点级失败路径（state=Failed，对应步骤变红，定位到失败节点）、网络层失败路径（步骤回落 pending）均通过，控制台无报错。
状态：完成 M10/M14 的 P0 任务——组合策略面板从直调 `POST /backtests/run` 改为调用 `POST /workflows/portfolio-research`，已同步治理测试、标准文档和 CHANGELOG；下一步是 workflow run 持久化和 trace_id 复盘。
```

```text
日期：2026-06-27（上一次）
测试：196 tests OK
Git 检查：develop 已本地提交 ea4418b；origin 已配置为 https://github.com/haisheng-bot/cullen.git；HTTPS push 缺少 GitHub 凭证，SSH push 缺少 public key，暂不能完成远端推送。
安全检查：未发现真实 API Key；git diff --check 通过。
状态：新增项目计划与进度总表，并同步 GitHub 发布阻塞点，作为后续同步进度、文档和开发计划的主入口。
```
