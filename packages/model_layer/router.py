from __future__ import annotations

from packages.model_layer.base import ModelProvider
from packages.model_layer.schemas import ModelRequest, ModelResponse


class ModelRouter:
    def __init__(self, providers: dict[str, ModelProvider], default_provider: str) -> None:
        self.providers = providers
        self.default_provider = default_provider

    def generate(self, request: ModelRequest) -> ModelResponse:
        provider_name = request.model_provider or self.default_provider
        provider = self.providers.get(provider_name) or self.providers.get(self.default_provider)
        if provider is None:
            raise ValueError("No model provider is available")
        return provider.generate(request)

