from __future__ import annotations

from sqlalchemy.orm import Session

from packages.db.models import AuditLog
from packages.model_layer.schemas import ModelResponse


def write_audit_log(session: Session, response: ModelResponse) -> AuditLog:
    """Persist a ModelResponse as an audit_logs row.

    This is the Audit Logger stage in the AI architecture pipeline
    (see docs/architecture/ai-development-architecture.md section 3).
    """
    summary = response.to_audit_summary()
    record = AuditLog(
        trace_id=summary["trace_id"],
        task_type=summary["task_type"],
        provider=summary["provider"],
        model_name=summary["model_name"],
        input_summary=summary["input_summary"],
        output_summary=summary["output_summary"],
        citations=summary["citations"],
        token_usage=summary["token_usage"],
        cost_estimate=summary["cost_estimate"],
        latency_ms=summary["latency_ms"],
        risk_disclaimer=summary["risk_disclaimer"],
    )
    session.add(record)
    session.flush()
    return record
