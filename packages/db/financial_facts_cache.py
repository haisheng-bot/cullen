from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.data_sources.sec_financials import AnnualFinancials
from packages.db.models import FinancialFactsCache

CACHE_TTL = timedelta(hours=24)


class _FinancialsClient(Protocol):
    def fetch_annual_series(self, symbol: str) -> list[AnnualFinancials]: ...


def get_or_fetch_annual_series(
    session: Session, financials_client: _FinancialsClient, symbol: str
) -> list[AnnualFinancials]:
    """Every fiscal year's `AnnualFinancials` for `symbol` (with `filed_date`
    populated), using a fresh cache row if one exists, otherwise fetching
    from `financials_client` and caching the result. Mirrors
    `packages/db/price_history_cache.py::get_or_fetch_closes`.
    """
    cached = _get_fresh_cache_row(session, symbol)
    if cached is not None:
        return [AnnualFinancials(**row) for row in cached.annual_series]

    series = financials_client.fetch_annual_series(symbol)
    annual_series = [dataclasses.asdict(item) for item in series]
    session.add(FinancialFactsCache(symbol=symbol.upper(), annual_series=annual_series))
    session.flush()
    return series


def _get_fresh_cache_row(session: Session, symbol: str) -> FinancialFactsCache | None:
    statement = (
        select(FinancialFactsCache)
        .where(FinancialFactsCache.symbol == symbol.upper())
        .order_by(FinancialFactsCache.fetched_at.desc())
        .limit(1)
    )
    row = session.scalars(statement).first()
    if row is None:
        return None
    fetched_at = row.fetched_at if row.fetched_at.tzinfo else row.fetched_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - fetched_at > CACHE_TTL:
        return None
    return row
