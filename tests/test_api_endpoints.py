import importlib.util
import unittest

if importlib.util.find_spec("fastapi") is None:
    raise unittest.SkipTest("FastAPI is not installed in this Python environment")

from apps.api import main
from packages.data_sources.market_trend import TrendPoint, TrendResponse
from packages.data_sources.price_history import HistoryPoint, HistoryResponse
from packages.data_sources.fred import FREDObservation, FREDSeriesResponse
from packages.data_sources.sec_filings import Filing, FilingListResponse
from packages.data_sources.sec_financials import SECFinancialsError
from packages.news_layer.schemas import NewsItem, NewsPolicyResponse
from packages.universe_layer.schemas import UniverseResult, UniverseStock
from packages.ai_agents.base import AgentResult
from packages.model_layer.schemas import RISK_DISCLAIMER, ModelResponse, TokenUsage
from packages.workflow_layer.schemas import ScreeningCandidate, ScreeningResult
from packages.backtesting.schemas import BacktestResult, EquityPoint, StrategyConfig, SymbolContribution


class FakeTrendClient:
    def fetch_trend(self, symbol: str, range_: str = "1d", interval: str = "1m") -> TrendResponse:
        return TrendResponse(
            symbol=symbol,
            range=range_,
            interval=interval,
            currency="USD",
            exchange_name="NMS",
            regular_market_price=102.0,
            previous_close=100.0,
            points=[
                TrendPoint(timestamp="2026-06-25T13:30:00+00:00", close=100.0, volume=1000),
                TrendPoint(timestamp="2026-06-25T13:31:00+00:00", close=102.0, volume=1200),
            ],
            source="test-source",
            analysis_time="2026-06-25T13:32:00+00:00",
        )


class FakeHistoryClient:
    def fetch_history(self, symbol: str, range_: str = "10y", interval: str = "1d") -> HistoryResponse:
        return HistoryResponse(
            symbol=symbol,
            range=range_,
            interval=interval,
            currency="USD",
            exchange_name="NMS",
            points=[
                HistoryPoint(date="2016-06-20", open=95.0, high=96.0, low=94.0, close=95.8, volume=1_000_000),
                HistoryPoint(date="2016-06-21", open=97.0, high=98.5, low=96.5, close=98.0, volume=1_200_000),
            ],
            source="test-source",
            analysis_time="2026-06-25T13:32:00+00:00",
        )


class FakeSECFilingClient:
    def list_filings(
        self, symbol: str, forms: tuple[str, ...] = ("10-K", "10-Q", "8-K"), limit: int = 10
    ) -> FilingListResponse:
        return FilingListResponse(
            symbol=symbol,
            cik="0000320193",
            company_name="Apple Inc.",
            filings=[
                Filing(
                    form="10-K",
                    filing_date="2025-11-01",
                    report_date="2025-09-30",
                    accession_number="0000320193-25-000100",
                    primary_document="aapl-10k.htm",
                    document_url=(
                        "https://www.sec.gov/Archives/edgar/data/320193/"
                        "000032019325000100/aapl-10k.htm"
                    ),
                )
            ][:limit],
            source="test-source",
            analysis_time="2026-06-25T13:32:00+00:00",
        )


class FakeSECFinancialsClient:
    def fetch_financial_facts(self, symbol: str):
        raise SECFinancialsError("no test fixture wired for financial facts")


class FakeFREDClient:
    def fetch_observations(
        self,
        series_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
    ) -> FREDSeriesResponse:
        return FREDSeriesResponse(
            series_id=series_id.upper(),
            observations=[
                FREDObservation(date="2026-05-01", value=5.33),
                FREDObservation(date="2026-04-01", value=None),
            ],
            source="test-source",
            analysis_time="2026-06-25T13:32:00+00:00",
        )


class FakeNewsPolicyClient:
    def fetch(self, symbol: str, years: int = 3, limit: int = 30) -> NewsPolicyResponse:
        return NewsPolicyResponse(
            symbol=symbol,
            years=years,
            items=[
                NewsItem(
                    title="Apple executive update",
                    summary="SEC 8-K governance disclosure.",
                    url="https://www.sec.gov/example",
                    source="SEC EDGAR",
                    published_at="2026-06-25T00:00:00+00:00",
                    category="management_change",
                    symbols=[symbol],
                )
            ][:limit],
            sources=["SEC EDGAR"],
            generated_at="2026-06-25T13:32:00+00:00",
            coverage_note="test coverage note",
        )


class FakeSECFilingAgent:
    def run(self, symbol: str, *, trace_id: str | None = None, write_audit: bool = True) -> AgentResult:
        response = ModelResponse(
            provider="mock",
            model_name="mock-model-v0",
            task_type="sec_filing_summary",
            output="Apple filed a routine 10-Q with no notable governance changes.",
            citations=["https://www.sec.gov/example-10q.htm"],
            confidence=0.5,
            token_usage=TokenUsage(input_tokens=10, output_tokens=10, total_tokens=20),
            cost_estimate=0.0,
            latency_ms=1,
            trace_id="trace-sec-001",
            input_summary="Recent SEC filings for AAPL",
        )
        return AgentResult(
            symbol=symbol,
            task_type="sec_filing_summary",
            response=response,
            generated_at="2026-06-25T13:32:00+00:00",
        )


class FakeScreeningWorkflow:
    def screen(self, limit: int = 20) -> ScreeningResult:
        return ScreeningResult(
            market="US",
            requested_limit=limit,
            scored_count=1,
            candidates=[
                ScreeningCandidate(
                    rank=1,
                    symbol="AAPL",
                    name="Apple Inc.",
                    sector="Technology",
                    total_score=80,
                    recommendation="观察",
                    factors=[{"name": "technical", "score": 80, "weight": 0.2, "explanation": "test"}],
                    reasons=["区间走势为正，短线动量偏强。"],
                    risks=["推荐等级仅表示研究关注优先级，不代表买入建议。"],
                    source="test-source",
                    algorithm_version="algorithm-v0.3",
                )
            ],
            skipped=[],
            source="test-source",
            generated_at="2026-06-25T13:32:00+00:00",
        )


class FakeBacktestEngine:
    def run(self, config: StrategyConfig) -> BacktestResult:
        return BacktestResult(
            strategy_name=config.strategy_name,
            symbols=config.symbols,
            start_date=config.start_date,
            end_date=config.end_date,
            signal_mode=config.signal_mode,
            initial_cash=config.initial_cash,
            final_value=11_000.0,
            total_return_percent=10.0,
            annualized_return_percent=9.5,
            max_drawdown_percent=8.0,
            sharpe_ratio=1.1,
            win_rate_percent=60.0,
            best_contributor="AAPL",
            worst_contributor="MSFT",
            contributions=[
                SymbolContribution(symbol="AAPL", pnl_cash=800.0, contribution_percent=8.0),
                SymbolContribution(symbol="MSFT", pnl_cash=200.0, contribution_percent=2.0),
            ],
            benchmark_symbol=config.benchmark_symbol,
            benchmark_total_return_percent=7.0,
            alpha_percent=2.5,
            beta=1.0,
            equity_curve=[
                EquityPoint(date=config.start_date, portfolio_value=config.initial_cash, benchmark_value=config.initial_cash),
                EquityPoint(date=config.end_date, portfolio_value=11_000.0, benchmark_value=10_700.0),
            ],
            trades=[],
            suggestions=["建议降低 MSFT 权重，提高 AAPL 权重。"],
            risks=["历史回测结果不代表未来表现，不构成任何投资建议。"],
            source="test-source",
            algorithm_version="backtesting-v0.1",
            generated_at="2026-06-25T13:32:00+00:00",
        )


class FakeUniverseScanner:
    def scan(self, limit: int = 100) -> UniverseResult:
        return UniverseResult(
            universe_date="2026-06-25",
            universe_name="us_most_active_top_100",
            market="US",
            limit=limit,
            source="test-source",
            generated_at="2026-06-25T13:32:00+00:00",
            items=[
                UniverseStock(rank=1, symbol="AAPL", name="Apple Inc.", sector="Technology"),
                UniverseStock(rank=2, symbol="MSFT", name="Microsoft Corporation", sector="Technology"),
            ][:limit],
            analysis_dimensions=["volume", "relative_volume", "market_cap"],
        )


class ApiEndpointsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.original_client = main.trend_client
        self.original_history_client = main.history_client
        self.original_sec_filing_client = main.sec_filing_client
        self.original_sec_financials_client = main.sec_financials_client
        self.original_fred_client = main.fred_client
        self.original_news_policy_client = main.news_policy_client
        self.original_sec_filing_agent = main.sec_filing_agent
        self.original_universe_scanner = main.universe_scanner
        self.original_screening_workflow = main.screening_workflow
        self.original_persist_screening_result = main._persist_screening_result
        self.original_fetch_score_history = main._fetch_score_history
        self.original_backtest_engine = main.backtest_engine
        self.original_persist_backtest_run = main._persist_backtest_run
        main.trend_client = FakeTrendClient()
        main.history_client = FakeHistoryClient()
        main.sec_filing_client = FakeSECFilingClient()
        main.sec_financials_client = FakeSECFinancialsClient()
        main.fred_client = FakeFREDClient()
        main.news_policy_client = FakeNewsPolicyClient()
        main.sec_filing_agent = FakeSECFilingAgent()
        main.universe_scanner = FakeUniverseScanner()
        main.screening_workflow = FakeScreeningWorkflow()
        main.backtest_engine = FakeBacktestEngine()
        self.persisted_screening_results: list = []
        main._persist_screening_result = self.persisted_screening_results.append
        self.persisted_backtest_runs: list = []
        main._persist_backtest_run = lambda config, result: self.persisted_backtest_runs.append(
            (config, result)
        )
        main._fetch_score_history = lambda symbol, limit: [
            {
                "screened_at": "2026-06-25T13:32:00+00:00",
                "rank": 1,
                "total_score": 80,
                "recommendation": "观察",
                "factors": [{"name": "technical", "score": 80, "weight": 0.2, "explanation": "test"}],
                "reasons": ["区间走势为正，短线动量偏强。"],
                "risks": [],
                "algorithm_version": "algorithm-v0.3",
            }
        ]

    def tearDown(self) -> None:
        main.trend_client = self.original_client
        main.history_client = self.original_history_client
        main.sec_filing_client = self.original_sec_filing_client
        main.sec_financials_client = self.original_sec_financials_client
        main.fred_client = self.original_fred_client
        main.news_policy_client = self.original_news_policy_client
        main.sec_filing_agent = self.original_sec_filing_agent
        main.universe_scanner = self.original_universe_scanner
        main.screening_workflow = self.original_screening_workflow
        main._persist_screening_result = self.original_persist_screening_result
        main._fetch_score_history = self.original_fetch_score_history
        main.backtest_engine = self.original_backtest_engine
        main._persist_backtest_run = self.original_persist_backtest_run

    def test_popular_stocks_endpoint(self) -> None:
        payload = main.get_popular_us_stocks()

        self.assertEqual("US", payload["market"])
        self.assertGreaterEqual(len(payload["items"]), 3)

    def test_quote_endpoint(self) -> None:
        payload = main.get_stock_quote("AAPL")

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual(102.0, payload["price"])
        self.assertEqual(2.0, payload["change"])

    def test_trend_endpoint(self) -> None:
        payload = main.get_stock_trend("AAPL", range_="1d", interval="1m")

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual(2, len(payload["points"]))

    def test_history_endpoint(self) -> None:
        payload = main.get_stock_price_history("AAPL", range_="10y", interval="1d")

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual("10y", payload["range"])
        self.assertEqual(2, len(payload["points"]))
        self.assertEqual(95.0, payload["points"][0]["open"])

    def test_sec_filings_endpoint(self) -> None:
        payload = main.get_stock_sec_filings("AAPL", forms="10-K,10-Q,8-K", limit=10)

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual("0000320193", payload["cik"])
        self.assertEqual(1, len(payload["filings"]))
        self.assertEqual("10-K", payload["filings"][0]["form"])

    def test_fred_observations_endpoint(self) -> None:
        payload = main.get_fred_observations("fedfunds", limit=2)

        self.assertEqual("FEDFUNDS", payload["series_id"])
        self.assertEqual(2, len(payload["observations"]))
        self.assertEqual(5.33, payload["observations"][0]["value"])

    def test_sec_summary_agent_endpoint(self) -> None:
        payload = main.get_stock_sec_summary("AAPL")

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual("sec_filing_summary", payload["task_type"])
        self.assertEqual(RISK_DISCLAIMER, payload["risk_disclaimer"])
        self.assertIn("10-Q", payload["conclusion"])

    def test_news_policy_endpoint(self) -> None:
        payload = main.get_stock_news_policy("AAPL", years=3, limit=10)

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual(3, payload["years"])
        self.assertEqual("management_change", payload["items"][0]["category"])

    def test_stock_screening_endpoint(self) -> None:
        payload = main.get_stock_screening(limit=5)

        self.assertEqual("US", payload["market"])
        self.assertEqual(1, payload["scored_count"])
        self.assertEqual("AAPL", payload["candidates"][0]["symbol"])
        self.assertEqual(1, payload["candidates"][0]["rank"])
        self.assertEqual(1, len(self.persisted_screening_results))

    def test_score_history_endpoint(self) -> None:
        payload = main.get_stock_score_history("AAPL", limit=10)

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual(1, len(payload["items"]))
        self.assertEqual(80, payload["items"][0]["total_score"])
        self.assertEqual("algorithm-v0.3", payload["items"][0]["algorithm_version"])

    def test_recommendation_endpoint(self) -> None:
        payload = main.get_stock_recommendation("AAPL")

        self.assertEqual("AAPL", payload["symbol"])
        self.assertIn(payload["recommendation"], {"强关注", "观察", "中性", "回避"})
        self.assertEqual("algorithm-v0.3", payload["algorithm_version"])
        self.assertTrue(payload["factors"])

    def test_most_active_universe_endpoint(self) -> None:
        payload = main.get_most_active_universe(limit=2)

        self.assertEqual("US", payload["market"])
        self.assertEqual("us_most_active_top_100", payload["universe_name"])
        self.assertEqual(2, len(payload["items"]))

    def test_run_backtest_endpoint(self) -> None:
        request = main.BacktestRunRequest(
            strategy_name="my_strategy",
            symbols=["aapl", "msft"],
            start_date="2023-01-01",
            end_date="2023-12-31",
        )

        payload = main.run_backtest(request)

        self.assertEqual(["AAPL", "MSFT"], payload["symbols"])
        self.assertEqual("AAPL", payload["best_contributor"])
        self.assertEqual("backtesting-v0.1", payload["algorithm_version"])
        self.assertTrue(payload["risks"])
        self.assertEqual(1, len(self.persisted_backtest_runs))

    def test_run_backtest_endpoint_passes_through_ai_score_signal_mode(self) -> None:
        request = main.BacktestRunRequest(
            strategy_name="ai_strategy",
            symbols=["aapl"],
            start_date="2023-01-01",
            end_date="2023-12-31",
            signal_mode="ai_score",
            entry_rules=main.EntryRulesRequest(min_ai_score=65),
            exit_rules=main.ExitRulesRequest(max_ai_score=35),
        )

        payload = main.run_backtest(request)

        self.assertEqual("ai_score", payload["signal_mode"])
        config, _ = self.persisted_backtest_runs[0]
        self.assertEqual("ai_score", config.signal_mode)
        self.assertEqual(65, config.entry_rules.min_ai_score)
        self.assertEqual(35, config.exit_rules.max_ai_score)


if __name__ == "__main__":
    unittest.main()
