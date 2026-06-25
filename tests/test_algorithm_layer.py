import unittest

from packages.algorithm_layer.recommendation import TrendRecommendationAlgorithm, recommendation_label
from packages.algorithm_layer.schemas import (
    AlgorithmPoint,
    RISK_DISCLAIMER,
    FinancialFactorsInput,
    RecommendationInput,
)


class AlgorithmLayerTest(unittest.TestCase):
    def test_recommendation_label_boundaries(self) -> None:
        self.assertEqual("强关注", recommendation_label(85))
        self.assertEqual("观察", recommendation_label(70))
        self.assertEqual("中性", recommendation_label(50))
        self.assertEqual("回避", recommendation_label(49))

    def test_trend_recommendation_returns_explainable_result(self) -> None:
        data = RecommendationInput(
            symbol="AAPL",
            latest_price=104.0,
            previous_close=100.0,
            points=[
                AlgorithmPoint(timestamp="2026-06-25T13:30:00+00:00", close=100.0, volume=1000),
                AlgorithmPoint(timestamp="2026-06-25T13:31:00+00:00", close=102.0, volume=1200),
                AlgorithmPoint(timestamp="2026-06-25T13:32:00+00:00", close=104.0, volume=1800),
            ],
            source="test-source",
            analysis_time="2026-06-25T13:33:00+00:00",
        )

        result = TrendRecommendationAlgorithm().recommend(data)

        self.assertEqual("AAPL", result.symbol)
        self.assertEqual("algorithm-v0.2", result.algorithm_version)
        self.assertGreaterEqual(result.total_score, 0)
        self.assertLessEqual(result.total_score, 100)
        self.assertEqual(5, len(result.factors))
        self.assertTrue(result.reasons)
        self.assertTrue(result.risks)
        self.assertEqual(RISK_DISCLAIMER, result.risk_disclaimer)
        factor_names = {factor.name for factor in result.factors}
        self.assertEqual(
            {"fundamentals", "growth", "valuation", "technical", "volatility_risk"}, factor_names
        )
        self.assertIn("未提供财务数据", " ".join(result.risks))

    def test_recommendation_uses_real_fundamentals_when_provided(self) -> None:
        data = RecommendationInput(
            symbol="AAPL",
            latest_price=104.0,
            previous_close=100.0,
            points=[
                AlgorithmPoint(timestamp="2026-06-25T13:30:00+00:00", close=100.0, volume=1000),
                AlgorithmPoint(timestamp="2026-06-25T13:32:00+00:00", close=104.0, volume=1800),
            ],
            source="test-source",
            analysis_time="2026-06-25T13:33:00+00:00",
            financial_factors=FinancialFactorsInput(
                revenue=416_161_000_000,
                previous_revenue=391_035_000_000,
                net_income=112_010_000_000,
                eps_diluted=7.46,
                stockholders_equity=73_733_000_000,
                shares_outstanding=14_773_260_000,
            ),
        )

        result = TrendRecommendationAlgorithm().recommend(data)

        factors_by_name = {factor.name: factor for factor in result.factors}
        self.assertGreater(factors_by_name["fundamentals"].score, 50)
        self.assertGreater(factors_by_name["growth"].score, 50)
        self.assertNotIn("未提供财务数据", " ".join(result.risks))

    def test_trend_recommendation_requires_points(self) -> None:
        data = RecommendationInput(
            symbol="AAPL",
            latest_price=100.0,
            previous_close=99.0,
            points=[],
            source="test-source",
            analysis_time="2026-06-25T13:33:00+00:00",
        )

        with self.assertRaisesRegex(ValueError, "points are required"):
            TrendRecommendationAlgorithm().recommend(data)


if __name__ == "__main__":
    unittest.main()

