from packages.data_sources.market_trend import (
    RISK_DISCLAIMER,
    MarketTrendError,
    normalize_symbol,
    parse_yahoo_chart_payload,
    validate_range_and_interval,
)
import unittest


def sample_payload() -> dict:
    return {
        "chart": {
            "result": [
                {
                    "meta": {
                        "currency": "USD",
                        "exchangeName": "NMS",
                        "regularMarketPrice": 210.5,
                        "previousClose": 209.1,
                    },
                    "timestamp": [1719322200, 1719322260, 1719322320],
                    "indicators": {
                        "quote": [
                            {
                                "close": [210.1, None, 211.25],
                                "volume": [1200, 1300, 1400],
                            }
                        ]
                    },
                }
            ],
            "error": None,
        }
    }


class MarketTrendTest(unittest.TestCase):
    def test_normalize_symbol_accepts_us_symbols(self) -> None:
        self.assertEqual("AAPL", normalize_symbol(" aapl "))
        self.assertEqual("BRK-B", normalize_symbol("brk-b"))

    def test_validate_range_and_interval_rejects_unsupported_values(self) -> None:
        validate_range_and_interval("1d", "1m")

        with self.assertRaisesRegex(ValueError, "unsupported range"):
            validate_range_and_interval("10y", "1d")

    def test_parse_yahoo_chart_payload_filters_empty_points(self) -> None:
        response = parse_yahoo_chart_payload(sample_payload(), "AAPL", "1d", "1m")

        self.assertEqual("AAPL", response.symbol)
        self.assertEqual("USD", response.currency)
        self.assertEqual("NMS", response.exchange_name)
        self.assertEqual("Yahoo Finance chart API", response.source)
        self.assertEqual(RISK_DISCLAIMER, response.risk_disclaimer)
        self.assertEqual(2, len(response.points))
        self.assertEqual(210.1, response.points[0].close)
        self.assertEqual(211.25, response.points[1].close)
        self.assertEqual(211.25, response.to_quote_dict()["latest_point_price"])
        self.assertIn("change_percent", response.to_quote_dict())

    def test_parse_yahoo_chart_payload_reports_api_errors(self) -> None:
        payload = {"chart": {"result": None, "error": {"description": "not found"}}}

        with self.assertRaisesRegex(MarketTrendError, "not found"):
            parse_yahoo_chart_payload(payload, "BAD", "1d", "1m")


if __name__ == "__main__":
    unittest.main()
