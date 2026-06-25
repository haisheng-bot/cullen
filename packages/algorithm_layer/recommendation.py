from __future__ import annotations

from statistics import mean

from packages.algorithm_layer.base import RecommendationAlgorithm
from packages.algorithm_layer.schemas import (
    FactorScore,
    FinancialFactorsInput,
    RecommendationInput,
    RecommendationResult,
)

NO_DATA_SCORE = 50


class TrendRecommendationAlgorithm(RecommendationAlgorithm):
    """algorithm-v0.2: adds fundamentals/growth/valuation factors from real SEC
    XBRL data alongside the v0.1 technical/risk factors. See
    docs/standards/ALGORITHM_STANDARD.md section 9 for the version roadmap.
    """

    algorithm_version = "algorithm-v0.2"

    def recommend(self, data: RecommendationInput) -> RecommendationResult:
        if not data.points:
            raise ValueError("points are required for recommendation")

        closes = [point.close for point in data.points]
        volumes = [point.volume for point in data.points if point.volume is not None]
        first_close = closes[0]
        latest_price = data.latest_price
        previous_close = data.previous_close or first_close

        day_change_percent = _percent_change(latest_price, previous_close)
        trend_change_percent = _percent_change(latest_price, first_close)
        volatility_percent = _volatility_percent(closes)

        technical_score, technical_explanation = _technical_score(
            trend_change_percent, day_change_percent, _volume_score(volumes)
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


def _volume_score(volumes: list[int]) -> int:
    if not volumes:
        return 55
    average_volume = mean(volumes)
    latest_volume = volumes[-1]
    if average_volume <= 0:
        return 55
    ratio = latest_volume / average_volume
    return max(35, min(90, round(55 + ratio * 18)))


def _volatility_percent(closes: list[float]) -> float:
    if not closes:
        return 0.0
    average_close = mean(closes)
    if average_close == 0:
        return 0.0
    return (max(closes) - min(closes)) / average_close * 100


def _technical_score(
    trend_change_percent: float, day_change_percent: float, volume_score: int
) -> tuple[int, str]:
    trend_score = _trend_score(trend_change_percent)
    day_score = _trend_score(day_change_percent)
    composite = round(trend_score * 0.5625 + day_score * 0.3125 + volume_score * 0.125)
    explanation = (
        f"区间走势 {trend_change_percent:.2f}%，相对前收盘 {day_change_percent:.2f}%，"
        "结合成交量活跃度估算"
    )
    return max(0, min(100, composite)), explanation


def _fundamentals_score(factors: FinancialFactorsInput | None) -> tuple[int, str]:
    if factors is None or factors.revenue in (None, 0) or factors.net_income is None:
        return NO_DATA_SCORE, "未提供财务数据，暂以中性分计入。"

    net_margin_percent = factors.net_income / factors.revenue * 100
    score = max(10, min(95, round(50 + net_margin_percent * 1.5)))
    return score, f"净利润率约 {net_margin_percent:.1f}%（基于最近年度 SEC 财报）"


def _growth_score(factors: FinancialFactorsInput | None) -> tuple[int, str]:
    if factors is None or not factors.previous_revenue or factors.revenue is None:
        return NO_DATA_SCORE, "未提供同比营收数据，暂以中性分计入。"

    growth_percent = (factors.revenue - factors.previous_revenue) / factors.previous_revenue * 100
    score = max(10, min(95, round(50 + growth_percent * 1.2)))
    return score, f"营收同比增长约 {growth_percent:.1f}%（基于最近两个年度 SEC 财报）"


def _valuation_score(factors: FinancialFactorsInput | None, latest_price: float) -> tuple[int, str]:
    if factors is None or not factors.eps_diluted or factors.eps_diluted <= 0:
        return NO_DATA_SCORE, "未提供每股盈余（EPS）数据，暂以中性分计入。"

    pe_ratio = latest_price / factors.eps_diluted
    score = _pe_band_score(pe_ratio)
    return score, f"按最新价格估算 P/E 约 {pe_ratio:.1f}（绝对档位估算，非行业相对）"


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
