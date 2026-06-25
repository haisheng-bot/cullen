from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DISCLAIMER = "本系统仅用于投资研究辅助，不构成任何投资建议。"


class ProjectGovernanceTest(unittest.TestCase):
    def test_required_paths_exist(self) -> None:
        required_paths = [
            "README.md",
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
            "docs/standards/project-standard-v0.1.md",
            "docs/standards/MODEL_STANDARD.md",
            "docs/standards/ALGORITHM_STANDARD.md",
            "docs/standards/UNIVERSE_STANDARD.md",
            "docs/standards/NEWS_POLICY_STANDARD.md",
            "docs/standards/PORTFOLIO_STRATEGY_STANDARD.md",
            "docs/standards/version-management.md",
            "docs/standards/github-collaboration.md",
            "docs/standards/agile-iteration.md",
            "docs/standards/AI_TOOL_COLLABORATION.md",
            "docs/product/PRD.md",
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
            "docs/standards/project-standard-v0.1.md",
            "docs/standards/MODEL_STANDARD.md",
            "docs/standards/ALGORITHM_STANDARD.md",
            "docs/standards/UNIVERSE_STANDARD.md",
            "docs/standards/NEWS_POLICY_STANDARD.md",
            "docs/standards/PORTFOLIO_STRATEGY_STANDARD.md",
            "docs/standards/github-collaboration.md",
            "docs/standards/agile-iteration.md",
            "docs/standards/AI_TOOL_COLLABORATION.md",
            "docs/product/PRD.md",
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

        required_terms = [
            "AI Investment Research Platform",
            "Stock Screener",
            "Stock Research",
            "Portfolio",
            "Strategy Engine",
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
        self.assertIn("Portfolio", requirements)
        self.assertIn("Strategy Workflow", requirements)

    def test_github_templates_cover_ai_and_compliance_workflow(self) -> None:
        pr_template = (ROOT / ".github/pull_request_template.md").read_text(encoding="utf-8")
        bug_template = (ROOT / ".github/ISSUE_TEMPLATE/bug_report.md").read_text(encoding="utf-8")
        feature_template = (ROOT / ".github/ISSUE_TEMPLATE/feature_request.md").read_text(encoding="utf-8")
        issue_config = (ROOT / ".github/ISSUE_TEMPLATE/config.yml").read_text(encoding="utf-8")
        github_standard = (ROOT / "docs/standards/github-collaboration.md").read_text(encoding="utf-8")

        required_pr_terms = [
            "AI 开发标识",
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
        html = (ROOT / "apps/web/index.html").read_text(encoding="utf-8")

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
        html = (ROOT / "apps/web/index.html").read_text(encoding="utf-8")

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
        html = (ROOT / "apps/web/index.html").read_text(encoding="utf-8")

        required_terms = [
            "扫描最活跃 100 只",
            "loadMostActiveUniverse(100)",
            "state.stocks.forEach",
            "overflow-y: auto",
            "height: 1086px",
            "height: 48px",
            "组合策略选择",
            "portfolio-strategy",
            "portfolio-list",
            "addCurrentSymbolToPortfolio",
            "renderPortfolioList",
            "removeSymbolFromPortfolio",
        ]
        missing = [term for term in required_terms if term not in html]
        self.assertEqual([], missing)

        removed_terms = ["stock-group", "chunkStocks", "details.open", "slice(0, 20)"]
        present = [term for term in removed_terms if term in html]
        self.assertEqual([], present)

    def test_project_interface_includes_portfolio_strategy_workflow(self) -> None:
        html = (ROOT / "apps/web/index.html").read_text(encoding="utf-8")
        standard = (ROOT / "docs/standards/PORTFOLIO_STRATEGY_STANDARD.md").read_text(encoding="utf-8")

        required_html_terms = [
            "Portfolio Strategy Workflow",
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
            "postJson(\"/backtests/run\"",
            "buildBacktestPayload",
            "renderBacktestResult",
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
            "POST /backtests/run",
        ]
        missing_standard = [term for term in required_standard_terms if term not in standard]
        self.assertEqual([], missing_standard)

    def test_project_interface_includes_us_concept_preview(self) -> None:
        html = (ROOT / "apps/web/index.html").read_text(encoding="utf-8")

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

    def test_main_analysis_sections_follow_requested_order(self) -> None:
        html = (ROOT / "apps/web/index.html").read_text(encoding="utf-8")

        self.assertLess(html.index("项目开发界面"), html.index("美国概念板块预览"))
        self.assertLess(html.index("美国概念板块预览"), html.index("常用分析维度解读"))

    def test_project_interface_includes_news_policy_panel(self) -> None:
        html = (ROOT / "apps/web/index.html").read_text(encoding="utf-8")

        required_terms = [
            "Policy & News",
            "news-list",
            "/news?years=3",
            "coverage_note",
        ]
        missing = [term for term in required_terms if term not in html]
        self.assertEqual([], missing)

    def test_chart_interface_has_sliding_crosshair_metrics(self) -> None:
        html = (ROOT / "apps/web/index.html").read_text(encoding="utf-8")

        required_terms = [
            "chart-inspector",
            "pointermove",
            "mousemove",
            "updateChartHover",
            "updateChartHoverFromClientPoint",
            "document.addEventListener(\"mousemove\"",
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
