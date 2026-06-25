import unittest

from packages.data_sources.fred import (
    RISK_DISCLAIMER,
    FREDClient,
    FREDError,
    parse_fred_observations_payload,
)


def sample_payload() -> dict:
    return {
        "observations": [
            {"date": "2026-05-01", "value": "5.33"},
            {"date": "2026-04-01", "value": "."},
            {"date": "2026-03-01", "value": "5.25"},
        ]
    }


class FREDTest(unittest.TestCase):
    def test_parse_fred_observations_payload_treats_dot_as_missing(self) -> None:
        response = parse_fred_observations_payload(sample_payload(), "FEDFUNDS")

        self.assertEqual("FEDFUNDS", response.series_id)
        self.assertEqual(RISK_DISCLAIMER, response.risk_disclaimer)
        self.assertEqual(3, len(response.observations))
        self.assertEqual(5.33, response.observations[0].value)
        self.assertIsNone(response.observations[1].value)

    def test_parse_fred_observations_payload_raises_on_api_error(self) -> None:
        payload = {"error_message": "Bad Request. The value for api_key is not registered."}

        with self.assertRaisesRegex(FREDError, "api_key"):
            parse_fred_observations_payload(payload, "FEDFUNDS")

    def test_fetch_observations_requires_configured_api_key(self) -> None:
        client = FREDClient(api_key=None)

        with self.assertRaisesRegex(FREDError, "FRED_API_KEY is not configured"):
            client.fetch_observations("FEDFUNDS")


if __name__ == "__main__":
    unittest.main()
