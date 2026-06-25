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
            "packages/algorithm_layer",
            "packages/model_layer",
            "packages/scoring",
            "packages/backtesting",
            "packages/brokers",
            "docs/standards/project-standard-v0.1.md",
            "docs/standards/MODEL_STANDARD.md",
            "docs/standards/ALGORITHM_STANDARD.md",
            "docs/standards/UNIVERSE_STANDARD.md",
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
        ]
        missing = [term for term in required_terms if term not in html]
        self.assertEqual([], missing)

    def test_stock_universe_list_uses_scrollable_top_20(self) -> None:
        html = (ROOT / "apps/web/index.html").read_text(encoding="utf-8")

        required_terms = [
            "扫描最活跃 20 只",
            "loadMostActiveUniverse(20)",
            "state.stocks.slice(0, 20)",
            "overflow-y: auto",
        ]
        missing = [term for term in required_terms if term not in html]
        self.assertEqual([], missing)

        removed_terms = ["stock-group", "chunkStocks", "details.open"]
        present = [term for term in removed_terms if term in html]
        self.assertEqual([], present)


if __name__ == "__main__":
    unittest.main()
