import unittest
from dataclasses import dataclass

from packages.backtesting.schemas import BacktestResult, EquityPoint, StrategyConfig
from packages.config import Settings
from packages.data_sources.sec_financials import AnnualFinancials
from packages.db.audit import write_audit_log
from packages.db.backtest_runs import write_backtest_run
from packages.db.financial_facts_cache import get_or_fetch_annual_series
from packages.db.job_queue import count_jobs, create_job, get_job, list_jobs, update_job_status
from packages.db.models import AuditLog, Base
from packages.db.portfolios import (
    add_symbol,
    ensure_default_portfolios,
    get_portfolio_config,
    list_portfolios,
    remove_symbol,
    save_portfolio_config,
)
from packages.db.price_history_cache import get_or_fetch_closes
from packages.db.report_archives import get_report_archive, list_report_archives, save_report_archive
from packages.db.session import build_engine
from packages.db.strategies import delete_strategy, get_strategy, save_strategy
from packages.db.stock_scores import get_score_history, write_screening_result
from packages.db.workflow_runs import (
    get_workflow_run_by_trace_id,
    list_workflow_runs,
    write_workflow_run,
)
from packages.model_layer.mock_provider import MockModelProvider
from packages.model_layer.schemas import RISK_DISCLAIMER, ModelRequest
from packages.workflow_layer.schemas import ScreeningCandidate, ScreeningResult
from sqlalchemy.orm import Session


def make_sqlite_engine():
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


class SettingsTest(unittest.TestCase):
    def test_settings_default_to_local_sqlite_without_env_file(self) -> None:
        settings = Settings(_env_file=None)

        self.assertTrue(settings.database_url)
        self.assertIsNone(settings.openai_api_key)
        self.assertIsNone(settings.anthropic_api_key)


class AuditLogPersistenceTest(unittest.TestCase):
    def test_audit_log_table_round_trips(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            session.add(
                AuditLog(
                    trace_id="trace-db-001",
                    task_type="stock_analysis",
                    provider="mock",
                    model_name="mock-model-v0",
                    input_summary="Analyze AAPL.",
                    output_summary="Mock response for stock_analysis: Analyze AAPL.",
                    citations=["Yahoo Finance chart API"],
                    token_usage={"input_tokens": 2, "output_tokens": 6, "total_tokens": 8},
                    cost_estimate=0.0,
                    latency_ms=1,
                    risk_disclaimer=RISK_DISCLAIMER,
                )
            )
            session.commit()

        with Session(engine) as session:
            row = session.query(AuditLog).filter_by(trace_id="trace-db-001").one()

        self.assertEqual("stock_analysis", row.task_type)
        self.assertEqual(["Yahoo Finance chart API"], row.citations)
        self.assertEqual(RISK_DISCLAIMER, row.risk_disclaimer)
        self.assertIsNotNone(row.created_at)

    def test_write_audit_log_persists_model_response(self) -> None:
        engine = make_sqlite_engine()
        request = ModelRequest(
            task_type="news_sentiment",
            system_instruction="Summarize sentiment.",
            user_input="Summarize NVDA news.",
            trace_id="trace-db-002",
        )
        response = MockModelProvider().generate(request)

        with Session(engine) as session:
            record = write_audit_log(session, response)
            session.commit()
            record_id = record.id

        with Session(engine) as session:
            row = session.get(AuditLog, record_id)

        self.assertEqual("trace-db-002", row.trace_id)
        self.assertEqual("news_sentiment", row.task_type)
        self.assertIn("Summarize NVDA news.", row.input_summary)
        self.assertEqual(RISK_DISCLAIMER, row.risk_disclaimer)


class StockScorePersistenceTest(unittest.TestCase):
    def _make_result(self, total_score: int = 80) -> ScreeningResult:
        return ScreeningResult(
            market="US",
            requested_limit=5,
            scored_count=1,
            candidates=[
                ScreeningCandidate(
                    rank=1,
                    symbol="AAPL",
                    name="Apple Inc.",
                    sector="Technology",
                    total_score=total_score,
                    recommendation="观察",
                    factors=[{"name": "technical", "score": total_score, "weight": 0.2, "explanation": "test"}],
                    reasons=["区间走势为正，短线动量偏强。"],
                    risks=[],
                    source="test-source",
                    algorithm_version="algorithm-v0.3",
                )
            ],
            skipped=[],
            source="test-source",
            generated_at="2026-06-25T13:32:00+00:00",
        )

    def test_write_screening_result_persists_each_candidate(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            records = write_screening_result(session, self._make_result())
            self.assertEqual(1, len(records))
            self.assertEqual("AAPL", records[0].symbol)
            self.assertEqual(80, records[0].total_score)
            session.commit()

    def test_get_score_history_returns_newest_first(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            write_screening_result(session, self._make_result(total_score=60))
            session.commit()
        with Session(engine) as session:
            write_screening_result(session, self._make_result(total_score=85))
            session.commit()

        with Session(engine) as session:
            history = get_score_history(session, "aapl", limit=10)

        self.assertEqual(2, len(history))
        self.assertEqual(85, history[0].total_score)
        self.assertEqual(60, history[1].total_score)


@dataclass
class _FakeHistoryPoint:
    date: str
    close: float


@dataclass
class _FakeHistoryResponse:
    points: list[_FakeHistoryPoint]


class _CountingFakeHistoryClient:
    def __init__(self) -> None:
        self.call_count = 0

    def fetch_history(self, symbol: str, range_: str = "10y", interval: str = "1d") -> _FakeHistoryResponse:
        self.call_count += 1
        return _FakeHistoryResponse(
            points=[_FakeHistoryPoint(date="2023-01-03", close=100.0), _FakeHistoryPoint(date="2023-01-04", close=101.0)]
        )


class PriceHistoryCachePersistenceTest(unittest.TestCase):
    def test_get_or_fetch_closes_caches_after_first_call(self) -> None:
        engine = make_sqlite_engine()
        client = _CountingFakeHistoryClient()

        with Session(engine) as session:
            first = get_or_fetch_closes(session, client, "AAPL")
            session.commit()
        with Session(engine) as session:
            second = get_or_fetch_closes(session, client, "AAPL")
            session.commit()

        self.assertEqual([("2023-01-03", 100.0), ("2023-01-04", 101.0)], first)
        self.assertEqual(first, second)
        self.assertEqual(1, client.call_count, "second call should hit the cache, not the network")


class PortfolioConfigPersistenceTest(unittest.TestCase):
    def test_save_portfolio_config_round_trips_weights_and_cash(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            save_portfolio_config(session, "Core Watch", {"AAPL": 0.4, "MSFT": 0.5}, 0.1)
            session.commit()

        with Session(engine) as session:
            config = get_portfolio_config(session, "Core Watch")

        self.assertEqual({"AAPL": 0.4, "MSFT": 0.5}, config.target_weights)
        self.assertEqual(0.1, config.cash_weight)


class ReportArchivePersistenceTest(unittest.TestCase):
    def test_save_report_archive_round_trips_markdown_and_html(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            save_report_archive(
                session,
                trace_id="trace-report-db",
                portfolio_name="Core Watch",
                title="Core Watch Research Report",
                markdown="# Report",
                html="<h1>Report</h1>",
                source_summary={"symbols": ["AAPL"]},
                risk_disclaimer=RISK_DISCLAIMER,
                generated_at="2026-07-02T00:00:00+00:00",
            )
            session.commit()

        with Session(engine) as session:
            report = get_report_archive(session, "trace-report-db")
            reports = list_report_archives(session, portfolio_name="Core Watch")

        self.assertEqual("Core Watch Research Report", report.title)
        self.assertEqual("<h1>Report</h1>", report.html)
        self.assertEqual(1, len(reports))

    def test_save_report_archive_upserts_by_trace_id(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            save_report_archive(
                session,
                trace_id="trace-report-upsert",
                portfolio_name="Core Watch",
                title="Old",
                markdown="# Old",
                html="<h1>Old</h1>",
                source_summary={},
                risk_disclaimer=RISK_DISCLAIMER,
                generated_at="2026-07-02T00:00:00+00:00",
            )
            save_report_archive(
                session,
                trace_id="trace-report-upsert",
                portfolio_name="Core Watch",
                title="New",
                markdown="# New",
                html="<h1>New</h1>",
                source_summary={},
                risk_disclaimer=RISK_DISCLAIMER,
                generated_at="2026-07-02T00:00:01+00:00",
            )
            session.commit()

        with Session(engine) as session:
            reports = list_report_archives(session)

        self.assertEqual(1, len(reports))
        self.assertEqual("New", reports[0].title)


class StrategyPersistenceTest(unittest.TestCase):
    def test_save_strategy_round_trips_preferences_and_constraints(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            save_strategy(
                session,
                "Momentum Aggressive",
                {"optimizer_method": "minimum_variance", "backtest_mode": "ai_score"},
                {"max_position_weight": 0.3, "max_drawdown": 0.15},
            )
            session.commit()

        with Session(engine) as session:
            strategy = get_strategy(session, "Momentum Aggressive")

        self.assertEqual(
            {"optimizer_method": "minimum_variance", "backtest_mode": "ai_score"}, strategy.preferences
        )
        self.assertEqual({"max_position_weight": 0.3, "max_drawdown": 0.15}, strategy.constraints)

    def test_save_strategy_is_an_upsert_by_name(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            save_strategy(session, "Defensive", {"optimizer_method": "equal_weight"}, {})
            save_strategy(session, "Defensive", {"optimizer_method": "risk_parity"}, {})
            session.commit()

        with Session(engine) as session:
            strategy = get_strategy(session, "Defensive")

        self.assertEqual("risk_parity", strategy.preferences["optimizer_method"])

    def test_delete_strategy_removes_it(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            save_strategy(session, "Temp", {}, {})
            session.commit()

        with Session(engine) as session:
            deleted = delete_strategy(session, "Temp")
            session.commit()

        with Session(engine) as session:
            self.assertTrue(deleted)
            self.assertIsNone(get_strategy(session, "Temp"))


class _CountingFakeFinancialsClient:
    def __init__(self) -> None:
        self.call_count = 0

    def fetch_annual_series(self, symbol: str) -> list[AnnualFinancials]:
        self.call_count += 1
        return [
            AnnualFinancials(
                fiscal_year=2024,
                end_date="2024-12-31",
                revenue=1000.0,
                net_income=200.0,
                eps_diluted=None,
                total_assets=None,
                stockholders_equity=None,
                shares_outstanding=None,
                operating_income=None,
                current_assets=None,
                current_liabilities=None,
                net_fixed_assets=None,
                cash=None,
                total_debt=None,
                filed_date="2025-02-15",
            )
        ]


class FinancialFactsCachePersistenceTest(unittest.TestCase):
    def test_get_or_fetch_annual_series_caches_after_first_call(self) -> None:
        engine = make_sqlite_engine()
        client = _CountingFakeFinancialsClient()

        with Session(engine) as session:
            first = get_or_fetch_annual_series(session, client, "AAPL")
            session.commit()
        with Session(engine) as session:
            second = get_or_fetch_annual_series(session, client, "AAPL")
            session.commit()

        self.assertEqual(1, len(first))
        self.assertEqual("2024-12-31", first[0].end_date)
        self.assertEqual("2025-02-15", first[0].filed_date)
        self.assertEqual(first, second)
        self.assertEqual(1, client.call_count, "second call should hit the cache, not the network")


class BacktestRunPersistenceTest(unittest.TestCase):
    def test_write_backtest_run_persists_config_and_result(self) -> None:
        engine = make_sqlite_engine()
        config = StrategyConfig(
            strategy_name="test_strategy", symbols=["AAPL"], start_date="2023-01-01", end_date="2023-12-31"
        )
        result = BacktestResult(
            strategy_name="test_strategy",
            symbols=["AAPL"],
            start_date="2023-01-01",
            end_date="2023-12-31",
            signal_mode="technical",
            scoring_profile="balanced",
            initial_cash=10_000.0,
            final_value=11_000.0,
            total_return_percent=10.0,
            annualized_return_percent=10.0,
            max_drawdown_percent=5.0,
            sharpe_ratio=1.0,
            win_rate_percent=50.0,
            best_contributor="AAPL",
            worst_contributor=None,
            contributions=[],
            benchmark_symbol="SPY",
            benchmark_total_return_percent=8.0,
            alpha_percent=2.0,
            beta=1.0,
            equity_curve=[EquityPoint(date="2023-01-01", portfolio_value=10_000.0)],
            trades=[],
            suggestions=[],
            risks=[],
            source="test-source",
            algorithm_version="backtesting-v0.1",
            generated_at="2026-06-25T13:32:00+00:00",
        )

        with Session(engine) as session:
            record = write_backtest_run(session, config, result)
            self.assertEqual("test_strategy", record.strategy_name)
            self.assertEqual(["AAPL"], record.config["symbols"])
            self.assertAlmostEqual(11_000.0, record.result["final_value"])
            session.commit()


class PortfolioPersistenceTest(unittest.TestCase):
    def test_ensure_default_portfolios_seeds_once(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            ensure_default_portfolios(session)
            session.commit()
        with Session(engine) as session:
            ensure_default_portfolios(session)
            session.commit()

        with Session(engine) as session:
            portfolios = list_portfolios(session)

        self.assertEqual(5, len(portfolios))
        core_watch = next(p for p in portfolios if p.name == "Core Watch")
        self.assertEqual(["AAPL", "MSFT", "NVDA"], core_watch.symbols)

    def test_add_symbol_creates_portfolio_and_is_idempotent(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            add_symbol(session, "Momentum", "TSLA")
            session.commit()
        with Session(engine) as session:
            add_symbol(session, "Momentum", "TSLA")
            session.commit()

        with Session(engine) as session:
            portfolios = list_portfolios(session)

        self.assertEqual(1, len(portfolios))
        self.assertEqual(["TSLA"], portfolios[0].symbols)

    def test_remove_symbol_drops_it_from_portfolio(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            add_symbol(session, "Momentum", "TSLA")
            add_symbol(session, "Momentum", "NVDA")
            session.commit()
        with Session(engine) as session:
            remove_symbol(session, "Momentum", "TSLA")
            session.commit()

        with Session(engine) as session:
            portfolio = list_portfolios(session)[0]

        self.assertEqual(["NVDA"], portfolio.symbols)

    def test_remove_symbol_returns_none_for_missing_portfolio(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            result = remove_symbol(session, "Nonexistent", "AAPL")

        self.assertIsNone(result)


def _workflow_run_response(trace_id: str, workflow_name: str, state: str) -> dict:
    return {
        "trace_id": trace_id,
        "workflow_name": workflow_name,
        "workflow_version": "v0.1",
        "state": state,
        "started_at": "2026-06-27T00:00:00+00:00",
        "completed_at": "2026-06-27T00:00:01+00:00",
        "risk_disclaimer": RISK_DISCLAIMER,
    }


class WorkflowRunPersistenceTest(unittest.TestCase):
    def test_write_and_fetch_by_trace_id_round_trips(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            write_workflow_run(
                session,
                {"portfolio_name": "Core Watch"},
                _workflow_run_response("trace-1", "portfolio_research_module", "completed"),
            )
            session.commit()

        with Session(engine) as session:
            record = get_workflow_run_by_trace_id(session, "trace-1")

        self.assertEqual("portfolio_research_module", record.workflow_name)
        self.assertEqual("completed", record.state)

    def test_list_workflow_runs_orders_newest_first(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            write_workflow_run(
                session, {}, _workflow_run_response("trace-old", "portfolio_research_module", "completed")
            )
            write_workflow_run(
                session, {}, _workflow_run_response("trace-new", "portfolio_research_module", "completed")
            )
            session.commit()

        with Session(engine) as session:
            records = list_workflow_runs(session)

        self.assertEqual(["trace-new", "trace-old"], [r.trace_id for r in records])

    def test_list_workflow_runs_filters_by_workflow_name_and_state(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            write_workflow_run(
                session, {}, _workflow_run_response("trace-module", "portfolio_research_module", "completed")
            )
            write_workflow_run(
                session,
                {},
                _workflow_run_response("trace-workflow", "portfolio_research_workflow", "Failed"),
            )
            session.commit()

        with Session(engine) as session:
            module_only = list_workflow_runs(session, workflow_name="portfolio_research_module")
            failed_only = list_workflow_runs(session, state="Failed")

        self.assertEqual(["trace-module"], [r.trace_id for r in module_only])
        self.assertEqual(["trace-workflow"], [r.trace_id for r in failed_only])


class JobQueuePersistenceTest(unittest.TestCase):
    def test_create_and_get_job_round_trips(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            create_job(session, "job-1", "screening", {"limit": 5})
            session.commit()

        with Session(engine) as session:
            record = get_job(session, "job-1")

        self.assertEqual("screening", record.job_type)
        self.assertEqual("pending", record.status)
        self.assertEqual({"limit": 5}, record.payload)
        self.assertEqual(0, record.progress_percent)
        self.assertIsNone(record.started_at)

    def test_get_job_returns_none_for_missing_id(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            record = get_job(session, "missing")

        self.assertIsNone(record)

    def test_update_job_status_sets_started_and_completed_timestamps(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            create_job(session, "job-2", "screening", {})
            session.commit()

        with Session(engine) as session:
            update_job_status(session, "job-2", "running", progress_percent=10)
            session.commit()
        with Session(engine) as session:
            running = get_job(session, "job-2")
        self.assertIsNotNone(running.started_at)
        self.assertIsNone(running.completed_at)
        self.assertEqual(10, running.progress_percent)

        with Session(engine) as session:
            update_job_status(session, "job-2", "completed", result={"ok": True}, progress_percent=100)
            session.commit()
        with Session(engine) as session:
            completed = get_job(session, "job-2")
        self.assertIsNotNone(completed.completed_at)
        self.assertEqual({"ok": True}, completed.result)
        self.assertEqual(100, completed.progress_percent)

    def test_update_job_status_records_error_message_on_failure(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            create_job(session, "job-3", "portfolio_research", {})
            session.commit()

        with Session(engine) as session:
            update_job_status(session, "job-3", "failed", error_message="boom")
            session.commit()

        with Session(engine) as session:
            record = get_job(session, "job-3")

        self.assertEqual("failed", record.status)
        self.assertEqual("boom", record.error_message)
        self.assertIsNotNone(record.completed_at)

    def test_update_job_status_returns_none_for_missing_job(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            result = update_job_status(session, "missing", "running")

        self.assertIsNone(result)

    def test_list_jobs_orders_newest_first_and_filters(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            create_job(session, "job-old", "screening", {})
            create_job(session, "job-new", "portfolio_research", {})
            update_job_status(session, "job-new", "completed")
            session.commit()

        with Session(engine) as session:
            all_jobs = list_jobs(session)
            screening_only = list_jobs(session, job_type="screening")
            completed_only = list_jobs(session, status="completed")

        self.assertEqual(["job-new", "job-old"], [j.id for j in all_jobs])
        self.assertEqual(["job-old"], [j.id for j in screening_only])
        self.assertEqual(["job-new"], [j.id for j in completed_only])

    def test_count_jobs_matches_filters(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            create_job(session, "job-a", "screening", {})
            create_job(session, "job-b", "screening", {})
            create_job(session, "job-c", "portfolio_research", {})
            session.commit()

        with Session(engine) as session:
            self.assertEqual(3, count_jobs(session))
            self.assertEqual(2, count_jobs(session, job_type="screening"))
            self.assertEqual(0, count_jobs(session, status="completed"))


if __name__ == "__main__":
    unittest.main()
