"""Agent base class implementing the required AI pipeline.

Per docs/architecture/ai-development-architecture.md section 3:

    Policy Guard -> Data Context Builder -> Workflow Executor
        -> Model Layer -> Agent Executor -> Output Validator -> Audit Logger

Agents only define task input/output and call into Model Layer via
ModelRouter; they never import a model SDK or read API keys directly
(see MODEL_STANDARD.md section 9).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from packages.data_sources.market_trend import normalize_symbol
from packages.db.audit import write_audit_log
from packages.db.session import session_scope
from packages.model_layer.router import ModelRouter
from packages.model_layer.schemas import ModelRequest, ModelResponse


@dataclass(frozen=True)
class AgentResult:
    symbol: str
    task_type: str
    response: ModelResponse
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "task_type": self.task_type,
            "model": f"{self.response.provider}/{self.response.model_name}",
            "data_source": self.response.citations,
            "input_summary": self.response.input_summary,
            "conclusion": self.response.output,
            "analysis_time": self.generated_at,
            "trace_id": self.response.trace_id,
            "risk_disclaimer": self.response.risk_disclaimer,
        }


class Agent(ABC):
    task_type: str
    system_instruction: str
    default_model_provider: str | None = None

    def __init__(self, router: ModelRouter) -> None:
        self.router = router

    @abstractmethod
    def build_context(self, symbol: str) -> dict[str, Any]:
        """Data Context Builder: gather inputs from data sources.

        Must return a dict containing at least a non-empty "citations" list,
        since Output Validator rejects responses without a data source.
        """

    @abstractmethod
    def build_user_input(self, symbol: str, context: dict[str, Any]) -> str:
        """Workflow Executor: turn the gathered context into model user_input."""

    def run(self, symbol: str, *, trace_id: str | None = None, write_audit: bool = True) -> AgentResult:
        normalized_symbol = normalize_symbol(symbol)  # Policy Guard
        context = self.build_context(normalized_symbol)  # Data Context Builder
        user_input = self.build_user_input(normalized_symbol, context)  # Workflow Executor

        request = ModelRequest(
            task_type=self.task_type,
            system_instruction=self.system_instruction,
            user_input=user_input,
            context=context,
            model_provider=self.default_model_provider,
            trace_id=trace_id or str(uuid4()),
        )
        response = self.router.generate(request)  # Model Layer (includes Output Validator)

        if write_audit:
            with session_scope() as session:
                write_audit_log(session, response)  # Audit Logger

        return AgentResult(
            symbol=normalized_symbol,
            task_type=self.task_type,
            response=response,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
