from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

RISK_DISCLAIMER = "本系统仅用于投资研究辅助，不构成任何投资建议。"


@dataclass(frozen=True)
class ResearchConstraints:
    max_position_weight: float = 0.35
    min_cash_weight: float = 0.10
    max_drawdown: float = 0.20
    benchmark_symbol: str = "SPY"
    backtest_years: int = 3


@dataclass(frozen=True)
class StrategyPreferences:
    scoring_mode: str = "algorithm_v0.3"
    backtest_mode: str = "ai_score"
    optimizer_method: str = "minimum_variance"
    rebalance_frequency: str = "monthly"


@dataclass(frozen=True)
class PortfolioResearchRunRequest:
    portfolio_name: str
    symbols: list[str]
    research_goal: str = "balanced_growth"
    constraints: ResearchConstraints = field(default_factory=ResearchConstraints)
    strategy_preferences: StrategyPreferences = field(default_factory=StrategyPreferences)

    def to_dict(self) -> dict[str, Any]:
        return {
            "portfolio_name": self.portfolio_name,
            "symbols": self.symbols,
            "research_goal": self.research_goal,
            "constraints": self.constraints.__dict__,
            "strategy_preferences": self.strategy_preferences.__dict__,
        }


@dataclass(frozen=True)
class PortfolioResearchRunResult:
    trace_id: str
    state: str
    portfolio: dict
    score_summary: dict | None
    backtest_summary: dict | None
    risk_summary: dict | None
    optimized_weights: dict | None
    ai_explanation: dict | None
    recommendation: dict | None
    warnings: list[str]
    workflow: dict
    source: str
    started_at: str
    completed_at: str
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_name": "portfolio_research_module",
            "workflow_version": "portfolio-research-module-v0.1",
            "trace_id": self.trace_id,
            "state": self.state,
            "portfolio": self.portfolio,
            "score_summary": self.score_summary,
            "backtest_summary": self.backtest_summary,
            "risk_summary": self.risk_summary,
            "optimized_weights": self.optimized_weights,
            "ai_explanation": self.ai_explanation,
            "recommendation": self.recommendation,
            "warnings": self.warnings,
            "workflow": self.workflow,
            "source": self.source,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "risk_disclaimer": self.risk_disclaimer,
        }
