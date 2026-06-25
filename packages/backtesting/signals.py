"""Signal Engine: price/technical-only signals for the Portfolio Strategy
Engine. Wraps packages.algorithm_layer.technical_indicators instead of
duplicating its formulas, so a backtested signal and the live
recommendation's `technical` factor are scored identically.
"""
from __future__ import annotations

from packages.algorithm_layer.technical_indicators import (
    MIN_CLOSES_FOR_INDICATORS,
    calculate_momentum_percent,
    detect_ma_cross,
    technical_indicator_score,
)

NEUTRAL_SCORE = 50

_MA_CROSS_MATCHES: dict[str, set[str]] = {
    "golden_cross": {"golden_cross"},
    "bullish": {"bullish"},
    "golden_or_bullish": {"golden_cross", "bullish"},
    "death_cross": {"death_cross"},
    "bearish": {"bearish"},
    "death_or_bearish": {"death_cross", "bearish"},
}


def technical_score(closes: list[float]) -> tuple[int, str]:
    """0-100 technical score as of the last close in `closes`. Falls back
    to a neutral score when there isn't enough daily history yet (e.g.
    near the start of the backtest window or a recent IPO).
    """
    if len(closes) < MIN_CLOSES_FOR_INDICATORS:
        return NEUTRAL_SCORE, (
            f"日线数据不足（需 {MIN_CLOSES_FOR_INDICATORS} 个交易日以上），暂以中性分计入"
        )
    return technical_indicator_score(closes)


def momentum_percent(closes: list[float], lookback: int = 10) -> float | None:
    return calculate_momentum_percent(closes, lookback=lookback)


def ma_cross_state(closes: list[float]) -> str:
    return detect_ma_cross(closes, short_period=5, long_period=20)


def matches_ma_cross_filter(cross_state: str, filter_value: str | None) -> bool:
    """`filter_value` is one of MA_CROSS_FILTERS (e.g. "golden_or_bullish")
    or None, meaning the filter is disabled (always matches).
    """
    if filter_value is None:
        return True
    allowed_states = _MA_CROSS_MATCHES.get(filter_value)
    if allowed_states is None:
        raise ValueError(f"unsupported ma_cross filter: {filter_value}")
    return cross_state in allowed_states
