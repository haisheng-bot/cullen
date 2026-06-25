from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


RISK_DISCLAIMER = "本系统仅用于投资研究辅助，不构成任何投资建议。"


@dataclass(frozen=True)
class UniverseStock:
    rank: int
    symbol: str
    name: str
    sector: str | None = None
    volume: int | None = None
    price: float | None = None
    change_percent: float | None = None
    market_cap: float | None = None
    pe_ratio: float | None = None
    relative_volume: float | None = None
    analysis_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "symbol": self.symbol,
            "name": self.name,
            "sector": self.sector,
            "volume": self.volume,
            "price": self.price,
            "change_percent": self.change_percent,
            "market_cap": self.market_cap,
            "pe_ratio": self.pe_ratio,
            "relative_volume": self.relative_volume,
            "analysis_tags": self.analysis_tags,
        }


@dataclass(frozen=True)
class UniverseResult:
    universe_date: str
    universe_name: str
    market: str
    limit: int
    source: str
    generated_at: str
    items: list[UniverseStock]
    analysis_dimensions: list[str]
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "universe_date": self.universe_date,
            "universe_name": self.universe_name,
            "market": self.market,
            "limit": self.limit,
            "source": self.source,
            "generated_at": self.generated_at,
            "items": [item.to_dict() for item in self.items],
            "analysis_dimensions": self.analysis_dimensions,
            "risk_disclaimer": self.risk_disclaimer,
        }

