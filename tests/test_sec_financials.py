import unittest

from packages.data_sources.sec_financials import parse_companyfacts_payload, parse_companyfacts_series


def sample_companyfacts_payload() -> dict:
    return {
        "entityName": "Apple Inc.",
        "facts": {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": {
                    "units": {
                        "USD": [
                            {
                                "fy": 2025,
                                "fp": "FY",
                                "form": "10-K",
                                "start": "2024-09-29",
                                "end": "2025-09-27",
                                "val": 416161000000,
                                "filed": "2025-11-01",
                            },
                            {
                                "fy": 2024,
                                "fp": "FY",
                                "form": "10-K",
                                "start": "2023-10-01",
                                "end": "2024-09-28",
                                "val": 391035000000,
                                "filed": "2024-11-01",
                            },
                            {
                                "fy": 2025,
                                "fp": "FY",
                                "form": "10-K",
                                "start": "2023-10-01",
                                "end": "2024-09-28",
                                "val": 391035000000,
                                "filed": "2025-11-01",
                            },
                            {
                                "fy": 2025,
                                "fp": "Q1",
                                "form": "10-Q",
                                "start": "2024-09-29",
                                "end": "2024-12-28",
                                "val": 124300000000,
                                "filed": "2025-01-30",
                            },
                        ]
                    }
                },
                "NetIncomeLoss": {
                    "units": {
                        "USD": [
                            {"fy": 2025, "fp": "FY", "form": "10-K", "end": "2025-09-27", "val": 112010000000, "filed": "2025-11-01"},
                            {"fy": 2024, "fp": "FY", "form": "10-K", "end": "2024-09-28", "val": 93736000000, "filed": "2024-11-01"},
                        ]
                    }
                },
                "EarningsPerShareDiluted": {
                    "units": {
                        "USD/shares": [
                            {"fy": 2025, "fp": "FY", "form": "10-K", "end": "2025-09-27", "val": 7.46, "filed": "2025-11-01"},
                            {"fy": 2024, "fp": "FY", "form": "10-K", "end": "2024-09-28", "val": 6.08, "filed": "2024-11-01"},
                        ]
                    }
                },
                "OperatingIncomeLoss": {
                    "units": {
                        "USD": [
                            {"fy": 2025, "fp": "FY", "form": "10-K", "end": "2025-09-27", "val": 130000000000, "filed": "2025-11-01"},
                        ]
                    }
                },
                "AssetsCurrent": {
                    "units": {
                        "USD": [
                            {"fy": 2025, "fp": "FY", "form": "10-K", "end": "2025-09-27", "val": 150000000000, "filed": "2025-11-01"},
                        ]
                    }
                },
                "LiabilitiesCurrent": {
                    "units": {
                        "USD": [
                            {"fy": 2025, "fp": "FY", "form": "10-K", "end": "2025-09-27", "val": 130000000000, "filed": "2025-11-01"},
                        ]
                    }
                },
                "PropertyPlantAndEquipmentNet": {
                    "units": {
                        "USD": [
                            {"fy": 2025, "fp": "FY", "form": "10-K", "end": "2025-09-27", "val": 45000000000, "filed": "2025-11-01"},
                        ]
                    }
                },
                "CashAndCashEquivalentsAtCarryingValue": {
                    "units": {
                        "USD": [
                            {"fy": 2025, "fp": "FY", "form": "10-K", "end": "2025-09-27", "val": 30000000000, "filed": "2025-11-01"},
                        ]
                    }
                },
                "LongTermDebtNoncurrent": {
                    "units": {
                        "USD": [
                            {"fy": 2025, "fp": "FY", "form": "10-K", "end": "2025-09-27", "val": 85000000000, "filed": "2025-11-01"},
                        ]
                    }
                },
            }
        },
    }


class SECFinancialsTest(unittest.TestCase):
    def test_parse_companyfacts_payload_dedupes_by_end_date(self) -> None:
        response = parse_companyfacts_payload(sample_companyfacts_payload(), "AAPL", "0000320193")

        self.assertEqual("Apple Inc.", response.company_name)
        self.assertEqual("2025-09-27", response.latest.end_date)
        self.assertEqual(416161000000, response.latest.revenue)
        self.assertEqual(112010000000, response.latest.net_income)
        self.assertEqual(7.46, response.latest.eps_diluted)

        self.assertEqual("2024-09-28", response.previous.end_date)
        self.assertEqual(391035000000, response.previous.revenue)

    def test_parse_companyfacts_payload_extracts_magic_formula_inputs(self) -> None:
        response = parse_companyfacts_payload(sample_companyfacts_payload(), "AAPL", "0000320193")

        self.assertEqual(130000000000, response.latest.operating_income)
        self.assertEqual(150000000000, response.latest.current_assets)
        self.assertEqual(130000000000, response.latest.current_liabilities)
        self.assertEqual(45000000000, response.latest.net_fixed_assets)
        self.assertEqual(30000000000, response.latest.cash)
        # Only LongTermDebtNoncurrent is present in the fixture; current debt
        # tags are absent and should default to 0 rather than None.
        self.assertEqual(85000000000, response.latest.total_debt)

    def test_parse_companyfacts_payload_defaults_total_debt_to_zero_when_absent(self) -> None:
        response = parse_companyfacts_payload(sample_companyfacts_payload(), "AAPL", "0000320193")

        # The previous year has no debt tags in the fixture at all.
        self.assertEqual(0, response.previous.total_debt)

    def test_parse_companyfacts_payload_handles_missing_facts(self) -> None:
        response = parse_companyfacts_payload({"entityName": "Empty Co"}, "EMPTY", "0000000001")

        self.assertIsNone(response.latest)
        self.assertIsNone(response.previous)


class ParseCompanyfactsSeriesTest(unittest.TestCase):
    def test_returns_every_fiscal_year_sorted_descending(self) -> None:
        series = parse_companyfacts_series(sample_companyfacts_payload(), "AAPL", "0000320193")

        self.assertEqual(["2025-09-27", "2024-09-28"], [item.end_date for item in series])

    def test_filed_date_uses_earliest_filing_not_a_later_restatement(self) -> None:
        # The fixture's FY2024 revenue (end=2024-09-28) appears twice: once
        # filed 2024-11-01 (the original 10-K) and again filed 2025-11-01
        # (as a comparative figure inside the FY2025 10-K). Point-in-time
        # reconstruction must anchor on the *original* filing date, not the
        # later one, or a backtest rebalancing in e.g. 2025-01 would
        # incorrectly believe FY2024 financials weren't disclosed yet.
        series = parse_companyfacts_series(sample_companyfacts_payload(), "AAPL", "0000320193")
        fy2024 = next(item for item in series if item.end_date == "2024-09-28")

        self.assertEqual("2024-11-01", fy2024.filed_date)
        self.assertEqual(391035000000, fy2024.revenue)

    def test_latest_fiscal_year_filed_date_matches_its_own_filing(self) -> None:
        series = parse_companyfacts_series(sample_companyfacts_payload(), "AAPL", "0000320193")
        fy2025 = next(item for item in series if item.end_date == "2025-09-27")

        self.assertEqual("2025-11-01", fy2025.filed_date)
        self.assertEqual(416161000000, fy2025.revenue)

    def test_handles_missing_facts(self) -> None:
        series = parse_companyfacts_series({"entityName": "Empty Co"}, "EMPTY", "0000000001")

        self.assertEqual([], series)


if __name__ == "__main__":
    unittest.main()
