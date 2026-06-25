import unittest

from packages.algorithm_layer.recommendation import TrendRecommendationAlgorithm
from packages.data_sources.market_trend import MarketTrendError, TrendPoint, TrendResponse
from packages.universe_layer.schemas import UniverseResult, UniverseStock
from packages.workflow_layer.stock_screening import StockScreeningWorkflow


class FakeUniverseScanner:
    def scan(self, limit: int = 100) -> UniverseResult:
        return UniverseResult(
            universe_date="2026-06-25",
            universe_name="us_most_active_top_100",
            market="US",
            limit=limit,
            source="test-universe-source",
            generated_at="2026-06-25T13:32:00+00:00",
            items=[
                UniverseStock(rank=1, symbol="AAPL", name="Apple Inc.", sector="Technology"),
                UniverseStock(rank=2, symbol="WEAK", name="Weak Co.", sector="Industrials"),
                UniverseStock(rank=3, symbol="BAD", name="Bad Co.", sector="Energy"),
            ][:limit],
            analysis_dimensions=["volume"],
        )


class FakeTrendClient:
    def fetch_trend(self, symbol: str, range_: str = "1d", interval: str = "1m") -> TrendResponse:
        if symbol == "BAD":
            raise MarketTrendError("no data for BAD")

        closes = {"AAPL": [100.0, 110.0], "WEAK": [100.0, 95.0]}[symbol]
        return TrendResponse(
            symbol=symbol,
            range=range_,
            interval=interval,
            currency="USD",
            exchange_name="NMS",
            regular_market_price=closes[-1],
            previous_close=closes[0],
            points=[
                TrendPoint(timestamp="2026-06-25T13:30:00+00:00", close=closes[0], volume=1000),
                TrendPoint(timestamp="2026-06-25T13:31:00+00:00", close=closes[1], volume=1200),
            ],
            source="test-trend-source",
            analysis_time="2026-06-25T13:32:00+00:00",
        )


class StockScreeningWorkflowTest(unittest.TestCase):
    def test_screen_ranks_candidates_and_skips_failures(self) -> None:
        workflow = StockScreeningWorkflow(
            universe_scanner=FakeUniverseScanner(),
            trend_client=FakeTrendClient(),
            algorithm=TrendRecommendationAlgorithm(),
            financial_factors_fetcher=lambda symbol: None,
        )

        result = workflow.screen(limit=3)

        self.assertEqual(2, result.scored_count)
        self.assertEqual(["AAPL", "WEAK"], [c.symbol for c in result.candidates])
        self.assertEqual([1, 2], [c.rank for c in result.candidates])
        self.assertGreater(result.candidates[0].total_score, result.candidates[1].total_score)
        self.assertEqual(1, len(result.skipped))
        self.assertEqual("BAD", result.skipped[0].symbol)


if __name__ == "__main__":
    unittest.main()
