import unittest

from packages.data_sources.sec_filings import (
    RISK_DISCLAIMER,
    SECFilingError,
    parse_submissions_payload,
    parse_ticker_map_payload,
)


def sample_ticker_map() -> dict:
    return {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
        "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corporation"},
    }


def sample_submissions_payload() -> dict:
    return {
        "name": "Apple Inc.",
        "filings": {
            "recent": {
                "form": ["10-K", "4", "10-Q", "8-K"],
                "filingDate": ["2025-11-01", "2025-10-15", "2025-08-01", "2025-07-20"],
                "reportDate": ["2025-09-30", "", "2025-06-30", "2025-07-20"],
                "accessionNumber": [
                    "0000320193-25-000100",
                    "0000320193-25-000099",
                    "0000320193-25-000080",
                    "0000320193-25-000070",
                ],
                "primaryDocument": ["aapl-10k.htm", "form4.xml", "aapl-10q.htm", "aapl-8k.htm"],
            }
        },
    }


class SECFilingsTest(unittest.TestCase):
    def test_parse_ticker_map_payload_resolves_cik(self) -> None:
        cik = parse_ticker_map_payload(sample_ticker_map(), "aapl")

        self.assertEqual("0000320193", cik)

    def test_parse_ticker_map_payload_raises_for_unknown_symbol(self) -> None:
        with self.assertRaisesRegex(SECFilingError, "No SEC CIK found"):
            parse_ticker_map_payload(sample_ticker_map(), "ZZZZ")

    def test_parse_submissions_payload_filters_to_requested_forms(self) -> None:
        response = parse_submissions_payload(
            sample_submissions_payload(), "AAPL", "0000320193", ("10-K", "10-Q", "8-K"), limit=10
        )

        self.assertEqual("Apple Inc.", response.company_name)
        self.assertEqual(RISK_DISCLAIMER, response.risk_disclaimer)
        self.assertEqual(3, len(response.filings))
        self.assertEqual({"10-K", "10-Q", "8-K"}, {f.form for f in response.filings})

        ten_k = next(f for f in response.filings if f.form == "10-K")
        self.assertEqual(
            "https://www.sec.gov/Archives/edgar/data/320193/000032019325000100/aapl-10k.htm",
            ten_k.document_url,
        )

    def test_parse_submissions_payload_respects_limit(self) -> None:
        response = parse_submissions_payload(
            sample_submissions_payload(), "AAPL", "0000320193", ("10-K", "10-Q", "8-K"), limit=1
        )

        self.assertEqual(1, len(response.filings))


if __name__ == "__main__":
    unittest.main()
