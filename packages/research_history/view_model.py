from __future__ import annotations

from packages.research_history.schemas import RunSummary


def summarize_run(
    *,
    trace_id: str,
    workflow_name: str,
    workflow_version: str,
    state: str,
    request: dict,
    response: dict,
    started_at: str,
    completed_at: str,
) -> RunSummary:
    """Builds one history-list row from a persisted `WorkflowRun`. `request`/
    `response` come from two different shapes depending on `workflow_name`
    (`portfolio_research_workflow` vs `portfolio_research_module`); both
    happen to share a `response["portfolio"] = {"name", "symbols"}` shape, so
    only the recommendation/backtest summary fields need a fallback lookup.
    """
    portfolio = response.get("portfolio") or {}
    return RunSummary(
        trace_id=trace_id,
        workflow_name=workflow_name,
        workflow_version=workflow_version,
        state=state,
        portfolio_name=portfolio.get("name"),
        symbols=portfolio.get("symbols") or [],
        strategy_library_name=request.get("strategy_library_name"),
        summary_text=_build_summary_text(response),
        started_at=started_at,
        completed_at=completed_at,
    )


def _build_summary_text(response: dict) -> str:
    recommendation = response.get("recommendation") or response.get("portfolio_recommendation") or {}
    backtest = response.get("backtest_summary") or response.get("backtest") or {}

    parts = []
    action = recommendation.get("action")
    if action:
        parts.append(f"建议：{action}")
    total_return = backtest.get("total_return_percent")
    if total_return is not None:
        parts.append(f"回测总收益 {total_return}%")
    return "；".join(parts) if parts else "暂无摘要"
