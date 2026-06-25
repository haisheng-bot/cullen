"""Builds the default ModelRouter based on configured API keys.

No Agent or Workflow should construct providers directly; they ask
this factory for a router instead. Without any model API key
configured, everything falls back to MockModelProvider so the system
stays usable offline (see docs/standards/agile-iteration.md "即开发即使用").
"""
from __future__ import annotations

from packages.config import get_settings
from packages.model_layer.mock_provider import MockModelProvider
from packages.model_layer.providers.litellm_provider import LiteLLMProvider
from packages.model_layer.router import ModelRouter


def build_default_router() -> ModelRouter:
    settings = get_settings()
    providers = {"mock": MockModelProvider()}
    default_provider = "mock"

    has_model_key = any(
        [
            settings.openai_api_key,
            settings.anthropic_api_key,
            settings.google_api_key,
            settings.deepseek_api_key,
            settings.qwen_api_key,
        ]
    )
    if has_model_key:
        providers["litellm"] = LiteLLMProvider()
        default_provider = "litellm"

    return ModelRouter(providers=providers, default_provider=default_provider)
