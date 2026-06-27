from __future__ import annotations

from sqlalchemy.orm import Session

from packages.db.workflow_runs import get_workflow_run_by_trace_id, write_workflow_run
from packages.portfolio_research.schemas import PortfolioResearchRunRequest


def write_portfolio_research_run(
    session: Session, request: PortfolioResearchRunRequest, response: dict
) -> None:
    write_workflow_run(session, request.to_dict(), response)


def get_portfolio_research_run(session: Session, trace_id: str) -> dict | None:
    record = get_workflow_run_by_trace_id(session, trace_id)
    if record is None or record.workflow_name != "portfolio_research_module":
        return None
    return record.response
