import unittest

from packages.research_history.view_model import summarize_run


class SummarizeRunTest(unittest.TestCase):
    def test_summarizes_module_shaped_response(self) -> None:
        summary = summarize_run(
            trace_id="trace-1",
            workflow_name="portfolio_research_module",
            workflow_version="portfolio-research-module-v0.1",
            state="completed",
            request={"portfolio_name": "Core Watch", "strategy_library_name": "市值加权防守型"},
            response={
                "portfolio": {"name": "Core Watch", "symbols": ["AAPL", "MSFT"]},
                "recommendation": {"action": "research_candidate"},
                "backtest_summary": {"total_return_percent": 12.5},
            },
            started_at="2026-06-27T00:00:00+00:00",
            completed_at="2026-06-27T00:00:01+00:00",
        )

        self.assertEqual("Core Watch", summary.portfolio_name)
        self.assertEqual(["AAPL", "MSFT"], summary.symbols)
        self.assertEqual("市值加权防守型", summary.strategy_library_name)
        self.assertIn("research_candidate", summary.summary_text)
        self.assertIn("12.5%", summary.summary_text)

    def test_summarizes_workflow_shaped_response(self) -> None:
        summary = summarize_run(
            trace_id="trace-2",
            workflow_name="portfolio_research_workflow",
            workflow_version="portfolio-research-workflow-v0.1",
            state="Recommendation Ready",
            request={"portfolio_name": "Core Watch", "strategy_library_name": None},
            response={
                "portfolio": {"name": "Core Watch", "symbols": ["NVDA"]},
                "portfolio_recommendation": {"action": "research_candidate"},
                "backtest": {"total_return_percent": 8.0, "scoring_profile": "growth"},
            },
            started_at="2026-06-27T00:00:00+00:00",
            completed_at="2026-06-27T00:00:01+00:00",
        )

        self.assertEqual(["NVDA"], summary.symbols)
        self.assertIsNone(summary.strategy_library_name)
        self.assertIn("research_candidate", summary.summary_text)
        self.assertIn("8.0%", summary.summary_text)

    def test_falls_back_to_placeholder_summary_when_no_recommendation_or_backtest(self) -> None:
        summary = summarize_run(
            trace_id="trace-3",
            workflow_name="portfolio_research_module",
            workflow_version="portfolio-research-module-v0.1",
            state="failed",
            request={"portfolio_name": "Core Watch"},
            response={"portfolio": {"name": "Core Watch", "symbols": []}},
            started_at="2026-06-27T00:00:00+00:00",
            completed_at="2026-06-27T00:00:01+00:00",
        )

        self.assertEqual("暂无摘要", summary.summary_text)


if __name__ == "__main__":
    unittest.main()
