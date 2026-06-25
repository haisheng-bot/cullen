import importlib.util
import unittest

if importlib.util.find_spec("fastapi") is None:
    raise unittest.SkipTest("FastAPI is not installed in this Python environment")

from apps.api import main
from packages.data_sources.market_trend import TrendPoint, TrendResponse


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


class ApiEndpointsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.original_client = main.trend_client
        main.trend_client = FakeTrendClient()

    def tearDown(self) -> None:
        main.trend_client = self.original_client

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


if __name__ == "__main__":
    unittest.main()
