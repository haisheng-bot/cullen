from __future__ import annotations

import statistics
from datetime import datetime, timezone

from packages.backtesting.allocation import apply_weight_constraints, equal_weight, market_cap_weighted
from packages.backtesting.performance import TRADING_DAYS_PER_YEAR, periodic_returns
from packages.portfolio_optimizer.schemas import OPTIMIZER_METHODS, PortfolioOptimizerResult


def optimize_portfolio(
    *,
    method: str,
    closes_by_symbol: dict[str, list[tuple[str, float]]],
    market_caps: dict[str, float | None] | None = None,
    max_position_weight: float = 0.25,
    min_cash_weight: float = 0.10,
) -> PortfolioOptimizerResult:
    if method not in OPTIMIZER_METHODS:
        raise ValueError(f"unsupported optimizer method: {method}")
    symbols = sorted(closes_by_symbol)
    close_values = {symbol: [close for _, close in closes] for symbol, closes in closes_by_symbol.items()}
    if method == "equal_weight":
        raw = equal_weight(symbols)
    elif method == "market_cap":
        raw = market_cap_weighted(market_caps or {})
    elif method == "minimum_variance":
        raw = _inverse_variance_weights(close_values)
    else:
        raw = _inverse_volatility_weights(close_values)

    constrained = apply_weight_constraints(raw, max_position_weight, min_cash_weight)
    invested = sum(constrained.values())
    risk = _portfolio_volatility_percent(close_values, constrained)
    return PortfolioOptimizerResult(
        method=method,
        symbols=symbols,
        target_weights={symbol: round(constrained.get(symbol, 0.0), 6) for symbol in symbols},
        cash_weight=round(max(0.0, 1.0 - invested), 6),
        max_position_weight=max_position_weight,
        expected_risk_percent=round(risk, 2) if risk is not None else None,
        notes=_optimizer_notes(method),
        source="OpenStock AI Portfolio Optimizer v0.1",
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def _inverse_variance_weights(closes_by_symbol: dict[str, list[float]]) -> dict[str, float]:
    values = {}
    for symbol, closes in closes_by_symbol.items():
        returns = periodic_returns(closes)
        variance = statistics.variance(returns) if len(returns) >= 2 else None
        values[symbol] = 1 / variance if variance and variance > 0 else 1.0
    return _normalize(values)


def _inverse_volatility_weights(closes_by_symbol: dict[str, list[float]]) -> dict[str, float]:
    values = {}
    for symbol, closes in closes_by_symbol.items():
        returns = periodic_returns(closes)
        volatility = statistics.stdev(returns) if len(returns) >= 2 else None
        values[symbol] = 1 / volatility if volatility and volatility > 0 else 1.0
    return _normalize(values)


def _normalize(values: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, value) for value in values.values())
    if total <= 0:
        return equal_weight(sorted(values))
    return {symbol: max(0.0, value) / total for symbol, value in values.items()}


def _portfolio_volatility_percent(
    closes_by_symbol: dict[str, list[float]], weights: dict[str, float]
) -> float | None:
    returns_by_symbol = {symbol: periodic_returns(closes) for symbol, closes in closes_by_symbol.items()}
    length = min((len(values) for values in returns_by_symbol.values()), default=0)
    if length < 2:
        return None
    portfolio_returns = []
    for index in range(length):
        portfolio_returns.append(
            sum(returns_by_symbol[symbol][index] * weights.get(symbol, 0.0) for symbol in returns_by_symbol)
        )
    if len(portfolio_returns) < 2:
        return None
    return statistics.stdev(portfolio_returns) * (TRADING_DAYS_PER_YEAR ** 0.5) * 100


def _optimizer_notes(method: str) -> list[str]:
    notes = {
        "equal_weight": "等权重基线，适合作为其他优化方法的对照。",
        "market_cap": "市值权重使用最新可得股数和价格估算，不是点时间历史市值。",
        "minimum_variance": "Minimum Variance v0.1 使用逆方差近似，后续可接协方差矩阵求解器。",
        "risk_parity": "Risk Parity v0.1 使用逆波动率近似，后续可接风险贡献迭代求解。",
    }
    return [notes[method], "本结果仅用于投资研究辅助，不构成任何投资建议。"]
