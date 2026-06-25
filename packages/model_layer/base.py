from __future__ import annotations

from abc import ABC, abstractmethod

from packages.model_layer.schemas import ModelRequest, ModelResponse


class ModelProvider(ABC):
    provider_name: str

    @abstractmethod
    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a model response using a provider-specific backend."""

