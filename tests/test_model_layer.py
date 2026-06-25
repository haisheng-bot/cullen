import unittest

from packages.model_layer.mock_provider import MockModelProvider
from packages.model_layer.router import ModelRouter
from packages.model_layer.schemas import RISK_DISCLAIMER, ModelRequest


class ModelLayerTest(unittest.TestCase):
    def test_mock_provider_returns_standard_response(self) -> None:
        request = ModelRequest(
            task_type="stock_analysis",
            system_instruction="Analyze stock data.",
            user_input="Analyze AAPL.",
            context={"citations": ["Yahoo Finance chart API"]},
            trace_id="trace-001",
        )

        response = MockModelProvider().generate(request)

        self.assertEqual("mock", response.provider)
        self.assertEqual("stock_analysis", response.task_type)
        self.assertEqual(["Yahoo Finance chart API"], response.citations)
        self.assertEqual(RISK_DISCLAIMER, response.risk_disclaimer)
        self.assertEqual("trace-001", response.to_audit_summary()["trace_id"])

    def test_router_falls_back_to_default_provider(self) -> None:
        router = ModelRouter(providers={"mock": MockModelProvider()}, default_provider="mock")
        request = ModelRequest(
            task_type="news_sentiment",
            system_instruction="Summarize sentiment.",
            user_input="Summarize NVDA news.",
            context={"citations": ["Yahoo Finance RSS"]},
            model_provider="missing",
        )

        response = router.generate(request)

        self.assertEqual("mock", response.provider)
        self.assertIn("news_sentiment", response.output)


if __name__ == "__main__":
    unittest.main()

