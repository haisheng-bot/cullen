from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RISK_DISCLAIMER = "本系统仅用于投资研究辅助，不构成任何投资建议。"


@dataclass(frozen=True)
class RunSummary:
    trace_id: str
    workflow_name: str
    workflow_version: str
    state: str
    portfolio_name: str | None
    symbols: list[str]
    strategy_library_name: str | None
    summary_text: str
    started_at: str
    completed_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "workflow_name": self.workflow_name,
            "workflow_version": self.workflow_version,
            "state": self.state,
            "portfolio_name": self.portfolio_name,
            "symbols": self.symbols,
            "strategy_library_name": self.strategy_library_name,
            "summary_text": self.summary_text,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


@dataclass(frozen=True)
class RunHistoryResult:
    items: list[RunSummary]
    total_count: int
    limit: int
    offset: int
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items],
            "total_count": self.total_count,
            "limit": self.limit,
            "offset": self.offset,
            "risk_disclaimer": self.risk_disclaimer,
        }
