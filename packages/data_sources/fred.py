"""FRED (Federal Reserve Economic Data) macro series adapter.

Unlike yfinance/SEC EDGAR, FRED requires a free API key. Register at
https://fred.stlouisfed.org/docs/api/api_key.html and set FRED_API_KEY
in `.env`. Without a key this client raises FREDError with guidance;
it never falls back to a hardcoded key.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from packages.config import get_settings
from packages.data_sources.market_trend import RISK_DISCLAIMER

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


class FREDError(RuntimeError):
    """Raised when FRED data cannot be fetched or parsed, or no key is configured."""


@dataclass(frozen=True)
class FREDObservation:
    date: str
    value: float | None


@dataclass(frozen=True)
class FREDSeriesResponse:
    series_id: str
    observations: list[FREDObservation]
    source: str
    analysis_time: str
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "series_id": self.series_id,
            "observations": [obs.__dict__ for obs in self.observations],
            "source": self.source,
            "analysis_time": self.analysis_time,
            "risk_disclaimer": self.risk_disclaimer,
        }


class FREDClient:
    source_name = "FRED (Federal Reserve Economic Data)"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key

    def fetch_observations(
        self,
        series_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
    ) -> FREDSeriesResponse:
        api_key = self._api_key or get_settings().fred_api_key
        if not api_key:
            raise FREDError(
                "FRED_API_KEY is not configured. Get a free key at "
                "https://fred.stlouisfed.org/docs/api/api_key.html and set it in .env."
            )

        normalized_series_id = series_id.strip().upper()
        if not normalized_series_id:
            raise ValueError("series_id is required")

        params = {
            "series_id": normalized_series_id,
            "api_key": api_key,
            "file_type": "json",
            "limit": str(limit),
            "sort_order": "desc",
        }
        if start_date:
            params["observation_start"] = start_date
        if end_date:
            params["observation_end"] = end_date

        url = f"{BASE_URL}?{urlencode(params)}"
        request = Request(url, headers={"User-Agent": "OpenStockAI/0.1"})

        try:
            with urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise FREDError(f"Failed to fetch FRED series {normalized_series_id}") from exc

        return parse_fred_observations_payload(payload, normalized_series_id)


def parse_fred_observations_payload(payload: dict[str, Any], series_id: str) -> FREDSeriesResponse:
    if "error_message" in payload:
        raise FREDError(payload["error_message"])

    raw_observations = payload.get("observations") or []
    observations = [
        FREDObservation(
            date=item["date"],
            value=None if item.get("value") in (None, ".") else float(item["value"]),
        )
        for item in raw_observations
    ]

    return FREDSeriesResponse(
        series_id=series_id,
        observations=observations,
        source=FREDClient.source_name,
        analysis_time=datetime.now(timezone.utc).isoformat(),
    )
