"""Position Sizing: turns a set of eligible symbols into target portfolio
weights (summing to 1.0 before cap/cash-floor constraints are applied).
"""
from __future__ import annotations

import statistics

from packages.backtesting.schemas import ALLOCATION_METHODS


def equal_weight(symbols: list[str]) -> dict[str, float]:
    if not symbols:
        return {}
    weight = 1.0 / len(symbols)
    return {symbol: weight for symbol in symbols}


def volatility_weighted(closes_by_symbol: dict[str, list[float]], lookback: int = 20) -> dict[str, float]:
    """Inverse-volatility weighting: lower trailing volatility gets more
    weight (a simple risk-parity proxy computable from price data alone).
    """
    if not closes_by_symbol:
        return {}
    inverse_vol = {}
    for symbol, closes in closes_by_symbol.items():
        vol = _trailing_volatility(closes, lookback)
        inverse_vol[symbol] = 1.0 / vol if vol and vol > 0 else 1.0
    total = sum(inverse_vol.values())
    if total <= 0:
        return equal_weight(list(closes_by_symbol.keys()))
    return {symbol: value / total for symbol, value in inverse_vol.items()}


def technical_score_weighted(scores_by_symbol: dict[str, int]) -> dict[str, float]:
    if not scores_by_symbol:
        return {}
    positive_scores = {symbol: max(score, 0) for symbol, score in scores_by_symbol.items()}
    total = sum(positive_scores.values())
    if total <= 0:
        return equal_weight(list(scores_by_symbol.keys()))
    return {symbol: score / total for symbol, score in positive_scores.items()}


def market_cap_weighted(market_caps_by_symbol: dict[str, float | None]) -> dict[str, float]:
    if not market_caps_by_symbol:
        return {}
    positive_caps = {
        symbol: cap for symbol, cap in market_caps_by_symbol.items() if cap and cap > 0
    }
    total = sum(positive_caps.values())
    if total <= 0:
        return equal_weight(list(market_caps_by_symbol.keys()))
    # Symbols with unknown market cap fall back to a zero weight rather than
    # breaking the whole allocation; this is a documented approximation
    # (latest known shares outstanding, not point-in-time).
    return {symbol: positive_caps.get(symbol, 0.0) / total for symbol in market_caps_by_symbol}


def apply_weight_constraints(
    weights: dict[str, float], max_position_weight: float, min_cash_weight: float
) -> dict[str, float]:
    """Scales `weights` (assumed to sum to ~1.0) down to the investable
    fraction `1 - min_cash_weight`, then iteratively caps any symbol above
    `max_position_weight` and redistributes the excess proportionally
    among the remaining uncapped symbols. If the cap is too tight for the
    number of symbols to absorb the full investable fraction, the leftover
    is simply left uninvested (effectively more cash than `min_cash_weight`
    requested) rather than violating the cap.
    """
    if not weights:
        return {}

    total = sum(weights.values())
    if total <= 0:
        return {symbol: 0.0 for symbol in weights}

    investable = max(0.0, 1.0 - min_cash_weight)
    target = {symbol: (weight / total) * investable for symbol, weight in weights.items()}

    capped: set[str] = set()
    for _ in range(len(target) + 1):
        over_cap = {
            symbol: weight
            for symbol, weight in target.items()
            if symbol not in capped and weight > max_position_weight
        }
        if not over_cap:
            break

        excess = sum(weight - max_position_weight for weight in over_cap.values())
        for symbol in over_cap:
            target[symbol] = max_position_weight
            capped.add(symbol)

        remaining = {symbol: weight for symbol, weight in target.items() if symbol not in capped}
        remaining_total = sum(remaining.values())
        if remaining_total <= 0:
            break
        for symbol in remaining:
            target[symbol] += excess * (remaining[symbol] / remaining_total)

    return target


def compute_target_weights(
    method: str,
    symbols: list[str],
    *,
    closes_by_symbol: dict[str, list[float]] | None = None,
    technical_scores: dict[str, int] | None = None,
    market_caps: dict[str, float | None] | None = None,
) -> dict[str, float]:
    if method not in ALLOCATION_METHODS:
        raise ValueError(f"unsupported allocation method: {method}")
    if method == "equal_weight":
        return equal_weight(symbols)
    if method == "volatility_weighted":
        return volatility_weighted(closes_by_symbol or {})
    if method == "technical_score_weighted":
        return technical_score_weighted(technical_scores or {})
    return market_cap_weighted(market_caps or {})


def _trailing_volatility(closes: list[float], lookback: int) -> float | None:
    if len(closes) < lookback + 1:
        return None
    window = closes[-lookback - 1 :]
    returns = [
        (window[i] - window[i - 1]) / window[i - 1]
        for i in range(1, len(window))
        if window[i - 1] != 0
    ]
    if len(returns) < 2:
        return None
    return statistics.pstdev(returns)
