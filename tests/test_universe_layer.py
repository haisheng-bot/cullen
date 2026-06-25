import unittest

from packages.universe_layer.most_active import (
    MOST_ACTIVE_DIMENSIONS,
    build_analysis_tags,
    fallback_most_active,
    parse_yahoo_most_active,
)


class UniverseLayerTest(unittest.TestCase):
    def test_parse_yahoo_most_active_payload(self) -> None:
        payload = {
            "finance": {
                "result": [
                    {
                        "quotes": [
                            {
                                "symbol": "AAPL",
                                "longName": "Apple Inc.",
                                "sector": "Technology",
                                "regularMarketVolume": 12345678,
                                "regularMarketPrice": 200.5,
                                "regularMarketChangePercent": 3.2,
                                "marketCap": 3_000_000_000_000,
                                "trailingPE": 31.5,
                            }
                        ]
                    }
                ]
            }
        }

        items = parse_yahoo_most_active(payload, limit=100)

        self.assertEqual(1, len(items))
        self.assertEqual("AAPL", items[0].symbol)
        self.assertIn("high-volume", items[0].analysis_tags)
        self.assertIn("large-move", items[0].analysis_tags)
        self.assertIn("mega-cap", items[0].analysis_tags)

    def test_fallback_most_active_returns_candidates(self) -> None:
        items = fallback_most_active(limit=3)

        self.assertEqual(3, len(items))
        self.assertEqual(1, items[0].rank)
        self.assertIn("fallback", items[0].analysis_tags)

    def test_analysis_dimensions_include_market_standard_filters(self) -> None:
        required = {"volume", "relative_volume", "market_cap", "pe_ratio", "rsi", "sector"}

        self.assertTrue(required.issubset(set(MOST_ACTIVE_DIMENSIONS)))

    def test_build_analysis_tags(self) -> None:
        tags = build_analysis_tags(
            volume=12_000_000,
            change_percent=-4.0,
            market_cap=250_000_000_000,
            pe_ratio=75.0,
        )

        self.assertIn("high-volume", tags)
        self.assertIn("large-move", tags)
        self.assertIn("mega-cap", tags)
        self.assertIn("high-valuation", tags)


if __name__ == "__main__":
    unittest.main()

