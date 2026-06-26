from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.db.models import Portfolio

DEFAULT_PORTFOLIOS: dict[str, list[str]] = {
    "Core Watch": ["AAPL", "MSFT", "NVDA"],
    "Momentum": [],
    "AI Theme": [],
    "Semiconductor": [],
    "Risk Hedge": [],
}


def ensure_default_portfolios(session: Session) -> None:
    """Seed the default named watchlists on first read. No-op for names
    that already exist, so it's safe to call on every `/portfolios` request.
    """
    existing_names = set(session.scalars(select(Portfolio.name)))
    for name, symbols in DEFAULT_PORTFOLIOS.items():
        if name not in existing_names:
            session.add(Portfolio(name=name, symbols=list(symbols)))
    session.flush()


def list_portfolios(session: Session) -> list[Portfolio]:
    statement = select(Portfolio).order_by(Portfolio.id)
    return list(session.scalars(statement))


def add_symbol(session: Session, name: str, symbol: str) -> Portfolio:
    """Add `symbol` to the named portfolio, creating the portfolio if it
    doesn't exist yet. Idempotent: adding the same symbol twice is a no-op.
    """
    portfolio = session.scalar(select(Portfolio).where(Portfolio.name == name))
    if portfolio is None:
        portfolio = Portfolio(name=name, symbols=[])
        session.add(portfolio)
    if symbol not in portfolio.symbols:
        portfolio.symbols = [*portfolio.symbols, symbol]
    session.flush()
    return portfolio


def remove_symbol(session: Session, name: str, symbol: str) -> Portfolio | None:
    """Remove `symbol` from the named portfolio. Returns None if the
    portfolio doesn't exist.
    """
    portfolio = session.scalar(select(Portfolio).where(Portfolio.name == name))
    if portfolio is None:
        return None
    portfolio.symbols = [item for item in portfolio.symbols if item != symbol]
    session.flush()
    return portfolio
