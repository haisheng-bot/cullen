import tempfile
import unittest
from datetime import date
from pathlib import Path

from packages.data_sources.market_trend import RISK_DISCLAIMER
from packages.data_sources.tiger_openapi import (
    TigerOpenAPIClient,
    TigerOpenAPIConfig,
    TigerOpenAPIError,
    parse_tiger_kline_payload,
    parse_tiger_quote_payload,
)


class FakeTigerQuoteAdapter:
    def get_quote(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "price": 210.5,
            "previous_close": 200.0,
            "currency": "USD",
            "exchange": "NASDAQ",
        }


class FakeTigerKlineAdapter:
    def get_kline(self, symbol: str, period: str, start_date: date, end_date: date) -> list[dict]:
        return [
            {
                "date": "2026-06-25",
                "open": "200.00",
                "high": "211.00",
                "low": "198.00",
                "close": "210.50",
                "volume": "1000000",
                "amount": "210500000",
            },
            {
                "date": "2026-06-24",
                "open": "198.00",
                "high": "201.00",
                "low": "197.00",
                "close": "200.00",
                "volume": "900000",
                "amount": "180000000",
            },
        ]


class TigerOpenAPIDataSourceTest(unittest.TestCase):
    def test_config_reports_missing_credentials_without_secret_values(self) -> None:
        config = TigerOpenAPIConfig(
            tiger_id=None,
            account=None,
            license=None,
            private_key_path=None,
            env="sandbox",
        )

        self.assertFalse(config.is_configured)
        self.assertEqual(
            ["TIGER_ID", "TIGER_ACCOUNT", "TIGER_LICENSE", "TIGER_PRIVATE_KEY_PATH"],
            config.missing_fields,
        )

    def test_status_is_read_only_and_contains_risk_disclaimer(self) -> None:
        client = TigerOpenAPIClient(
            config=TigerOpenAPIConfig(None, None, None, None, env="sandbox")
        )
        status = client.status().to_dict()

        self.assertFalse(status["configured"])
        self.assertFalse(status["trading_enabled"])
        self.assertEqual("sandbox", status["env"])
        self.assertEqual(RISK_DISCLAIMER, status["risk_disclaimer"])

    def test_fetch_quote_requires_configuration(self) -> None:
        client = TigerOpenAPIClient(
            config=TigerOpenAPIConfig(None, None, None, None, env="sandbox"),
            quote_adapter=FakeTigerQuoteAdapter(),
        )

        with self.assertRaisesRegex(TigerOpenAPIError, "not configured"):
            client.fetch_quote("AAPL")

    def test_fetch_quote_uses_injected_read_only_adapter(self) -> None:
        with tempfile.NamedTemporaryFile() as key_file:
            config = TigerOpenAPIConfig(
                tiger_id="tiger-id",
                account="paper-account",
                license="paper-license",
                private_key_path=key_file.name,
                env="sandbox",
            )
            client = TigerOpenAPIClient(config=config, quote_adapter=FakeTigerQuoteAdapter())

            quote = client.fetch_quote("aapl").to_dict()

        self.assertEqual("AAPL", quote["symbol"])
        self.assertEqual(210.5, quote["price"])
        self.assertEqual(10.5, quote["change"])
        self.assertEqual(5.25, quote["change_percent"])
        self.assertEqual("Tiger Brokers OpenAPI", quote["source"])
        self.assertEqual(RISK_DISCLAIMER, quote["risk_disclaimer"])

    def test_fetch_kline_uses_injected_read_only_adapter_for_three_year_reference(self) -> None:
        with tempfile.NamedTemporaryFile() as key_file:
            config = TigerOpenAPIConfig(
                tiger_id="tiger-id",
                account="paper-account",
                license="paper-license",
                private_key_path=key_file.name,
                env="sandbox",
            )
            client = TigerOpenAPIClient(
                config=config,
                kline_adapter=FakeTigerKlineAdapter(),
            )

            history = client.fetch_kline(
                "aapl", period="day", years=3, end_date=date(2026, 6, 26)
            ).to_dict()

        self.assertEqual("AAPL", history["symbol"])
        self.assertEqual("day", history["period"])
        self.assertEqual(3, history["years"])
        self.assertEqual("2023-06-27", history["start_date"])
        self.assertEqual("2026-06-26", history["end_date"])
        self.assertEqual("historical_kline_reference", history["data_scope"])
        self.assertEqual(2, len(history["points"]))
        self.assertEqual("2026-06-24", history["points"][0]["date"])
        self.assertEqual(900000, history["points"][0]["volume"])
        self.assertEqual(180000000.0, history["points"][0]["amount"])
        self.assertEqual(RISK_DISCLAIMER, history["risk_disclaimer"])

    def test_fetch_kline_rejects_more_than_three_years(self) -> None:
        with tempfile.NamedTemporaryFile() as key_file:
            client = TigerOpenAPIClient(
                config=TigerOpenAPIConfig(
                    tiger_id="tiger-id",
                    account="paper-account",
                    license="paper-license",
                    private_key_path=key_file.name,
                    env="sandbox",
                ),
                kline_adapter=FakeTigerKlineAdapter(),
            )

            with self.assertRaisesRegex(ValueError, "1 to 3 years"):
                client.fetch_kline("AAPL", years=4)

    def test_config_rejects_missing_private_key_file(self) -> None:
        config = TigerOpenAPIConfig(
            tiger_id="tiger-id",
            account="paper-account",
            license="paper-license",
            private_key_path=str(Path("/tmp/openstock-missing-tiger-key.pem")),
            env="sandbox",
        )

        self.assertIn("TIGER_PRIVATE_KEY_PATH(file_not_found)", config.missing_fields)
        self.assertFalse(config.is_configured)

    def test_parse_quote_payload_accepts_common_sdk_field_names(self) -> None:
        quote = parse_tiger_quote_payload(
            {"latestPrice": "50.25", "prevClose": "50", "market": "NYSE"},
            "XYZ",
        )

        self.assertEqual(50.25, quote.price)
        self.assertEqual(0.25, quote.change)
        self.assertEqual(0.5, quote.change_percent)
        self.assertEqual("NYSE", quote.exchange_name)

    def test_parse_kline_payload_accepts_common_sdk_field_names(self) -> None:
        points = parse_tiger_kline_payload(
            [
                {
                    "beginTime": 1782345600000,
                    "openPrice": "10",
                    "highPrice": "12",
                    "lowPrice": "9",
                    "closePrice": "11",
                    "vol": "1234",
                    "turnover": "13574",
                }
            ]
        )

        self.assertEqual(1, len(points))
        self.assertEqual("2026-06-25", points[0].date)
        self.assertEqual(11.0, points[0].close)
        self.assertEqual(1234, points[0].volume)
        self.assertEqual(13574.0, points[0].amount)


if __name__ == "__main__":
    unittest.main()
