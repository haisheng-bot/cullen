import unittest

from packages.portfolio_research.engine import PortfolioResearchEngine
from packages.portfolio_research.schemas import PortfolioResearchRunRequest, RISK_DISCLAIMER


class PortfolioResearchEngineTest(unittest.TestCase):
    def test_run_combines_workflow_risk_optimizer_and_archives(self) -> None:
        archived = []
        request = PortfolioResearchRunRequest(
            portfolio_name="Core Watch",
            symbols=["AAPL", "MSFT"],
        )

        engine = PortfolioResearchEngine(
            workflow_runner=lambda _: {
                "workflow_name": "portfolio_research_workflow",
                "workflow_version": "portfolio-research-workflow-v0.1",
                "trace_id": "trace-1",
                "state": "Recommendation Ready",
                "started_at": "2026-06-27T00:00:00+00:00",
                "completed_at": "2026-06-27T00:00:01+00:00",
                "node_results": [],
                "portfolio": {"name": "Core Watch", "symbols": ["AAPL", "MSFT"]},
                "backtest": {
                    "strategy_name": "Core Watch",
                    "symbols": ["AAPL", "MSFT"],
                    "signal_mode": "ai_score",
                    "scoring_profile": "growth",
                    "total_return_percent": 10.0,
                    "annualized_return_percent": 9.0,
                    "max_drawdown_percent": 8.0,
                    "risks": ["test risk"],
                },
                "ai_summary": {"conclusion": "test", "key_findings": []},
                "portfolio_recommendation": {"action": "research_candidate"},
                "risk_disclaimer": RISK_DISCLAIMER,
            },
            risk_runner=lambda _: {"volatility_percent": 18.0},
            optimizer_runner=lambda _: {"target_weights": {"AAPL": 0.5, "MSFT": 0.4}, "cash_weight": 0.1},
            archive_writer=lambda req, response: archived.append((req, response)),
        )

        payload = engine.run(request)

        self.assertEqual("portfolio_research_module", payload["workflow_name"])
        self.assertEqual("completed", payload["state"])
        self.assertEqual("trace-1", payload["trace_id"])
        self.assertEqual({"volatility_percent": 18.0}, payload["risk_summary"])
        self.assertEqual({"target_weights": {"AAPL": 0.5, "MSFT": 0.4}, "cash_weight": 0.1}, payload["optimized_weights"])
        self.assertEqual(["test risk"], payload["warnings"])
        self.assertEqual("growth", payload["score_summary"]["scoring_profile"])
        self.assertEqual(1, len(archived))


if __name__ == "__main__":
    unittest.main()
