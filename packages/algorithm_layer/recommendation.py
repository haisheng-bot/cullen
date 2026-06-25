from __future__ import annotations

from statistics import mean

from packages.algorithm_layer.base import RecommendationAlgorithm
from packages.algorithm_layer.schemas import (
    FactorScore,
    FinancialFactorsInput,
    RecommendationInput,
    RecommendationResult,
    TechnicalSeriesInput,
)
from packages.algorithm_layer.technical_indicators import (
    MIN_CLOSES_FOR_INDICATORS,
    calculate_momentum_percent,
    calculate_rsi,
    detect_ma_cross,
)

NO_DATA_SCORE = 50


class TrendRecommendationAlgorithm(RecommendationAlgorithm):
    """algorithm-v0.2.2: fundamentals/valuation factors enriched with
    Magic Formula-style metrics (ROC and EV/EBIT earnings yield) alongside
    the existing net margin and P/E, since they capture capital efficiency
    and cheapness that net margin/P/E alone miss. Technical factor (RSI-14/
    MA(5,20) cross/10-day momentum) unchanged from v0.2.1. See
    docs/standards/ALGORITHM_STANDARD.md section 9 for the version roadmap.
    """

    algorithm_version = "algorithm-v0.2.2"

    def recommend(self, data: RecommendationInput) -> RecommendationResult:
        if not data.points:
            raise ValueError("points are required for recommendation")

        closes = [point.close for point in data.points]
        first_close = closes[0]
        latest_price = data.latest_price
        previous_close = data.previous_close or first_close

        day_change_percent = _percent_change(latest_price, previous_close)
        trend_change_percent = _percent_change(latest_price, first_close)
        volatility_percent = _volatility_percent(closes)

        technical_score, technical_explanation = _technical_score(
            data.technical_series, trend_change_percent, day_change_percent
        )
        fundamentals_score, fundamentals_explanation = _fundamentals_score(data.financial_factors)
        growth_score, growth_explanation = _growth_score(data.financial_factors)
        valuation_score, valuation_explanation = _valuation_score(data.financial_factors, latest_price)

        factors = [
            FactorScore(
                name="fundamentals",
                score=fundamentals_score,
                weight=0.30,
                explanation=fundamentals_explanation,
            ),
            FactorScore(
                name="growth",
                score=growth_score,
                weight=0.20,
                explanation=growth_explanation,
            ),
            FactorScore(
                name="valuation",
                score=valuation_score,
                weight=0.20,
                explanation=valuation_explanation,
            ),
            FactorScore(
                name="technical",
                score=technical_score,
                weight=0.20,
                explanation=technical_explanation,
            ),
            FactorScore(
                name="volatility_risk",
                score=_risk_score(volatility_percent),
                weight=0.10,
                explanation=f"区间波动估算 {volatility_percent:.2f}%",
            ),
        ]

        total_score = round(sum(factor.score * factor.weight for factor in factors))
        recommendation = recommendation_label(total_score)
        reasons = build_reasons(trend_change_percent, day_change_percent, volatility_percent)
        risks = build_risks(volatility_percent, recommendation, data.financial_factors)

        return RecommendationResult(
            symbol=data.symbol,
            total_score=total_score,
            recommendation=recommendation,
            factors=factors,
            reasons=reasons,
            risks=risks,
            source=data.source,
            algorithm_version=self.algorithm_version,
            analysis_time=data.analysis_time,
        )


def recommendation_label(score: int) -> str:
    if score >= 85:
        return "强关注"
    if score >= 70:
        return "观察"
    if score >= 50:
        return "中性"
    return "回避"


def build_reasons(
    trend_change_percent: float, day_change_percent: float, volatility_percent: float
) -> list[str]:
    reasons = []
    if trend_change_percent > 0:
        reasons.append("区间走势为正，短线动量偏强。")
    else:
        reasons.append("区间走势为负，短线动量偏弱。")
    if day_change_percent > 0:
        reasons.append("当前价格高于前收盘价。")
    else:
        reasons.append("当前价格低于或接近前收盘价。")
    if volatility_percent < 1.5:
        reasons.append("区间波动相对可控。")
    else:
        reasons.append("区间波动较高，需要结合风险承受能力观察。")
    return reasons


def build_risks(
    volatility_percent: float,
    recommendation: str,
    financial_factors: FinancialFactorsInput | None,
) -> list[str]:
    risks = ["新闻情绪因子尚未接入（计划 algorithm-v0.3），估值评分为绝对档位启发式，非行业相对。"]
    if financial_factors is None:
        risks.append("未提供财务数据，基本面/成长性/估值三项暂以中性分计入。")
    if volatility_percent >= 2.5:
        risks.append("短线波动较大，评分可能快速变化。")
    if recommendation in {"强关注", "观察"}:
        risks.append("推荐等级仅表示研究关注优先级，不代表买入建议。")
    return risks


def _percent_change(current: float, baseline: float) -> float:
    if baseline == 0:
        return 0.0
    return (current - baseline) / baseline * 100


def _trend_score(change_percent: float) -> int:
    return max(0, min(100, round(60 + change_percent * 8)))


def _risk_score(volatility_percent: float) -> int:
    return max(20, min(95, round(95 - volatility_percent * 18)))


def _volatility_percent(closes: list[float]) -> float:
    if not closes:
        return 0.0
    average_close = mean(closes)
    if average_close == 0:
        return 0.0
    return (max(closes) - min(closes)) / average_close * 100


_CROSS_LABELS = {
    "golden_cross": "金叉",
    "death_cross": "死叉",
    "bullish": "多头排列",
    "bearish": "空头排列",
    "flat": "走势平缓",
}

_CROSS_SCORES = {
    "golden_cross": 80,
    "bullish": 65,
    "flat": 50,
    "bearish": 35,
    "death_cross": 20,
}


def _rsi_score(rsi: float) -> int:
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


def _technical_score(
    technical_series: TechnicalSeriesInput | None,
    trend_change_percent: float,
    day_change_percent: float,
) -> tuple[int, str]:
    if technical_series is not None and len(technical_series.closes) >= MIN_CLOSES_FOR_INDICATORS:
        closes = technical_series.closes
        momentum_percent = calculate_momentum_percent(closes, lookback=10) or 0.0
        rsi = calculate_rsi(closes, period=14) or 50.0
        cross_state = detect_ma_cross(closes, short_period=5, long_period=20)

        momentum_score = _trend_score(momentum_percent)
        rsi_score = _rsi_score(rsi)
        cross_score = _CROSS_SCORES[cross_state]

        composite = round(momentum_score * 0.4 + rsi_score * 0.3 + cross_score * 0.3)
        explanation = (
            f"动量(10日) {momentum_percent:+.2f}%，RSI(14) {rsi:.1f}，"
            f"均线(5/20)状态：{_CROSS_LABELS[cross_state]}"
        )
        return max(0, min(100, composite)), explanation

    trend_score = _trend_score(trend_change_percent)
    day_score = _trend_score(day_change_percent)
    composite = round(trend_score * 0.6 + day_score * 0.4)
    explanation = (
        f"日线数据不足（需 {MIN_CLOSES_FOR_INDICATORS} 个交易日以上），暂以区间走势 "
        f"{trend_change_percent:.2f}% 与相对前收盘 {day_change_percent:.2f}% 估算"
    )
    return max(0, min(100, composite)), explanation


def _net_margin_score(factors: FinancialFactorsInput) -> tuple[int, str] | None:
    if factors.revenue in (None, 0) or factors.net_income is None:
        return None
    net_margin_percent = factors.net_income / factors.revenue * 100
    score = max(10, min(95, round(50 + net_margin_percent * 1.5)))
    return score, f"净利润率约 {net_margin_percent:.1f}%"


def _roc_score(factors: FinancialFactorsInput) -> tuple[int, str] | None:
    """Greenblatt-style Return on Capital: EBIT / (net working capital +
    net fixed assets). Measures capital efficiency independent of margin.
    """
    if factors.operating_income is None or factors.current_assets is None:
        return None
    if factors.current_liabilities is None or factors.net_fixed_assets is None:
        return None

    net_working_capital = factors.current_assets - factors.current_liabilities
    capital_employed = net_working_capital + factors.net_fixed_assets
    if capital_employed <= 0:
        return None

    roc_percent = factors.operating_income / capital_employed * 100
    score = max(10, min(95, round(50 + roc_percent * 1.5)))
    return score, f"资本回报率(ROC)约 {roc_percent:.1f}%"


def _fundamentals_score(factors: FinancialFactorsInput | None) -> tuple[int, str]:
    if factors is None:
        return NO_DATA_SCORE, "未提供财务数据，暂以中性分计入。"

    net_margin = _net_margin_score(factors)
    roc = _roc_score(factors)
    if net_margin is None and roc is None:
        return NO_DATA_SCORE, "未提供财务数据，暂以中性分计入。"
    if net_margin is None:
        score, explanation = roc
        return score, f"{explanation}（基于最近年度 SEC 财报，缺净利润率数据）"
    if roc is None:
        score, explanation = net_margin
        return score, f"{explanation}（基于最近年度 SEC 财报，缺 ROC 数据）"

    margin_score, margin_explanation = net_margin
    roc_score, roc_explanation = roc
    score = round(margin_score * 0.5 + roc_score * 0.5)
    return score, f"{margin_explanation}，{roc_explanation}（基于最近年度 SEC 财报）"


def _growth_score(factors: FinancialFactorsInput | None) -> tuple[int, str]:
    if factors is None or not factors.previous_revenue or factors.revenue is None:
        return NO_DATA_SCORE, "未提供同比营收数据，暂以中性分计入。"

    growth_percent = (factors.revenue - factors.previous_revenue) / factors.previous_revenue * 100
    score = max(10, min(95, round(50 + growth_percent * 1.2)))
    return score, f"营收同比增长约 {growth_percent:.1f}%（基于最近两个年度 SEC 财报）"


def _pe_score(factors: FinancialFactorsInput, latest_price: float) -> tuple[int, str] | None:
    if not factors.eps_diluted or factors.eps_diluted <= 0:
        return None
    pe_ratio = latest_price / factors.eps_diluted
    return _pe_band_score(pe_ratio), f"P/E 约 {pe_ratio:.1f}"


def _ev_to_ebit_score(factors: FinancialFactorsInput, latest_price: float) -> tuple[int, str] | None:
    """Greenblatt-style earnings yield, expressed as an EV/EBIT ratio so it
    can reuse the same cheap/expensive band as P/E.
    """
    if factors.operating_income is None or factors.operating_income <= 0:
        return None
    if factors.shares_outstanding is None or factors.shares_outstanding <= 0:
        return None

    market_cap = latest_price * factors.shares_outstanding
    enterprise_value = market_cap + (factors.total_debt or 0) - (factors.cash or 0)
    if enterprise_value <= 0:
        return None

    ev_to_ebit = enterprise_value / factors.operating_income
    return _pe_band_score(ev_to_ebit), f"EV/EBIT 约 {ev_to_ebit:.1f}"


def _valuation_score(factors: FinancialFactorsInput | None, latest_price: float) -> tuple[int, str]:
    if factors is None:
        return NO_DATA_SCORE, "未提供估值相关数据，暂以中性分计入。"

    pe = _pe_score(factors, latest_price)
    ev_to_ebit = _ev_to_ebit_score(factors, latest_price)
    if pe is None and ev_to_ebit is None:
        return NO_DATA_SCORE, "未提供估值相关数据，暂以中性分计入。"
    if pe is None:
        score, explanation = ev_to_ebit
        return score, f"{explanation}（绝对档位估算，非行业相对，缺 EPS 数据）"
    if ev_to_ebit is None:
        score, explanation = pe
        return score, f"{explanation}（绝对档位估算，非行业相对，缺企业价值数据）"

    pe_score, pe_explanation = pe
    ev_score, ev_explanation = ev_to_ebit
    score = round(pe_score * 0.5 + ev_score * 0.5)
    return score, f"{pe_explanation}，{ev_explanation}（绝对档位估算，非行业相对）"


def _pe_band_score(pe_ratio: float) -> int:
    if pe_ratio < 15:
        return 85
    if pe_ratio < 25:
        return 70
    if pe_ratio < 40:
        return 55
    if pe_ratio < 60:
        return 40
    return 25
