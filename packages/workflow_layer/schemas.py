from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RISK_DISCLAIMER = "本系统仅用于投资研究辅助，不构成任何投资建议。"


@dataclass(frozen=True)
class ScreeningCandidate:
    rank: int
    symbol: str
    name: str
    sector: str
    total_score: int
    recommendation: str
    factors: list[dict[str, Any]]
    reasons: list[str]
    risks: list[str]
    source: str
    algorithm_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "symbol": self.symbol,
            "name": self.name,
            "sector": self.sector,
            "total_score": self.total_score,
            "recommendation": self.recommendation,
            "factors": self.factors,
            "reasons": self.reasons,
            "risks": self.risks,
            "source": self.source,
            "algorithm_version": self.algorithm_version,
        }


@dataclass(frozen=True)
class SkippedCandidate:
    symbol: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"symbol": self.symbol, "reason": self.reason}


@dataclass(frozen=True)
class ScreeningResult:
    market: str
    requested_limit: int
    scored_count: int
    candidates: list[ScreeningCandidate]
    skipped: list[SkippedCandidate]
    source: str
    generated_at: str
    scoring_profile: str = "balanced"
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "market": self.market,
            "requested_limit": self.requested_limit,
            "scored_count": self.scored_count,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "skipped": [skipped.to_dict() for skipped in self.skipped],
            "source": self.source,
            "generated_at": self.generated_at,
            "scoring_profile": self.scoring_profile,
            "risk_disclaimer": self.risk_disclaimer,
        }
