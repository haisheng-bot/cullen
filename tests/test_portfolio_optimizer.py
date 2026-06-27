import unittest

from packages.portfolio_optimizer.engine import optimize_portfolio
from packages.portfolio_optimizer.schemas import RISK_DISCLAIMER


SERIES = {
    "LOW": [("2024-01-01", 100.0), ("2024-01-02", 101.0), ("2024-01-03", 102.0), ("2024-01-04", 103.0)],
    "HIGH": [("2024-01-01", 100.0), ("2024-01-02", 110.0), ("2024-01-03", 90.0), ("2024-01-04", 120.0)],
}


class PortfolioOptimizerTest(unittest.TestCase):
    def test_equal_weight_respects_cash_and_cap(self) -> None:
        result = optimize_portfolio(
            method="equal_weight",
            closes_by_symbol=SERIES,
            max_position_weight=0.5,
            min_cash_weight=0.1,
        )

        payload = result.to_dict()

        self.assertEqual("equal_weight", payload["method"])
        self.assertEqual({"HIGH": 0.45, "LOW": 0.45}, payload["target_weights"])
        self.assertEqual(0.1, payload["cash_weight"])
        self.assertEqual(RISK_DISCLAIMER, payload["risk_disclaimer"])

    def test_minimum_variance_favors_lower_variance_symbol(self) -> None:
        result = optimize_portfolio(
            method="minimum_variance",
            closes_by_symbol=SERIES,
            max_position_weight=1.0,
            min_cash_weight=0.0,
        )

        self.assertGreater(result.target_weights["LOW"], result.target_weights["HIGH"])
        self.assertIsNotNone(result.expected_risk_percent)

    def test_market_cap_uses_market_caps(self) -> None:
        result = optimize_portfolio(
            method="market_cap",
            closes_by_symbol=SERIES,
            market_caps={"LOW": 100.0, "HIGH": 300.0},
            max_position_weight=1.0,
            min_cash_weight=0.0,
        )

        self.assertAlmostEqual(0.25, result.target_weights["LOW"])
        self.assertAlmostEqual(0.75, result.target_weights["HIGH"])

    def test_unsupported_method_raises(self) -> None:
        with self.assertRaises(ValueError):
            optimize_portfolio(method="unsupported", closes_by_symbol=SERIES)


if __name__ == "__main__":
    unittest.main()
