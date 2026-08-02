"""Pydantic schemas for the async job queue API."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


JobType = Literal["screening", "portfolio_research"]
JobStatus = Literal["pending", "running", "completed", "failed", "cancelled"]


class JobSubmissionResponse(BaseModel):
    """Response returned immediately when a job is submitted."""

    job_id: str
    job_type: JobType
    status: JobStatus
    created_at: datetime
    message: str = "Job submitted successfully."


class JobResult(BaseModel):
    """Payload returned for a completed job. Kept generic so different job
    types can store their own shape in `result`.
    """

    status: JobStatus
    result: dict[str, Any] | None = None
    error_message: str | None = None
    progress_percent: int = Field(0, ge=0, le=100)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class JobDetailResponse(BaseModel):
    """Full job detail, used by `GET /jobs/{job_id}`."""

    job_id: str
    job_type: JobType
    status: JobStatus
    payload: dict[str, Any]
    result: dict[str, Any] | None = None
    error_message: str | None = None
    progress_percent: int = Field(0, ge=0, le=100)
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class JobListResponse(BaseModel):
    """List of jobs returned by `GET /jobs`."""

    items: list[JobDetailResponse]
    total_count: int
    limit: int
    offset: int
