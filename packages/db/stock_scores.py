from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.db.models import StockScore
from packages.workflow_layer.schemas import ScreeningResult


def write_screening_result(session: Session, result: ScreeningResult) -> list[StockScore]:
    """Persist every scored candidate from a screening run as one row each,
    so later runs can be compared against history for the same symbol.
    """
    records = [
        StockScore(
            symbol=candidate.symbol,
            name=candidate.name,
            sector=candidate.sector,
            rank=candidate.rank,
            total_score=candidate.total_score,
            recommendation=candidate.recommendation,
            factors=candidate.factors,
            reasons=candidate.reasons,
            risks=candidate.risks,
            source=candidate.source,
            algorithm_version=candidate.algorithm_version,
        )
        for candidate in result.candidates
    ]
    session.add_all(records)
    session.flush()
    return records


def get_score_history(session: Session, symbol: str, limit: int = 30) -> list[StockScore]:
    """Most recent screened scores for a symbol, newest first."""
    statement = (
        select(StockScore)
        .where(StockScore.symbol == symbol.upper())
        .order_by(StockScore.screened_at.desc(), StockScore.id.desc())
        .limit(limit)
    )
    return list(session.scalars(statement))
