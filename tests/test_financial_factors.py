import unittest

from packages.algorithm_layer.financial_factors import fundamentals_score, growth_score, valuation_score
from packages.algorithm_layer.schemas import FinancialFactorsInput


class FundamentalsScoreTest(unittest.TestCase):
    def test_none_factors_is_neutral(self) -> None:
        score, explanation = fundamentals_score(None)
        self.assertEqual(50, score)
        self.assertIn("未提供财务数据", explanation)

    def test_blends_net_margin_and_roc_when_both_available(self) -> None:
        factors = FinancialFactorsInput(
            revenue=1000.0,
            net_income=200.0,  # 20% net margin -> 50 + 20*1.5 = 80
            operating_income=150.0,
            current_assets=500.0,
            current_liabilities=200.0,
            net_fixed_assets=100.0,  # capital employed 400, ROC 37.5% -> 50+37.5*1.5=106 capped 95
        )
        score, explanation = fundamentals_score(factors)
        self.assertEqual(round(80 * 0.5 + 95 * 0.5), score)
        self.assertIn("净利润率约 20.0%", explanation)
        self.assertIn("资本回报率(ROC)约 37.5%", explanation)

    def test_falls_back_to_net_margin_only_when_roc_inputs_missing(self) -> None:
        factors = FinancialFactorsInput(revenue=1000.0, net_income=100.0)
        score, explanation = fundamentals_score(factors)
        self.assertEqual(65, score)
        self.assertIn("缺 ROC 数据", explanation)


class GrowthScoreTest(unittest.TestCase):
    def test_none_previous_revenue_is_neutral(self) -> None:
        score, explanation = growth_score(FinancialFactorsInput(revenue=100.0))
        self.assertEqual(50, score)
        self.assertIn("未提供同比营收数据", explanation)

    def test_positive_growth_scores_above_fifty(self) -> None:
        factors = FinancialFactorsInput(revenue=120.0, previous_revenue=100.0)
        score, explanation = growth_score(factors)
        self.assertEqual(round(50 + 20 * 1.2), score)
        self.assertIn("营收同比增长约 20.0%", explanation)


class ValuationScoreTest(unittest.TestCase):
    def test_none_factors_is_neutral(self) -> None:
        score, _ = valuation_score(None, latest_price=100.0)
        self.assertEqual(50, score)

    def test_cheap_pe_scores_high(self) -> None:
        factors = FinancialFactorsInput(eps_diluted=10.0)
        score, explanation = valuation_score(factors, latest_price=100.0)  # P/E 10 -> band 85
        self.assertEqual(85, score)
        self.assertIn("P/E 约 10.0", explanation)

    def test_blends_pe_and_ev_to_ebit_when_both_available(self) -> None:
        factors = FinancialFactorsInput(
            eps_diluted=10.0,  # P/E 10 -> 85
            operating_income=50.0,
            shares_outstanding=10.0,
            total_debt=0.0,
            cash=0.0,
        )
        # market_cap = 100*10=1000, EV=1000, EV/EBIT=1000/50=20 -> band 70
        score, explanation = valuation_score(factors, latest_price=100.0)
        self.assertEqual(round(85 * 0.5 + 70 * 0.5), score)
        self.assertIn("EV/EBIT 约 20.0", explanation)


if __name__ == "__main__":
    unittest.main()
