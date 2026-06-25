import unittest
from typing import Any

from packages.ai_agents.base import Agent, AgentResult
from packages.ai_agents.sec_filing_agent import SECFilingAgent
from packages.data_sources.sec_filings import Filing, FilingListResponse
from packages.db.models import Base
from packages.db.session import get_engine
from packages.model_layer.mock_provider import MockModelProvider
from packages.model_layer.router import ModelRouter
from packages.model_layer.schemas import RISK_DISCLAIMER


class EchoAgent(Agent):
    task_type = "echo_test"
    system_instruction = "Echo the input for testing."

    def build_context(self, symbol: str) -> dict[str, Any]:
        return {"citations": [f"test-source for {symbol}"]}

    def build_user_input(self, symbol: str, context: dict[str, Any]) -> str:
        return f"Echo request for {symbol}"


class AgentBaseTest(unittest.TestCase):
    def test_run_executes_pipeline_without_audit_write(self) -> None:
        router = ModelRouter(providers={"mock": MockModelProvider()}, default_provider="mock")
        agent = EchoAgent(router)

        result = agent.run("aapl", write_audit=False)

        self.assertIsInstance(result, AgentResult)
        self.assertEqual("AAPL", result.symbol)
        self.assertEqual("echo_test", result.task_type)
        self.assertEqual(RISK_DISCLAIMER, result.response.risk_disclaimer)
        payload = result.to_dict()
        self.assertEqual("AAPL", payload["symbol"])
        self.assertIn("mock/", payload["model"])
        self.assertEqual(RISK_DISCLAIMER, payload["risk_disclaimer"])

    def test_run_writes_audit_log_by_default(self) -> None:
        Base.metadata.create_all(get_engine())
        router = ModelRouter(providers={"mock": MockModelProvider()}, default_provider="mock")
        agent = EchoAgent(router)

        result = agent.run("AAPL")

        self.assertIsNotNone(result.response.trace_id)


class FakeSECFilingClient:
    def list_filings(self, symbol, forms=("10-K", "10-Q", "8-K"), limit=5):
        return FilingListResponse(
            symbol=symbol,
            cik="0000320193",
            company_name="Apple Inc.",
            filings=[
                Filing(
                    form="10-Q",
                    filing_date="2026-05-01",
                    report_date="2026-03-28",
                    accession_number="0000320193-26-000013",
                    primary_document="aapl-20260328.htm",
                    document_url=(
                        "https://www.sec.gov/Archives/edgar/data/320193/"
                        "000032019326000013/aapl-20260328.htm"
                    ),
                )
            ],
            source="SEC EDGAR",
            analysis_time="2026-06-25T13:32:00+00:00",
        )


class SECFilingAgentTest(unittest.TestCase):
    def test_sec_filing_agent_produces_compliant_result(self) -> None:
        router = ModelRouter(providers={"mock": MockModelProvider()}, default_provider="mock")
        agent = SECFilingAgent(router, sec_client=FakeSECFilingClient())

        result = agent.run("AAPL", write_audit=False)

        self.assertEqual("sec_filing_summary", result.task_type)
        self.assertIn(
            "https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm",
            result.response.citations,
        )
        self.assertEqual(RISK_DISCLAIMER, result.response.risk_disclaimer)


if __name__ == "__main__":
    unittest.main()
