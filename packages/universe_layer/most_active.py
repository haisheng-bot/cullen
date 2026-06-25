from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from packages.universe_layer.schemas import UniverseResult, UniverseStock


MOST_ACTIVE_DIMENSIONS = [
    "volume",
    "relative_volume",
    "dollar_volume",
    "price_change_percent",
    "market_cap",
    "pe_ratio",
    "eps_growth",
    "revenue_growth",
    "rsi",
    "moving_average_position",
    "volatility",
    "52_week_position",
    "sector",
    "analyst_rating",
]

FALLBACK_MOST_ACTIVE_US = [
    ("NVDA", "NVIDIA Corporation", "Semiconductors"),
    ("TSLA", "Tesla, Inc.", "Consumer Discretionary"),
    ("AAPL", "Apple Inc.", "Technology"),
    ("AMD", "Advanced Micro Devices, Inc.", "Semiconductors"),
    ("PLTR", "Palantir Technologies Inc.", "Technology"),
    ("AMZN", "Amazon.com, Inc.", "Consumer Discretionary"),
    ("MSFT", "Microsoft Corporation", "Technology"),
    ("META", "Meta Platforms, Inc.", "Communication Services"),
    ("GOOGL", "Alphabet Inc.", "Communication Services"),
    ("JPM", "JPMorgan Chase & Co.", "Financials"),
]


class MostActiveUniverseScanner:
    source_name = "Yahoo Finance Most Active compatible scanner"
    yahoo_url = (
        "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
        "?formatted=false&scrIds=most_actives&count={limit}"
    )

    def scan(self, limit: int = 100) -> UniverseResult:
        normalized_limit = max(1, min(limit, 100))
        try:
            items = self._fetch_yahoo_most_active(normalized_limit)
            source = "Yahoo Finance predefined most_actives"
        except Exception:
            items = fallback_most_active(normalized_limit)
            source = "static fallback most active US watchlist"

        now = datetime.now(timezone.utc)
        return UniverseResult(
            universe_date=now.date().isoformat(),
            universe_name="us_most_active_top_100",
            market="US",
            limit=normalized_limit,
            source=source,
            generated_at=now.isoformat(),
            items=items,
            analysis_dimensions=MOST_ACTIVE_DIMENSIONS,
        )

    def _fetch_yahoo_most_active(self, limit: int) -> list[UniverseStock]:
        request = Request(
            self.yahoo_url.format(limit=limit),
            headers={"User-Agent": "OpenStockAI/0.1"},
        )
        try:
            with urlopen(request, timeout=12) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError("failed to fetch Yahoo most active universe") from exc
        return parse_yahoo_most_active(payload, limit)


def parse_yahoo_most_active(payload: dict[str, Any], limit: int) -> list[UniverseStock]:
    quotes = payload.get("finance", {}).get("result", [{}])[0].get("quotes", [])
    items: list[UniverseStock] = []
    for index, quote in enumerate(quotes[:limit], start=1):
        symbol = quote.get("symbol")
        if not symbol:
            continue
        items.append(
            UniverseStock(
                rank=index,
                symbol=symbol,
                name=quote.get("longName") or quote.get("shortName") or symbol,
                sector=quote.get("sector"),
                volume=_to_int(quote.get("regularMarketVolume")),
                price=_to_float(quote.get("regularMarketPrice")),
                change_percent=_to_float(quote.get("regularMarketChangePercent")),
                market_cap=_to_float(quote.get("marketCap")),
                pe_ratio=_to_float(quote.get("trailingPE")),
                relative_volume=None,
                analysis_tags=build_analysis_tags(
                    volume=_to_int(quote.get("regularMarketVolume")),
                    change_percent=_to_float(quote.get("regularMarketChangePercent")),
                    market_cap=_to_float(quote.get("marketCap")),
                    pe_ratio=_to_float(quote.get("trailingPE")),
                ),
            )
        )
    if not items:
        raise RuntimeError("Yahoo most active payload contained no usable quotes")
    return items


def fallback_most_active(limit: int) -> list[UniverseStock]:
    items = []
    for index, (symbol, name, sector) in enumerate(FALLBACK_MOST_ACTIVE_US[:limit], start=1):
        items.append(
            UniverseStock(
                rank=index,
                symbol=symbol,
                name=name,
                sector=sector,
                analysis_tags=["fallback", "needs-live-refresh"],
            )
        )
    return items


def build_analysis_tags(
    volume: int | None,
    change_percent: float | None,
    market_cap: float | None,
    pe_ratio: float | None,
) -> list[str]:
    tags: list[str] = []
    if volume is not None and volume >= 10_000_000:
        tags.append("high-volume")
    if change_percent is not None and abs(change_percent) >= 3:
        tags.append("large-move")
    if market_cap is not None and market_cap >= 200_000_000_000:
        tags.append("mega-cap")
    if pe_ratio is not None and pe_ratio > 0:
        if pe_ratio < 20:
            tags.append("valuation-watch")
        elif pe_ratio > 60:
            tags.append("high-valuation")
    if not tags:
        tags.append("screening-candidate")
    return tags


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None

