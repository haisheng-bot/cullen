"""Signal Engine: price/technical-only signals for the Portfolio Strategy
Engine. Wraps packages.algorithm_layer.technical_indicators instead of
duplicating its formulas, so a backtested signal and the live
recommendation's `technical` factor are scored identically.
"""
from __future__ import annotations

from packages.algorithm_layer.financial_factors import fundamentals_score, growth_score, valuation_score
from packages.algorithm_layer.schemas import FinancialFactorsInput
from packages.algorithm_layer.technical_indicators import (
    MIN_CLOSES_FOR_INDICATORS,
    calculate_momentum_percent,
    detect_ma_cross,
    technical_indicator_score,
    volatility_risk_score,
)
from packages.data_sources.sec_financials import AnnualFinancials

NEUTRAL_SCORE = 50

# algorithm-v0.3's weights (fundamentals .30 / growth .20 / valuation .20 /
# technical .10 / news_sentiment .10 / volatility_risk .10) with
# news_sentiment dropped (no historical news archive exists to backtest it
# without lookahead bias — see docs/standards/PORTFOLIO_STRATEGY_STANDARD.md)
# and the rest renormalized to sum to 1.0.
AI_SCORE_WEIGHTS = {
    "fundamentals": 1 / 3,
    "growth": 2 / 9,
    "valuation": 2 / 9,
    "technical": 1 / 9,
    "volatility_risk": 1 / 9,
}

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


def select_financials_as_of(
    series: list[AnnualFinancials], as_of_date: str
) -> tuple[AnnualFinancials | None, AnnualFinancials | None]:
    """The (latest, previous) fiscal-year snapshots actually known on
    `as_of_date` — entries with no `filed_date`, or `filed_date` after
    `as_of_date`, are excluded. This is the lookahead-bias fix: a backtest
    rebalancing in 2024-06 must not see a 10-K filed in 2024-11.
    """
    known = sorted(
        (item for item in series if item.filed_date and item.filed_date <= as_of_date),
        key=lambda item: item.end_date,
        reverse=True,
    )
    latest = known[0] if known else None
    previous = known[1] if len(known) > 1 else None
    return latest, previous


def ai_score(
    latest: AnnualFinancials | None, previous: AnnualFinancials | None, closes: list[float]
) -> tuple[int, str]:
    """Backtest-only composite score: algorithm-v0.3's fundamentals/growth/
    valuation/technical/volatility_risk factors (news_sentiment excluded,
    weights renormalized — see `AI_SCORE_WEIGHTS`). `latest`/`previous`
    should come from `select_financials_as_of` to stay point-in-time-safe.
    """
    factors_input = _to_financial_factors_input(latest, previous)
    latest_price = closes[-1] if closes else 0.0

    fundamentals, fundamentals_explanation = fundamentals_score(factors_input)
    growth, growth_explanation = growth_score(factors_input)
    valuation, valuation_explanation = valuation_score(factors_input, latest_price)
    technical, technical_explanation = technical_score(closes)
    volatility, volatility_explanation = volatility_risk_score(closes)

    composite = round(
        fundamentals * AI_SCORE_WEIGHTS["fundamentals"]
        + growth * AI_SCORE_WEIGHTS["growth"]
        + valuation * AI_SCORE_WEIGHTS["valuation"]
        + technical * AI_SCORE_WEIGHTS["technical"]
        + volatility * AI_SCORE_WEIGHTS["volatility_risk"]
    )
    explanation = (
        f"{fundamentals_explanation}；{growth_explanation}；{valuation_explanation}；"
        f"{technical_explanation}；{volatility_explanation}"
    )
    return max(0, min(100, composite)), explanation


def _to_financial_factors_input(
    latest: AnnualFinancials | None, previous: AnnualFinancials | None
) -> FinancialFactorsInput | None:
    if latest is None:
        return None
    return FinancialFactorsInput(
        revenue=latest.revenue,
        previous_revenue=previous.revenue if previous else None,
        net_income=latest.net_income,
        eps_diluted=latest.eps_diluted,
        stockholders_equity=latest.stockholders_equity,
        shares_outstanding=latest.shares_outstanding,
        operating_income=latest.operating_income,
        current_assets=latest.current_assets,
        current_liabilities=latest.current_liabilities,
        net_fixed_assets=latest.net_fixed_assets,
        cash=latest.cash,
        total_debt=latest.total_debt,
    )
