from __future__ import annotations

from packages.scoring_profiles.schemas import ScoringProfile

FACTOR_NAMES = (
    "fundamentals",
    "growth",
    "valuation",
    "technical",
    "news_sentiment",
    "volatility_risk",
)

BALANCED = ScoringProfile(
    name="balanced",
    label="Balanced 均衡",
    description="algorithm-v0.3 默认权重，六因子均衡覆盖，无特定风格倾向。",
    weights={
        "fundamentals": 0.30,
        "growth": 0.20,
        "valuation": 0.20,
        "technical": 0.10,
        "news_sentiment": 0.10,
        "volatility_risk": 0.10,
    },
)

GROWTH = ScoringProfile(
    name="growth",
    label="Growth 成长",
    description="偏好高成长公司，容忍较高估值，技术面权重略升以捕捉动量。",
    weights={
        "fundamentals": 0.20,
        "growth": 0.35,
        "valuation": 0.10,
        "technical": 0.15,
        "news_sentiment": 0.10,
        "volatility_risk": 0.10,
    },
)

VALUE = ScoringProfile(
    name="value",
    label="Value 价值",
    description="偏好低估值且盈利稳健的公司，弱化短期技术面和新闻噪音。",
    weights={
        "fundamentals": 0.35,
        "growth": 0.10,
        "valuation": 0.35,
        "technical": 0.05,
        "news_sentiment": 0.05,
        "volatility_risk": 0.10,
    },
)

DEFENSIVE = ScoringProfile(
    name="defensive",
    label="Defensive 防守",
    description="大幅提高波动风险因子权重，优先规避高波动标的。",
    weights={
        "fundamentals": 0.30,
        "growth": 0.10,
        "valuation": 0.15,
        "technical": 0.05,
        "news_sentiment": 0.10,
        "volatility_risk": 0.30,
    },
)

MOMENTUM = ScoringProfile(
    name="momentum",
    label="Momentum 动量",
    description="技术面和新闻情绪主导，基本面和估值降为辅助信号。",
    weights={
        "fundamentals": 0.15,
        "growth": 0.15,
        "valuation": 0.10,
        "technical": 0.35,
        "news_sentiment": 0.15,
        "volatility_risk": 0.10,
    },
)

_PROFILES: dict[str, ScoringProfile] = {
    profile.name: profile for profile in (BALANCED, GROWTH, VALUE, DEFENSIVE, MOMENTUM)
}
PROFILE_NAMES = tuple(_PROFILES)


def get_profile(name: str) -> ScoringProfile:
    try:
        return _PROFILES[name]
    except KeyError:
        raise ValueError(f"unknown scoring profile: {name}") from None


def list_profiles() -> list[ScoringProfile]:
    return list(_PROFILES.values())
