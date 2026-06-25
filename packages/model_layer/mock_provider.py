from __future__ import annotations

from time import perf_counter

from packages.model_layer.base import ModelProvider
from packages.model_layer.schemas import ModelRequest, ModelResponse, TokenUsage


class MockModelProvider(ModelProvider):
    provider_name = "mock"

    def generate(self, request: ModelRequest) -> ModelResponse:
        started = perf_counter()
        output = f"Mock response for {request.task_type}: {request.user_input}"
        output_tokens = len(output.split())
        input_tokens = len(request.system_instruction.split()) + len(request.user_input.split())
        return ModelResponse(
            provider=self.provider_name,
            model_name=request.model_name or "mock-model-v0",
            task_type=request.task_type,
            output=output,
            citations=list(request.context.get("citations", [])),
            confidence=0.5,
            token_usage=TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            ),
            cost_estimate=0.0,
            latency_ms=int((perf_counter() - started) * 1000),
            trace_id=request.trace_id,
            input_summary=request.user_input[:500],
        )

