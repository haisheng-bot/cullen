from __future__ import annotations

from dataclasses import dataclass
from typing import Any


RISK_DISCLAIMER = "本系统仅用于投资研究辅助，不构成任何投资建议。"


@dataclass(frozen=True)
class NewsItem:
    title: str
    summary: str
    url: str
    source: str
    published_at: str
    category: str
    symbols: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "summary": self.summary,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at,
            "category": self.category,
            "symbols": self.symbols,
        }


@dataclass(frozen=True)
class NewsPolicyResponse:
    symbol: str
    years: int
    items: list[NewsItem]
    sources: list[str]
    generated_at: str
    coverage_note: str
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "years": self.years,
            "items": [item.to_dict() for item in self.items],
            "sources": self.sources,
            "generated_at": self.generated_at,
            "coverage_note": self.coverage_note,
            "risk_disclaimer": self.risk_disclaimer,
        }

