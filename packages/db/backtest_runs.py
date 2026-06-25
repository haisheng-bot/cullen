from __future__ import annotations

from sqlalchemy.orm import Session

from packages.backtesting.schemas import BacktestResult, StrategyConfig
from packages.db.models import BacktestRun


def write_backtest_run(
    session: Session, config: StrategyConfig, result: BacktestResult
) -> BacktestRun:
    """Persist one /backtests/run call. No read helper yet — there's no GET
    endpoint to consume it until a frontend needs to revisit past runs; add
    one alongside `get_backtest_run` when that's actually needed.
    """
    record = BacktestRun(
        strategy_name=config.strategy_name,
        config=config.to_dict(),
        result=result.to_dict(),
    )
    session.add(record)
    session.flush()
    return record
