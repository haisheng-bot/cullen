from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.db.models import Strategy


def list_strategies(session: Session) -> list[Strategy]:
    statement = select(Strategy).order_by(Strategy.id)
    return list(session.scalars(statement))


def get_strategy(session: Session, name: str) -> Strategy | None:
    return session.scalar(select(Strategy).where(Strategy.name == name))


def save_strategy(
    session: Session,
    name: str,
    preferences: dict,
    constraints: dict,
) -> Strategy:
    strategy = get_strategy(session, name)
    if strategy is None:
        strategy = Strategy(name=name)
        session.add(strategy)
    strategy.preferences = dict(preferences)
    strategy.constraints = dict(constraints)
    session.flush()
    return strategy


def delete_strategy(session: Session, name: str) -> bool:
    strategy = get_strategy(session, name)
    if strategy is None:
        return False
    session.delete(strategy)
    session.flush()
    return True
