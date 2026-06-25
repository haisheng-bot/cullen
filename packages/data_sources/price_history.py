"""Free, multi-year daily price history via the Yahoo Finance chart API.

This corresponds to the "yfinance" data source named in
docs/standards/project-standard-v0.1.md. It reuses the same public chart
endpoint as packages.data_sources.market_trend, but targets long daily/
weekly/monthly ranges (up to ~10 years) instead of intraday trend data.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from packages.data_sources.market_trend import RISK_DISCLAIMER, normalize_symbol

SUPPORTED_HISTORY_RANGES = {"1y", "2y", "5y", "10y", "max"}
SUPPORTED_HISTORY_INTERVALS = {"1d", "1wk", "1mo"}


class PriceHistoryError(RuntimeError):
    """Raised when historical price data cannot be fetched or parsed."""


@dataclass(frozen=True)
class HistoryPoint:
    date: str
    open: float | None
    high: float | None
    low: float | None
    close: float
    volume: int | None = None


@dataclass(frozen=True)
class HistoryResponse:
    symbol: str
    range: str
    interval: str
    currency: str | None
    exchange_name: str | None
    points: list[HistoryPoint]
    source: str
    analysis_time: str
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "range": self.range,
            "interval": self.interval,
            "currency": self.currency,
            "exchange_name": self.exchange_name,
            "points": [point.__dict__ for point in self.points],
            "source": self.source,
            "analysis_time": self.analysis_time,
            "risk_disclaimer": self.risk_disclaimer,
        }


class YahooFinanceHistoryClient:
    base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
    source_name = "Yahoo Finance chart API (yfinance-compatible)"

    def fetch_history(
        self, symbol: str, range_: str = "10y", interval: str = "1d"
    ) -> HistoryResponse:
        normalized_symbol = normalize_symbol(symbol)
        validate_history_range_and_interval(range_, interval)

        params = urlencode({"range": range_, "interval": interval})
        url = f"{self.base_url}/{normalized_symbol}?{params}"
        request = Request(url, headers={"User-Agent": "OpenStockAI/0.1"})

        try:
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise PriceHistoryError(f"Failed to fetch price history for {normalized_symbol}") from exc

        return parse_yahoo_history_payload(payload, normalized_symbol, range_, interval)


def validate_history_range_and_interval(range_: str, interval: str) -> None:
    if range_ not in SUPPORTED_HISTORY_RANGES:
        raise ValueError(f"unsupported history range: {range_}")
    if interval not in SUPPORTED_HISTORY_INTERVALS:
        raise ValueError(f"unsupported history interval: {interval}")


def parse_yahoo_history_payload(
    payload: dict[str, Any], symbol: str, range_: str, interval: str
) -> HistoryResponse:
    chart = payload.get("chart", {})
    error = chart.get("error")
    if error:
        description = error.get("description", "unknown chart error")
        raise PriceHistoryError(description)

    results = chart.get("result") or []
    if not results:
        raise PriceHistoryError(f"No price history found for {symbol}")

    result = results[0]
    meta = result.get("meta", {})
    timestamps = result.get("timestamp") or []
    indicators = result.get("indicators", {})
    quote = (indicators.get("quote") or [{}])[0]
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []

    points: list[HistoryPoint] = []
    for index, raw_timestamp in enumerate(timestamps):
        close = closes[index] if index < len(closes) else None
        if close is None:
            continue
        date = datetime.fromtimestamp(raw_timestamp, tz=timezone.utc).date().isoformat()
        points.append(
            HistoryPoint(
                date=date,
                open=_round_or_none(opens, index),
                high=_round_or_none(highs, index),
                low=_round_or_none(lows, index),
                close=round(float(close), 4),
                volume=volumes[index] if index < len(volumes) else None,
            )
        )

    if not points:
        raise PriceHistoryError(f"No usable price history found for {symbol}")

    return HistoryResponse(
        symbol=symbol,
        range=range_,
        interval=interval,
        currency=meta.get("currency"),
        exchange_name=meta.get("exchangeName"),
        points=points,
        source=YahooFinanceHistoryClient.source_name,
        analysis_time=datetime.now(timezone.utc).isoformat(),
    )


def _round_or_none(values: list[float | None], index: int) -> float | None:
    if index >= len(values) or values[index] is None:
        return None
    return round(float(values[index]), 4)
