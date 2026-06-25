import unittest

from packages.data_sources.sec_financials import parse_companyfacts_payload


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

    def test_parse_companyfacts_payload_handles_missing_facts(self) -> None:
        response = parse_companyfacts_payload({"entityName": "Empty Co"}, "EMPTY", "0000000001")

        self.assertIsNone(response.latest)
        self.assertIsNone(response.previous)


if __name__ == "__main__":
    unittest.main()
