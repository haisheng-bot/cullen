from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.db.models import PriceHistoryCache

CACHE_TTL = timedelta(hours=24)


class _HistoryClient(Protocol):
    def fetch_history(self, symbol: str, range_: str, interval: str): ...


def get_or_fetch_closes(
    session: Session, history_client: _HistoryClient, symbol: str, range_: str = "10y", interval: str = "1d"
) -> list[tuple[str, float]]:
    """Returns (date_iso, close) pairs for `symbol`, using a same-day cache
    row if one exists, otherwise fetching from `history_client` and caching
    the result. This is what makes repeated/multi-symbol backtest runs fast
    without hammering Yahoo Finance.
    """
    cached = _get_fresh_cache_row(session, symbol, range_, interval)
    if cached is not None:
        return [(point["date"], point["close"]) for point in cached.points]

    history = history_client.fetch_history(symbol, range_=range_, interval=interval)
    points = [{"date": point.date, "close": point.close} for point in history.points]
    session.add(
        PriceHistoryCache(symbol=symbol.upper(), range=range_, interval=interval, points=points)
    )
    session.flush()
    return [(point["date"], point["close"]) for point in points]


def _get_fresh_cache_row(
    session: Session, symbol: str, range_: str, interval: str
) -> PriceHistoryCache | None:
    statement = (
        select(PriceHistoryCache)
        .where(
            PriceHistoryCache.symbol == symbol.upper(),
            PriceHistoryCache.range == range_,
            PriceHistoryCache.interval == interval,
        )
        .order_by(PriceHistoryCache.fetched_at.desc())
        .limit(1)
    )
    row = session.scalars(statement).first()
    if row is None:
        return None
    fetched_at = row.fetched_at if row.fetched_at.tzinfo else row.fetched_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - fetched_at > CACHE_TTL:
        return None
    return row
