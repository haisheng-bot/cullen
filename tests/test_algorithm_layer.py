import unittest

from packages.algorithm_layer.recommendation import TrendRecommendationAlgorithm, recommendation_label
from packages.algorithm_layer.schemas import AlgorithmPoint, RISK_DISCLAIMER, RecommendationInput


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
        self.assertEqual("algorithm-v0.1", result.algorithm_version)
        self.assertGreaterEqual(result.total_score, 0)
        self.assertLessEqual(result.total_score, 100)
        self.assertEqual(4, len(result.factors))
        self.assertTrue(result.reasons)
        self.assertTrue(result.risks)
        self.assertEqual(RISK_DISCLAIMER, result.risk_disclaimer)

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

