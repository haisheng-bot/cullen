from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


RISK_DISCLAIMER = "本系统仅用于投资研究辅助，不构成任何投资建议。"


@dataclass(frozen=True)
class ModelRequest:
    task_type: str
    system_instruction: str
    user_input: str
    context: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] | None = None
    model_provider: str | None = None
    model_name: str | None = None
    temperature: float = 0.2
    max_tokens: int = 2000
    trace_id: str | None = None


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True)
class ModelResponse:
    provider: str
    model_name: str
    task_type: str
    output: str
    citations: list[str]
    confidence: float | None
    token_usage: TokenUsage
    cost_estimate: float | None
    latency_ms: int | None
    trace_id: str | None
    input_summary: str = ""
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_audit_summary(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "task_type": self.task_type,
            "provider": self.provider,
            "model_name": self.model_name,
            "input_summary": self.input_summary[:500],
            "output_summary": self.output[:500],
            "citations": self.citations,
            "token_usage": {
                "input_tokens": self.token_usage.input_tokens,
                "output_tokens": self.token_usage.output_tokens,
                "total_tokens": self.token_usage.total_tokens,
            },
            "cost_estimate": self.cost_estimate,
            "latency_ms": self.latency_ms,
            "risk_disclaimer": self.risk_disclaimer,
        }

