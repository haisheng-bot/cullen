"""Performance Evaluator: turns an equity curve + trade history into the
standard backtest metrics (total/annualized return, max drawdown, Sharpe,
win rate, alpha/beta vs. a benchmark).
"""
from __future__ import annotations

import statistics
from datetime import date

TRADING_DAYS_PER_YEAR = 252


def total_return_percent(initial_value: float, final_value: float) -> float:
    if initial_value <= 0:
        return 0.0
    return (final_value - initial_value) / initial_value * 100


def annualized_return_percent(total_return_pct: float, start_date: str, end_date: str) -> float:
    num_days = (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days
    if num_days <= 0:
        return 0.0
    growth = 1 + total_return_pct / 100
    if growth <= 0:
        # Total loss or worse: CAGR is undefined as a real growth rate.
        return -100.0
    years = num_days / 365.25
    return (growth ** (1 / years) - 1) * 100


def max_drawdown_percent(values: list[float]) -> float:
    if not values:
        return 0.0
    peak = values[0]
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        if peak <= 0:
            continue
        drawdown = (peak - value) / peak
        worst = max(worst, drawdown)
    return worst * 100


def periodic_returns(values: list[float]) -> list[float]:
    """Simple period-over-period % change (e.g. daily or monthly)."""
    returns = []
    for previous, current in zip(values, values[1:]):
        if previous != 0:
            returns.append((current - previous) / previous)
    return returns


def sharpe_ratio(
    returns: list[float], periods_per_year: int, risk_free_rate_annual: float = 0.0
) -> float | None:
    if len(returns) < 2:
        return None
    risk_free_per_period = risk_free_rate_annual / periods_per_year
    excess_returns = [r - risk_free_per_period for r in returns]
    average_excess = statistics.mean(excess_returns)
    volatility = statistics.stdev(excess_returns)
    if volatility == 0:
        return None
    return average_excess / volatility * (periods_per_year ** 0.5)


def win_rate_percent(trade_pnls: list[float]) -> float | None:
    if not trade_pnls:
        return None
    wins = sum(1 for pnl in trade_pnls if pnl > 0)
    return wins / len(trade_pnls) * 100


def alpha_beta_percent(
    portfolio_returns: list[float], benchmark_returns: list[float], periods_per_year: int
) -> tuple[float | None, float | None]:
    """Alpha is annualized (%); beta is unitless. Both None if there isn't
    enough overlapping return history or the benchmark has zero variance.
    """
    paired = list(zip(portfolio_returns, benchmark_returns))
    if len(paired) < 2:
        return None, None
    portfolio_aligned = [p for p, _ in paired]
    benchmark_aligned = [b for _, b in paired]

    benchmark_variance = statistics.variance(benchmark_aligned)
    if benchmark_variance == 0:
        return None, None

    beta = statistics.covariance(portfolio_aligned, benchmark_aligned) / benchmark_variance
    alpha_per_period = statistics.mean(portfolio_aligned) - beta * statistics.mean(benchmark_aligned)
    alpha_annual_percent = ((1 + alpha_per_period) ** periods_per_year - 1) * 100
    return alpha_annual_percent, beta


def best_worst_contributor(
    contributions: list[tuple[str, float]],
) -> tuple[str | None, str | None]:
    """`contributions` is a list of (symbol, pnl_cash). Returns
    (best_symbol, worst_symbol), either None if there are no contributions.
    """
    if not contributions:
        return None, None
    best = max(contributions, key=lambda item: item[1])
    worst = min(contributions, key=lambda item: item[1])
    return best[0], worst[0]
