"""Output compliance validation for Model Layer responses.

Implements the checks required by MODEL_STANDARD.md section 13: every
ModelResponse must carry a risk disclaimer, model identity, and at
least one citation/data source, and must not contain banned phrases
that promise gains or induce a buy/sell action. This runs inside the
Model Layer, before a response reaches any Agent or Workflow.
"""
from __future__ import annotations

from packages.model_layer.schemas import RISK_DISCLAIMER, ModelResponse

BANNED_PHRASES = (
    "必买",
    "保证上涨",
    "无风险",
    "稳赚",
    "立即买入",
    "立即卖出",
)


class OutputValidationError(RuntimeError):
    """Raised when a ModelResponse fails compliance validation."""


def find_banned_phrases(text: str) -> list[str]:
    return [phrase for phrase in BANNED_PHRASES if phrase in text]


def validate_model_response(response: ModelResponse) -> None:
    """Raise OutputValidationError listing every compliance violation found."""
    violations: list[str] = []

    if not response.risk_disclaimer or response.risk_disclaimer != RISK_DISCLAIMER:
        violations.append("missing or altered risk_disclaimer")

    if not response.citations:
        violations.append("missing citations / data source")

    if not response.provider or not response.model_name:
        violations.append("missing model provider/model_name")

    banned_found = find_banned_phrases(response.output)
    if banned_found:
        violations.append(f"banned phrases in output: {', '.join(banned_found)}")

    if violations:
        raise OutputValidationError(
            f"ModelResponse failed compliance validation: {'; '.join(violations)}"
        )
