"""Reusable Workflow Engine primitives.

The engine is intentionally small: it owns orchestration, state transitions
and observability metadata, while business modules continue to own real
algorithm, model, risk and reporting logic.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import StrEnum
from time import perf_counter
from typing import Any
from uuid import uuid4

from packages.workflow_layer.schemas import RISK_DISCLAIMER


class WorkflowState(StrEnum):
    CREATED = "Created"
    CONFIGURED = "Configured"
    WAITING = "Waiting"
    RUNNING = "Running"
    COMPLETED = "Completed"
    AI_REVIEWING = "AI Reviewing"
    RECOMMENDATION_READY = "Recommendation Ready"
    ARCHIVED = "Archived"
    FAILED = "Failed"


ALLOWED_TRANSITIONS: dict[WorkflowState, set[WorkflowState]] = {
    WorkflowState.CREATED: {WorkflowState.CONFIGURED, WorkflowState.FAILED},
    WorkflowState.CONFIGURED: {WorkflowState.WAITING, WorkflowState.FAILED},
    WorkflowState.WAITING: {WorkflowState.RUNNING, WorkflowState.FAILED},
    WorkflowState.RUNNING: {
        WorkflowState.COMPLETED,
        WorkflowState.AI_REVIEWING,
        WorkflowState.FAILED,
    },
    WorkflowState.COMPLETED: {
        WorkflowState.AI_REVIEWING,
        WorkflowState.RECOMMENDATION_READY,
        WorkflowState.ARCHIVED,
    },
    WorkflowState.AI_REVIEWING: {WorkflowState.RECOMMENDATION_READY, WorkflowState.FAILED},
    WorkflowState.RECOMMENDATION_READY: {WorkflowState.ARCHIVED},
    WorkflowState.ARCHIVED: set(),
    WorkflowState.FAILED: set(),
}


class WorkflowEngineError(RuntimeError):
    """Raised when workflow execution or state transitions fail."""


@dataclass(frozen=True)
class WorkflowExecutionContext:
    workflow_name: str
    workflow_version: str
    trace_id: str
    payload: dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    risk_disclaimer: str = RISK_DISCLAIMER


@dataclass(frozen=True)
class WorkflowNode:
    name: str
    handler: Callable[[WorkflowExecutionContext, dict[str, Any]], dict[str, Any]]
    module: str
    description: str = ""


@dataclass(frozen=True)
class WorkflowNodeResult:
    name: str
    module: str
    state: WorkflowState
    input_summary: dict[str, Any]
    output_summary: dict[str, Any] | None
    duration_ms: int
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "module": self.module,
            "state": self.state.value,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


@dataclass(frozen=True)
class WorkflowRunResult:
    workflow_name: str
    workflow_version: str
    trace_id: str
    state: WorkflowState
    started_at: str
    completed_at: str
    node_results: list[WorkflowNodeResult]
    payload: dict[str, Any]
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_name": self.workflow_name,
            "workflow_version": self.workflow_version,
            "trace_id": self.trace_id,
            "state": self.state.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "node_results": [result.to_dict() for result in self.node_results],
            "payload": self.payload,
            "risk_disclaimer": self.risk_disclaimer,
        }


def transition_workflow_state(current: WorkflowState, next_state: WorkflowState) -> WorkflowState:
    if next_state not in ALLOWED_TRANSITIONS[current]:
        raise WorkflowEngineError(f"invalid workflow transition: {current.value} -> {next_state.value}")
    return next_state


class WorkflowEngine:
    def __init__(
        self,
        name: str,
        nodes: list[WorkflowNode],
        version: str = "workflow-engine-v1.0",
    ) -> None:
        if not name.strip():
            raise ValueError("workflow name is required")
        if not nodes:
            raise ValueError("workflow requires at least one node")
        self.name = name
        self.nodes = nodes
        self.version = version

    def run(self, payload: dict[str, Any], trace_id: str | None = None) -> WorkflowRunResult:
        state = WorkflowState.CREATED
        started_at = datetime.now(timezone.utc).isoformat()
        context = WorkflowExecutionContext(
            workflow_name=self.name,
            workflow_version=self.version,
            trace_id=trace_id or str(uuid4()),
            payload=payload,
        )

        state = transition_workflow_state(state, WorkflowState.CONFIGURED)
        state = transition_workflow_state(state, WorkflowState.WAITING)
        state = transition_workflow_state(state, WorkflowState.RUNNING)

        current_payload = dict(payload)
        node_results: list[WorkflowNodeResult] = []

        for node in self.nodes:
            node_input = _summarize_payload(current_payload)
            node_start = perf_counter()
            try:
                output = node.handler(context, current_payload)
                if not isinstance(output, dict):
                    raise WorkflowEngineError(f"workflow node {node.name} must return a dict")
                current_payload.update(output)
                node_results.append(
                    WorkflowNodeResult(
                        name=node.name,
                        module=node.module,
                        state=WorkflowState.COMPLETED,
                        input_summary=node_input,
                        output_summary=_summarize_payload(output),
                        duration_ms=_elapsed_ms(node_start),
                    )
                )
            except Exception as exc:
                node_results.append(
                    WorkflowNodeResult(
                        name=node.name,
                        module=node.module,
                        state=WorkflowState.FAILED,
                        input_summary=node_input,
                        output_summary=None,
                        duration_ms=_elapsed_ms(node_start),
                        error=str(exc),
                    )
                )
                state = WorkflowState.FAILED
                return WorkflowRunResult(
                    workflow_name=self.name,
                    workflow_version=self.version,
                    trace_id=context.trace_id,
                    state=state,
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    node_results=node_results,
                    payload=current_payload,
                )

        state = transition_workflow_state(state, WorkflowState.COMPLETED)
        state = transition_workflow_state(state, WorkflowState.RECOMMENDATION_READY)

        return WorkflowRunResult(
            workflow_name=self.name,
            workflow_version=self.version,
            trace_id=context.trace_id,
            state=state,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc).isoformat(),
            node_results=node_results,
            payload=current_payload,
        )


def _elapsed_ms(start: float) -> int:
    return int((perf_counter() - start) * 1000)


def _summarize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, list):
            summary[key] = {"type": "list", "count": len(value)}
        elif isinstance(value, dict):
            summary[key] = {"type": "dict", "keys": sorted(value.keys())[:20]}
        elif is_dataclass(value):
            summary[key] = {"type": value.__class__.__name__}
        else:
            summary[key] = value
    return summary
