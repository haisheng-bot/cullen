from __future__ import annotations

from statistics import mean

from packages.algorithm_layer.base import RecommendationAlgorithm
from packages.algorithm_layer.schemas import FactorScore, RecommendationInput, RecommendationResult


class TrendRecommendationAlgorithm(RecommendationAlgorithm):
    algorithm_version = "algorithm-v0.1"

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
        volume_score = _volume_score(volumes)

        factors = [
            FactorScore(
                name="trend",
                score=_trend_score(trend_change_percent),
                weight=0.45,
                explanation=f"区间价格变化 {trend_change_percent:.2f}%",
            ),
            FactorScore(
                name="day_change",
                score=_trend_score(day_change_percent),
                weight=0.25,
                explanation=f"相对前收盘变化 {day_change_percent:.2f}%",
            ),
            FactorScore(
                name="volatility_risk",
                score=_risk_score(volatility_percent),
                weight=0.20,
                explanation=f"区间波动估算 {volatility_percent:.2f}%",
            ),
            FactorScore(
                name="volume_activity",
                score=volume_score,
                weight=0.10,
                explanation="基于区间成交量活跃度的第一阶段估算",
            ),
        ]

        total_score = round(sum(factor.score * factor.weight for factor in factors))
        recommendation = recommendation_label(total_score)
        reasons = build_reasons(trend_change_percent, day_change_percent, volatility_percent)
        risks = build_risks(volatility_percent, recommendation)

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


def build_risks(volatility_percent: float, recommendation: str) -> list[str]:
    risks = ["第一阶段算法仅基于行情走势，尚未接入财报、估值和新闻情绪。"]
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

