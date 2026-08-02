import importlib.util
import time
import unittest
import uuid
from datetime import date

if importlib.util.find_spec("fastapi") is None:
    raise unittest.SkipTest("FastAPI is not installed in this Python environment")

from apps.api import main
from packages.data_sources.market_trend import TrendPoint, TrendResponse
from packages.data_sources.price_history import HistoryPoint, HistoryResponse
from packages.data_sources.fred import FREDObservation, FREDSeriesResponse
from packages.data_sources.sec_filings import Filing, FilingListResponse
from packages.data_sources.sec_financials import SECFinancialsError
from packages.data_sources.tiger_openapi import (
    TigerOpenAPIClient,
    TigerOpenAPIConfig,
    TigerOpenAPIError,
)
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


class FakeReportAgent:
    def run(self, symbol: str, *, trace_id: str | None = None, write_audit: bool = True) -> AgentResult:
        response = ModelResponse(
            provider="mock",
            model_name="mock-model-v0",
            task_type="stock_research_report",
            output="AAPL scores 70/100 with positive momentum and steady recent news coverage.",
            citations=["test-source", "https://example.com/news/1"],
            confidence=0.5,
            token_usage=TokenUsage(input_tokens=10, output_tokens=10, total_tokens=20),
            cost_estimate=0.0,
            latency_ms=1,
            trace_id="trace-report-001",
            input_summary="Algorithm score and recent news for AAPL",
        )
        return AgentResult(
            symbol=symbol,
            task_type="stock_research_report",
            response=response,
            generated_at="2026-06-25T13:32:00+00:00",
        )


class FakeScreeningWorkflow:
    def screen(self, limit: int = 20, profile=None) -> ScreeningResult:
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
            scoring_profile=config.scoring_profile,
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


class FakeTigerQuoteAdapter:
    def get_quote(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "price": 210.5,
            "previous_close": 200.0,
            "currency": "USD",
            "exchange": "NASDAQ",
        }


class FakeTigerKlineAdapter:
    def get_kline(self, symbol: str, period: str, start_date: date, end_date: date) -> list[dict]:
        return [
            {
                "date": "2026-06-24",
                "open": 198.0,
                "high": 201.0,
                "low": 197.0,
                "close": 200.0,
                "volume": 900000,
                "amount": 180000000,
            },
            {
                "date": "2026-06-25",
                "open": 200.0,
                "high": 211.0,
                "low": 198.0,
                "close": 210.5,
                "volume": 1000000,
                "amount": 210500000,
            },
        ]


class ApiEndpointsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.original_client = main.trend_client
        self.original_history_client = main.history_client
        self.original_sec_filing_client = main.sec_filing_client
        self.original_sec_financials_client = main.sec_financials_client
        self.original_fred_client = main.fred_client
        self.original_news_policy_client = main.news_policy_client
        self.original_sec_filing_agent = main.sec_filing_agent
        self.original_report_agent = main.report_agent
        self.original_tiger_openapi_client = main.tiger_openapi_client
        self.original_universe_scanner = main.universe_scanner
        self.original_screening_workflow = main.screening_workflow
        self.original_persist_screening_result = main._persist_screening_result
        self.original_fetch_score_history = main._fetch_score_history
        self.original_backtest_engine = main.backtest_engine
        self.original_portfolio_research_workflow = main.portfolio_research_workflow
        self.original_persist_backtest_run = main._persist_backtest_run
        self.original_persist_workflow_run = main._persist_workflow_run
        self.original_fetch_workflow_run = main._fetch_workflow_run
        self.original_list_portfolios = main._list_portfolios
        self.original_add_portfolio_symbol = main._add_portfolio_symbol
        self.original_remove_portfolio_symbol = main._remove_portfolio_symbol
        self.original_save_portfolio_config = main._save_portfolio_config
        self.original_portfolio_risk_response = main._portfolio_risk_response
        self.original_portfolio_optimizer_response = main._portfolio_optimizer_response
        self.original_run_portfolio_research_module = main._run_portfolio_research_module
        self.original_fetch_portfolio_research_run = main._fetch_portfolio_research_run
        self.original_save_report_for_trace_id = main._save_report_for_trace_id
        self.original_list_reports = main._list_reports
        self.original_get_report = main._get_report
        main.trend_client = FakeTrendClient()
        main.history_client = FakeHistoryClient()
        main.sec_filing_client = FakeSECFilingClient()
        main.sec_financials_client = FakeSECFinancialsClient()
        main.fred_client = FakeFREDClient()
        main.news_policy_client = FakeNewsPolicyClient()
        main.sec_filing_agent = FakeSECFilingAgent()
        main.report_agent = FakeReportAgent()
        main.tiger_openapi_client = TigerOpenAPIClient(
            config=TigerOpenAPIConfig(None, None, None, None, env="sandbox")
        )
        main.universe_scanner = FakeUniverseScanner()
        main.screening_workflow = FakeScreeningWorkflow()
        main.backtest_engine = FakeBacktestEngine()
        main.portfolio_research_workflow = main.PortfolioResearchWorkflow(
            universe_scanner=main.universe_scanner,
            backtest_engine=main.backtest_engine,
        )
        self.persisted_screening_results: list = []
        main._persist_screening_result = self.persisted_screening_results.append
        self.persisted_backtest_runs: list = []
        main._persist_backtest_run = lambda config, result: self.persisted_backtest_runs.append(
            (config, result)
        )
        self.persisted_workflow_runs: dict[str, dict] = {}

        def fake_persist_workflow_run(request, response: dict) -> None:
            self.persisted_workflow_runs[response["trace_id"]] = response

        main._persist_workflow_run = fake_persist_workflow_run
        main._fetch_workflow_run = self.persisted_workflow_runs.get
        self.fake_portfolios: dict[str, list[str]] = {"Core Watch": ["AAPL"]}
        main._list_portfolios = lambda: [
            {"name": name, "symbols": symbols, "updated_at": "2026-06-25T13:32:00+00:00"}
            for name, symbols in self.fake_portfolios.items()
        ]

        def fake_add_portfolio_symbol(name: str, symbol: str) -> dict:
            symbols = self.fake_portfolios.setdefault(name, [])
            if symbol not in symbols:
                symbols.append(symbol)
            return {"name": name, "symbols": symbols, "updated_at": "2026-06-25T13:32:00+00:00"}

        def fake_remove_portfolio_symbol(name: str, symbol: str):
            if name not in self.fake_portfolios:
                return None
            self.fake_portfolios[name] = [item for item in self.fake_portfolios[name] if item != symbol]
            return {"name": name, "symbols": self.fake_portfolios[name], "updated_at": "2026-06-25T13:32:00+00:00"}

        main._add_portfolio_symbol = fake_add_portfolio_symbol
        main._remove_portfolio_symbol = fake_remove_portfolio_symbol
        main._save_portfolio_config = lambda name, request: {
            "name": name,
            "symbols": self.fake_portfolios.get(name, sorted(request.target_weights)),
            "config": {
                "target_weights": request.target_weights,
                "cash_weight": request.cash_weight,
                "updated_at": "2026-06-27T00:00:00+00:00",
            },
            "updated_at": "2026-06-25T13:32:00+00:00",
        }
        main._portfolio_risk_response = lambda request: {
            "symbols": [symbol.upper() for symbol in request.symbols],
            "weights": request.weights,
            "volatility_percent": 18.5,
            "beta": 1.1,
            "max_drawdown_percent": 12.0,
            "average_correlation": 0.45,
            "concentration_percent": 60.0,
            "sector_exposure": {"Technology": 100.0},
            "source": "OpenStock AI Risk Engine v0.1",
            "generated_at": "2026-06-27T00:00:00+00:00",
            "risk_disclaimer": RISK_DISCLAIMER,
        }
        main._portfolio_optimizer_response = lambda request: {
            "method": request.method,
            "symbols": [symbol.upper() for symbol in request.symbols],
            "target_weights": {"AAPL": 0.45, "MSFT": 0.45},
            "cash_weight": 0.1,
            "max_position_weight": request.max_position_weight,
            "expected_risk_percent": 16.2,
            "notes": ["test"],
            "source": "OpenStock AI Portfolio Optimizer v0.1",
            "generated_at": "2026-06-27T00:00:00+00:00",
            "risk_disclaimer": RISK_DISCLAIMER,
        }
        self.persisted_portfolio_research_runs: dict[str, dict] = {}
        main._run_portfolio_research_module = lambda request: {
            "workflow_name": "portfolio_research_module",
            "workflow_version": "portfolio-research-module-v0.1",
            "trace_id": "portfolio-trace-1",
            "state": "completed",
            "portfolio": {"name": request.portfolio_name, "symbols": [symbol.upper() for symbol in request.symbols]},
            "score_summary": {
                "scoring_mode": request.strategy_preferences.scoring_mode,
                "scoring_profile": request.strategy_preferences.scoring_profile,
            },
            "backtest_summary": {"total_return_percent": 10.0},
            "risk_summary": {"volatility_percent": 18.5},
            "optimized_weights": {"target_weights": {"AAPL": 0.45, "MSFT": 0.45}},
            "ai_explanation": {"conclusion": "test"},
            "recommendation": {"action": "research_candidate"},
            "warnings": [],
            "workflow": {"node_results": []},
            "source": "OpenStock AI Portfolio Research Module v0.1",
            "started_at": "2026-06-27T00:00:00+00:00",
            "completed_at": "2026-06-27T00:00:01+00:00",
            "risk_disclaimer": RISK_DISCLAIMER,
        }
        main._fetch_portfolio_research_run = self.persisted_portfolio_research_runs.get
        self.reports: dict[str, dict] = {}

        def fake_save_report_for_trace_id(trace_id: str) -> dict:
            run = self.persisted_portfolio_research_runs.get(trace_id)
            if run is None:
                raise main.HTTPException(status_code=404, detail="portfolio research run not found")
            portfolio_name = run["portfolio"]["name"]
            report = {
                "trace_id": trace_id,
                "portfolio_name": portfolio_name,
                "title": f"{portfolio_name} Research Report",
                "markdown": f"# {portfolio_name} Research Report",
                "html": f"<h1>{portfolio_name} Research Report</h1>",
                "source_summary": {"symbols": run["portfolio"]["symbols"]},
                "risk_disclaimer": RISK_DISCLAIMER,
                "generated_at": run["completed_at"],
            }
            self.reports[trace_id] = report
            return report

        main._save_report_for_trace_id = fake_save_report_for_trace_id
        def fake_list_reports(limit: int, offset: int, portfolio_name: str | None) -> dict:
            reports = [
                {key: value for key, value in report.items() if key not in {"markdown", "html"}}
                for report in self.reports.values()
                if portfolio_name is None or report["portfolio_name"] == portfolio_name
            ]
            return {
                "items": reports[offset : offset + limit],
                "total_count": len(reports),
                "limit": limit,
                "offset": offset,
                "risk_disclaimer": RISK_DISCLAIMER,
            }

        main._list_reports = fake_list_reports
        main._get_report = self.reports.get
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
        main.report_agent = self.original_report_agent
        main.tiger_openapi_client = self.original_tiger_openapi_client
        main.universe_scanner = self.original_universe_scanner
        main.screening_workflow = self.original_screening_workflow
        main._persist_screening_result = self.original_persist_screening_result
        main._fetch_score_history = self.original_fetch_score_history
        main.backtest_engine = self.original_backtest_engine
        main.portfolio_research_workflow = self.original_portfolio_research_workflow
        main._persist_backtest_run = self.original_persist_backtest_run
        main._persist_workflow_run = self.original_persist_workflow_run
        main._fetch_workflow_run = self.original_fetch_workflow_run
        main._list_portfolios = self.original_list_portfolios
        main._add_portfolio_symbol = self.original_add_portfolio_symbol
        main._remove_portfolio_symbol = self.original_remove_portfolio_symbol
        main._save_portfolio_config = self.original_save_portfolio_config
        main._portfolio_risk_response = self.original_portfolio_risk_response
        main._portfolio_optimizer_response = self.original_portfolio_optimizer_response
        main._run_portfolio_research_module = self.original_run_portfolio_research_module
        main._fetch_portfolio_research_run = self.original_fetch_portfolio_research_run
        main._save_report_for_trace_id = self.original_save_report_for_trace_id
        main._list_reports = self.original_list_reports
        main._get_report = self.original_get_report

    def test_popular_stocks_endpoint(self) -> None:
        payload = main.get_popular_us_stocks()

        self.assertEqual("US", payload["market"])
        self.assertGreaterEqual(len(payload["items"]), 3)

    def test_quote_endpoint(self) -> None:
        payload = main.get_stock_quote("AAPL")

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual(102.0, payload["price"])
        self.assertEqual(2.0, payload["change"])
        self.assertEqual("test-source", payload["data_quality"]["source"])
        self.assertIn(payload["data_quality"]["freshness"], {"fresh", "recent", "stale"})
        self.assertEqual([], payload["data_quality"]["missing_fields"])

    def test_tiger_status_endpoint_is_read_only(self) -> None:
        payload = main.get_tiger_openapi_status()

        self.assertFalse(payload["configured"])
        self.assertFalse(payload["trading_enabled"])
        self.assertEqual(RISK_DISCLAIMER, payload["risk_disclaimer"])

    def test_data_sources_health_endpoint_lists_config_and_fallbacks(self) -> None:
        payload = main.get_data_sources_health()

        self.assertEqual("ok", payload["overall_status"])
        self.assertEqual(RISK_DISCLAIMER, payload["risk_disclaimer"])
        sources = {item["name"]: item for item in payload["items"]}
        self.assertEqual("available", sources["Yahoo Market Data"]["status"])
        self.assertEqual("available", sources["SEC EDGAR"]["status"])
        self.assertEqual("not_configured", sources["FRED Macro"]["status"])
        self.assertEqual("not_configured", sources["Tiger Brokers OpenAPI"]["status"])
        self.assertIn("fallback", sources["Tiger Brokers OpenAPI"])

    def test_tiger_quote_endpoint_returns_503_when_not_configured(self) -> None:
        with self.assertRaises(main.HTTPException) as context:
            main.get_tiger_stock_quote("AAPL")

        self.assertEqual(503, context.exception.status_code)
        self.assertIn("not configured", context.exception.detail)

    def test_tiger_quote_endpoint_uses_read_only_adapter(self) -> None:
        import tempfile

        with tempfile.NamedTemporaryFile() as key_file:
            main.tiger_openapi_client = TigerOpenAPIClient(
                config=TigerOpenAPIConfig(
                    tiger_id="tiger-id",
                    account="paper-account",
                    license="paper-license",
                    private_key_path=key_file.name,
                    env="sandbox",
                ),
                quote_adapter=FakeTigerQuoteAdapter(),
            )

            payload = main.get_tiger_stock_quote("aapl")

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual(210.5, payload["price"])
        self.assertEqual("Tiger Brokers OpenAPI", payload["source"])

    def test_tiger_history_endpoint_returns_503_when_not_configured(self) -> None:
        with self.assertRaises(main.HTTPException) as context:
            main.get_tiger_stock_history("AAPL", years=3, period="day")

        self.assertEqual(503, context.exception.status_code)
        self.assertIn("not configured", context.exception.detail)

    def test_tiger_history_endpoint_uses_read_only_kline_adapter(self) -> None:
        import tempfile

        with tempfile.NamedTemporaryFile() as key_file:
            main.tiger_openapi_client = TigerOpenAPIClient(
                config=TigerOpenAPIConfig(
                    tiger_id="tiger-id",
                    account="paper-account",
                    license="paper-license",
                    private_key_path=key_file.name,
                    env="sandbox",
                ),
                kline_adapter=FakeTigerKlineAdapter(),
            )

            payload = main.get_tiger_stock_history("aapl", years=3, period="day")

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual("day", payload["period"])
        self.assertEqual(3, payload["years"])
        self.assertEqual(2, len(payload["points"]))
        self.assertEqual(900000, payload["points"][0]["volume"])
        self.assertEqual(210500000.0, payload["points"][1]["amount"])
        self.assertEqual("historical_kline_reference", payload["data_scope"])
        self.assertEqual("Tiger Brokers OpenAPI", payload["data_quality"]["source"])

    def test_trend_endpoint(self) -> None:
        payload = main.get_stock_trend("AAPL", range_="1d", interval="1m")

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual(2, len(payload["points"]))
        self.assertEqual([], payload["data_quality"]["missing_fields"])

    def test_history_endpoint(self) -> None:
        payload = main.get_stock_price_history("AAPL", range_="10y", interval="1d")

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual("10y", payload["range"])
        self.assertEqual(2, len(payload["points"]))
        self.assertEqual(95.0, payload["points"][0]["open"])
        self.assertEqual("test-source", payload["data_quality"]["source"])

    def test_sec_filings_endpoint(self) -> None:
        payload = main.get_stock_sec_filings("AAPL", forms="10-K,10-Q,8-K", limit=10)

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual("0000320193", payload["cik"])
        self.assertEqual(1, len(payload["filings"]))
        self.assertEqual("10-K", payload["filings"][0]["form"])
        self.assertEqual("test-source", payload["data_quality"]["source"])

    def test_fred_observations_endpoint(self) -> None:
        payload = main.get_fred_observations("fedfunds", limit=2)

        self.assertEqual("FEDFUNDS", payload["series_id"])
        self.assertEqual(2, len(payload["observations"]))
        self.assertEqual(5.33, payload["observations"][0]["value"])
        self.assertEqual("test-source", payload["data_quality"]["source"])

    def test_sec_summary_agent_endpoint(self) -> None:
        payload = main.get_stock_sec_summary("AAPL")

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual("sec_filing_summary", payload["task_type"])
        self.assertEqual(RISK_DISCLAIMER, payload["risk_disclaimer"])
        self.assertIn("10-Q", payload["conclusion"])

    def test_report_agent_endpoint(self) -> None:
        payload = main.get_stock_report("AAPL")

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual("stock_research_report", payload["task_type"])
        self.assertEqual(RISK_DISCLAIMER, payload["risk_disclaimer"])
        self.assertIn("70/100", payload["conclusion"])

    def test_news_policy_endpoint(self) -> None:
        payload = main.get_stock_news_policy("AAPL", years=3, limit=10)

        self.assertEqual("AAPL", payload["symbol"])
        self.assertEqual(3, payload["years"])
        self.assertEqual("management_change", payload["items"][0]["category"])
        self.assertEqual("SEC EDGAR", payload["data_quality"]["source"])
        self.assertIn("fallback", payload["data_quality"])

    def test_stock_screening_endpoint(self) -> None:
        payload = main.get_stock_screening(limit=5)

        self.assertEqual("US", payload["market"])
        self.assertEqual(1, payload["scored_count"])
        self.assertEqual("AAPL", payload["candidates"][0]["symbol"])
        self.assertEqual(1, payload["candidates"][0]["rank"])
        self.assertEqual(1, len(self.persisted_screening_results))

    def test_stock_screening_endpoint_rejects_unknown_scoring_profile(self) -> None:
        with self.assertRaises(main.HTTPException) as ctx:
            main.get_stock_screening(limit=5, scoring_profile="not-a-profile")
        self.assertEqual(400, ctx.exception.status_code)

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
        self.assertEqual("balanced", payload["scoring_profile"])

    def test_recommendation_endpoint_accepts_scoring_profile(self) -> None:
        payload = main.get_stock_recommendation("AAPL", scoring_profile="momentum")

        self.assertEqual("momentum", payload["scoring_profile"])

    def test_recommendation_endpoint_rejects_unknown_scoring_profile(self) -> None:
        with self.assertRaises(main.HTTPException) as ctx:
            main.get_stock_recommendation("AAPL", scoring_profile="not-a-profile")
        self.assertEqual(400, ctx.exception.status_code)

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

    def test_portfolio_research_workflow_endpoint(self) -> None:
        request = main.PortfolioResearchWorkflowRequest(
            portfolio_name="API Workflow",
            universe_limit=2,
            selected_symbols=["aapl", "msft"],
            backtest=main.BacktestRunRequest(
                strategy_name="API Portfolio Workflow",
                symbols=["nvda"],
                start_date="2023-01-01",
                end_date="2023-12-31",
            ),
        )

        payload = main.run_portfolio_research_workflow(request)

        self.assertEqual("portfolio_research_workflow", payload["workflow_name"])
        self.assertEqual("portfolio-research-workflow-v0.1", payload["workflow_version"])
        self.assertEqual("Recommendation Ready", payload["state"])
        self.assertEqual("API Workflow", payload["portfolio"]["name"])
        self.assertEqual(["AAPL", "MSFT"], payload["portfolio"]["symbols"])
        self.assertEqual(["AAPL", "MSFT"], payload["backtest"]["symbols"])
        self.assertEqual("research_candidate", payload["portfolio_recommendation"]["action"])
        self.assertIn("回测总收益 10.0%", payload["ai_summary"]["key_findings"][0])
        self.assertEqual(7, len(payload["node_results"]))
        self.assertEqual(1, len(self.persisted_backtest_runs))
        self.assertIn(payload["trace_id"], self.persisted_workflow_runs)

    def test_portfolio_research_module_endpoint(self) -> None:
        payload = main.run_portfolio_research(
            main.PortfolioResearchRunRequest(
                portfolio_name="Core Watch",
                symbols=["aapl", "msft"],
            )
        )

        self.assertEqual("portfolio_research_module", payload["workflow_name"])
        self.assertEqual("completed", payload["state"])
        self.assertEqual(["AAPL", "MSFT"], payload["portfolio"]["symbols"])
        self.assertEqual({"volatility_percent": 18.5}, payload["risk_summary"])
        self.assertEqual(RISK_DISCLAIMER, payload["risk_disclaimer"])
        self.assertEqual("balanced", payload["score_summary"]["scoring_profile"])

    def test_portfolio_research_module_endpoint_threads_scoring_profile(self) -> None:
        payload = main.run_portfolio_research(
            main.PortfolioResearchRunRequest(
                portfolio_name="Core Watch",
                symbols=["aapl", "msft"],
                strategy_preferences=main.PortfolioResearchStrategyPreferencesRequest(
                    scoring_profile="growth"
                ),
            )
        )

        self.assertEqual("growth", payload["score_summary"]["scoring_profile"])

    def test_get_portfolio_research_module_endpoint(self) -> None:
        self.persisted_portfolio_research_runs["portfolio-trace-1"] = {
            "workflow_name": "portfolio_research_module",
            "trace_id": "portfolio-trace-1",
            "state": "completed",
            "risk_disclaimer": RISK_DISCLAIMER,
        }

        payload = main.get_portfolio_research("portfolio-trace-1")

        self.assertEqual("portfolio-trace-1", payload["trace_id"])
        self.assertEqual("completed", payload["state"])

    def test_get_portfolio_research_workflow_run_endpoint(self) -> None:
        self.persisted_workflow_runs["trace-123"] = {
            "workflow_name": "portfolio_research_workflow",
            "workflow_version": "portfolio-research-workflow-v0.1",
            "trace_id": "trace-123",
            "state": "Recommendation Ready",
            "started_at": "2026-06-27T00:00:00+00:00",
            "completed_at": "2026-06-27T00:00:01+00:00",
            "node_results": [],
            "risk_disclaimer": RISK_DISCLAIMER,
        }

        payload = main.get_portfolio_research_workflow_run("trace-123")

        self.assertEqual("trace-123", payload["trace_id"])
        self.assertEqual("Recommendation Ready", payload["state"])

    def test_get_portfolio_research_workflow_run_endpoint_404(self) -> None:
        with self.assertRaises(main.HTTPException) as context:
            main.get_portfolio_research_workflow_run("missing-trace")

        self.assertEqual(404, context.exception.status_code)

    def test_get_portfolios_endpoint(self) -> None:
        payload = main.get_portfolios()

        self.assertEqual([{"name": "Core Watch", "symbols": ["AAPL"], "updated_at": "2026-06-25T13:32:00+00:00"}], payload["items"])

    def test_add_portfolio_symbol_endpoint(self) -> None:
        payload = main.add_portfolio_symbol("Momentum", main.PortfolioSymbolRequest(symbol="tsla"))

        self.assertEqual("Momentum", payload["name"])
        self.assertEqual(["TSLA"], payload["symbols"])

    def test_add_portfolio_symbol_endpoint_rejects_invalid_symbol(self) -> None:
        with self.assertRaises(Exception):
            main.add_portfolio_symbol("Momentum", main.PortfolioSymbolRequest(symbol=""))

    def test_remove_portfolio_symbol_endpoint(self) -> None:
        payload = main.remove_portfolio_symbol("Core Watch", "aapl")

        self.assertEqual([], payload["symbols"])

    def test_remove_portfolio_symbol_endpoint_404_for_missing_portfolio(self) -> None:
        with self.assertRaises(main.HTTPException) as context:
            main.remove_portfolio_symbol("Nonexistent", "AAPL")

        self.assertEqual(404, context.exception.status_code)

    def test_update_portfolio_config_endpoint(self) -> None:
        payload = main.update_portfolio_config(
            "Core Watch",
            main.PortfolioConfigRequest(target_weights={"AAPL": 0.5, "MSFT": 0.4}, cash_weight=0.1),
        )

        self.assertEqual("Core Watch", payload["name"])
        self.assertEqual({"AAPL": 0.5, "MSFT": 0.4}, payload["config"]["target_weights"])
        self.assertEqual(0.1, payload["config"]["cash_weight"])

    def test_update_strategy_endpoint(self) -> None:
        payload = main.update_strategy(
            "Momentum Aggressive",
            main.StrategyRequest(
                preferences={"optimizer_method": "minimum_variance", "backtest_mode": "ai_score"},
                constraints={"max_position_weight": 0.3},
            ),
        )

        self.assertEqual("Momentum Aggressive", payload["name"])
        self.assertEqual("minimum_variance", payload["preferences"]["optimizer_method"])
        self.assertEqual(0.3, payload["constraints"]["max_position_weight"])

    def test_update_strategy_endpoint_rejects_unknown_optimizer_method(self) -> None:
        with self.assertRaises(main.HTTPException) as context:
            main.update_strategy(
                "Broken", main.StrategyRequest(preferences={"optimizer_method": "not_a_method"})
            )

        self.assertEqual(400, context.exception.status_code)

    def test_get_strategies_endpoint_includes_saved_strategy(self) -> None:
        main.update_strategy("List Me", main.StrategyRequest(preferences={"optimizer_method": "equal_weight"}))

        payload = main.get_strategies()

        names = [item["name"] for item in payload["items"]]
        self.assertIn("List Me", names)

    def test_remove_strategy_endpoint(self) -> None:
        main.update_strategy("Disposable", main.StrategyRequest())

        result = main.remove_strategy("Disposable")

        self.assertEqual("Disposable", result["deleted"])
        names = [item["name"] for item in main.get_strategies()["items"]]
        self.assertNotIn("Disposable", names)

    def test_remove_strategy_endpoint_404_for_missing_strategy(self) -> None:
        with self.assertRaises(main.HTTPException) as context:
            main.remove_strategy("Nonexistent Strategy")

        self.assertEqual(404, context.exception.status_code)

    def _seed_workflow_run(self, label: str, portfolio_name: str, strategy_library_name: str | None) -> str:
        # workflow_runs.trace_id is unique and this suite runs against the
        # persistent local sqlite file, so a fixed literal would collide on rerun.
        trace_id = f"{label}-{uuid.uuid4()}"
        with main.session_scope() as session:
            main.write_workflow_run(
                session,
                {"portfolio_name": portfolio_name, "strategy_library_name": strategy_library_name},
                {
                    "trace_id": trace_id,
                    "workflow_name": "portfolio_research_module",
                    "workflow_version": "portfolio-research-module-v0.1",
                    "state": "completed",
                    "started_at": "2026-06-27T00:00:00+00:00",
                    "completed_at": "2026-06-27T00:00:01+00:00",
                    "risk_disclaimer": RISK_DISCLAIMER,
                    "portfolio": {"name": portfolio_name, "symbols": ["AAPL"]},
                    "recommendation": {"action": "research_candidate"},
                    "backtest_summary": {"total_return_percent": 5.0},
                },
            )
            session.commit()
        return trace_id

    def _seed_portfolio_research_run(self, label: str, portfolio_name: str) -> str:
        trace_id = f"{label}-{uuid.uuid4()}"
        self.persisted_portfolio_research_runs[trace_id] = {
            "trace_id": trace_id,
            "workflow_name": "portfolio_research_module",
            "workflow_version": "portfolio-research-module-v0.1",
            "state": "completed",
            "started_at": "2026-06-27T00:00:00+00:00",
            "completed_at": "2026-06-27T00:00:01+00:00",
            "risk_disclaimer": RISK_DISCLAIMER,
            "portfolio": {"name": portfolio_name, "symbols": ["AAPL", "MSFT"]},
            "recommendation": {"action": "research_candidate"},
            "backtest_summary": {"total_return_percent": 5.0},
            "risk_summary": {"volatility_percent": 18.5},
            "optimized_weights": {"target_weights": {"AAPL": 0.5, "MSFT": 0.4}},
            "ai_explanation": {"conclusion": "test"},
        }
        return trace_id

    def test_research_run_history_endpoint_lists_with_summary(self) -> None:
        trace_id = self._seed_workflow_run("history-trace-1", "History Test Portfolio", "History Test Strategy")

        payload = main.get_research_run_history(
            limit=20,
            offset=0,
            workflow_name=None,
            state=None,
            portfolio_name="History Test Portfolio",
            strategy_library_name=None,
            start_date=None,
            end_date=None,
        )

        item = next(i for i in payload["items"] if i["trace_id"] == trace_id)
        self.assertEqual("History Test Strategy", item["strategy_library_name"])
        self.assertIn("research_candidate", item["summary_text"])
        self.assertEqual(RISK_DISCLAIMER, payload["risk_disclaimer"])

    def test_research_run_history_endpoint_filters_by_strategy_library_name(self) -> None:
        trace_a = self._seed_workflow_run("history-trace-2", "Filter Portfolio", "Strategy A")
        trace_b = self._seed_workflow_run("history-trace-3", "Filter Portfolio", "Strategy B")

        payload = main.get_research_run_history(
            limit=20,
            offset=0,
            workflow_name=None,
            state=None,
            portfolio_name=None,
            strategy_library_name="Strategy A",
            start_date=None,
            end_date=None,
        )

        trace_ids = [item["trace_id"] for item in payload["items"]]
        self.assertIn(trace_a, trace_ids)
        self.assertNotIn(trace_b, trace_ids)

    def test_research_run_history_endpoint_paginates(self) -> None:
        # Unique portfolio_name per run: this suite hits the persistent local
        # sqlite file, so a fixed name would accumulate rows across test runs
        # and make an exact total_count assertion flaky.
        portfolio_name = f"Page Portfolio {uuid.uuid4()}"
        self._seed_workflow_run("history-trace-4", portfolio_name, None)
        self._seed_workflow_run("history-trace-5", portfolio_name, None)

        first_page = main.get_research_run_history(
            limit=1,
            offset=0,
            workflow_name=None,
            state=None,
            portfolio_name=portfolio_name,
            strategy_library_name=None,
            start_date=None,
            end_date=None,
        )

        self.assertEqual(1, len(first_page["items"]))
        self.assertEqual(2, first_page["total_count"])

    def test_create_report_from_trace_endpoint_persists_report(self) -> None:
        trace_id = self._seed_portfolio_research_run("report-trace-1", "Report Portfolio")

        report = main.create_report_from_trace(trace_id)

        self.assertEqual(trace_id, report["trace_id"])
        self.assertEqual("Report Portfolio", report["portfolio_name"])
        self.assertIn("# Report Portfolio Research Report", report["markdown"])
        self.assertIn("<h1>Report Portfolio Research Report</h1>", report["html"])
        self.assertEqual(RISK_DISCLAIMER, report["risk_disclaimer"])

        readback = main.get_report(trace_id)
        self.assertEqual(report["markdown"], readback["markdown"])

    def test_get_reports_endpoint_lists_generated_reports(self) -> None:
        trace_id = self._seed_portfolio_research_run("report-trace-2", "Report List Portfolio")
        main.create_report_from_trace(trace_id)

        payload = main.get_reports(limit=20, offset=0, portfolio_name="Report List Portfolio")

        trace_ids = [item["trace_id"] for item in payload["items"]]
        self.assertIn(trace_id, trace_ids)
        self.assertEqual(RISK_DISCLAIMER, payload["risk_disclaimer"])

    def test_create_report_from_trace_endpoint_404_for_missing_trace(self) -> None:
        with self.assertRaises(main.HTTPException) as context:
            main.create_report_from_trace("missing-trace")

        self.assertEqual(404, context.exception.status_code)

    def test_analyze_portfolio_risk_endpoint(self) -> None:
        payload = main.analyze_portfolio_risk_endpoint(
            main.PortfolioRiskRequest(
                symbols=["aapl", "msft"],
                weights={"AAPL": 0.6, "MSFT": 0.4},
                sector_map={"AAPL": "Technology", "MSFT": "Technology"},
            )
        )

        self.assertEqual(["AAPL", "MSFT"], payload["symbols"])
        self.assertEqual(18.5, payload["volatility_percent"])
        self.assertEqual(RISK_DISCLAIMER, payload["risk_disclaimer"])

    def test_optimize_portfolio_endpoint(self) -> None:
        payload = main.optimize_portfolio_endpoint(
            main.PortfolioOptimizerRequest(
                symbols=["aapl", "msft"],
                method="minimum_variance",
                max_position_weight=0.5,
                min_cash_weight=0.1,
            )
        )

        self.assertEqual("minimum_variance", payload["method"])
        self.assertEqual(["AAPL", "MSFT"], payload["symbols"])
        self.assertEqual({"AAPL": 0.45, "MSFT": 0.45}, payload["target_weights"])
        self.assertEqual(RISK_DISCLAIMER, payload["risk_disclaimer"])

    def _poll_job(self, job_id: str, attempts: int = 30, delay: float = 0.05):
        # Jobs run on a real APScheduler background thread even in tests
        # (main.screening_workflow / main.portfolio_research_workflow are
        # swapped for fakes above, so completion is near-instant).
        detail = main.get_job_detail(job_id)
        for _ in range(attempts):
            if detail.status in ("completed", "failed"):
                return detail
            time.sleep(delay)
            detail = main.get_job_detail(job_id)
        return detail

    def test_submit_screening_job_endpoint(self) -> None:
        submission = main.submit_screening_job(limit=5, scoring_profile="balanced")

        self.assertEqual("screening", submission.job_type)
        self.assertEqual("pending", submission.status)

        detail = self._poll_job(submission.job_id)

        self.assertEqual("completed", detail.status)
        self.assertEqual("AAPL", detail.result["candidates"][0]["symbol"])

        # The job queue archives via the real write_screening_result (not
        # the main._persist_screening_result test double), so verify
        # against the real table like the workflow-run job test does.
        with main.session_scope() as session:
            history = main.get_score_history(session, "AAPL", limit=5)
        self.assertTrue(any(item.algorithm_version == "algorithm-v0.3" for item in history))

    def test_submit_screening_job_endpoint_rejects_unknown_scoring_profile(self) -> None:
        with self.assertRaises(main.HTTPException) as context:
            main.submit_screening_job(limit=5, scoring_profile="not-a-profile")

        self.assertEqual(400, context.exception.status_code)

    def test_submit_portfolio_research_job_endpoint(self) -> None:
        request = main.PortfolioResearchWorkflowRequest(
            portfolio_name="Job API Workflow",
            universe_limit=2,
            selected_symbols=["aapl", "msft"],
            backtest=main.BacktestRunRequest(
                strategy_name="Job API Portfolio Workflow",
                symbols=["nvda"],
                start_date="2023-01-01",
                end_date="2023-12-31",
            ),
        )

        submission = main.submit_portfolio_research_job(request)
        detail = self._poll_job(submission.job_id)

        self.assertEqual("completed", detail.status)
        self.assertEqual(submission.job_id, detail.result["trace_id"])
        self.assertEqual("Job API Workflow", detail.result["portfolio"]["name"])
        self.assertEqual("research_candidate", detail.result["portfolio_recommendation"]["action"])

        # The job queue archives via the real write_workflow_run (not the
        # main._persist_workflow_run test double), so verify against the
        # real table like _seed_workflow_run does elsewhere in this suite.
        with main.session_scope() as session:
            archived = main.get_workflow_run_by_trace_id(session, submission.job_id)
        self.assertIsNotNone(archived)
        self.assertEqual("portfolio_research_workflow", archived.workflow_name)

    def test_get_job_detail_endpoint_404_for_missing_job(self) -> None:
        with self.assertRaises(main.HTTPException) as context:
            main.get_job_detail("does-not-exist")

        self.assertEqual(404, context.exception.status_code)

    def test_list_jobs_endpoint_filters_by_job_type(self) -> None:
        submission = main.submit_screening_job(limit=5, scoring_profile="balanced")
        self._poll_job(submission.job_id)

        payload = main.list_jobs_endpoint(job_type="screening", status=None, limit=20, offset=0)

        job_ids = [item.job_id for item in payload.items]
        self.assertIn(submission.job_id, job_ids)
        self.assertGreaterEqual(payload.total_count, 1)


if __name__ == "__main__":
    unittest.main()
