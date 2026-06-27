from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RISK_DISCLAIMER = "本系统仅用于投资研究辅助，不构成任何投资建议。"


@dataclass(frozen=True)
class PortfolioRiskReport:
    symbols: list[str]
    weights: dict[str, float]
    volatility_percent: float | None
    beta: float | None
    max_drawdown_percent: float
    average_correlation: float | None
    concentration_percent: float
    sector_exposure: dict[str, float]
    source: str
    generated_at: str
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbols": self.symbols,
            "weights": self.weights,
            "volatility_percent": self.volatility_percent,
            "beta": self.beta,
            "max_drawdown_percent": self.max_drawdown_percent,
            "average_correlation": self.average_correlation,
            "concentration_percent": self.concentration_percent,
            "sector_exposure": self.sector_exposure,
            "source": self.source,
            "generated_at": self.generated_at,
            "risk_disclaimer": self.risk_disclaimer,
        }
