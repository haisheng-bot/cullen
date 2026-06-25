"""Portfolio Strategy Engine schemas.

V1 (backtesting-v0.1) scope was price/technical-only signals. V2
(backtesting-v0.2) adds an opt-in `signal_mode="ai_score"` that uses
point-in-time-reconstructed SEC fundamentals (see
docs/standards/PORTFOLIO_STRATEGY_STANDARD.md) — `min_technical_score`/
`max_technical_score` still mean exactly "technical_score" in both modes
(never silently redefined); `min_ai_score`/`max_ai_score` are the new,
separately-named ai_score thresholds, only evaluated when
`signal_mode == "ai_score"`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

RISK_DISCLAIMER = "本系统仅用于投资研究辅助，不构成任何投资建议。"

ALLOCATION_METHODS = (
    "equal_weight",
    "volatility_weighted",
    "technical_score_weighted",
    "market_cap_weighted",
)
REBALANCE_FREQUENCIES = ("weekly", "monthly", "quarterly")
MA_CROSS_FILTERS = (
    "golden_cross",
    "bullish",
    "golden_or_bullish",
    "death_cross",
    "bearish",
    "death_or_bearish",
)
SIGNAL_MODES = ("technical", "ai_score")


@dataclass(frozen=True)
class EntryRules:
    min_technical_score: int = 60
    min_momentum_percent: float | None = None
    require_ma_cross: str | None = None
    min_ai_score: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "min_technical_score": self.min_technical_score,
            "min_momentum_percent": self.min_momentum_percent,
            "require_ma_cross": self.require_ma_cross,
            "min_ai_score": self.min_ai_score,
        }


@dataclass(frozen=True)
class ExitRules:
    max_technical_score: int = 40
    stop_loss_percent: float | None = 0.08
    require_ma_cross: str | None = None
    max_ai_score: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_technical_score": self.max_technical_score,
            "stop_loss_percent": self.stop_loss_percent,
            "require_ma_cross": self.require_ma_cross,
            "max_ai_score": self.max_ai_score,
        }


@dataclass(frozen=True)
class AllocationConfig:
    method: str = "equal_weight"
    max_position_weight: float = 0.25
    min_cash_weight: float = 0.10

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "max_position_weight": self.max_position_weight,
            "min_cash_weight": self.min_cash_weight,
        }


@dataclass(frozen=True)
class RiskControls:
    max_portfolio_drawdown: float | None = 0.12
    max_sector_exposure: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_portfolio_drawdown": self.max_portfolio_drawdown,
            "max_sector_exposure": self.max_sector_exposure,
        }


@dataclass(frozen=True)
class StrategyConfig:
    strategy_name: str
    symbols: list[str]
    start_date: str
    end_date: str
    initial_cash: float = 10_000.0
    rebalance_frequency: str = "monthly"
    benchmark_symbol: str = "SPY"
    signal_mode: str = "technical"
    allocation: AllocationConfig = field(default_factory=AllocationConfig)
    entry_rules: EntryRules = field(default_factory=EntryRules)
    exit_rules: ExitRules = field(default_factory=ExitRules)
    risk: RiskControls = field(default_factory=RiskControls)
    sector_map: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "symbols": self.symbols,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_cash": self.initial_cash,
            "rebalance_frequency": self.rebalance_frequency,
            "benchmark_symbol": self.benchmark_symbol,
            "signal_mode": self.signal_mode,
            "allocation": self.allocation.to_dict(),
            "entry_rules": self.entry_rules.to_dict(),
            "exit_rules": self.exit_rules.to_dict(),
            "risk": self.risk.to_dict(),
            "sector_map": self.sector_map,
        }


@dataclass(frozen=True)
class EquityPoint:
    date: str
    portfolio_value: float
    benchmark_value: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "portfolio_value": self.portfolio_value,
            "benchmark_value": self.benchmark_value,
        }


@dataclass(frozen=True)
class Trade:
    symbol: str
    action: str
    date: str
    price: float
    shares: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "action": self.action,
            "date": self.date,
            "price": self.price,
            "shares": self.shares,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class SymbolContribution:
    symbol: str
    pnl_cash: float
    contribution_percent: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "pnl_cash": self.pnl_cash,
            "contribution_percent": self.contribution_percent,
        }


@dataclass(frozen=True)
class BacktestResult:
    strategy_name: str
    symbols: list[str]
    start_date: str
    end_date: str
    signal_mode: str
    initial_cash: float
    final_value: float
    total_return_percent: float
    annualized_return_percent: float
    max_drawdown_percent: float
    sharpe_ratio: float | None
    win_rate_percent: float | None
    best_contributor: str | None
    worst_contributor: str | None
    contributions: list[SymbolContribution]
    benchmark_symbol: str
    benchmark_total_return_percent: float | None
    alpha_percent: float | None
    beta: float | None
    equity_curve: list[EquityPoint]
    trades: list[Trade]
    suggestions: list[str]
    risks: list[str]
    source: str
    algorithm_version: str
    generated_at: str
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "symbols": self.symbols,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "signal_mode": self.signal_mode,
            "initial_cash": self.initial_cash,
            "final_value": self.final_value,
            "total_return_percent": self.total_return_percent,
            "annualized_return_percent": self.annualized_return_percent,
            "max_drawdown_percent": self.max_drawdown_percent,
            "sharpe_ratio": self.sharpe_ratio,
            "win_rate_percent": self.win_rate_percent,
            "best_contributor": self.best_contributor,
            "worst_contributor": self.worst_contributor,
            "contributions": [c.to_dict() for c in self.contributions],
            "benchmark_symbol": self.benchmark_symbol,
            "benchmark_total_return_percent": self.benchmark_total_return_percent,
            "alpha_percent": self.alpha_percent,
            "beta": self.beta,
            "equity_curve": [p.to_dict() for p in self.equity_curve],
            "trades": [t.to_dict() for t in self.trades],
            "suggestions": self.suggestions,
            "risks": self.risks,
            "source": self.source,
            "algorithm_version": self.algorithm_version,
            "generated_at": self.generated_at,
            "risk_disclaimer": self.risk_disclaimer,
        }
