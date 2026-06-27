from __future__ import annotations

import statistics
from datetime import datetime, timezone

from packages.backtesting.performance import (
    TRADING_DAYS_PER_YEAR,
    alpha_beta_percent,
    max_drawdown_percent,
    periodic_returns,
)
from packages.risk_engine.schemas import PortfolioRiskReport


def analyze_portfolio_risk(
    closes_by_symbol: dict[str, list[tuple[str, float]]],
    *,
    weights: dict[str, float] | None = None,
    benchmark_closes: list[tuple[str, float]] | None = None,
    sector_map: dict[str, str] | None = None,
) -> PortfolioRiskReport:
    symbols = sorted(closes_by_symbol)
    normalized_weights = _normalize_weights(symbols, weights or {})
    returns_by_symbol = {
        symbol: periodic_returns([close for _, close in closes])
        for symbol, closes in closes_by_symbol.items()
    }
    portfolio_returns = _portfolio_returns(returns_by_symbol, normalized_weights)
    portfolio_values = _growth_curve(portfolio_returns)
    benchmark_returns = periodic_returns([close for _, close in benchmark_closes]) if benchmark_closes else []
    _, beta = alpha_beta_percent(portfolio_returns, benchmark_returns, TRADING_DAYS_PER_YEAR)

    volatility = None
    if len(portfolio_returns) >= 2:
        volatility = statistics.stdev(portfolio_returns) * (TRADING_DAYS_PER_YEAR ** 0.5) * 100

    return PortfolioRiskReport(
        symbols=symbols,
        weights=normalized_weights,
        volatility_percent=round(volatility, 2) if volatility is not None else None,
        beta=round(beta, 4) if beta is not None else None,
        max_drawdown_percent=round(max_drawdown_percent(portfolio_values), 2),
        average_correlation=_average_correlation(returns_by_symbol),
        concentration_percent=round(max(normalized_weights.values(), default=0.0) * 100, 2),
        sector_exposure=_sector_exposure(normalized_weights, sector_map or {}),
        source="OpenStock AI Risk Engine v0.1",
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def _normalize_weights(symbols: list[str], weights: dict[str, float]) -> dict[str, float]:
    if not symbols:
        return {}
    selected = {symbol: max(0.0, weights.get(symbol, 0.0)) for symbol in symbols}
    total = sum(selected.values())
    if total <= 0:
        equal = 1 / len(symbols)
        return {symbol: equal for symbol in symbols}
    return {symbol: weight / total for symbol, weight in selected.items()}


def _portfolio_returns(returns_by_symbol: dict[str, list[float]], weights: dict[str, float]) -> list[float]:
    if not returns_by_symbol:
        return []
    length = min((len(values) for values in returns_by_symbol.values()), default=0)
    output = []
    for index in range(length):
        output.append(
            sum(returns_by_symbol[symbol][index] * weights.get(symbol, 0.0) for symbol in returns_by_symbol)
        )
    return output


def _growth_curve(returns: list[float]) -> list[float]:
    value = 100.0
    values = [value]
    for item in returns:
        value *= 1 + item
        values.append(value)
    return values


def _average_correlation(returns_by_symbol: dict[str, list[float]]) -> float | None:
    symbols = sorted(returns_by_symbol)
    correlations = []
    for left_index, left in enumerate(symbols):
        for right in symbols[left_index + 1 :]:
            length = min(len(returns_by_symbol[left]), len(returns_by_symbol[right]))
            if length < 2:
                continue
            left_returns = returns_by_symbol[left][:length]
            right_returns = returns_by_symbol[right][:length]
            left_std = statistics.stdev(left_returns)
            right_std = statistics.stdev(right_returns)
            if left_std == 0 or right_std == 0:
                continue
            correlations.append(
                statistics.covariance(left_returns, right_returns) / (left_std * right_std)
            )
    if not correlations:
        return None
    return round(statistics.mean(correlations), 4)


def _sector_exposure(weights: dict[str, float], sector_map: dict[str, str]) -> dict[str, float]:
    exposures: dict[str, float] = {}
    for symbol, weight in weights.items():
        sector = sector_map.get(symbol) or "Unknown"
        exposures[sector] = exposures.get(sector, 0.0) + weight * 100
    return {sector: round(value, 2) for sector, value in sorted(exposures.items())}
