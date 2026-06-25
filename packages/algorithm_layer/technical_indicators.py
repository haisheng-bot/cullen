"""Pure technical indicator functions for the Algorithm Layer.

No data source or model calls here — these take plain lists of daily
closes so they stay independently testable, per
docs/standards/ALGORITHM_STANDARD.md section 8.
"""
from __future__ import annotations

MIN_CLOSES_FOR_INDICATORS = 25


def calculate_sma(closes: list[float], period: int) -> float | None:
    if len(closes) < period:
        return None
    window = closes[-period:]
    return sum(window) / period


def calculate_sma_series(closes: list[float], period: int) -> list[float]:
    """SMA value ending at each index from `period - 1` onward."""
    if len(closes) < period:
        return []
    return [sum(closes[index - period + 1 : index + 1]) / period for index in range(period - 1, len(closes))]


def calculate_rsi(closes: list[float], period: int = 14) -> float | None:
    """RSI over the last `period` price changes, using a simple (not
    Wilder-smoothed) average of gains/losses for explainability.
    """
    if len(closes) < period + 1:
        return None

    changes = [closes[i] - closes[i - 1] for i in range(len(closes) - period, len(closes))]
    gains = [change for change in changes if change > 0]
    losses = [-change for change in changes if change < 0]

    average_gain = sum(gains) / period
    average_loss = sum(losses) / period

    if average_loss == 0:
        return 100.0
    relative_strength = average_gain / average_loss
    return 100 - (100 / (1 + relative_strength))


def detect_ma_cross(closes: list[float], short_period: int = 5, long_period: int = 20) -> str:
    """Return "golden_cross", "death_cross", "bullish", "bearish", or "flat"."""
    short_series = calculate_sma_series(closes, short_period)
    long_series = calculate_sma_series(closes, long_period)
    if len(short_series) < 2 or len(long_series) < 2:
        return "flat"

    # Align the two series on the same trailing index range.
    short_series = short_series[-len(long_series) :] if len(short_series) > len(long_series) else short_series
    long_series = long_series[-len(short_series) :]

    previous_short, latest_short = short_series[-2], short_series[-1]
    previous_long, latest_long = long_series[-2], long_series[-1]

    if previous_short <= previous_long and latest_short > latest_long:
        return "golden_cross"
    if previous_short >= previous_long and latest_short < latest_long:
        return "death_cross"
    if latest_short > latest_long:
        return "bullish"
    if latest_short < latest_long:
        return "bearish"
    return "flat"


def calculate_momentum_percent(closes: list[float], lookback: int = 10) -> float | None:
    if len(closes) < lookback + 1:
        return None
    baseline = closes[-lookback - 1]
    if baseline == 0:
        return None
    return (closes[-1] - baseline) / baseline * 100
