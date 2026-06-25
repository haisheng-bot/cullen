from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


RISK_DISCLAIMER = "本系统仅用于投资研究辅助，不构成任何投资建议。"
SUPPORTED_RANGES = {"1d", "5d", "1mo", "3mo", "6mo", "1y"}
SUPPORTED_INTERVALS = {"1m", "2m", "5m", "15m", "30m", "60m", "1d"}


class MarketTrendError(RuntimeError):
    """Raised when market trend data cannot be fetched or parsed."""


@dataclass(frozen=True)
class TrendPoint:
    timestamp: str
    close: float
    volume: int | None = None


@dataclass(frozen=True)
class TrendResponse:
    symbol: str
    range: str
    interval: str
    currency: str | None
    exchange_name: str | None
    regular_market_price: float | None
    previous_close: float | None
    points: list[TrendPoint]
    source: str
    analysis_time: str
    risk_disclaimer: str = RISK_DISCLAIMER

    @property
    def latest_price(self) -> float:
        return self.points[-1].close

    @property
    def price_change(self) -> float | None:
        baseline = self.previous_close
        if baseline in (None, 0):
            baseline = self.points[0].close if self.points else None
        if baseline in (None, 0):
            return None
        return round(self.latest_price - float(baseline), 4)

    @property
    def price_change_percent(self) -> float | None:
        baseline = self.previous_close
        if baseline in (None, 0):
            baseline = self.points[0].close if self.points else None
        if baseline in (None, 0):
            return None
        return round((self.latest_price - float(baseline)) / float(baseline) * 100, 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "range": self.range,
            "interval": self.interval,
            "currency": self.currency,
            "exchange_name": self.exchange_name,
            "regular_market_price": self.regular_market_price,
            "previous_close": self.previous_close,
            "points": [point.__dict__ for point in self.points],
            "source": self.source,
            "analysis_time": self.analysis_time,
            "risk_disclaimer": self.risk_disclaimer,
        }

    def to_quote_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "price": self.regular_market_price or self.latest_price,
            "latest_point_price": self.latest_price,
            "change": self.price_change,
            "change_percent": self.price_change_percent,
            "currency": self.currency,
            "exchange_name": self.exchange_name,
            "previous_close": self.previous_close,
            "source": self.source,
            "analysis_time": self.analysis_time,
            "risk_disclaimer": self.risk_disclaimer,
        }


class YahooFinanceChartClient:
    base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
    source_name = "Yahoo Finance chart API"

    def fetch_trend(self, symbol: str, range_: str = "1d", interval: str = "1m") -> TrendResponse:
        normalized_symbol = normalize_symbol(symbol)
        validate_range_and_interval(range_, interval)

        params = urlencode({"range": range_, "interval": interval})
        url = f"{self.base_url}/{normalized_symbol}?{params}"
        request = Request(url, headers={"User-Agent": "OpenStockAI/0.1"})

        try:
            with urlopen(request, timeout=12) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise MarketTrendError(f"Failed to fetch trend data for {normalized_symbol}") from exc

        return parse_yahoo_chart_payload(payload, normalized_symbol, range_, interval)


def normalize_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if not normalized:
        raise ValueError("symbol is required")
    if len(normalized) > 16:
        raise ValueError("symbol is too long")
    if not all(char.isalnum() or char in {".", "-"} for char in normalized):
        raise ValueError("symbol contains unsupported characters")
    return normalized


def validate_range_and_interval(range_: str, interval: str) -> None:
    if range_ not in SUPPORTED_RANGES:
        raise ValueError(f"unsupported range: {range_}")
    if interval not in SUPPORTED_INTERVALS:
        raise ValueError(f"unsupported interval: {interval}")
    if range_ != "1d" and interval in {"1m", "2m"}:
        raise ValueError("1m and 2m intervals are only supported for 1d range")


def parse_yahoo_chart_payload(
    payload: dict[str, Any], symbol: str, range_: str, interval: str
) -> TrendResponse:
    chart = payload.get("chart", {})
    error = chart.get("error")
    if error:
        description = error.get("description", "unknown chart error")
        raise MarketTrendError(description)

    results = chart.get("result") or []
    if not results:
        raise MarketTrendError(f"No trend data found for {symbol}")

    result = results[0]
    meta = result.get("meta", {})
    timestamps = result.get("timestamp") or []
    indicators = result.get("indicators", {})
    quote = (indicators.get("quote") or [{}])[0]
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []

    points: list[TrendPoint] = []
    for index, raw_timestamp in enumerate(timestamps):
        close = closes[index] if index < len(closes) else None
        if close is None:
            continue
        volume = volumes[index] if index < len(volumes) else None
        timestamp = datetime.fromtimestamp(raw_timestamp, tz=timezone.utc).isoformat()
        points.append(TrendPoint(timestamp=timestamp, close=round(float(close), 4), volume=volume))

    if not points:
        raise MarketTrendError(f"No usable trend points found for {symbol}")

    return TrendResponse(
        symbol=symbol,
        range=range_,
        interval=interval,
        currency=meta.get("currency"),
        exchange_name=meta.get("exchangeName"),
        regular_market_price=meta.get("regularMarketPrice"),
        previous_close=meta.get("previousClose"),
        points=points,
        source=YahooFinanceChartClient.source_name,
        analysis_time=datetime.now(timezone.utc).isoformat(),
    )
