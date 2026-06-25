from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DISCLAIMER = "本系统仅用于投资研究辅助，不构成任何投资建议。"


class ProjectGovernanceTest(unittest.TestCase):
    def test_required_paths_exist(self) -> None:
        required_paths = [
            "README.md",
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
            "packages/model_layer",
            "packages/scoring",
            "packages/backtesting",
            "packages/brokers",
            "docs/standards/project-standard-v0.1.md",
            "docs/standards/MODEL_STANDARD.md",
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


if __name__ == "__main__":
    unittest.main()
