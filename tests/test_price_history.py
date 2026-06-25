import unittest

from packages.data_sources.price_history import (
    RISK_DISCLAIMER,
    PriceHistoryError,
    parse_yahoo_history_payload,
    validate_history_range_and_interval,
)


def sample_payload() -> dict:
    return {
        "chart": {
            "result": [
                {
                    "meta": {"currency": "USD", "exchangeName": "NMS"},
                    "timestamp": [1466424600, 1466511000, 1466597400],
                    "indicators": {
                        "quote": [
                            {
                                "open": [95.0, None, 97.0],
                                "high": [96.0, None, 98.5],
                                "low": [94.0, None, 96.5],
                                "close": [95.8, None, 98.0],
                                "volume": [1_000_000, 1_100_000, 1_200_000],
                            }
                        ]
                    },
                }
            ],
            "error": None,
        }
    }


class PriceHistoryTest(unittest.TestCase):
    def test_validate_history_range_and_interval_accepts_ten_years(self) -> None:
        validate_history_range_and_interval("10y", "1d")

        with self.assertRaisesRegex(ValueError, "unsupported history range"):
            validate_history_range_and_interval("1d", "1d")

        with self.assertRaisesRegex(ValueError, "unsupported history interval"):
            validate_history_range_and_interval("10y", "1m")

    def test_parse_yahoo_history_payload_filters_empty_points_and_keeps_ohlcv(self) -> None:
        response = parse_yahoo_history_payload(sample_payload(), "AAPL", "10y", "1d")

        self.assertEqual("AAPL", response.symbol)
        self.assertEqual("Yahoo Finance chart API (yfinance-compatible)", response.source)
        self.assertEqual(RISK_DISCLAIMER, response.risk_disclaimer)
        self.assertEqual(2, len(response.points))
        self.assertEqual(95.0, response.points[0].open)
        self.assertEqual(98.0, response.points[1].close)
        self.assertEqual(1_200_000, response.points[1].volume)

    def test_parse_yahoo_history_payload_reports_api_errors(self) -> None:
        payload = {"chart": {"result": None, "error": {"description": "not found"}}}

        with self.assertRaisesRegex(PriceHistoryError, "not found"):
            parse_yahoo_history_payload(payload, "BAD", "10y", "1d")


if __name__ == "__main__":
    unittest.main()
