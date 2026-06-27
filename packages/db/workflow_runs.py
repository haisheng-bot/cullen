from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.db.models import WorkflowRun


def write_workflow_run(session: Session, request: dict, response: dict) -> WorkflowRun:
    """Persist one Portfolio Research Workflow response for trace_id replay."""
    record = WorkflowRun(
        trace_id=response["trace_id"],
        workflow_name=response["workflow_name"],
        workflow_version=response["workflow_version"],
        state=response["state"],
        request=request,
        response=response,
        risk_disclaimer=response["risk_disclaimer"],
        started_at=response["started_at"],
        completed_at=response["completed_at"],
    )
    session.add(record)
    session.flush()
    return record


def get_workflow_run_by_trace_id(session: Session, trace_id: str) -> WorkflowRun | None:
    return session.scalar(select(WorkflowRun).where(WorkflowRun.trace_id == trace_id))


def list_workflow_runs(
    session: Session, *, workflow_name: str | None = None, state: str | None = None
) -> list[WorkflowRun]:
    """Newest first. Only filters on indexed columns (`workflow_name`/
    `state`); portfolio/strategy/date filters live in `packages.research_history`
    since those fields are inside the `request`/`response` JSON blobs.
    """
    stmt = select(WorkflowRun).order_by(WorkflowRun.created_at.desc())
    if workflow_name is not None:
        stmt = stmt.where(WorkflowRun.workflow_name == workflow_name)
    if state is not None:
        stmt = stmt.where(WorkflowRun.state == state)
    return list(session.scalars(stmt))
