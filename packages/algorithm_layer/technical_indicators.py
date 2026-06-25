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


CROSS_LABELS = {
    "golden_cross": "金叉",
    "death_cross": "死叉",
    "bullish": "多头排列",
    "bearish": "空头排列",
    "flat": "走势平缓",
}

CROSS_SCORES = {
    "golden_cross": 80,
    "bullish": 65,
    "flat": 50,
    "bearish": 35,
    "death_cross": 20,
}


def trend_score(change_percent: float) -> int:
    """Maps a % price change to a 0-100 score, centered on 50 at 0%."""
    return max(0, min(100, round(60 + change_percent * 8)))


def rsi_score(rsi: float) -> int:
    """Maps RSI-14 to a 0-100 score. 30-70 is treated as the healthy
    momentum band (linear around neutral 50); above 70 is capped to reflect
    overbought pullback risk, below 30 is floored to reflect oversold risk.
    """
    if rsi >= 80:
        return 45
    if rsi >= 70:
        return 65
    if rsi >= 55:
        return round(50 + (rsi - 55) * (65 - 50) / (70 - 55))
    if rsi >= 40:
        return round(35 + (rsi - 40) * (50 - 35) / (55 - 40))
    if rsi >= 20:
        return round(20 + (rsi - 20) * (35 - 20) / (40 - 20))
    return 20


def technical_indicator_score(closes: list[float]) -> tuple[int, str]:
    """Composite 0-100 technical score: 10-day momentum (40%) + RSI-14 (30%)
    + MA(5/20) cross state (30%). Shared by the live Algorithm Layer
    (algorithm-v0.2.1+) and the Portfolio Strategy Engine's Signal Engine
    (`packages/backtesting/signals.py`) so both score technical strength the
    same way. Requires at least `MIN_CLOSES_FOR_INDICATORS` daily closes —
    callers should check length first (or catch the resulting `IndexError`/
    `ValueError` from the underlying indicator calls) and fall back to a
    neutral score otherwise.
    """
    momentum_percent = calculate_momentum_percent(closes, lookback=10) or 0.0
    rsi = calculate_rsi(closes, period=14) or 50.0
    cross_state = detect_ma_cross(closes, short_period=5, long_period=20)

    momentum_component = trend_score(momentum_percent)
    rsi_component = rsi_score(rsi)
    cross_component = CROSS_SCORES[cross_state]

    composite = round(momentum_component * 0.4 + rsi_component * 0.3 + cross_component * 0.3)
    explanation = (
        f"动量(10日) {momentum_percent:+.2f}%，RSI(14) {rsi:.1f}，"
        f"均线(5/20)状态：{CROSS_LABELS[cross_state]}"
    )
    return max(0, min(100, composite)), explanation
