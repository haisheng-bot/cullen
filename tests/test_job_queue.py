import time
import unittest
import uuid

from packages.backtesting.schemas import (
    BacktestResult,
    EquityPoint,
    StrategyConfig,
    SymbolContribution,
)
from packages.db.job_queue import create_job, get_job
from packages.db.session import session_scope
from packages.db.workflow_runs import get_workflow_run_by_trace_id
from packages.job_queue.engine import JobQueueEngine, _run_portfolio_research, _run_screening
from packages.universe_layer.schemas import UniverseResult, UniverseStock
from packages.workflow_layer.portfolio_research import PortfolioResearchRequest, PortfolioResearchWorkflow
from packages.workflow_layer.schemas import ScreeningCandidate, ScreeningResult


class FakeScreeningWorkflow:
    def __init__(self, raise_error: bool = False) -> None:
        self.raise_error = raise_error

    def screen(self, limit: int = 20, profile=None) -> ScreeningResult:
        if self.raise_error:
            raise ValueError("screening blew up")
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


class FakeUniverseScanner:
    def scan(self, limit: int = 100) -> UniverseResult:
        return UniverseResult(
            universe_date="2026-06-25",
            universe_name="us_most_active_top_100",
            market="US",
            limit=limit,
            source="test-source",
            generated_at="2026-06-25T13:32:00+00:00",
            items=[UniverseStock(rank=1, symbol="AAPL", name="Apple Inc.", sector="Technology")][:limit],
            analysis_dimensions=["technical", "fundamental"],
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
            worst_contributor="AAPL",
            contributions=[SymbolContribution(symbol="AAPL", pnl_cash=800.0, contribution_percent=8.0)],
            benchmark_symbol=config.benchmark_symbol,
            benchmark_total_return_percent=7.0,
            alpha_percent=2.5,
            beta=1.0,
            equity_curve=[
                EquityPoint(date=config.start_date, portfolio_value=config.initial_cash, benchmark_value=config.initial_cash),
                EquityPoint(date=config.end_date, portfolio_value=11_000.0, benchmark_value=10_700.0),
            ],
            trades=[],
            suggestions=["建议降低仓位。"],
            risks=["历史回测结果不代表未来表现，不构成任何投资建议。"],
            source="test-source",
            algorithm_version="backtesting-v0.1",
            generated_at="2026-06-25T13:32:00+00:00",
        )


def _make_strategy_config(name: str) -> StrategyConfig:
    return StrategyConfig(
        strategy_name=name,
        symbols=["AAPL"],
        start_date="2023-01-01",
        end_date="2023-12-31",
    )


class RunScreeningJobTest(unittest.TestCase):
    def test_run_screening_marks_job_completed_with_result(self) -> None:
        # job_queue.id is a real primary key on the persistent local sqlite
        # file, so a fixed literal would collide on rerun (see
        # ApiEndpointsTest._seed_workflow_run for the same pattern).
        job_id = f"job-screen-ok-{uuid.uuid4()}"
        with session_scope() as session:
            create_job(session, job_id, "screening", {"limit": 5})

        _run_screening(job_id, FakeScreeningWorkflow(), 5, profile=None)

        with session_scope() as session:
            record = get_job(session, job_id)
        self.assertEqual("completed", record.status)
        self.assertEqual(100, record.progress_percent)
        self.assertEqual("AAPL", record.result["candidates"][0]["symbol"])

    def test_run_screening_marks_job_failed_on_error(self) -> None:
        job_id = f"job-screen-fail-{uuid.uuid4()}"
        with session_scope() as session:
            create_job(session, job_id, "screening", {"limit": 5})

        _run_screening(job_id, FakeScreeningWorkflow(raise_error=True), 5, profile=None)

        with session_scope() as session:
            record = get_job(session, job_id)
        self.assertEqual("failed", record.status)
        self.assertIn("screening blew up", record.error_message)


class RunPortfolioResearchJobTest(unittest.TestCase):
    def test_run_portfolio_research_marks_job_completed_and_archives_workflow_run(self) -> None:
        # job_id doubles as workflow_runs.trace_id (unique), so it must be
        # fresh per run for the same reason as above.
        job_id = f"job-pr-ok-{uuid.uuid4()}"
        with session_scope() as session:
            create_job(session, job_id, "portfolio_research", {"portfolio_name": "Job Portfolio"})

        workflow = PortfolioResearchWorkflow(FakeUniverseScanner(), FakeBacktestEngine())
        request = PortfolioResearchRequest(
            strategy_config=_make_strategy_config("Job Portfolio Strategy"),
            portfolio_name="Job Portfolio",
            selected_symbols=["aapl"],
        )

        _run_portfolio_research(job_id, workflow, request, {"portfolio_name": "Job Portfolio"})

        with session_scope() as session:
            record = get_job(session, job_id)
        self.assertEqual("completed", record.status)
        self.assertEqual(job_id, record.result["trace_id"])
        self.assertEqual("Job Portfolio", record.result["portfolio"]["name"])
        self.assertEqual("research_candidate", record.result["portfolio_recommendation"]["action"])

        with session_scope() as session:
            archived = get_workflow_run_by_trace_id(session, job_id)
        self.assertIsNotNone(archived)
        self.assertEqual("portfolio_research_workflow", archived.workflow_name)


class JobQueueEngineAsyncTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = JobQueueEngine()

    def tearDown(self) -> None:
        self.engine.shutdown(wait=True)

    def test_submit_screening_runs_in_background_and_completes(self) -> None:
        record = self.engine.submit_screening(
            FakeScreeningWorkflow(), limit=5, profile=None, payload={"limit": 5}
        )
        self.assertEqual("pending", record.status)

        final_status = None
        for _ in range(20):
            with session_scope() as session:
                job = get_job(session, record.id)
            final_status = job.status
            if final_status in ("completed", "failed"):
                break
            time.sleep(0.1)

        self.assertEqual("completed", final_status)


if __name__ == "__main__":
    unittest.main()
