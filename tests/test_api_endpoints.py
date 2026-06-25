import importlib.util
import unittest

if importlib.util.find_spec("fastapi") is None:
    raise unittest.SkipTest("FastAPI is not installed in this Python environment")

from apps.api import main
from packages.data_sources.market_trend import TrendPoint, TrendResponse
from packages.universe_layer.schemas import UniverseResult, UniverseStock


class FakeTrendClient:
    def fetch_trend(self, symbol: str, range_: str = "1d", interval: str = "1m") -> TrendResponse:
        return TrendResponse(
            symbol=symbol,
            range=range_,
            interval=interval,
            currency="USD",
            exchange_name="NMS",
            regular_market_price=102.0,
            previous_close=100.0,
            points=[
                TrendPoint(timestamp="2026-06-25T13:30:00+00:00", close=100.0, volume=1000),
                TrendPoint(timestamp="2026-06-25T13:31:00+00:00", close=102.0, volume=1200),
            ],
            source="test-source",
            analysis_time="2026-06-25T13:32:00+00:00",
        )


class FakeUniverseScanner:
    def scan(self, limit: int = 100) -> UniverseResult:
        return UniverseResult(
            universe_date="2026-06-25",
            universe_name="us_most_active_top_100",
            market="US",
            limit=limit,
            source="test-source",
            generated_at="2026-06-25T13:32:00+00:00",
            items=[
                UniverseStock(rank=1, symbol="AAPL", name="Apple Inc.", sector="Technology"),
                UniverseStock(rank=2, symbol="MSFT", name="Microsoft Corporation", sector="Technology"),
            ][:limit],
            analysis_dimensions=["volume", "relative_volume", "market_cap"],
        )


class ApiEndpointsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.original_client = main.trend_client
        self.original_universe_scanner = main.universe_scanner
        main.trend_client = FakeTrendClient()
        main.universe_scanner = FakeUniverseScanner()

    def tearDown(self) -> None:
        main.trend_client = self.original_client
        main.universe_scanner = self.original_universe_scanner

    def test_popular_stocks_endpoint(self) -> None:
        payload = main.get_popular_us_stocks()

        self.assertEqual("US", payload["market"])
        self.assertGreaterEqual(len(payload["items"]), 3)

    def test_quote_endpoint(self) -> None:
        payload = main.get_stock_quote("AAPL")

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual(102.0, payload["price"])
        self.assertEqual(2.0, payload["change"])

    def test_trend_endpoint(self) -> None:
        payload = main.get_stock_trend("AAPL", range_="1d", interval="1m")

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual(2, len(payload["points"]))

    def test_recommendation_endpoint(self) -> None:
        payload = main.get_stock_recommendation("AAPL")

        self.assertEqual("AAPL", payload["symbol"])
        self.assertIn(payload["recommendation"], {"强关注", "观察", "中性", "回避"})
        self.assertEqual("algorithm-v0.1", payload["algorithm_version"])
        self.assertTrue(payload["factors"])

    def test_most_active_universe_endpoint(self) -> None:
        payload = main.get_most_active_universe(limit=2)

        self.assertEqual("US", payload["market"])
        self.assertEqual("us_most_active_top_100", payload["universe_name"])
        self.assertEqual(2, len(payload["items"]))


if __name__ == "__main__":
    unittest.main()
