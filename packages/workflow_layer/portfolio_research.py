"""Portfolio Research Workflow v0.1.

This workflow turns the user's requested research loop into a reusable
orchestration: Universe -> Portfolio -> Strategy -> Constraint -> Backtest
-> AI-style summary -> Recommendation. The summary is deterministic in v0.1;
later versions can swap that node for a Research/Report Agent without changing
the workflow boundary.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any

from packages.backtesting.schemas import BacktestResult, StrategyConfig
from packages.workflow_layer.engine import WorkflowEngine, WorkflowNode
from packages.workflow_layer.schemas import RISK_DISCLAIMER


@dataclass(frozen=True)
class PortfolioResearchRequest:
    strategy_config: StrategyConfig
    universe_limit: int = 100
    portfolio_name: str = "Workflow Portfolio"
    selected_symbols: list[str] | None = None


class PortfolioResearchWorkflow:
    """Business-level workflow for portfolio research and recommendation."""

    version = "portfolio-research-workflow-v0.1"

    def __init__(
        self,
        universe_scanner,
        backtest_engine,
        portfolio_symbols_fetcher: Callable[[str], list[str]] | None = None,
    ) -> None:
        self.universe_scanner = universe_scanner
        self.backtest_engine = backtest_engine
        self.portfolio_symbols_fetcher = portfolio_symbols_fetcher or (lambda name: [])

    def run(self, request: PortfolioResearchRequest, trace_id: str | None = None):
        engine = WorkflowEngine(
            name="portfolio_research_workflow",
            version=self.version,
            nodes=[
                WorkflowNode("Universe Builder", self._universe_builder, "Universe Layer"),
                WorkflowNode("Portfolio Builder", self._portfolio_builder, "Portfolio Layer"),
                WorkflowNode("Strategy Selector", self._strategy_selector, "Strategy Layer"),
                WorkflowNode("Constraint Config", self._constraint_config, "Constraint Engine"),
                WorkflowNode("Backtest Runner", self._backtest_runner, "Backtesting Engine"),
                WorkflowNode("AI Summary", self._ai_summary, "AI Research"),
                WorkflowNode("Portfolio Recommendation", self._recommendation, "Recommendation Engine"),
            ],
        )
        return engine.run(
            {
                "request": request,
                "portfolio_name": request.portfolio_name,
                "strategy_config": request.strategy_config,
                "universe_limit": request.universe_limit,
                "selected_symbols": request.selected_symbols,
            },
            trace_id=trace_id,
        )

    def _universe_builder(self, context, payload: dict[str, Any]) -> dict[str, Any]:
        limit = int(payload["universe_limit"])
        universe = self.universe_scanner.scan(limit=limit)
        symbols = [item.symbol for item in universe.items]
        return {
            "universe": universe.to_dict(),
            "universe_symbols": symbols,
        }

    def _portfolio_builder(self, context, payload: dict[str, Any]) -> dict[str, Any]:
        request: PortfolioResearchRequest = payload["request"]
        config: StrategyConfig = payload["strategy_config"]
        selected = request.selected_symbols or config.symbols or self.portfolio_symbols_fetcher(
            request.portfolio_name
        )
        if not selected:
            selected = payload["universe_symbols"][:5]

        normalized_symbols = list(dict.fromkeys(symbol.upper() for symbol in selected if symbol.strip()))
        if not normalized_symbols:
            raise ValueError("portfolio requires at least one symbol")

        return {
            "portfolio": {
                "name": request.portfolio_name,
                "symbols": normalized_symbols,
                "benchmark": config.benchmark_symbol,
                "source": "user_selection_or_universe",
            },
            "portfolio_symbols": normalized_symbols,
        }

    def _strategy_selector(self, context, payload: dict[str, Any]) -> dict[str, Any]:
        config: StrategyConfig = payload["strategy_config"]
        portfolio_symbols: list[str] = payload["portfolio_symbols"]
        final_config = replace(config, symbols=portfolio_symbols)
        return {
            "final_strategy_config": final_config,
            "strategy": {
                "name": final_config.strategy_name,
                "signal_mode": final_config.signal_mode,
                "rebalance_frequency": final_config.rebalance_frequency,
                "benchmark_symbol": final_config.benchmark_symbol,
                "start_date": final_config.start_date,
                "end_date": final_config.end_date,
            },
        }

    def _constraint_config(self, context, payload: dict[str, Any]) -> dict[str, Any]:
        config: StrategyConfig = payload["final_strategy_config"]
        return {
            "constraints": {
                "allocation": config.allocation.to_dict(),
                "entry_rules": config.entry_rules.to_dict(),
                "exit_rules": config.exit_rules.to_dict(),
                "risk": config.risk.to_dict(),
                "sector_map_count": len(config.sector_map),
            }
        }

    def _backtest_runner(self, context, payload: dict[str, Any]) -> dict[str, Any]:
        config: StrategyConfig = payload["final_strategy_config"]
        result = self.backtest_engine.run(config)
        return {
            "backtest_result": result,
            "backtest": result.to_dict(),
        }

    def _ai_summary(self, context, payload: dict[str, Any]) -> dict[str, Any]:
        result: BacktestResult = payload["backtest_result"]
        summary = _build_ai_summary(result)
        return {"ai_summary": summary}

    def _recommendation(self, context, payload: dict[str, Any]) -> dict[str, Any]:
        result: BacktestResult = payload["backtest_result"]
        summary: dict[str, Any] = payload["ai_summary"]
        return {
            "portfolio_recommendation": {
                "action": _recommended_action(result),
                "reasons": summary["key_findings"],
                "suggestions": result.suggestions,
                "risks": result.risks,
                "risk_disclaimer": RISK_DISCLAIMER,
            }
        }


def _build_ai_summary(result: BacktestResult) -> dict[str, Any]:
    findings = [
        f"回测总收益 {result.total_return_percent}%，年化收益 {result.annualized_return_percent}%。",
        f"最大回撤 {result.max_drawdown_percent}%，用于判断策略风险承受压力。",
    ]
    if result.sharpe_ratio is not None:
        findings.append(f"Sharpe Ratio 为 {result.sharpe_ratio}，用于衡量单位风险收益。")
    if result.alpha_percent is not None:
        findings.append(f"相对 {result.benchmark_symbol} 的 Alpha 为 {result.alpha_percent}%。")
    if result.best_contributor:
        findings.append(f"{result.best_contributor} 是本次回测贡献最大的标的。")
    if result.worst_contributor and result.worst_contributor != result.best_contributor:
        findings.append(f"{result.worst_contributor} 是本次回测拖累最大的标的。")

    return {
        "summary_type": "deterministic_ai_research_summary_v0.1",
        "conclusion": _summary_conclusion(result),
        "key_findings": findings,
        "risk_disclaimer": RISK_DISCLAIMER,
    }


def _summary_conclusion(result: BacktestResult) -> str:
    if result.total_return_percent > 0 and result.max_drawdown_percent <= 20:
        return "该组合在回测窗口内表现为正，且回撤处于可继续研究区间。"
    if result.total_return_percent > 0:
        return "该组合回测收益为正，但回撤偏高，需要进一步控制风险。"
    return "该组合回测收益不理想，建议调整标的、策略或约束后重新测试。"


def _recommended_action(result: BacktestResult) -> str:
    if result.total_return_percent > 0 and result.max_drawdown_percent <= 20:
        return "research_candidate"
    if result.total_return_percent > 0:
        return "reduce_risk_and_retest"
    return "revise_portfolio"
