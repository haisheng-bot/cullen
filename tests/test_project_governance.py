from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DISCLAIMER = "本系统仅用于投资研究辅助，不构成任何投资建议。"


class ProjectGovernanceTest(unittest.TestCase):
    def test_required_paths_exist(self) -> None:
        required_paths = [
            "README.md",
            "PROJECT_CONSTITUTION.md",
            "AI_DEVELOPMENT_CHARTER.md",
            "open-app.command",
            "LICENSE",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "CHANGELOG.md",
            ".env.example",
            ".gitignore",
            ".github/workflows/ci.yml",
            ".github/pull_request_template.md",
            ".github/ISSUE_TEMPLATE/config.yml",
            ".github/ISSUE_TEMPLATE/bug_report.md",
            ".github/ISSUE_TEMPLATE/feature_request.md",
            ".ai/AGENTS.md",
            ".ai/AI_STARTUP_PROTOCOL.md",
            ".ai/PROJECT_RULES.md",
            ".ai/CODING_STANDARD.md",
            ".ai/TEST_STANDARD.md",
            ".ai/GIT_STANDARD.md",
            ".ai/API_STANDARD.md",
            ".ai/DB_STANDARD.md",
            ".ai/RELEASE_STANDARD.md",
            ".ai/ADR/0001-ai-governance-directory.md",
            ".ai/TEMPLATES/PR_TEMPLATE.md",
            "apps/api/main.py",
            "apps/web/index.html",
            "apps/web/realtime-trend.html",
            "apps/api",
            "apps/web",
            "packages/data_sources",
            "packages/ai_agents",
            "packages/universe_layer",
            "packages/news_layer",
            "packages/algorithm_layer",
            "packages/model_layer",
            "packages/scoring",
            "packages/backtesting",
            "packages/brokers",
            "packages/risk_engine",
            "packages/portfolio_optimizer",
            "packages/portfolio_research",
            "packages/db/workflow_runs.py",
            "packages/risk_engine/engine.py",
            "packages/portfolio_optimizer/engine.py",
            "packages/portfolio_research/engine.py",
            "docs/standards/project-standard-v0.1.md",
            "docs/standards/MODEL_STANDARD.md",
            "docs/standards/ALGORITHM_STANDARD.md",
            "docs/standards/UNIVERSE_STANDARD.md",
            "docs/standards/NEWS_POLICY_STANDARD.md",
            "docs/standards/WORKFLOW_ENGINE_STANDARD.md",
            "docs/standards/PORTFOLIO_STRATEGY_STANDARD.md",
            "docs/standards/RISK_ENGINE_STANDARD.md",
            "docs/standards/PORTFOLIO_OPTIMIZER_STANDARD.md",
            "docs/standards/PORTFOLIO_RESEARCH_MODULE_STANDARD.md",
            "docs/standards/TIGER_OPENAPI_STANDARD.md",
            "docs/standards/version-management.md",
            "docs/standards/github-collaboration.md",
            "docs/standards/agile-iteration.md",
            "docs/standards/AI_TOOL_COLLABORATION.md",
            "docs/product/PRD.md",
            "docs/product/PERSONAL_PRODUCTIVITY_GOAL.md",
            "docs/product/PROJECT_PLAN_PROGRESS.md",
            "docs/product/IMPLEMENTATION_GAP_ANALYSIS.md",
            "docs/product/requirements-analysis.md",
            "docs/architecture/system-design.md",
            "docs/architecture/ai-development-architecture.md",
            "docs/api/api-design-v0.1.md",
        ]
        missing = [path for path in required_paths if not (ROOT / path).exists()]
        self.assertEqual([], missing)

    def test_required_docs_include_disclaimer(self) -> None:
        docs = [
            "README.md",
            "PROJECT_CONSTITUTION.md",
            "AI_DEVELOPMENT_CHARTER.md",
            ".ai/AI_STARTUP_PROTOCOL.md",
            "docs/standards/project-standard-v0.1.md",
            "docs/standards/MODEL_STANDARD.md",
            "docs/standards/ALGORITHM_STANDARD.md",
            "docs/standards/UNIVERSE_STANDARD.md",
            "docs/standards/NEWS_POLICY_STANDARD.md",
            "docs/standards/WORKFLOW_ENGINE_STANDARD.md",
            "docs/standards/PORTFOLIO_STRATEGY_STANDARD.md",
            "docs/standards/RISK_ENGINE_STANDARD.md",
            "docs/standards/PORTFOLIO_OPTIMIZER_STANDARD.md",
            "docs/standards/PORTFOLIO_RESEARCH_MODULE_STANDARD.md",
            "docs/standards/TIGER_OPENAPI_STANDARD.md",
            "docs/standards/github-collaboration.md",
            "docs/standards/agile-iteration.md",
            "docs/standards/AI_TOOL_COLLABORATION.md",
            "docs/product/PRD.md",
            "docs/product/PERSONAL_PRODUCTIVITY_GOAL.md",
            "docs/product/PROJECT_PLAN_PROGRESS.md",
            "docs/product/IMPLEMENTATION_GAP_ANALYSIS.md",
            "docs/product/requirements-analysis.md",
            "docs/architecture/system-design.md",
            "docs/architecture/ai-development-architecture.md",
            "docs/api/api-design-v0.1.md",
        ]
        missing = [path for path in docs if DISCLAIMER not in (ROOT / path).read_text(encoding="utf-8")]
        self.assertEqual([], missing)

    def test_product_prd_defines_investment_research_platform(self) -> None:
        prd = (ROOT / "docs/product/PRD.md").read_text(encoding="utf-8")
        requirements = (ROOT / "docs/product/requirements-analysis.md").read_text(encoding="utf-8")
        productivity_goal = (ROOT / "docs/product/PERSONAL_PRODUCTIVITY_GOAL.md").read_text(encoding="utf-8")
        plan_progress = (ROOT / "docs/product/PROJECT_PLAN_PROGRESS.md").read_text(encoding="utf-8")
        gap_analysis = (ROOT / "docs/product/IMPLEMENTATION_GAP_ANALYSIS.md").read_text(encoding="utf-8")

        required_terms = [
            "AI Investment Research Platform",
            "Personal Productivity Goal",
            "Stock Screener",
            "Stock Research",
            "Portfolio",
            "Strategy Engine",
            "Workflow Engine",
            "Portfolio Optimizer",
            "Risk Engine",
            "Backtesting Engine",
            "AI Research",
            "AI Report",
            "Strategy Marketplace",
            "Success Metrics",
        ]
        missing = [term for term in required_terms if term not in prd]
        self.assertEqual([], missing)
        self.assertIn("AI Investment Research Platform", requirements)
        self.assertIn("AI Portfolio Operating System", requirements)
        self.assertIn("Portfolio", requirements)
        self.assertIn("Strategy Workflow", requirements)
        self.assertIn("个人股票研究生产力工具", productivity_goal)
        self.assertIn("每日股票池扫描", productivity_goal)
        self.assertIn("研究报告归档", productivity_goal)
        self.assertIn("次日复盘", productivity_goal)
        self.assertIn("项目计划与进度总表", plan_progress)
        self.assertIn("进度差异", plan_progress)
        self.assertIn("同步触发", plan_progress)
        self.assertIn("Portfolio Research Workflow", plan_progress)
        self.assertIn("workflow_runs", plan_progress)
        self.assertIn("GET /workflows/portfolio-research/{trace_id}", plan_progress)
        self.assertIn("Portfolio 权重管理", plan_progress)
        self.assertIn("Risk Engine v0.1", plan_progress)
        self.assertIn("POST /risk/portfolio", plan_progress)
        self.assertIn("Portfolio Optimizer v0.1", plan_progress)
        self.assertIn("POST /optimizer/portfolio", plan_progress)
        self.assertIn("Portfolio Research Module v0.1", plan_progress)
        self.assertIn("POST /portfolio-research/run", plan_progress)
        self.assertIn("最近一次同步", plan_progress)
        self.assertIn("需求与实际开发差距分析", gap_analysis)
        self.assertIn("前端接入 Portfolio Research Workflow", gap_analysis)
        self.assertIn("Risk Engine v0.1", gap_analysis)
        self.assertIn("Portfolio Optimizer v0.1", gap_analysis)

    def test_highest_priority_ai_governance_rules_are_declared(self) -> None:
        constitution = (ROOT / "PROJECT_CONSTITUTION.md").read_text(encoding="utf-8")
        charter = (ROOT / "AI_DEVELOPMENT_CHARTER.md").read_text(encoding="utf-8")
        project_rules = (ROOT / ".ai/PROJECT_RULES.md").read_text(encoding="utf-8")
        agents = (ROOT / ".ai/AGENTS.md").read_text(encoding="utf-8")
        startup_protocol = (ROOT / ".ai/AI_STARTUP_PROTOCOL.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        required_constitution_terms = [
            "Priority:** Highest",
            "Portfolio 才是系统真正的核心对象",
            "Workflow 是唯一业务入口",
            "Model Center",
            "Strategy Object",
            "Explainability",
            "Version Control",
            DISCLAIMER,
        ]
        missing_constitution = [term for term in required_constitution_terms if term not in constitution]
        self.assertEqual([], missing_constitution)

        required_charter_terms = [
            "Priority:** Highest",
            "Code Last",
            "Mandatory Reading Order",
            "PROJECT_CONSTITUTION.md",
            "AI_DEVELOPMENT_CHARTER.md",
            "No Silent Refactor",
            "AI Self Review",
            DISCLAIMER,
        ]
        missing_charter = [term for term in required_charter_terms if term not in charter]
        self.assertEqual([], missing_charter)

        required_startup_terms = [
            "Priority:** Highest",
            "你现在是 OpenStock AI 项目的开发 Agent",
            "阅读 `PROJECT_CONSTITUTION.md`",
            "阅读 `AI_DEVELOPMENT_CHARTER.md`",
            "阅读当前模块 PRD",
            "阅读 Architecture",
            "阅读 Coding Standard",
            "输出你的理解",
            "输出开发计划",
            "等待确认",
            "完成后生成测试、更新文档、输出变更说明",
            DISCLAIMER,
        ]
        missing_startup = [term for term in required_startup_terms if term not in startup_protocol]
        self.assertEqual([], missing_startup)

        for document in [project_rules, agents, readme]:
            self.assertIn("PROJECT_CONSTITUTION.md", document)
            self.assertIn("AI_DEVELOPMENT_CHARTER.md", document)
            self.assertIn("AI_STARTUP_PROTOCOL.md", document)

    def test_workflow_engine_standard_defines_orchestration_boundary(self) -> None:
        standard = (ROOT / "docs/standards/WORKFLOW_ENGINE_STANDARD.md").read_text(encoding="utf-8")
        architecture = (ROOT / "docs/architecture/system-design.md").read_text(encoding="utf-8")
        source = (ROOT / "packages/workflow_layer/engine.py").read_text(encoding="utf-8")

        required_terms = [
            "Workflow Engine",
            "AI Portfolio Operating System",
            "Universe Builder",
            "Portfolio Builder",
            "Factor Engine",
            "Strategy Engine",
            "Constraint Engine",
            "Backtesting Engine",
            "Risk Engine",
            "AI Research Agent",
            "Recommendation Engine",
            "Report Engine",
            "Rebalance Engine",
            "Created",
            "Configured",
            "Waiting",
            "Running",
            "Completed",
            "AI Reviewing",
            "Recommendation Ready",
            "Archived",
            "trace_id",
            "duration_ms",
            "不得直接调用具体模型 SDK",
        ]
        combined = "\n".join([standard, architecture, source])
        missing = [term for term in required_terms if term not in combined]
        self.assertEqual([], missing)

    def test_github_templates_cover_ai_and_compliance_workflow(self) -> None:
        pr_template = (ROOT / ".github/pull_request_template.md").read_text(encoding="utf-8")
        bug_template = (ROOT / ".github/ISSUE_TEMPLATE/bug_report.md").read_text(encoding="utf-8")
        feature_template = (ROOT / ".github/ISSUE_TEMPLATE/feature_request.md").read_text(encoding="utf-8")
        issue_config = (ROOT / ".github/ISSUE_TEMPLATE/config.yml").read_text(encoding="utf-8")
        github_standard = (ROOT / "docs/standards/github-collaboration.md").read_text(encoding="utf-8")

        required_pr_terms = [
            "AI 开发标识",
            ".ai/AGENTS.md",
            ".ai/PROJECT_RULES.md",
            "codex",
            "claude-code",
            "Portfolio Strategy / Backtesting",
            "外部 API / 数据源",
            "AI 输出与投资合规",
            "安全检查",
            DISCLAIMER,
        ]
        missing_pr = [term for term in required_pr_terms if term not in pr_template]
        self.assertEqual([], missing_pr)

        required_issue_terms = [
            "影响模块",
            "Portfolio Strategy / Backtesting",
            "合规与安全",
            "Strategy Engine",
            "Risk Engine",
            "AI Research / Report",
            "验收标准",
            DISCLAIMER,
        ]
        issue_text = bug_template + feature_template
        missing_issue = [term for term in required_issue_terms if term not in issue_text]
        self.assertEqual([], missing_issue)

        self.assertIn("blank_issues_enabled: false", issue_config)
        self.assertIn("Issue 模板配置", github_standard)
        self.assertIn("不允许空白 Issue", github_standard)

    def test_project_interface_tracks_architecture_layers(self) -> None:
        # Retargeted at commit 1 of the web-react page-split migration (see
        # /Users/cullen/.claude/plans/vivid-wibbling-cake.md): the project dev-status board is
        # part of the persistent shell, so it lives in App.tsx (rendered on every route) rather
        # than any single page.
        html = (ROOT / "apps/web-react/src/App.tsx").read_text(encoding="utf-8")

        required_terms = [
            "项目开发界面",
            "Application",
            "Algorithm Layer",
            "Universe Layer",
            "Model Layer",
            "Data Layer",
            "Workflow / Agent",
            "Governance",
        ]
        missing = [term for term in required_terms if term not in html]
        self.assertEqual([], missing)

    def test_project_interface_includes_analysis_dimension_guide(self) -> None:
        # Retargeted at commit 5 of the web-react page-split migration (see
        # /Users/cullen/.claude/plans/vivid-wibbling-cake.md): the screener guide moved onto
        # the StockDetail route.
        html = (ROOT / "apps/web-react/src/pages/StockDetail.tsx").read_text(encoding="utf-8")

        required_terms = [
            "常用分析维度解读",
            "成交量",
            "相对成交量",
            "P/E",
            "RSI",
            "均线位置",
            "波动率",
            "52 周位置",
            "Beta",
            "行业强弱",
            "screener-guide-grid",
            "renderScreenerGuide",
            "/history?range=1y&interval=1d",
            "calculateRSI",
            "formatMoney",
        ]
        missing = [term for term in required_terms if term not in html]
        self.assertEqual([], missing)

    def test_stock_universe_list_uses_scrollable_top_100(self) -> None:
        # Retargeted at commits 1 and 7 of the web-react page-split migration (see
        # /Users/cullen/.claude/plans/vivid-wibbling-cake.md): the legacy sidebar mixed the
        # scrollable stock-universe list and the portfolio list in one blob; the split moves the
        # former to App.tsx's persistent shell and the latter to PortfolioResearch.tsx. Function
        # names that don't survive the move to React idioms (imperative `state.stocks.forEach`
        # DOM writes, a standalone `renderPortfolioList`/`addCurrentSymbolToPortfolio`) are checked
        # via their closest structural equivalent (JSX `.map` render, the renamed
        # `addSymbolToPortfolio`) instead of a literal string match.
        app_shell = (ROOT / "apps/web-react/src/App.tsx").read_text(encoding="utf-8")
        shell_css = (ROOT / "apps/web-react/src/index.css").read_text(encoding="utf-8")
        portfolio_research = (ROOT / "apps/web-react/src/pages/PortfolioResearch.tsx").read_text(encoding="utf-8")
        html = "\n".join([app_shell, shell_css, portfolio_research])

        required_terms = [
            "扫描最活跃 100 只",
            "/stocks/universe/most-active?limit=",
            "stocks.map((stock) =>",
            "overflow-y: auto",
            "height: 48px",
            "我的组合 Portfolios",
            "portfolio-strategy",
            "portfolio-list",
            "addSymbolToPortfolio",
            "portfolioNames.map((name) =>",
            "removeSymbolFromPortfolio",
        ]
        missing = [term for term in required_terms if term not in html]
        self.assertEqual([], missing)

        removed_terms = ["stock-group", "chunkStocks", "details.open", "slice(0, 20)"]
        present = [term for term in removed_terms if term in html]
        self.assertEqual([], present)

    def test_project_interface_includes_portfolio_strategy_workflow(self) -> None:
        # Retargeted at commit 7 (final) of the web-react page-split migration (see
        # /Users/cullen/.claude/plans/vivid-wibbling-cake.md): the workflow moved onto
        # PortfolioResearch.tsx, with research-run/report-archive/daily-home/data-source-health
        # terms now living on the pages that own them post-split (Reports.tsx, Dashboard.tsx,
        # StockDetail.tsx, components/DataSourceHealth.tsx) — joined here the same way
        # test_tiger_openapi_is_read_only_data_source already joins multiple files.
        portfolio_research = (ROOT / "apps/web-react/src/pages/PortfolioResearch.tsx").read_text(encoding="utf-8")
        reports = (ROOT / "apps/web-react/src/pages/Reports.tsx").read_text(encoding="utf-8")
        dashboard = (ROOT / "apps/web-react/src/pages/Dashboard.tsx").read_text(encoding="utf-8")
        stock_detail = (ROOT / "apps/web-react/src/pages/StockDetail.tsx").read_text(encoding="utf-8")
        data_source_health = (ROOT / "apps/web-react/src/components/DataSourceHealth.tsx").read_text(encoding="utf-8")
        html = "\n".join([portfolio_research, reports, dashboard, stock_detail, data_source_health])
        standard = (ROOT / "docs/standards/PORTFOLIO_STRATEGY_STANDARD.md").read_text(encoding="utf-8")

        required_html_terms = [
            "Portfolio Research Workbench",
            "股票池 Universe",
            "策略库 Strategy Library",
            "配置约束 Constraints",
            "运行回测 Backtest",
            "AI 自动分析结果",
            "Portfolio Recommendation",
            "workflow-strategy",
            "target-return",
            "max-drawdown",
            "max-position",
            "run-backtest-button",
            "save-portfolio-config-button",
            "Risk Engine v0.1",
            "risk-report-card",
            "Portfolio Optimizer v0.1",
            "Recommended Research Portfolio",
            "result-priority-grid",
            "optimizer-weight-grid",
            "weight-chip",
            "optimizer-card",
            "postJson(\"/portfolio-research/run\"",
            "postJson(\"/risk/portfolio\"",
            "postJson(\"/optimizer/portfolio\"",
            "putJson",
            "buildWorkflowPayload",
            "renderWorkflowResult",
            "workflow-trace-note",
            "GET /portfolio-research/",
            "Research Run 复盘",
            "research-run-list",
            "request(`/research-runs?",
            "loadResearchRunDetail",
            "request(`/portfolio-research/${encodeURIComponent(traceId)}`",
            "Report Archive",
            "report-archive-list",
            "postJson(`/reports/from-trace/${encodeURIComponent(traceId)}`",
            "request(`/reports?",
            "loadReportDetail",
            "每日研究首页",
            "daily-recommendation-list",
            "daily-run-list",
            "daily-portfolio-list",
            "loadDailyResearchHome",
            "request(\"/stocks/screening?limit=20\")",
            "request(\"/research-runs?limit=5&offset=0\")",
            "Data Source Health",
            "data-source-health-list",
            "loadDataSourceHealth",
            "request(\"/data-sources/health\")",
            "data_quality",
            "quality.source",
            "quality.freshness",
        ]
        missing_html = [term for term in required_html_terms if term not in html]
        self.assertEqual([], missing_html)

        required_standard_terms = [
            "股票池（Universe）",
            "选择策略（Strategy Library）",
            "配置约束（收益目标、最大回撤、仓位限制）",
            "运行回测（Backtest）",
            "AI 自动分析结果（收益、风险、原因）",
            "生成投资组合建议（Portfolio Recommendation）",
            "backtesting-v0.1",
            "POST /workflows/portfolio-research",
            "GET /workflows/portfolio-research/{trace_id}",
            "POST /risk/portfolio",
            "POST /optimizer/portfolio",
            "POST /portfolio-research/run",
        ]
        missing_standard = [term for term in required_standard_terms if term not in standard]
        self.assertEqual([], missing_standard)

    def test_project_interface_includes_strategy_library(self) -> None:
        # Retargeted at commit 6 of the web-react page-split migration (see
        # /Users/cullen/.claude/plans/vivid-wibbling-cake.md): Strategy Library carved out of
        # apps/web/index.html onto its own route.
        html = (ROOT / "apps/web-react/src/pages/StrategyLibrary.tsx").read_text(encoding="utf-8")
        standard = (ROOT / "docs/standards/PORTFOLIO_STRATEGY_STANDARD.md").read_text(encoding="utf-8")

        required_html_terms = [
            "strategy-list",
            "add-strategy-button",
            "loadStrategies",
            "renderStrategyList",
            "applyStrategy",
            "saveCurrentFormAsStrategy",
            "strategy-modal-form",
            "strategy-modal-name",
            '<select id="strategy-modal-name">',
            "STRATEGY_LIBRARY_OPTIONS",
            "generateStrategyResearchPortfolio",
            "推荐组合",
            "当前策略组合",
            "待保存",
            "已保存",
            "当前选择",
            "Risk Parity",
            "Black-Litterman",
            "submitStrategyModal",
            "deleteStrategyByName",
            "/strategies",
        ]
        missing_html = [term for term in required_html_terms if term not in html]
        self.assertEqual([], missing_html)
        self.assertNotIn('prompt("策略名称")', html)
        self.assertNotIn('placeholder="输入策略名称"', html)

        required_standard_terms = [
            "GET /strategies",
            "PUT /strategies/{name}",
            "DELETE /strategies/{name}",
        ]
        missing_standard = [term for term in required_standard_terms if term not in standard]
        self.assertEqual([], missing_standard)

    def test_project_interface_includes_portfolio_manager_v2(self) -> None:
        # Retargeted at commit 7 (final) of the web-react page-split migration (see
        # /Users/cullen/.claude/plans/vivid-wibbling-cake.md): portfolio manager v0.2 moved onto
        # PortfolioResearch.tsx.
        html = (ROOT / "apps/web-react/src/pages/PortfolioResearch.tsx").read_text(encoding="utf-8")
        standard = (ROOT / "docs/standards/PORTFOLIO_STRATEGY_STANDARD.md").read_text(encoding="utf-8")

        required_html_terms = [
            "portfolio-compare-button",
            "exportPortfolio",
            "openPortfolioImport",
            "importPortfolioFromData",
            "parsePortfolioImportText",
            "runPortfolioCompare",
            "fetchPortfolioRiskFor",
            "renderPortfolioCompareResult",
            "portfolio-import-input",
        ]
        missing_html = [term for term in required_html_terms if term not in html]
        self.assertEqual([], missing_html)

        required_standard_terms = [
            "Portfolio Manager v0.2",
        ]
        missing_standard = [term for term in required_standard_terms if term not in standard]
        self.assertEqual([], missing_standard)

    def test_project_interface_includes_us_concept_preview(self) -> None:
        # Retargeted at commit 4 of the web-react page-split migration (see
        # /Users/cullen/.claude/plans/vivid-wibbling-cake.md): the concept board moved off
        # apps/web/index.html onto its own MarketScanner route.
        html = (ROOT / "apps/web-react/src/pages/MarketScanner.tsx").read_text(encoding="utf-8")

        required_terms = [
            "美国概念板块预览",
            "concept-grid",
            "CONCEPT_DEFINITIONS",
            "renderConceptPreview",
            "matchesConcept",
            "AI / Cloud",
            "Semiconductors",
            "EV / Battery",
            "Crypto / Fintech",
            "Biotech / Pharma",
            "Aerospace / Defense",
            "Energy / Uranium",
            "Small Cap Momentum",
            "click to open leader",
        ]
        missing = [term for term in required_terms if term not in html]
        self.assertEqual([], missing)

    def test_tiger_openapi_is_read_only_data_source(self) -> None:
        standard = (ROOT / "docs/standards/TIGER_OPENAPI_STANDARD.md").read_text(encoding="utf-8")
        api_doc = (ROOT / "docs/api/api-design-v0.1.md").read_text(encoding="utf-8")
        env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
        source = (ROOT / "packages/data_sources/tiger_openapi.py").read_text(encoding="utf-8")

        required_terms = [
            "Tiger OpenAPI",
            "只读",
            "trading_enabled=false",
            "GET /integrations/tiger/status",
            "GET /stocks/{symbol}/tiger/quote",
            "GET /stocks/{symbol}/tiger/history",
            "近 3 年历史 K 线参考数据",
            "不得读取、抓取、逆向或自动操作用户已打开的老虎 App",
            "TIGER_ID",
            "TIGER_ACCOUNT",
            "TIGER_LICENSE",
            "TIGER_PRIVATE_KEY_PATH",
        ]
        combined = "\n".join([standard, api_doc, env_example, source])
        missing = [term for term in required_terms if term not in combined]
        self.assertEqual([], missing)

    def test_main_analysis_sections_follow_requested_order(self) -> None:
        # Retargeted at commit 1 of the web-react page-split migration (see
        # /Users/cullen/.claude/plans/vivid-wibbling-cake.md): once the dashboard/scanner/
        # analysis-guide content is split across routed pages, "position in one HTML blob" no
        # longer applies. The plan calls for checking nav-item order in App.tsx's route table
        # instead, since that's what now fixes the Dashboard -> Scanner -> Stock navigation flow
        # (dev board -> concept preview -> analysis-dimension guide, in the legacy layout).
        html = (ROOT / "apps/web-react/src/App.tsx").read_text(encoding="utf-8")

        self.assertLess(html.index('"Dashboard"'), html.index('"Scanner"'))
        self.assertLess(html.index('"Scanner"'), html.index('"Stock"'))

    def test_project_interface_includes_news_policy_panel(self) -> None:
        # Retargeted at commit 5 of the web-react page-split migration (see
        # /Users/cullen/.claude/plans/vivid-wibbling-cake.md): news/policy panel moved onto the
        # StockDetail route.
        html = (ROOT / "apps/web-react/src/pages/StockDetail.tsx").read_text(encoding="utf-8")

        required_terms = [
            "Policy & News",
            "news-list",
            "/news?years=3",
            "coverage_note",
        ]
        missing = [term for term in required_terms if term not in html]
        self.assertEqual([], missing)

    def test_chart_interface_has_sliding_crosshair_metrics(self) -> None:
        # Retargeted at commit 5 of the web-react page-split migration (see
        # /Users/cullen/.claude/plans/vivid-wibbling-cake.md): the OHLC chart + crosshair
        # inspector moved onto StockDetail.tsx / components/charts/OhlcChart.tsx.
        stock_detail = (ROOT / "apps/web-react/src/pages/StockDetail.tsx").read_text(encoding="utf-8")
        ohlc_chart = (ROOT / "apps/web-react/src/components/charts/OhlcChart.tsx").read_text(encoding="utf-8")
        html = "\n".join([stock_detail, ohlc_chart])

        required_terms = [
            "chart-inspector",
            "pointermove",
            "updateChartHover",
            "updateChartHoverFromClientPoint",
            "document.addEventListener(\"pointermove\"",
            "offsetX",
            "chartSizeKey",
            "inspect-volume",
            "inspect-turnover",
            "inspect-turnover-rate",
            "inspect-buy-volume",
            "inspect-sell-volume",
            "Turnover Rate",
            "Buy Vol",
            "Sell Vol",
            "estimateTradeFlow",
            "estimatedSharesOutstanding",
            "买/卖量为分钟线方向估算",
        ]
        missing = [term for term in required_terms if term not in html]
        self.assertEqual([], missing)


if __name__ == "__main__":
    unittest.main()
