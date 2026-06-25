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
            "docs/standards/version-management.md",
            "docs/standards/github-collaboration.md",
            "docs/standards/agile-iteration.md",
            "docs/standards/AI_TOOL_COLLABORATION.md",
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
            "docs/standards/github-collaboration.md",
            "docs/standards/agile-iteration.md",
            "docs/standards/AI_TOOL_COLLABORATION.md",
            "docs/product/requirements-analysis.md",
            "docs/architecture/system-design.md",
            "docs/architecture/ai-development-architecture.md",
            "docs/api/api-design-v0.1.md",
        ]
        missing = [path for path in docs if DISCLAIMER not in (ROOT / path).read_text(encoding="utf-8")]
        self.assertEqual([], missing)

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
        ]
        missing = [term for term in required_terms if term not in html]
        self.assertEqual([], missing)

        removed_terms = ["stock-group", "chunkStocks", "details.open", "slice(0, 20)"]
        present = [term for term in removed_terms if term in html]
        self.assertEqual([], present)

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
