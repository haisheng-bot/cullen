from __future__ import annotations

from time import perf_counter
from typing import Any, Callable

from packages.model_layer.base import ModelProvider
from packages.model_layer.schemas import ModelRequest, ModelResponse, TokenUsage


CompletionFunc = Callable[..., Any]


class LiteLLMProvider(ModelProvider):
    provider_name = "litellm"

    def __init__(
        self,
        default_model: str = "openai/gpt-4o-mini",
        completion_func: CompletionFunc | None = None,
    ) -> None:
        self.default_model = default_model
        self._completion_func = completion_func

    def generate(self, request: ModelRequest) -> ModelResponse:
        completion_func = self._completion_func or _load_litellm_completion()
        model_name = request.model_name or self.default_model
        started = perf_counter()
        messages = build_messages(request)

        raw_response = completion_func(
            model=model_name,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        latency_ms = int((perf_counter() - started) * 1000)
        output = extract_text(raw_response)
        token_usage = extract_token_usage(raw_response)

        return ModelResponse(
            provider=self.provider_name,
            model_name=model_name,
            task_type=request.task_type,
            output=output,
            citations=list(request.context.get("citations", [])),
            confidence=None,
            token_usage=token_usage,
            cost_estimate=None,
            latency_ms=latency_ms,
            trace_id=request.trace_id,
            input_summary=request.user_input[:500],
        )


def build_messages(request: ModelRequest) -> list[dict[str, str]]:
    context = request.context.get("summary") or request.context.get("input_summary") or ""
    user_content = request.user_input
    if context:
        user_content = f"Context:\n{context}\n\nUser request:\n{request.user_input}"
    return [
        {"role": "system", "content": request.system_instruction},
        {"role": "user", "content": user_content},
    ]


def extract_text(raw_response: Any) -> str:
    if isinstance(raw_response, dict):
        choices = raw_response.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            return str(message.get("content") or "")

    choices = getattr(raw_response, "choices", None) or []
    if choices:
        message = getattr(choices[0], "message", None)
        if isinstance(message, dict):
            return str(message.get("content") or "")
        return str(getattr(message, "content", "") or "")
    return ""


def extract_token_usage(raw_response: Any) -> TokenUsage:
    usage = raw_response.get("usage") if isinstance(raw_response, dict) else getattr(raw_response, "usage", None)
    if usage is None:
        return TokenUsage()
    if isinstance(usage, dict):
        input_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or input_tokens + output_tokens)
        return TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens, total_tokens=total_tokens)

    input_tokens = int(getattr(usage, "prompt_tokens", 0) or getattr(usage, "input_tokens", 0) or 0)
    output_tokens = int(
        getattr(usage, "completion_tokens", 0) or getattr(usage, "output_tokens", 0) or 0
    )
    total_tokens = int(getattr(usage, "total_tokens", 0) or input_tokens + output_tokens)
    return TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens, total_tokens=total_tokens)


def _load_litellm_completion() -> CompletionFunc:
    try:
        from litellm import completion
    except ImportError as exc:
        raise RuntimeError("LiteLLM is not installed. Install the model extra before using LiteLLMProvider.") from exc
    return completion

