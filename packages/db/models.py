from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AuditLog(Base):
    """Persisted record of every AI model call, per MODEL_STANDARD.md section 12."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    input_summary: Mapped[str] = mapped_column(Text, nullable=False)
    output_summary: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list] = mapped_column(JSON, default=list)
    token_usage: Mapped[dict] = mapped_column(JSON, default=dict)
    cost_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class StockScore(Base):
    """One row per candidate per screening run, so score history is
    queryable over time (`/stocks/{symbol}/score-history`). This is what
    turns AI 选股 from a stateless calculation into something with a
    track record per docs/product/mvp-roadmap.md M4.
    """

    __tablename__ = "stock_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    sector: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(16), nullable=False)
    factors: Mapped[list] = mapped_column(JSON, default=list)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    risks: Mapped[list] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(32), nullable=False)
    screened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )


class PriceHistoryCache(Base):
    """Cached daily OHLC-close history per symbol, so a multi-year
    Portfolio Strategy Engine backtest doesn't re-fetch the same symbol
    from Yahoo Finance on every run (see packages/db/price_history_cache.py).
    """

    __tablename__ = "price_history_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    range: Mapped[str] = mapped_column(String(8), nullable=False)
    interval: Mapped[str] = mapped_column(String(8), nullable=False)
    points: Mapped[list] = mapped_column(JSON, default=list)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class FinancialFactsCache(Base):
    """Cached point-in-time annual financials series per symbol (every
    fiscal year, with `filed_date`), so a `signal_mode="ai_score"` backtest
    doesn't re-fetch SEC EDGAR company facts on every run (see
    packages/db/financial_facts_cache.py).
    """

    __tablename__ = "financial_facts_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    annual_series: Mapped[list] = mapped_column(JSON, default=list)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class BacktestRun(Base):
    """One row per Portfolio Strategy Engine backtest run
    (`POST /backtests/run`), per docs/standards/PORTFOLIO_STRATEGY_STANDARD.md.
    """

    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_name: Mapped[str] = mapped_column(String(128), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
