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
class FinancialFactorsInput:
    """Optional real fundamentals, from SEC XBRL company facts (algorithm-v0.2).

    `operating_income`/`current_assets`/`current_liabilities`/`net_fixed_assets`/
    `cash`/`total_debt` (algorithm-v0.2.2) back the Magic Formula-style ROC and
    EV/EBIT earnings yield metrics that enrich the fundamentals/valuation factors.
    """

    revenue: float | None = None
    previous_revenue: float | None = None
    net_income: float | None = None
    eps_diluted: float | None = None
    stockholders_equity: float | None = None
    shares_outstanding: float | None = None
    operating_income: float | None = None
    current_assets: float | None = None
    current_liabilities: float | None = None
    net_fixed_assets: float | None = None
    cash: float | None = None
    total_debt: float | None = None


@dataclass(frozen=True)
class TechnicalSeriesInput:
    """Daily closes (oldest first) for RSI/MA-cross/momentum indicators
    (algorithm-v0.2.1). Distinct from `points`, which are intraday and only
    cover the current trading day.
    """

    closes: list[float]


@dataclass(frozen=True)
class NewsSignalInput:
    title: str
    summary: str = ""
    category: str = "company_news"
    source: str = ""


@dataclass(frozen=True)
class RecommendationInput:
    symbol: str
    latest_price: float
    previous_close: float | None
    points: list[AlgorithmPoint]
    source: str
    analysis_time: str
    financial_factors: FinancialFactorsInput | None = None
    technical_series: TechnicalSeriesInput | None = None
    news_signals: list[NewsSignalInput] = field(default_factory=list)


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
    scoring_profile: str = "balanced"
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
            "scoring_profile": self.scoring_profile,
            "risk_disclaimer": self.risk_disclaimer,
        }
