import unittest

from packages.algorithm_layer.recommendation import TrendRecommendationAlgorithm, recommendation_label
from packages.algorithm_layer.schemas import (
    AlgorithmPoint,
    RISK_DISCLAIMER,
    FinancialFactorsInput,
    NewsSignalInput,
    RecommendationInput,
    TechnicalSeriesInput,
)
from packages.scoring_profiles.profiles import get_profile


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
        self.assertEqual("algorithm-v0.3", result.algorithm_version)
        self.assertEqual("1y", result.recommendation_horizon)
        self.assertEqual("1y", result.to_dict()["recommendation_horizon"])
        self.assertGreaterEqual(result.total_score, 0)
        self.assertLessEqual(result.total_score, 100)
        self.assertEqual(6, len(result.factors))
        self.assertTrue(result.reasons)
        self.assertTrue(result.risks)
        self.assertEqual(RISK_DISCLAIMER, result.risk_disclaimer)
        factor_names = {factor.name for factor in result.factors}
        self.assertEqual(
            {
                "fundamentals",
                "growth",
                "valuation",
                "technical",
                "news_sentiment",
                "volatility_risk",
            },
            factor_names,
        )
        self.assertIn("未提供财务数据", " ".join(result.risks))
        self.assertIn("未提供新闻/披露信号", " ".join(result.risks))

    def test_recommend_defaults_to_balanced_profile(self) -> None:
        data = _basic_recommendation_input()

        result = TrendRecommendationAlgorithm().recommend(data)

        self.assertEqual("balanced", result.scoring_profile)
        weights_by_factor = {factor.name: factor.weight for factor in result.factors}
        self.assertEqual(get_profile("balanced").weights, weights_by_factor)

    def test_recommend_applies_requested_profile_weights(self) -> None:
        data = _basic_recommendation_input()
        momentum = get_profile("momentum")

        result = TrendRecommendationAlgorithm().recommend(data, profile=momentum)

        self.assertEqual("momentum", result.scoring_profile)
        weights_by_factor = {factor.name: factor.weight for factor in result.factors}
        self.assertEqual(momentum.weights, weights_by_factor)


def _basic_recommendation_input() -> RecommendationInput:
    return RecommendationInput(
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
        # No Magic Formula inputs (operating_income, current_assets, ...)
        # were provided, so fundamentals/valuation fall back to net
        # margin/P/E only and should say so explicitly.
        self.assertIn("缺 ROC 数据", factors_by_name["fundamentals"].explanation)
        self.assertIn("缺企业价值数据", factors_by_name["valuation"].explanation)

    def test_recommendation_blends_magic_formula_metrics_when_provided(self) -> None:
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
                operating_income=130_000_000_000,
                current_assets=150_000_000_000,
                current_liabilities=130_000_000_000,
                net_fixed_assets=45_000_000_000,
                cash=30_000_000_000,
                total_debt=85_000_000_000,
            ),
        )

        result = TrendRecommendationAlgorithm().recommend(data)

        factors_by_name = {factor.name: factor for factor in result.factors}
        self.assertIn("ROC", factors_by_name["fundamentals"].explanation)
        self.assertIn("EV/EBIT", factors_by_name["valuation"].explanation)
        self.assertNotIn("缺", factors_by_name["fundamentals"].explanation)
        self.assertNotIn("缺", factors_by_name["valuation"].explanation)

    def test_technical_factor_falls_back_without_daily_history(self) -> None:
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
        )

        result = TrendRecommendationAlgorithm().recommend(data)

        technical_factor = next(factor for factor in result.factors if factor.name == "technical")
        self.assertIn("日线数据不足", technical_factor.explanation)

    def test_technical_factor_uses_real_indicators_when_daily_history_provided(self) -> None:
        closes = [100.0 + index * 0.8 for index in range(30)]
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
            technical_series=TechnicalSeriesInput(closes=closes),
        )

        result = TrendRecommendationAlgorithm().recommend(data)

        technical_factor = next(factor for factor in result.factors if factor.name == "technical")
        self.assertIn("RSI(14)", technical_factor.explanation)
        self.assertIn("动量(10日)", technical_factor.explanation)
        self.assertNotIn("日线数据不足", technical_factor.explanation)
        # Sustained uptrend should score above the neutral default.
        self.assertGreater(technical_factor.score, 50)

    def test_news_sentiment_factor_uses_news_signals(self) -> None:
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
            news_signals=[
                NewsSignalInput(
                    title="Apple beats revenue expectations and raises dividend",
                    summary="Strong profit growth and new buyback program.",
                    category="company_news",
                    source="test-news",
                )
            ],
        )

        result = TrendRecommendationAlgorithm().recommend(data)

        news_factor = next(factor for factor in result.factors if factor.name == "news_sentiment")
        self.assertGreater(news_factor.score, 50)
        self.assertIn("正向词", news_factor.explanation)
        self.assertNotIn("未提供新闻/披露信号", " ".join(result.risks))

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
