from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RISK_DISCLAIMER = "本系统仅用于投资研究辅助，不构成任何投资建议。"

OPTIMIZER_METHODS = (
    "equal_weight",
    "market_cap",
    "minimum_variance",
    "risk_parity",
)


@dataclass(frozen=True)
class PortfolioOptimizerResult:
    method: str
    symbols: list[str]
    target_weights: dict[str, float]
    cash_weight: float
    max_position_weight: float
    expected_risk_percent: float | None
    notes: list[str]
    source: str
    generated_at: str
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "symbols": self.symbols,
            "target_weights": self.target_weights,
            "cash_weight": self.cash_weight,
            "max_position_weight": self.max_position_weight,
            "expected_risk_percent": self.expected_risk_percent,
            "notes": self.notes,
            "source": self.source,
            "generated_at": self.generated_at,
            "risk_disclaimer": self.risk_disclaimer,
        }
