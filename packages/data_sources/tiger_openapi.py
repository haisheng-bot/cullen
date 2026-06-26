"""Tiger Brokers OpenAPI read-only data source.

This module intentionally does not read or automate the Tiger desktop/mobile
app. It only models the official OpenAPI integration boundary and keeps
credentials in environment-backed Settings.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import importlib.util
from pathlib import Path
from typing import Any, Protocol

from packages.config import Settings, get_settings
from packages.data_sources.market_trend import RISK_DISCLAIMER, normalize_symbol


TIGER_SOURCE_NAME = "Tiger Brokers OpenAPI"


class TigerOpenAPIError(RuntimeError):
    """Raised when Tiger OpenAPI data cannot be fetched or configured."""


class TigerQuoteAdapter(Protocol):
    def get_quote(self, symbol: str) -> dict[str, Any]:
        """Return a normalized or SDK-native quote payload for one symbol."""


class TigerKlineAdapter(Protocol):
    def get_kline(
        self, symbol: str, period: str, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """Return SDK-native or normalized historical K-line rows."""


@dataclass(frozen=True)
class TigerOpenAPIConfig:
    tiger_id: str | None
    account: str | None
    license: str | None
    private_key_path: str | None
    env: str = "sandbox"

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "TigerOpenAPIConfig":
        settings = settings or get_settings()
        return cls(
            tiger_id=settings.tiger_id,
            account=settings.tiger_account,
            license=settings.tiger_license,
            private_key_path=settings.tiger_private_key_path,
            env=settings.tiger_env,
        )

    @property
    def missing_fields(self) -> list[str]:
        missing = []
        if not self.tiger_id:
            missing.append("TIGER_ID")
        if not self.account:
            missing.append("TIGER_ACCOUNT")
        if not self.license:
            missing.append("TIGER_LICENSE")
        if not self.private_key_path:
            missing.append("TIGER_PRIVATE_KEY_PATH")
        elif not Path(self.private_key_path).expanduser().exists():
            missing.append("TIGER_PRIVATE_KEY_PATH(file_not_found)")
        return missing

    @property
    def is_configured(self) -> bool:
        return not self.missing_fields


@dataclass(frozen=True)
class TigerIntegrationStatus:
    configured: bool
    sdk_available: bool
    env: str
    missing_fields: list[str]
    source: str
    trading_enabled: bool
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "configured": self.configured,
            "sdk_available": self.sdk_available,
            "env": self.env,
            "missing_fields": self.missing_fields,
            "source": self.source,
            "trading_enabled": self.trading_enabled,
            "risk_disclaimer": self.risk_disclaimer,
        }


@dataclass(frozen=True)
class TigerQuote:
    symbol: str
    price: float | None
    latest_point_price: float | None
    change: float | None
    change_percent: float | None
    currency: str | None
    exchange_name: str | None
    source: str
    analysis_time: str
    raw: dict[str, Any]
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "price": self.price,
            "latest_point_price": self.latest_point_price,
            "change": self.change,
            "change_percent": self.change_percent,
            "currency": self.currency,
            "exchange_name": self.exchange_name,
            "source": self.source,
            "analysis_time": self.analysis_time,
            "raw": self.raw,
            "risk_disclaimer": self.risk_disclaimer,
        }


@dataclass(frozen=True)
class TigerKlinePoint:
    date: str
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: int | None
    amount: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "amount": self.amount,
        }


@dataclass(frozen=True)
class TigerKlineResponse:
    symbol: str
    period: str
    years: int
    start_date: str
    end_date: str
    source: str
    analysis_time: str
    points: list[TigerKlinePoint]
    data_scope: str = "historical_kline_reference"
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "period": self.period,
            "years": self.years,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "source": self.source,
            "analysis_time": self.analysis_time,
            "data_scope": self.data_scope,
            "points": [point.to_dict() for point in self.points],
            "risk_disclaimer": self.risk_disclaimer,
        }


class TigerOpenAPIClient:
    """Read-only Tiger OpenAPI adapter.

    v0.1 deliberately exposes quote/status only. Order placement and automated
    trading are out of scope for OpenStock AI's first phase.
    """

    source_name = TIGER_SOURCE_NAME

    def __init__(
        self,
        config: TigerOpenAPIConfig | None = None,
        quote_adapter: TigerQuoteAdapter | None = None,
        kline_adapter: TigerKlineAdapter | None = None,
    ) -> None:
        self.config = config or TigerOpenAPIConfig.from_settings()
        self.quote_adapter = quote_adapter
        self.kline_adapter = kline_adapter

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "TigerOpenAPIClient":
        return cls(config=TigerOpenAPIConfig.from_settings(settings))

    def status(self) -> TigerIntegrationStatus:
        return TigerIntegrationStatus(
            configured=self.config.is_configured,
            sdk_available=is_tigeropen_sdk_available(),
            env=self.config.env,
            missing_fields=self.config.missing_fields,
            source=self.source_name,
            trading_enabled=False,
        )

    def fetch_quote(self, symbol: str) -> TigerQuote:
        normalized_symbol = normalize_symbol(symbol)
        status = self.status()
        if not status.configured:
            raise TigerOpenAPIError(
                "Tiger OpenAPI is not configured. Set TIGER_ID, TIGER_ACCOUNT, "
                "TIGER_LICENSE and TIGER_PRIVATE_KEY_PATH in .env."
            )
        if not status.sdk_available and self.quote_adapter is None:
            raise TigerOpenAPIError(
                "Tiger OpenAPI SDK is not installed. Install the official tigeropen "
                "package before enabling real Tiger market data."
            )
        adapter = self.quote_adapter
        if adapter is None:
            raise TigerOpenAPIError(
                "Tiger OpenAPI credentials are configured, but no read-only quote "
                "adapter has been wired yet. Use TigerOpenAPIClient(..., quote_adapter=...) "
                "or implement the official SDK adapter in this module."
            )
        payload = adapter.get_quote(normalized_symbol)
        return parse_tiger_quote_payload(payload, normalized_symbol)

    def fetch_kline(
        self,
        symbol: str,
        period: str = "day",
        years: int = 3,
        end_date: date | None = None,
    ) -> TigerKlineResponse:
        normalized_symbol = normalize_symbol(symbol)
        normalized_period = validate_tiger_kline_request(period, years)
        status = self.status()
        if not status.configured:
            raise TigerOpenAPIError(
                "Tiger OpenAPI is not configured. Set TIGER_ID, TIGER_ACCOUNT, "
                "TIGER_LICENSE and TIGER_PRIVATE_KEY_PATH in .env."
            )
        if not status.sdk_available and self.kline_adapter is None:
            raise TigerOpenAPIError(
                "Tiger OpenAPI SDK is not installed. Install the official tigeropen "
                "package before enabling real Tiger historical market data."
            )
        adapter = self.kline_adapter
        if adapter is None:
            raise TigerOpenAPIError(
                "Tiger OpenAPI credentials are configured, but no read-only K-line "
                "adapter has been wired yet. Use TigerOpenAPIClient(..., kline_adapter=...) "
                "or implement the official SDK adapter in this module."
            )

        actual_end = end_date or datetime.now(timezone.utc).date()
        actual_start = actual_end - timedelta(days=365 * years)
        rows = adapter.get_kline(normalized_symbol, normalized_period, actual_start, actual_end)
        return TigerKlineResponse(
            symbol=normalized_symbol,
            period=normalized_period,
            years=years,
            start_date=actual_start.isoformat(),
            end_date=actual_end.isoformat(),
            source=TIGER_SOURCE_NAME,
            analysis_time=datetime.now(timezone.utc).isoformat(),
            points=parse_tiger_kline_payload(rows),
        )


def is_tigeropen_sdk_available() -> bool:
    return importlib.util.find_spec("tigeropen") is not None


def parse_tiger_quote_payload(payload: dict[str, Any], symbol: str) -> TigerQuote:
    price = _first_number(payload, ("price", "latest_price", "latestPrice", "close", "latest"))
    previous_close = _first_number(payload, ("previous_close", "prev_close", "preClose", "prevClose"))
    change = _first_number(payload, ("change", "change_value", "changeValue"))
    change_percent = _first_number(payload, ("change_percent", "change_rate", "changeRate"))

    if change is None and price is not None and previous_close not in (None, 0):
        change = round(price - float(previous_close), 4)
    if change_percent is None and price is not None and previous_close not in (None, 0):
        change_percent = round((price - float(previous_close)) / float(previous_close) * 100, 4)

    return TigerQuote(
        symbol=symbol,
        price=price,
        latest_point_price=price,
        change=change,
        change_percent=change_percent,
        currency=str(payload.get("currency") or "USD"),
        exchange_name=payload.get("exchange") or payload.get("exchange_name") or payload.get("market"),
        source=TIGER_SOURCE_NAME,
        analysis_time=datetime.now(timezone.utc).isoformat(),
        raw=payload,
    )


def validate_tiger_kline_request(period: str, years: int) -> str:
    normalized_period = period.strip().lower()
    supported_periods = {"day", "week", "month"}
    if normalized_period not in supported_periods:
        raise ValueError(f"unsupported Tiger K-line period: {period}")
    if years < 1 or years > 3:
        raise ValueError("Tiger historical reference data supports 1 to 3 years")
    return normalized_period


def parse_tiger_kline_payload(rows: list[dict[str, Any]]) -> list[TigerKlinePoint]:
    points: list[TigerKlinePoint] = []
    for row in rows:
        point_date = _first_text(row, ("date", "time", "timestamp", "begin_time", "beginTime"))
        close = _first_number(row, ("close", "close_price", "closePrice"))
        if not point_date or close is None:
            continue
        points.append(
            TigerKlinePoint(
                date=_normalize_kline_date(point_date),
                open=_first_number(row, ("open", "open_price", "openPrice")),
                high=_first_number(row, ("high", "high_price", "highPrice")),
                low=_first_number(row, ("low", "low_price", "lowPrice")),
                close=close,
                volume=_first_int(row, ("volume", "vol")),
                amount=_first_number(row, ("amount", "turnover", "trade_amount", "tradeAmount")),
            )
        )
    return sorted(points, key=lambda point: point.date)


def _first_text(payload: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        return str(value)
    return None


def _first_int(payload: dict[str, Any], keys: tuple[str, ...]) -> int | None:
    number = _first_number(payload, keys)
    if number is None:
        return None
    return int(number)


def _normalize_kline_date(value: str) -> str:
    if value.isdigit():
        timestamp = int(value)
        if timestamp > 10_000_000_000:
            timestamp = timestamp // 1000
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()
    return value[:10]


def _first_number(payload: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        try:
            return round(float(value), 4)
        except (TypeError, ValueError):
            continue
    return None
