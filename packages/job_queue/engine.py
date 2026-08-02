"""Lightweight APScheduler-based job queue for OpenStock AI.

This module wraps long-running operations (screening, portfolio research) as
background jobs with persistence in the `job_queue` table. It keeps the API
layer free of scheduling details while giving callers a stable `job_id` to
poll for status and results.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

from packages.db.backtest_runs import write_backtest_run
from packages.db.job_queue import JobRecord, create_job, update_job_status
from packages.db.session import session_scope
from packages.db.stock_scores import write_screening_result
from packages.db.workflow_runs import write_workflow_run
from packages.scoring_profiles.schemas import ScoringProfile
from packages.workflow_layer.portfolio_research import (
    PortfolioResearchRequest,
    PortfolioResearchWorkflow,
    build_response,
)
from packages.workflow_layer.stock_screening import StockScreeningWorkflow


class JobQueueEngine:
    """Singleton-style scheduler wrapper.

    The scheduler is started lazily on first use so that importing the module
    does not spawn background threads during tests.
    """

    def __init__(self) -> None:
        self._scheduler: BackgroundScheduler | None = None

    @property
    def scheduler(self) -> BackgroundScheduler:
        if self._scheduler is None:
            self._scheduler = BackgroundScheduler()
            self._scheduler.start()
        return self._scheduler

    def submit_screening(
        self,
        workflow: StockScreeningWorkflow,
        *,
        limit: int,
        profile: ScoringProfile,
        payload: dict[str, Any],
    ) -> JobRecord:
        """Enqueue a screening job and return its record immediately."""
        job_id = str(uuid4())
        with session_scope() as session:
            record = create_job(session, job_id, "screening", payload)
        self.scheduler.add_job(
            func=_run_screening,
            trigger=DateTrigger(run_date=datetime.now(timezone.utc)),
            id=job_id,
            args=[job_id, workflow, limit, profile],
            replace_existing=True,
        )
        return record

    def submit_portfolio_research(
        self,
        workflow: PortfolioResearchWorkflow,
        *,
        request: PortfolioResearchRequest,
        payload: dict[str, Any],
    ) -> JobRecord:
        """Enqueue a portfolio research job and return its record immediately."""
        job_id = str(uuid4())
        with session_scope() as session:
            record = create_job(session, job_id, "portfolio_research", payload)
        self.scheduler.add_job(
            func=_run_portfolio_research,
            trigger=DateTrigger(run_date=datetime.now(timezone.utc)),
            id=job_id,
            args=[job_id, workflow, request, payload],
            replace_existing=True,
        )
        return record

    def shutdown(self, wait: bool = True) -> None:
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=wait)


# Module-level singleton. Tests can replace or shut this down as needed.
job_queue = JobQueueEngine()


def _run_screening(
    job_id: str,
    workflow: StockScreeningWorkflow,
    limit: int,
    profile: ScoringProfile,
) -> None:
    with session_scope() as session:
        update_job_status(session, job_id, "running", progress_percent=0)
    try:
        result = workflow.screen(limit=limit, profile=profile)
        result_dict = result.to_dict()

        # Persist individual candidate scores for history charts.
        try:
            with session_scope() as session:
                write_screening_result(session, result)
        except Exception:
            # Screening result is still valuable even if history persistence fails.
            pass

        with session_scope() as session:
            update_job_status(session, job_id, "completed", result=result_dict, progress_percent=100)
    except Exception as exc:  # noqa: BLE001
        with session_scope() as session:
            update_job_status(session, job_id, "failed", error_message=str(exc), progress_percent=0)


def _run_portfolio_research(
    job_id: str,
    workflow: PortfolioResearchWorkflow,
    request: PortfolioResearchRequest,
    request_payload: dict[str, Any],
) -> None:
    with session_scope() as session:
        update_job_status(session, job_id, "running", progress_percent=0)
    try:
        workflow_result = workflow.run(request, trace_id=job_id)
        response = build_response(workflow_result)

        # Reuse existing backtest_runs/workflow_runs tables for full traceability,
        # matching what the sync /workflows/portfolio-research endpoint persists.
        final_config = workflow_result.payload.get("final_strategy_config")
        backtest_result = workflow_result.payload.get("backtest_result")
        try:
            with session_scope() as session:
                if final_config is not None and backtest_result is not None:
                    write_backtest_run(session, final_config, backtest_result)
                write_workflow_run(session, request_payload, response)
        except Exception:
            # Workflow result is still returned even if archival fails.
            pass

        with session_scope() as session:
            update_job_status(session, job_id, "completed", result=response, progress_percent=100)
    except Exception as exc:  # noqa: BLE001
        with session_scope() as session:
            update_job_status(session, job_id, "failed", error_message=str(exc), progress_percent=0)
