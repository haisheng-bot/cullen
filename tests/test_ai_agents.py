import unittest
from typing import Any

from packages.ai_agents.base import Agent, AgentResult
from packages.ai_agents.report_agent import ReportAgent
from packages.ai_agents.sec_filing_agent import SECFilingAgent
from packages.algorithm_layer.recommendation import TrendRecommendationAlgorithm
from packages.data_sources.market_trend import TrendPoint, TrendResponse
from packages.data_sources.sec_filings import Filing, FilingListResponse
from packages.db.models import Base
from packages.db.session import get_engine
from packages.model_layer.mock_provider import MockModelProvider
from packages.model_layer.router import ModelRouter
from packages.model_layer.schemas import RISK_DISCLAIMER
from packages.news_layer.schemas import NewsItem, NewsPolicyResponse


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


class FakeTrendClient:
    def fetch_trend(self, symbol, range_="1d", interval="1m"):
        return TrendResponse(
            symbol=symbol,
            range=range_,
            interval=interval,
            currency="USD",
            exchange_name="NASDAQ",
            regular_market_price=102.0,
            previous_close=100.0,
            points=[
                TrendPoint(timestamp="2026-06-25T13:30:00+00:00", close=100.0, volume=1000),
                TrendPoint(timestamp="2026-06-25T13:31:00+00:00", close=102.0, volume=1200),
            ],
            source="test-trend-source",
            analysis_time="2026-06-25T13:32:00+00:00",
        )


class FakeReportNewsPolicyClient:
    def fetch(self, symbol, years=3, limit=30):
        return NewsPolicyResponse(
            symbol=symbol,
            years=years,
            items=[
                NewsItem(
                    title=f"{symbol} announces new product",
                    summary="Test summary",
                    url="https://example.com/news/1",
                    source="Test Source",
                    published_at="2026-06-24T00:00:00+00:00",
                    category="company_news",
                    symbols=[symbol],
                )
            ],
            sources=["Test Source"],
            generated_at="2026-06-25T13:32:00+00:00",
            coverage_note="test coverage",
        )


class ReportAgentTest(unittest.TestCase):
    def test_report_agent_produces_compliant_result(self) -> None:
        router = ModelRouter(providers={"mock": MockModelProvider()}, default_provider="mock")
        agent = ReportAgent(
            router,
            trend_client=FakeTrendClient(),
            recommendation_algorithm=TrendRecommendationAlgorithm(),
            news_policy_client=FakeReportNewsPolicyClient(),
        )

        result = agent.run("AAPL", write_audit=False)

        self.assertEqual("stock_research_report", result.task_type)
        self.assertEqual(RISK_DISCLAIMER, result.response.risk_disclaimer)
        self.assertIn("https://example.com/news/1", result.response.citations)
        self.assertIn("AAPL", result.response.output)


if __name__ == "__main__":
    unittest.main()
