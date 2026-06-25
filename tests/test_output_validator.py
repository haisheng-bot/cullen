import unittest

from packages.model_layer.mock_provider import MockModelProvider
from packages.model_layer.router import ModelRouter
from packages.model_layer.schemas import RISK_DISCLAIMER, ModelRequest, ModelResponse, TokenUsage
from packages.model_layer.validator import (
    OutputValidationError,
    find_banned_phrases,
    validate_model_response,
)


def make_response(**overrides) -> ModelResponse:
    defaults = dict(
        provider="mock",
        model_name="mock-model-v0",
        task_type="stock_analysis",
        output="AAPL shows steady momentum.",
        citations=["Yahoo Finance chart API"],
        confidence=0.5,
        token_usage=TokenUsage(input_tokens=1, output_tokens=1, total_tokens=2),
        cost_estimate=0.0,
        latency_ms=1,
        trace_id="trace-001",
    )
    defaults.update(overrides)
    return ModelResponse(**defaults)


class OutputValidatorTest(unittest.TestCase):
    def test_find_banned_phrases_detects_matches(self) -> None:
        self.assertEqual(["保证上涨"], find_banned_phrases("This stock is a 保证上涨 pick."))
        self.assertEqual([], find_banned_phrases("This is a neutral research note."))

    def test_validate_model_response_passes_for_compliant_response(self) -> None:
        validate_model_response(make_response())

    def test_validate_model_response_rejects_missing_disclaimer(self) -> None:
        with self.assertRaisesRegex(OutputValidationError, "risk_disclaimer"):
            validate_model_response(make_response(risk_disclaimer=""))

    def test_validate_model_response_rejects_missing_citations(self) -> None:
        with self.assertRaisesRegex(OutputValidationError, "citations"):
            validate_model_response(make_response(citations=[]))

    def test_validate_model_response_rejects_banned_phrases(self) -> None:
        with self.assertRaisesRegex(OutputValidationError, "稳赚"):
            validate_model_response(make_response(output="这是稳赚的机会"))

    def test_router_runs_validation_before_returning(self) -> None:
        router = ModelRouter(providers={"mock": MockModelProvider()}, default_provider="mock")
        response = router.generate(
            ModelRequest(
                task_type="stock_analysis",
                system_instruction="Analyze stock data.",
                user_input="Analyze AAPL.",
                context={"citations": ["Yahoo Finance chart API"]},
            )
        )

        self.assertEqual(RISK_DISCLAIMER, response.risk_disclaimer)


if __name__ == "__main__":
    unittest.main()
