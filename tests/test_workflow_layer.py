import unittest

from packages.algorithm_layer.recommendation import TrendRecommendationAlgorithm
from packages.backtesting.schemas import BacktestResult, EquityPoint, StrategyConfig, SymbolContribution
from packages.data_sources.market_trend import MarketTrendError, TrendPoint, TrendResponse
from packages.universe_layer.schemas import UniverseResult, UniverseStock
from packages.workflow_layer.engine import (
    WorkflowEngine,
    WorkflowEngineError,
    WorkflowNode,
    WorkflowState,
    transition_workflow_state,
)
from packages.workflow_layer.portfolio_research import (
    PortfolioResearchRequest,
    PortfolioResearchWorkflow,
)
from packages.workflow_layer.stock_screening import StockScreeningWorkflow


class FakeUniverseScanner:
    def scan(self, limit: int = 100) -> UniverseResult:
        return UniverseResult(
            universe_date="2026-06-25",
            universe_name="us_most_active_top_100",
            market="US",
            limit=limit,
            source="test-universe-source",
            generated_at="2026-06-25T13:32:00+00:00",
            items=[
                UniverseStock(rank=1, symbol="AAPL", name="Apple Inc.", sector="Technology"),
                UniverseStock(rank=2, symbol="WEAK", name="Weak Co.", sector="Industrials"),
                UniverseStock(rank=3, symbol="BAD", name="Bad Co.", sector="Energy"),
            ][:limit],
            analysis_dimensions=["volume"],
        )


class FakeTrendClient:
    def fetch_trend(self, symbol: str, range_: str = "1d", interval: str = "1m") -> TrendResponse:
        if symbol == "BAD":
            raise MarketTrendError("no data for BAD")

        closes = {"AAPL": [100.0, 110.0], "WEAK": [100.0, 95.0]}[symbol]
        return TrendResponse(
            symbol=symbol,
            range=range_,
            interval=interval,
            currency="USD",
            exchange_name="NMS",
            regular_market_price=closes[-1],
            previous_close=closes[0],
            points=[
                TrendPoint(timestamp="2026-06-25T13:30:00+00:00", close=closes[0], volume=1000),
                TrendPoint(timestamp="2026-06-25T13:31:00+00:00", close=closes[1], volume=1200),
            ],
            source="test-trend-source",
            analysis_time="2026-06-25T13:32:00+00:00",
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
            algorithm_version="backtesting-v0.2",
            generated_at="2026-06-25T13:32:00+00:00",
        )


class StockScreeningWorkflowTest(unittest.TestCase):
    def test_screen_ranks_candidates_and_skips_failures(self) -> None:
        workflow = StockScreeningWorkflow(
            universe_scanner=FakeUniverseScanner(),
            trend_client=FakeTrendClient(),
            algorithm=TrendRecommendationAlgorithm(),
            financial_factors_fetcher=lambda symbol: None,
        )

        result = workflow.screen(limit=3)

        self.assertEqual(2, result.scored_count)
        self.assertEqual(["AAPL", "WEAK"], [c.symbol for c in result.candidates])
        self.assertEqual([1, 2], [c.rank for c in result.candidates])
        self.assertGreater(result.candidates[0].total_score, result.candidates[1].total_score)
        self.assertEqual(1, len(result.skipped))
        self.assertEqual("BAD", result.skipped[0].symbol)


class WorkflowEngineTest(unittest.TestCase):
    def test_runs_nodes_in_order_and_returns_observable_result(self) -> None:
        calls: list[str] = []

        def universe_node(context, payload):
            calls.append(f"{context.trace_id}:universe")
            return {"symbols": ["AAPL", "MSFT"], "universe_name": "Most Active"}

        def strategy_node(context, payload):
            calls.append(f"{context.trace_id}:strategy")
            return {"target_weights": {"AAPL": 0.5, "MSFT": 0.5}}

        engine = WorkflowEngine(
            name="portfolio_research_workflow",
            nodes=[
                WorkflowNode(name="Universe Builder", module="Universe Layer", handler=universe_node),
                WorkflowNode(name="Strategy Engine", module="Strategy Layer", handler=strategy_node),
            ],
        )

        result = engine.run({"market": "US"}, trace_id="trace-workflow-001")
        payload = result.to_dict()

        self.assertEqual("Recommendation Ready", payload["state"])
        self.assertEqual("trace-workflow-001", payload["trace_id"])
        self.assertEqual(["trace-workflow-001:universe", "trace-workflow-001:strategy"], calls)
        self.assertEqual({"AAPL": 0.5, "MSFT": 0.5}, payload["payload"]["target_weights"])
        self.assertEqual(2, len(payload["node_results"]))
        self.assertEqual("Completed", payload["node_results"][0]["state"])
        self.assertEqual({"type": "list", "count": 2}, payload["node_results"][1]["input_summary"]["symbols"])
        self.assertIn("本系统仅用于投资研究辅助", payload["risk_disclaimer"])

    def test_captures_failed_node_without_running_later_nodes(self) -> None:
        calls: list[str] = []

        def failing_node(context, payload):
            calls.append("failed")
            raise RuntimeError("factor service unavailable")

        def skipped_node(context, payload):
            calls.append("skipped")
            return {"should_not_run": True}

        engine = WorkflowEngine(
            name="failure_workflow",
            nodes=[
                WorkflowNode(name="Factor Engine", module="Algorithm Layer", handler=failing_node),
                WorkflowNode(name="Report Engine", module="Report Layer", handler=skipped_node),
            ],
        )

        result = engine.run({"symbols": ["AAPL"]})

        self.assertEqual(WorkflowState.FAILED, result.state)
        self.assertEqual(["failed"], calls)
        self.assertEqual("Failed", result.node_results[0].state.value)
        self.assertEqual("factor service unavailable", result.node_results[0].error)

    def test_rejects_invalid_state_transition(self) -> None:
        with self.assertRaisesRegex(WorkflowEngineError, "invalid workflow transition"):
            transition_workflow_state(WorkflowState.CREATED, WorkflowState.RUNNING)


class PortfolioResearchWorkflowTest(unittest.TestCase):
    def test_runs_portfolio_research_chain(self) -> None:
        workflow = PortfolioResearchWorkflow(
            universe_scanner=FakeUniverseScanner(),
            backtest_engine=FakeBacktestEngine(),
        )
        request = PortfolioResearchRequest(
            strategy_config=StrategyConfig(
                strategy_name="Workflow Test",
                symbols=["AAPL", "MSFT"],
                start_date="2025-01-01",
                end_date="2025-12-31",
            ),
            universe_limit=3,
            portfolio_name="Core Workflow",
        )

        result = workflow.run(request, trace_id="trace-portfolio-001")
        payload = result.payload

        self.assertEqual(WorkflowState.RECOMMENDATION_READY, result.state)
        self.assertEqual(7, len(result.node_results))
        self.assertEqual(["AAPL", "MSFT"], payload["portfolio_symbols"])
        self.assertEqual("Workflow Test", payload["strategy"]["name"])
        self.assertEqual(10.0, payload["backtest_result"].total_return_percent)
        self.assertEqual("research_candidate", payload["portfolio_recommendation"]["action"])
        self.assertIn("回测总收益 10.0%", payload["ai_summary"]["key_findings"][0])


if __name__ == "__main__":
    unittest.main()
