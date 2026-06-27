import unittest

from packages.risk_engine.engine import analyze_portfolio_risk
from packages.risk_engine.schemas import RISK_DISCLAIMER


class RiskEngineTest(unittest.TestCase):
    def test_analyze_portfolio_risk_outputs_core_mvp_metrics(self) -> None:
        report = analyze_portfolio_risk(
            {
                "AAPL": [("2024-01-01", 100.0), ("2024-01-02", 101.0), ("2024-01-03", 99.0), ("2024-01-04", 103.0)],
                "MSFT": [("2024-01-01", 50.0), ("2024-01-02", 51.0), ("2024-01-03", 52.0), ("2024-01-04", 53.0)],
            },
            weights={"AAPL": 0.6, "MSFT": 0.4},
            benchmark_closes=[
                ("2024-01-01", 400.0),
                ("2024-01-02", 401.0),
                ("2024-01-03", 399.0),
                ("2024-01-04", 404.0),
            ],
            sector_map={"AAPL": "Technology", "MSFT": "Technology"},
        )

        payload = report.to_dict()

        self.assertEqual(["AAPL", "MSFT"], payload["symbols"])
        self.assertEqual({"AAPL": 0.6, "MSFT": 0.4}, payload["weights"])
        self.assertIsNotNone(payload["volatility_percent"])
        self.assertIsNotNone(payload["beta"])
        self.assertGreaterEqual(payload["max_drawdown_percent"], 0.0)
        self.assertIsNotNone(payload["average_correlation"])
        self.assertEqual(60.0, payload["concentration_percent"])
        self.assertEqual({"Technology": 100.0}, payload["sector_exposure"])
        self.assertEqual(RISK_DISCLAIMER, payload["risk_disclaimer"])


if __name__ == "__main__":
    unittest.main()
