import importlib.util
import unittest

if importlib.util.find_spec("fastapi") is None:
    raise unittest.SkipTest("FastAPI is not installed in this Python environment")

from apps.api import main
from packages.data_sources.market_trend import TrendPoint, TrendResponse
from packages.data_sources.price_history import HistoryPoint, HistoryResponse
from packages.data_sources.sec_filings import Filing, FilingListResponse
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


class FakeHistoryClient:
    def fetch_history(self, symbol: str, range_: str = "10y", interval: str = "1d") -> HistoryResponse:
        return HistoryResponse(
            symbol=symbol,
            range=range_,
            interval=interval,
            currency="USD",
            exchange_name="NMS",
            points=[
                HistoryPoint(date="2016-06-20", open=95.0, high=96.0, low=94.0, close=95.8, volume=1_000_000),
                HistoryPoint(date="2016-06-21", open=97.0, high=98.5, low=96.5, close=98.0, volume=1_200_000),
            ],
            source="test-source",
            analysis_time="2026-06-25T13:32:00+00:00",
        )


class FakeSECFilingClient:
    def list_filings(
        self, symbol: str, forms: tuple[str, ...] = ("10-K", "10-Q", "8-K"), limit: int = 10
    ) -> FilingListResponse:
        return FilingListResponse(
            symbol=symbol,
            cik="0000320193",
            company_name="Apple Inc.",
            filings=[
                Filing(
                    form="10-K",
                    filing_date="2025-11-01",
                    report_date="2025-09-30",
                    accession_number="0000320193-25-000100",
                    primary_document="aapl-10k.htm",
                    document_url=(
                        "https://www.sec.gov/Archives/edgar/data/320193/"
                        "000032019325000100/aapl-10k.htm"
                    ),
                )
            ][:limit],
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
        self.original_history_client = main.history_client
        self.original_sec_filing_client = main.sec_filing_client
        self.original_universe_scanner = main.universe_scanner
        main.trend_client = FakeTrendClient()
        main.history_client = FakeHistoryClient()
        main.sec_filing_client = FakeSECFilingClient()
        main.universe_scanner = FakeUniverseScanner()

    def tearDown(self) -> None:
        main.trend_client = self.original_client
        main.history_client = self.original_history_client
        main.sec_filing_client = self.original_sec_filing_client
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

    def test_history_endpoint(self) -> None:
        payload = main.get_stock_price_history("AAPL", range_="10y", interval="1d")

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual("10y", payload["range"])
        self.assertEqual(2, len(payload["points"]))
        self.assertEqual(95.0, payload["points"][0]["open"])

    def test_sec_filings_endpoint(self) -> None:
        payload = main.get_stock_sec_filings("AAPL", forms="10-K,10-Q,8-K", limit=10)

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual("0000320193", payload["cik"])
        self.assertEqual(1, len(payload["filings"]))
        self.assertEqual("10-K", payload["filings"][0]["form"])

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
