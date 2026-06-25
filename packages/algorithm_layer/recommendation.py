from __future__ import annotations

from packages.algorithm_layer import financial_factors
from packages.algorithm_layer.base import RecommendationAlgorithm
from packages.algorithm_layer.schemas import (
    FactorScore,
    FinancialFactorsInput,
    NewsSignalInput,
    RecommendationInput,
    RecommendationResult,
    TechnicalSeriesInput,
)
from packages.algorithm_layer.technical_indicators import (
    MIN_CLOSES_FOR_INDICATORS,
    calculate_volatility_percent,
    technical_indicator_score,
    trend_score,
    volatility_risk_score,
)

NO_DATA_SCORE = 50


class TrendRecommendationAlgorithm(RecommendationAlgorithm):
    """algorithm-v0.3: adds a replaceable news sentiment factor on top of
    the v0.2.2 financial/valuation/technical factors. The first v0.3
    implementation uses rule-based public news and SEC disclosure signals;
    it can later be replaced by FinBERT or an LLM without changing the
    RecommendationInput contract.
    """

    algorithm_version = "algorithm-v0.3"

    def recommend(self, data: RecommendationInput) -> RecommendationResult:
        if not data.points:
            raise ValueError("points are required for recommendation")

        closes = [point.close for point in data.points]
        first_close = closes[0]
        latest_price = data.latest_price
        previous_close = data.previous_close or first_close

        day_change_percent = _percent_change(latest_price, previous_close)
        trend_change_percent = _percent_change(latest_price, first_close)
        volatility_percent = calculate_volatility_percent(closes)

        technical_score, technical_explanation = _technical_score(
            data.technical_series, trend_change_percent, day_change_percent
        )
        fundamentals_score, fundamentals_explanation = financial_factors.fundamentals_score(data.financial_factors)
        growth_score, growth_explanation = financial_factors.growth_score(data.financial_factors)
        valuation_score, valuation_explanation = financial_factors.valuation_score(data.financial_factors, latest_price)
        news_score, news_explanation = _news_sentiment_score(data.news_signals)
        risk_score, _ = volatility_risk_score(closes)

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
                weight=0.10,
                explanation=technical_explanation,
            ),
            FactorScore(
                name="news_sentiment",
                score=news_score,
                weight=0.10,
                explanation=news_explanation,
            ),
            FactorScore(
                name="volatility_risk",
                score=risk_score,
                weight=0.10,
                explanation=f"区间波动估算 {volatility_percent:.2f}%",
            ),
        ]

        total_score = round(sum(factor.score * factor.weight for factor in factors))
        recommendation = recommendation_label(total_score)
        reasons = build_reasons(trend_change_percent, day_change_percent, volatility_percent)
        risks = build_risks(volatility_percent, recommendation, data.financial_factors, data.news_signals)

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
    news_signals: list[NewsSignalInput],
) -> list[str]:
    risks = ["新闻情绪为规则化初版估算，估值评分为绝对档位启发式，非行业相对。"]
    if financial_factors is None:
        risks.append("未提供财务数据，基本面/成长性/估值三项暂以中性分计入。")
    if not news_signals:
        risks.append("未提供新闻/披露信号，新闻情绪暂以中性分计入。")
    if volatility_percent >= 2.5:
        risks.append("短线波动较大，评分可能快速变化。")
    if recommendation in {"强关注", "观察"}:
        risks.append("推荐等级仅表示研究关注优先级，不代表买入建议。")
    return risks


def _percent_change(current: float, baseline: float) -> float:
    if baseline == 0:
        return 0.0
    return (current - baseline) / baseline * 100


_POSITIVE_NEWS_TERMS = {
    "beat",
    "beats",
    "raise",
    "raises",
    "raised",
    "upgrade",
    "upgraded",
    "growth",
    "record",
    "approval",
    "approved",
    "launch",
    "launched",
    "partnership",
    "contract",
    "wins",
    "strong",
    "profit",
    "revenue",
    "buyback",
    "dividend",
    "surges",
}

_NEGATIVE_NEWS_TERMS = {
    "miss",
    "misses",
    "cut",
    "cuts",
    "downgrade",
    "downgraded",
    "lawsuit",
    "probe",
    "investigation",
    "resign",
    "resignation",
    "bankruptcy",
    "layoff",
    "warning",
    "recall",
    "antitrust",
    "fraud",
    "loss",
    "plunges",
    "risk",
    "risks",
}


def _news_sentiment_score(news_signals: list[NewsSignalInput]) -> tuple[int, str]:
    if not news_signals:
        return NO_DATA_SCORE, "未提供新闻/披露信号，暂以中性分计入。"

    positive_hits = 0
    negative_hits = 0
    disclosure_risk_hits = 0
    for signal in news_signals:
        text = f"{signal.title} {signal.summary}".lower()
        positive_hits += sum(1 for term in _POSITIVE_NEWS_TERMS if term in text)
        negative_hits += sum(1 for term in _NEGATIVE_NEWS_TERMS if term in text)
        if signal.category in {"management_change", "governance", "policy"}:
            disclosure_risk_hits += 1

    raw_score = 50 + positive_hits * 5 - negative_hits * 6 - disclosure_risk_hits * 2
    score = max(20, min(85, round(raw_score)))
    explanation = (
        f"基于 {len(news_signals)} 条新闻/SEC 披露信号，正向词 {positive_hits}，"
        f"负向词 {negative_hits}，治理/政策披露 {disclosure_risk_hits} 条（规则化估算）"
    )
    return score, explanation


def _technical_score(
    technical_series: TechnicalSeriesInput | None,
    trend_change_percent: float,
    day_change_percent: float,
) -> tuple[int, str]:
    if technical_series is not None and len(technical_series.closes) >= MIN_CLOSES_FOR_INDICATORS:
        return technical_indicator_score(technical_series.closes)

    trend_score_value = trend_score(trend_change_percent)
    day_score_value = trend_score(day_change_percent)
    composite = round(trend_score_value * 0.6 + day_score_value * 0.4)
    explanation = (
        f"日线数据不足（需 {MIN_CLOSES_FOR_INDICATORS} 个交易日以上），暂以区间走势 "
        f"{trend_change_percent:.2f}% 与相对前收盘 {day_change_percent:.2f}% 估算"
    )
    return max(0, min(100, composite)), explanation
