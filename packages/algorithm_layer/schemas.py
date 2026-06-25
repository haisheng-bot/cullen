from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


RISK_DISCLAIMER = "本系统仅用于投资研究辅助，不构成任何投资建议。"


@dataclass(frozen=True)
class AlgorithmPoint:
    timestamp: str
    close: float
    volume: int | None = None


@dataclass(frozen=True)
class RecommendationInput:
    symbol: str
    latest_price: float
    previous_close: float | None
    points: list[AlgorithmPoint]
    source: str
    analysis_time: str


@dataclass(frozen=True)
class FactorScore:
    name: str
    score: int
    weight: float
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "weight": self.weight,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class RecommendationResult:
    symbol: str
    total_score: int
    recommendation: str
    factors: list[FactorScore]
    reasons: list[str]
    risks: list[str]
    source: str
    algorithm_version: str
    analysis_time: str
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "total_score": self.total_score,
            "recommendation": self.recommendation,
            "factors": [factor.to_dict() for factor in self.factors],
            "reasons": self.reasons,
            "risks": self.risks,
            "source": self.source,
            "algorithm_version": self.algorithm_version,
            "analysis_time": self.analysis_time,
            "risk_disclaimer": self.risk_disclaimer,
        }

