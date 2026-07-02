# Changelog

## [0.1.0] - Unreleased

### Added

* Report Archive v0.1（P4）：新增 `report_archives` 表、`packages/portfolio_research/reports.py` 和 `/reports` API，可从 Portfolio Research `trace_id` 生成 Markdown/HTML 报告，支持报告列表和详情；前端 Portfolio Research Workbench 新增 Report Archive 面板，可生成当前 trace 报告、刷新归档并查看 HTML 详情
* 重新排序当前开发计划：下一阶段从 Research Run 复盘页、Report Archive、每日研究首页开始，随后补数据源健康检查和数据质量标记，再做 Portfolio/Strategy/Stock Research 增强，最后推进 Risk/Optimizer v0.2、Model Center、Agent Center、Rebalance 和 Marketplace 远期设计
* Research Run 复盘页（P3）：前端 Portfolio Research Workbench 新增历史复盘面板，消费既有 `GET /research-runs` 和 `GET /portfolio-research/{trace_id}`，支持按组合、策略库存档名、状态和日期筛选历史研究运行，点击记录后复用现有结果区展示 Workflow 节点、回测、Risk、Optimizer、AI Summary 和 Recommendation
* Algorithm Layer 推荐结果新增 `recommendation_horizon=1y`，明确当前 AI 算法制作只做 1 年推荐；3 年/5 年/10 年预测、复杂优化器和自动交易算法不进入当前范围
* Research Run History API v0.1（`packages/research_history`，`GET /research-runs`），复用既有 `workflow_runs` 表，按 `workflow_name`/`state`/`portfolio_name`/`strategy_library_name`/日期查询历史研究运行列表，返回 trace_id、组合、策略库存档名、状态、摘要和时间；新增 `strategy_library_name` 字段（`PortfolioResearchRunRequest`/`PortfolioResearchWorkflowRequest`），前端「策略库」应用/新增/更新会记住当前应用的存档名并随 `/portfolio-research/run` 提交
* Scoring Profiles 模型权重模块 v0.1（`packages/scoring_profiles`），把 Algorithm Layer 评分权重从硬编码抽成 5 个内置只读权重组（Balanced/Growth/Value/Defensive/Momentum），接入 `/stocks/{symbol}/recommendation`、`/stocks/screening`、`/backtests/run`、`/portfolio-research/run` 的 `scoring_profile` 参数；`packages/backtesting/signals.py` 的 `AI_SCORE_WEIGHTS` 硬编码常量同步移除，改为按 profile 动态排除 `news_sentiment` 后重新归一化
* Project Constitution v1.0 and AI Development Charter v1.0 as highest-priority project governance rules; README, `.ai/AGENTS.md`, `.ai/PROJECT_RULES.md`, and governance tests now reference them as mandatory development inputs
* AI Startup Protocol v1.0 (`.ai/AI_STARTUP_PROTOCOL.md`) defining the mandatory read-plan-confirm-develop-test-document sequence for every development Agent
* 重建 project5 为 OpenStock AI
* 项目标准文档 v0.1
* 需求分析 v0.1
* 系统设计框架
* AI 开发架构标准
* GitHub 协作标准
* 版本管理标准
* 敏捷迭代与即开发即使用标准
* 基础 CI 和治理测试
* 实时走势 API 和前端趋势图 MVP
* 独立 Model Layer 标准、目录和 mock provider
* AI 开发工具协作标准，支持 Codex、Claude Code、Cursor 混用开发
* 美股操作界面 MVP，包含热门美股、搜索、报价和实时走势
* 双击启动脚本 `open-app.command`
* 独立 Algorithm Layer 和趋势型推荐算法，并接入操作界面
* LiteLLM-compatible Model Layer provider 和标准
* 项目开发界面，展示版本、架构层和当前可用状态
* Universe Layer，用于每日扫描美股最活跃 Top 100 候选池
* 操作界面增加常用分析维度解读区域
* News / Policy Layer，展示最近新闻和 3 年 SEC 披露线索
* 走势图升级为券商式滑动界面，支持十字坐标、成交量和成交额读数
* 常用分析维度升级为可用数据面板，展示成交量、Rel Vol、RSI、均线、52 周位置等实时指标
* 实时行情坐标分析增加估算换手率、买量和卖量展示
* 操作界面增加美国概念板块预览，按 Most Active Top 100 聚合 AI、半导体、EV、Crypto 等概念热度
* Algorithm Layer 升级到 algorithm-v0.3，推荐评分加入规则化新闻情绪因子
* 后端基础：统一配置管理、数据库连接层、audit_logs 表，以及 Docker Compose（Postgres + Redis）和数据库初始化脚本
* yfinance 风格免费历史日线数据源（近 10 年日 / 周 / 月线 OHLCV），接入 `/stocks/{symbol}/history`
* SEC EDGAR 财报申报读取（免费，按代码解析 CIK，列出 10-K / 10-Q / 8-K 原文链接），接入 `/stocks/{symbol}/filings`
* FRED 宏观数据源（需用户自备免费 API Key），接入 `/macro/{series_id}/observations`
* Model Layer Output Validator：返回前强制检查风险提示、数据来源、模型信息和禁止词，已接入 ModelRouter
* Agent 基类（`packages/ai_agents/base.py`）落地 Policy Guard → Data Context Builder → Workflow Executor → Model Layer → Output Validator → Audit Logger 流水线
* SEC Filing Agent（M3 第一个 Agent），接入 `/stocks/{symbol}/sec-summary`，已用真实 SEC EDGAR 数据端到端联调并验证 audit_logs 落库
* Model Layer 路由工厂 `build_default_router()`：无 Key 时 fallback 到 mock provider，配置任意模型 Key 后自动切换 litellm provider
* SEC EDGAR XBRL 财务数据源（`packages/data_sources/sec_financials.py`），免费读取营收/净利润/EPS/股东权益等真实财报数据
* Algorithm Layer 升级到 `algorithm-v0.2`：加入基本面、成长性、估值三个真实数据因子，与原技术面/风险因子合并为五维度评分，`/stocks/{symbol}/recommendation` 已接入真实 SEC 财务数据并端到端联调
* Workflow Layer 和 AI 选股批量排序：`packages/workflow_layer/stock_screening.py` 把候选池逐个用 Algorithm Layer 并发评分排序，接入 `/stocks/screening`，已端到端联调
* Algorithm Layer 升级到 `algorithm-v0.2.1`：technical 因子改用真实技术指标（`packages/algorithm_layer/technical_indicators.py` 计算 RSI-14、MA(5/20) 金叉死叉、10 日动量），取代原区间涨跌幅粗略估算，日线数据不足时自动退化为旧估算并提示，`/stocks/{symbol}/recommendation` 与 `/stocks/screening` 均已接入并端到端联调
* 选股结果落库存历史：新增 `stock_scores` 表（`packages/db/models.py`），`/stocks/screening` 每次调用都会把候选评分写入数据库，新增 `/stocks/{symbol}/score-history` 读取某只股票历次评分，已用真实数据端到端联调
* Algorithm Layer 升级到 `algorithm-v0.2.2`：`fundamentals`/`valuation` 因子加入 Magic Formula 经典指标 ROC（资本回报率）和 EV/EBIT，跟原有净利润率/P/E 各占 50% 权重，新增 SEC XBRL 标签读取（营业利润、流动资产/负债、固定资产、现金、负债），任一指标缺数据时自动退化为只用另一半，已用真实 AAPL/SOFI 等多只股票数据端到端联调
* Algorithm Layer 升级到 `algorithm-v0.3`：推荐评分加入规则化新闻情绪因子
* Portfolio Strategy Engine（`backtesting-v0.1`）：新增顶层包 `packages/backtesting/`（signals/allocation/risk/performance/engine），对一组股票在指定区间执行仓位分配、买卖规则、风险熔断和回测评估，第一阶段仅用价格/技术信号（动量、RSI、均线金死叉），不接入完整 AI 评分以避免财报数据的未来穿越问题，详见 `docs/standards/PORTFOLIO_STRATEGY_STANDARD.md`
* 新增 `PriceHistoryCache`/`BacktestRun` 表（`packages/db/models.py`），历史价格 24 小时缓存，回测配置与结果落库
* 新增 `POST /backtests/run`（项目第一个 POST 接口），前端组合策略工作流已接入并端到端联调
* Portfolio Strategy Engine 升级到 `backtesting-v0.2`：`packages/data_sources/sec_financials.py` 新增 `parse_companyfacts_series`，按每条 XBRL 财务事实最早的 `filed` 日期重建历史财报快照；新增 `StrategyConfig.signal_mode="ai_score"`，复用 algorithm-v0.3 的基本面/成长/估值/技术/波动风险五因子（新闻情绪因子因无历史新闻归档数据源被排除，剩余权重按比例重新归一化），回测仅在调仓日已披露的财报范围内打分，避免未来数据穿越；新增 `FinancialFactsCache` 表缓存历史财报系列；提取 `packages/algorithm_layer/financial_factors.py`（基本面/成长/估值评分）和 `technical_indicators.volatility_risk_score`，供实时推荐和回测共用，已用核心回归测试验证「财报数据在披露日之前不可见」
* Portfolio（关注组合）持久化：新增 `portfolios` 表（`packages/db/models.py`）和 `packages/db/portfolios.py`（默认组合自动播种、增删股票），新增 `GET /portfolios`、`POST /portfolios/{name}/symbols`、`DELETE /portfolios/{name}/symbols/{symbol}`，前端「组合策略选择」从纯内存状态改为调用这三个接口，修复了刷新页面后组合清单丢失的问题，已用 Playwright 端到端验证（增删后刷新页面数据仍存在）
* 新增 Report Agent（`packages/ai_agents/report_agent.py`），接入 `GET /stocks/{symbol}/report`：复用 `/stocks/{symbol}/recommendation` 的五因子算法评分组装逻辑和 News/Policy Layer 近期新闻，走 Agent 标准流水线（Policy Guard → Data Context Builder → Workflow Executor → Model Layer → Output Validator → Audit Logger），由模型把评分和新闻综合成一段研究结论；工作台右侧「生成研究报告」按钮已接入真实接口（此前为 `alert` 占位），已用真实数据（AAPL）端到端联调
* 组合策略工作流前端体验改造（`apps/web/index.html`，无后端改动）：新增「高级设置」折叠区，把此前硬编码且界面不可见的 `signal_mode`（新增 `ai_score` 选项入口）、`rebalance_frequency`、`benchmark_symbol`、`exit_rules.stop_loss_percent` 改为可配置字段；回测结果新增净值曲线图（组合 vs 基准，原生 Canvas 绘制）和完整交易明细表，此前 `equity_curve`/`trades` 已在响应中但未被渲染；新增提交前字段校验（按既有 min/max 校验并高亮出错字段）、运行中 spinner 反馈、失败时的中文友好提示；6 步流程标题改为根据组合/表单/运行状态动态显示 pending/active/done，不再是纯静态文案；已用 Playwright 端到端验证（校验拦截、`ai_score` 模式请求体、图表与交易表渲染、步骤状态切换）
* 新增 `docs/product/IMPLEMENTATION_GAP_ANALYSIS.md`，同步需求与实际开发差距：明确当前已完成架构骨架、核心 API、初版页面、初版算法、初版回测和初版 workflow；待补齐稳定数据体系、完整风险引擎、组合优化器、多 Agent 自动研究、正式报告系统和前端完整 workflow 化；README、PRD、需求分析和 MVP 路线图已同步下一阶段收口方向
* 新增 `docs/product/PROJECT_PLAN_PROGRESS.md`，把项目计划、实际进度、进度差异、下一步和同步触发条件放在同一张表内，作为后续同步进度、同步文档、同步开发计划的主入口
* 组合策略面板接入 Portfolio Research Workflow（`apps/web/index.html`，无后端改动）：提交从直调 `POST /backtests/run` 改为调用 `POST /workflows/portfolio-research`（Universe Builder → Portfolio Builder → Strategy Selector → Constraint Config → Backtest Runner → AI Summary → Portfolio Recommendation 七节点工作流），`buildBacktestPayload` 改为 `buildWorkflowPayload`，`renderBacktestResult` 改由新增的 `renderWorkflowResult` 编排调用；6 步流程指示器改为按真实 `node_results` 状态驱动（新增 error 态，节点失败时对应步骤变红），不再是写死的 pending/done；新增 AI 总结卡片（`ai_summary`，明确标注为模板生成，非实时模型推理）和 Portfolio Recommendation 卡片（action/reasons/suggestions/risks）；新增节点级失败的中文友好提示（区分于网络层错误），因为 workflow 节点异常会被 engine 吞掉以 `state: "Failed"` 返回 200，不会走 `postJson` 的 catch 路径；`POST /backtests/run` 端点保留，供脚本/测试/未来调用方使用，前端面板不再直接调用；同步更新 `tests/test_project_governance.py` 和 `docs/standards/PORTFOLIO_STRATEGY_STANDARD.md` 的治理断言与 API 文档
* 新增 `.ai/` AI 开发规范目录（`AGENTS.md`、项目规则、编码/测试/Git/API/DB/发布标准、ADR/LESSONS/TEMPLATES），并把 `.ai/AGENTS.md` / `.ai/PROJECT_RULES.md` 纳入 README、PR 模板和治理测试
* Portfolio Research Workflow run 持久化：新增 `workflow_runs` 表和 `packages/db/workflow_runs.py`，`POST /workflows/portfolio-research` 每次运行后保存可序列化 workflow 响应，新增 `GET /workflows/portfolio-research/{trace_id}` 按 trace_id 复盘节点状态、回测结果、AI Summary 和 Portfolio Recommendation；前端组合策略结果展示 trace_id 和复盘接口
* Portfolio 权重管理 v0.1：新增 `portfolio_configs` 表，`PUT /portfolios/{name}/config` 保存目标权重、现金比例和策略配置；前端组合策略面板新增 Save Weights，并在组合列表展示已保存配置
* Risk Engine v0.1：新增 `packages/risk_engine` 和 `POST /risk/portfolio`，输出 Volatility、Beta、Max Drawdown、Average Correlation、Concentration、Sector Exposure；前端 workflow 完成后展示风险摘要
* Portfolio Optimizer v0.1：新增 `packages/portfolio_optimizer` 和 `POST /optimizer/portfolio`，支持 Equal Weight、Market Cap、Minimum Variance、Risk Parity 初版；前端 workflow 完成后展示 Optimizer 目标权重摘要
* Portfolio Research Module v0.1：新增 `packages/portfolio_research`，用 `POST /portfolio-research/run` 和 `GET /portfolio-research/{trace_id}` 统一整合 Workflow、Backtesting、Risk Engine、Portfolio Optimizer、AI Summary 和 Recommendation；前端 Portfolio Research Workbench 改为调用统一入口，减少模块拼装感
* 策略库（Strategy Library）：新增 `strategies` 表和 `packages/db/strategies.py`，新增 `GET/PUT/DELETE /strategies`，把"策略"（仓位分配方法、信号模式、再平衡频率、约束）做成独立于 Portfolio（股票桶）的可复用实体，而不是像 `PortfolioConfig.strategy_config` 那样绑死在某个组合名下；左边栏「组合策略选择」改造为「策略库 Strategy Library」面板，提供新增/应用/更新/删除已保存策略（应用只写回表单不自动运行，便于调整后再运行或另存为新策略）；选股加入组合的动作从左边栏挪到右边栏「研究操作」，跟"当前正在看的股票"绑定，不再需要为每个组合桶单独重复选股票
* 删除 `PortfolioConfig.strategy_config` 重叠字段：组合（Portfolio）现在只管股票和目标权重/现金比例，策略参数全部收敛到上面新增的策略库，不再有两套地方各存一份同样含义的 `allocation_method`/`signal_mode`/`rebalance_frequency`/`benchmark_symbol`；`PUT /portfolios/{name}/config` 请求体不再接受 `strategy_config`，「Save Weights」按钮现在名副其实——只保存权重，不再悄悄带一份过时的策略快照

### Fixed

* 修复策略库「新增策略」使用浏览器原生 `prompt()` 导致弹窗提交体验不稳定、没有内联错误和加载反馈的问题；改为工作台内置策略名称弹层，提交走原有 `PUT /strategies/{name}` API，保存成功后自动关闭弹层并刷新策略列表
* 策略库「新增策略」弹层不再要求手动输入策略名称，改为从 PRD 策略库清单中选择固定策略项（Equal Weight、Momentum、Risk Parity、Black-Litterman 等），降低命名不一致和提交失败感
* 策略库左侧面板改为持续展示“可选策略组合”：固定策略清单和历史保存的自定义策略都可见，并标出“当前选择 / 已保存 / 待保存”，避免策略组合只藏在新增弹窗里
* 策略卡片新增「推荐组合」动作：选择某个策略组合后直接运行 Portfolio Research，输出该策略下的 Recommended Research Portfolio、回测、风险、优化权重和 Portfolio Recommendation；结果明确标注仅用于投资研究辅助，不构成投资建议
* 优化 Portfolio Research Workbench 结果页布局：把 Recommended Research Portfolio、Portfolio Recommendation 和 Risk Engine 提前为主结果区，目标权重改为可扫读的权重卡片，回测图表和交易明细后置并降低高度，减少长报表感
* 组合策略回测（`POST /backtests/run`）使用「市值加权」（`market_cap_weighted`）分配方式时运行缓慢：`shares_outstanding_fetcher` 此前在每个调仓日对每只候选股都重新发起一次未缓存的 SEC EDGAR companyfacts 请求（最长 20 秒超时），多调仓日 × 多股票的回测会触发数百次重复网络请求；现改为 `PortfolioBacktestEngine.run()` 每只股票每次回测只预取一次（`packages/backtesting/engine.py`），且 `apps/api/main.py::_fetch_shares_outstanding` 改为复用已有 24 小时缓存的年度财报序列（`get_or_fetch_annual_series`）取股数，不再发起额外请求；新增回归测试验证调用次数不随调仓日数量增长
* `PortfolioBacktestEngine.run()` 的历史价格 / 财报 / 股数三处按股票预取改为线程池并发（`MAX_CONCURRENT_REQUESTS = 8`，与 `StockScreeningWorkflow` 一致），冷缓存多股票回测不再逐个串行等待网络请求
* `SECFilingClient.get_cik()`（`packages/data_sources/sec_filings.py`）此前每遇到一个未缓存过的股票代码都会重新下载一次完整的 SEC ticker→CIK 映射表（几千条记录的大文件），现改为整张表只下载一次解析进内存缓存（加锁防止并发请求重复下载），后续任意股票代码的解析不再产生网络请求
* 修复 `_fetch_companyfacts_payload` / `_fetch_json`（`sec_financials.py` / `sec_filings.py`）未捕获 `http.client.IncompleteRead` 导致的请求崩溃：SEC EDGAR 在响应大文件时偶发连接中断，此前会让 `/stocks/{symbol}/recommendation`、`/backtests/run` 等接口直接抛出未处理异常返回 500，现已归类为「数据缺失」按既有的 best-effort 降级路径处理
