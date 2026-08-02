"""Job queue persistence for async long-running tasks.

OpenStock AI has several operations that can take tens of seconds (screening
the Most Active universe, running a full Portfolio Research workflow). This
module provides a small, database-backed job queue so callers can submit a
task, receive a job_id, and poll for status/progress without blocking an
HTTP worker.

The queue is intentionally lightweight: APScheduler handles scheduling and
execution (see `packages.job_queue.engine`), while this module only persists
state for the API layer to submit/query jobs.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.db.models import JobRecord


def create_job(session: Session, job_id: str, job_type: str, payload: dict[str, Any]) -> JobRecord:
    """Persist a new pending job and return the record."""
    record = JobRecord(
        id=job_id,
        job_type=job_type,
        status="pending",
        payload=payload,
        progress_percent=0,
    )
    session.add(record)
    session.flush()
    return record


def get_job(session: Session, job_id: str) -> JobRecord | None:
    """Fetch a single job by id."""
    return session.scalar(select(JobRecord).where(JobRecord.id == job_id))


def list_jobs(
    session: Session,
    *,
    job_type: str | None = None,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[JobRecord]:
    """List jobs, newest first, with optional filters."""
    stmt = select(JobRecord).order_by(JobRecord.created_at.desc())
    if job_type:
        stmt = stmt.where(JobRecord.job_type == job_type)
    if status:
        stmt = stmt.where(JobRecord.status == status)
    return list(session.scalars(stmt.offset(offset).limit(limit)).all())


def count_jobs(session: Session, *, job_type: str | None = None, status: str | None = None) -> int:
    """Count jobs matching the same filters as `list_jobs`, for pagination totals."""
    stmt = select(func.count()).select_from(JobRecord)
    if job_type:
        stmt = stmt.where(JobRecord.job_type == job_type)
    if status:
        stmt = stmt.where(JobRecord.status == status)
    return session.scalar(stmt) or 0


def update_job_status(
    session: Session,
    job_id: str,
    status: str | None,
    *,
    result: dict[str, Any] | None = None,
    error_message: str | None = None,
    progress_percent: int | None = None,
) -> JobRecord | None:
    """Update a job's status and optional fields.

    Automatically sets started_at when transitioning to 'running' and
    completed_at when transitioning to a terminal state.
    """
    record = session.scalar(select(JobRecord).where(JobRecord.id == job_id))
    if record is None:
        return None

    now = datetime.now(timezone.utc)
    if status is not None:
        record.status = status
        if status == "running" and record.started_at is None:
            record.started_at = now
        if status in ("completed", "failed", "cancelled"):
            record.completed_at = now

    if result is not None:
        record.result = result
    if error_message is not None:
        record.error_message = error_message
    if progress_percent is not None:
        record.progress_percent = max(0, min(100, progress_percent))

    return record


def increment_job_progress(session: Session, job_id: str, progress_percent: int) -> JobRecord | None:
    """Convenience helper to bump progress without changing status."""
    return update_job_status(session, job_id, status=None, progress_percent=progress_percent)
