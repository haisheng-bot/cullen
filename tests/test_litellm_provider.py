import unittest

from packages.model_layer.providers.litellm_provider import (
    LiteLLMProvider,
    build_messages,
    extract_text,
    extract_token_usage,
)
from packages.model_layer.schemas import ModelRequest


class LiteLLMProviderTest(unittest.TestCase):
    def test_build_messages_includes_context(self) -> None:
        request = ModelRequest(
            task_type="report_generation",
            system_instruction="You are an analyst.",
            user_input="Analyze AAPL.",
            context={"summary": "AAPL close price is 200.", "citations": ["Yahoo Finance"]},
        )

        messages = build_messages(request)

        self.assertEqual("system", messages[0]["role"])
        self.assertIn("AAPL close price", messages[1]["content"])
        self.assertIn("Analyze AAPL", messages[1]["content"])

    def test_litellm_provider_uses_openai_compatible_response(self) -> None:
        def fake_completion(**kwargs):
            self.assertEqual("openai/gpt-4o-mini", kwargs["model"])
            self.assertEqual(2, len(kwargs["messages"]))
            return {
                "choices": [{"message": {"content": "Structured model output"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            }

        provider = LiteLLMProvider(completion_func=fake_completion)
        response = provider.generate(
            ModelRequest(
                task_type="stock_analysis",
                system_instruction="Analyze stock data.",
                user_input="Analyze MSFT.",
                context={"citations": ["Yahoo Finance"]},
                trace_id="trace-litellm-001",
            )
        )

        self.assertEqual("litellm", response.provider)
        self.assertEqual("openai/gpt-4o-mini", response.model_name)
        self.assertEqual("Structured model output", response.output)
        self.assertEqual(["Yahoo Finance"], response.citations)
        self.assertEqual(15, response.token_usage.total_tokens)
        self.assertEqual("trace-litellm-001", response.trace_id)

    def test_extract_helpers_handle_dict_response(self) -> None:
        raw = {
            "choices": [{"message": {"content": "hello"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 2},
        }

        self.assertEqual("hello", extract_text(raw))
        self.assertEqual(3, extract_token_usage(raw).total_tokens)


if __name__ == "__main__":
    unittest.main()

