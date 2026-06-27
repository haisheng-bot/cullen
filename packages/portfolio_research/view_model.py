from __future__ import annotations

from packages.portfolio_research.schemas import PortfolioResearchRunRequest, PortfolioResearchRunResult


def build_portfolio_research_view(
    request: PortfolioResearchRunRequest,
    *,
    workflow_response: dict,
    risk_response: dict | None,
    optimizer_response: dict | None,
) -> PortfolioResearchRunResult:
    backtest = workflow_response.get("backtest") or {}
    recommendation = workflow_response.get("portfolio_recommendation")
    ai_summary = workflow_response.get("ai_summary")
    warnings = list(backtest.get("risks") or [])
    if risk_response is None:
        warnings.append("Risk Engine 暂未返回结果。")
    if optimizer_response is None:
        warnings.append("Portfolio Optimizer 暂未返回结果。")

    return PortfolioResearchRunResult(
        trace_id=workflow_response["trace_id"],
        state=_normalize_state(workflow_response.get("state")),
        portfolio=workflow_response.get("portfolio") or {
            "name": request.portfolio_name,
            "symbols": request.symbols,
        },
        score_summary=_score_summary(workflow_response),
        backtest_summary=_backtest_summary(backtest),
        risk_summary=risk_response,
        optimized_weights=optimizer_response,
        ai_explanation=ai_summary,
        recommendation=recommendation,
        warnings=warnings,
        workflow={
            "name": workflow_response.get("workflow_name"),
            "version": workflow_response.get("workflow_version"),
            "node_results": workflow_response.get("node_results") or [],
            "response": workflow_response,
        },
        source="OpenStock AI Portfolio Research Module v0.1",
        started_at=workflow_response["started_at"],
        completed_at=workflow_response["completed_at"],
    )


def _normalize_state(state: str | None) -> str:
    if state == "Recommendation Ready":
        return "completed"
    if state == "Failed":
        return "failed"
    return (state or "unknown").lower().replace(" ", "_")


def _backtest_summary(backtest: dict) -> dict | None:
    if not backtest:
        return None
    keys = [
        "strategy_name",
        "symbols",
        "total_return_percent",
        "annualized_return_percent",
        "max_drawdown_percent",
        "sharpe_ratio",
        "alpha_percent",
        "beta",
        "best_contributor",
        "worst_contributor",
        "source",
        "algorithm_version",
    ]
    return {key: backtest.get(key) for key in keys}


def _score_summary(workflow_response: dict) -> dict | None:
    backtest = workflow_response.get("backtest") or {}
    return {
        "scoring_mode": "algorithm_v0.3",
        "signal_mode": backtest.get("signal_mode"),
        "symbols": backtest.get("symbols") or [],
        "note": "v0.1 uses workflow/backtest outputs as the unified scoring summary.",
    }
