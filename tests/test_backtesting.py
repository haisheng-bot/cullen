import statistics
import unittest
from datetime import date, timedelta

from packages.algorithm_layer.technical_indicators import technical_indicator_score
from packages.backtesting import allocation, performance, risk, signals
from packages.backtesting.engine import PortfolioBacktestEngine
from packages.backtesting.schemas import (
    AllocationConfig,
    EntryRules,
    ExitRules,
    RiskControls,
    StrategyConfig,
)
from packages.data_sources.sec_financials import AnnualFinancials


def _annual_financials(end_date: str, filed_date: str | None, revenue: float, **overrides) -> AnnualFinancials:
    fields = dict(
        fiscal_year=None,
        end_date=end_date,
        revenue=revenue,
        net_income=None,
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
        filed_date=filed_date,
    )
    fields.update(overrides)
    return AnnualFinancials(**fields)


def _weekday_dates(start: str, count: int) -> list[str]:
    current = date.fromisoformat(start)
    dates = []
    while len(dates) < count:
        if current.weekday() < 5:
            dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates


def _trending_closes(start_price: float, daily_change_percent: float, num_days: int, start: str = "2022-01-03"):
    dates = _weekday_dates(start, num_days)
    closes = []
    price = start_price
    for _ in dates:
        closes.append(round(price, 4))
        price *= 1 + daily_change_percent
    return list(zip(dates, closes))


class SignalsTest(unittest.TestCase):
    def test_technical_score_neutral_when_insufficient_data(self) -> None:
        score, explanation = signals.technical_score([100.0, 101.0, 99.0])
        self.assertEqual(signals.NEUTRAL_SCORE, score)
        self.assertIn("日线数据不足", explanation)

    def test_technical_score_matches_shared_indicator_function(self) -> None:
        closes = [c for _, c in _trending_closes(100.0, 0.01, 30)]
        self.assertEqual(technical_indicator_score(closes), signals.technical_score(closes))

    def test_momentum_percent_delegates(self) -> None:
        closes = [100.0] * 9 + [110.0]
        self.assertAlmostEqual(10.0, signals.momentum_percent(closes, lookback=9))

    def test_matches_ma_cross_filter(self) -> None:
        self.assertTrue(signals.matches_ma_cross_filter("golden_cross", None))
        self.assertTrue(signals.matches_ma_cross_filter("golden_cross", "golden_or_bullish"))
        self.assertTrue(signals.matches_ma_cross_filter("bullish", "golden_or_bullish"))
        self.assertFalse(signals.matches_ma_cross_filter("bearish", "golden_or_bullish"))

    def test_matches_ma_cross_filter_rejects_unknown_value(self) -> None:
        with self.assertRaises(ValueError):
            signals.matches_ma_cross_filter("flat", "not_a_real_filter")


class SelectFinancialsAsOfTest(unittest.TestCase):
    def test_excludes_fiscal_years_filed_after_as_of_date(self) -> None:
        series = [
            _annual_financials("2024-12-31", "2025-02-15", revenue=200.0),
            _annual_financials("2023-12-31", "2024-02-15", revenue=100.0),
        ]

        latest, previous = signals.select_financials_as_of(series, "2024-06-01")

        self.assertEqual("2023-12-31", latest.end_date)
        self.assertIsNone(previous)

    def test_includes_a_fiscal_year_on_its_exact_filed_date(self) -> None:
        series = [_annual_financials("2024-12-31", "2025-02-15", revenue=200.0)]

        latest, _ = signals.select_financials_as_of(series, "2025-02-15")

        self.assertEqual("2024-12-31", latest.end_date)

    def test_excludes_entries_with_no_filed_date(self) -> None:
        series = [_annual_financials("2024-12-31", None, revenue=200.0)]

        latest, previous = signals.select_financials_as_of(series, "2030-01-01")

        self.assertIsNone(latest)
        self.assertIsNone(previous)

    def test_returns_latest_and_previous_once_both_are_filed(self) -> None:
        series = [
            _annual_financials("2024-12-31", "2025-02-15", revenue=200.0),
            _annual_financials("2023-12-31", "2024-02-15", revenue=100.0),
        ]

        latest, previous = signals.select_financials_as_of(series, "2025-03-01")

        self.assertEqual("2024-12-31", latest.end_date)
        self.assertEqual("2023-12-31", previous.end_date)


class AiScoreTest(unittest.TestCase):
    def test_no_financials_falls_back_to_neutral_fundamentals_and_valuation(self) -> None:
        closes = [c for _, c in _trending_closes(100.0, 0.0, 30)]

        score, explanation = signals.ai_score(None, None, closes)

        self.assertIn("未提供财务数据", explanation)
        self.assertIn("未提供估值相关数据", explanation)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_matches_hand_computed_weighted_composite(self) -> None:
        closes = [100.0] * 29 + [110.0]
        latest = _annual_financials(
            "2024-12-31",
            "2025-02-15",
            revenue=1000.0,
            net_income=200.0,
            eps_diluted=10.0,
        )
        previous = _annual_financials("2023-12-31", "2024-02-15", revenue=800.0)

        score, _ = signals.ai_score(latest, previous, closes)

        from packages.algorithm_layer.financial_factors import fundamentals_score, growth_score, valuation_score
        from packages.algorithm_layer.schemas import FinancialFactorsInput
        from packages.algorithm_layer.technical_indicators import volatility_risk_score

        factors = FinancialFactorsInput(revenue=1000.0, previous_revenue=800.0, net_income=200.0, eps_diluted=10.0)
        fundamentals, _ = fundamentals_score(factors)
        growth, _ = growth_score(factors)
        valuation, _ = valuation_score(factors, 110.0)
        technical, _ = signals.technical_score(closes)
        volatility, _ = volatility_risk_score(closes)
        expected = round(
            fundamentals * signals.AI_SCORE_WEIGHTS["fundamentals"]
            + growth * signals.AI_SCORE_WEIGHTS["growth"]
            + valuation * signals.AI_SCORE_WEIGHTS["valuation"]
            + technical * signals.AI_SCORE_WEIGHTS["technical"]
            + volatility * signals.AI_SCORE_WEIGHTS["volatility_risk"]
        )
        self.assertEqual(max(0, min(100, expected)), score)

    def test_weights_sum_to_one(self) -> None:
        self.assertAlmostEqual(1.0, sum(signals.AI_SCORE_WEIGHTS.values()))


class AllocationTest(unittest.TestCase):
    def test_equal_weight(self) -> None:
        self.assertEqual(
            {"A": 0.25, "B": 0.25, "C": 0.25, "D": 0.25},
            allocation.equal_weight(["A", "B", "C", "D"]),
        )

    def test_equal_weight_empty(self) -> None:
        self.assertEqual({}, allocation.equal_weight([]))

    def test_volatility_weighted_favors_lower_volatility(self) -> None:
        # Alternating +/-0.5% (low) vs. +/-3% (high) — both nonzero so
        # neither hits the "no/zero volatility" fallback branch.
        low_vol = []
        high_vol = []
        low_price = high_price = 100.0
        for i in range(25):
            low_price *= 1.005 if i % 2 == 0 else 1 / 1.005
            high_price *= 1.03 if i % 2 == 0 else 1 / 1.03
            low_vol.append(low_price)
            high_vol.append(high_price)

        weights = allocation.volatility_weighted({"LOW": low_vol, "HIGH": high_vol}, lookback=20)
        self.assertGreater(weights["LOW"], weights["HIGH"])
        self.assertAlmostEqual(1.0, sum(weights.values()), places=6)

    def test_technical_score_weighted(self) -> None:
        weights = allocation.technical_score_weighted({"A": 80, "B": 20})
        self.assertAlmostEqual(0.8, weights["A"])
        self.assertAlmostEqual(0.2, weights["B"])

    def test_technical_score_weighted_falls_back_to_equal_when_all_nonpositive(self) -> None:
        weights = allocation.technical_score_weighted({"A": 0, "B": 0})
        self.assertEqual({"A": 0.5, "B": 0.5}, weights)

    def test_market_cap_weighted(self) -> None:
        weights = allocation.market_cap_weighted({"A": 100.0, "B": 300.0})
        self.assertAlmostEqual(0.25, weights["A"])
        self.assertAlmostEqual(0.75, weights["B"])

    def test_market_cap_weighted_missing_cap_treated_as_zero(self) -> None:
        weights = allocation.market_cap_weighted({"A": 100.0, "B": None})
        self.assertAlmostEqual(1.0, weights["A"])
        self.assertAlmostEqual(0.0, weights["B"])

    def test_apply_weight_constraints_caps_and_redistributes(self) -> None:
        weights = allocation.apply_weight_constraints(
            {"A": 0.6, "B": 0.2, "C": 0.2}, max_position_weight=0.4, min_cash_weight=0.0
        )
        self.assertAlmostEqual(0.4, weights["A"])
        self.assertAlmostEqual(0.3, weights["B"])
        self.assertAlmostEqual(0.3, weights["C"])

    def test_apply_weight_constraints_respects_cash_floor(self) -> None:
        weights = allocation.apply_weight_constraints(
            {"A": 0.5, "B": 0.5}, max_position_weight=1.0, min_cash_weight=0.2
        )
        self.assertAlmostEqual(0.4, weights["A"])
        self.assertAlmostEqual(0.4, weights["B"])

    def test_apply_weight_constraints_leaves_cash_uninvested_when_cap_too_tight(self) -> None:
        weights = allocation.apply_weight_constraints(
            {"A": 1.0}, max_position_weight=0.3, min_cash_weight=0.0
        )
        self.assertAlmostEqual(0.3, weights["A"])

    def test_compute_target_weights_rejects_unsupported_method(self) -> None:
        with self.assertRaises(ValueError):
            allocation.compute_target_weights("not_a_method", ["A"])


class RiskTest(unittest.TestCase):
    def test_is_stop_loss_breached(self) -> None:
        self.assertTrue(risk.is_stop_loss_breached(100.0, 90.0, 0.08))
        self.assertFalse(risk.is_stop_loss_breached(100.0, 95.0, 0.08))
        self.assertFalse(risk.is_stop_loss_breached(100.0, 50.0, None))

    def test_drawdown_from_peak(self) -> None:
        self.assertAlmostEqual(0.12, risk.drawdown_from_peak(88.0, 100.0))
        self.assertEqual(0.0, risk.drawdown_from_peak(50.0, 0.0))

    def test_is_portfolio_drawdown_breached(self) -> None:
        self.assertTrue(risk.is_portfolio_drawdown_breached(88.0, 100.0, 0.12))
        self.assertFalse(risk.is_portfolio_drawdown_breached(88.0, 100.0, None))

    def test_sector_exposures_skips_unmapped_symbols(self) -> None:
        exposures = risk.sector_exposures(
            {"A": 0.3, "B": 0.3, "C": 0.4}, {"A": "Tech", "B": "Tech"}
        )
        self.assertEqual({"Tech": 0.6}, exposures)

    def test_breached_sectors(self) -> None:
        self.assertEqual(["Tech"], risk.breached_sectors({"Tech": 0.6, "Energy": 0.3}, 0.5))
        self.assertEqual([], risk.breached_sectors({"Tech": 0.6}, None))


class PerformanceTest(unittest.TestCase):
    def test_total_return_percent(self) -> None:
        self.assertAlmostEqual(20.0, performance.total_return_percent(10_000, 12_000))
        self.assertEqual(0.0, performance.total_return_percent(0, 12_000))

    def test_annualized_return_percent_two_year_quadruple(self) -> None:
        cagr = performance.annualized_return_percent(300.0, "2022-01-01", "2024-01-01")
        self.assertAlmostEqual(100.0, cagr, delta=0.5)

    def test_annualized_return_percent_zero_days(self) -> None:
        self.assertEqual(0.0, performance.annualized_return_percent(10.0, "2023-01-01", "2023-01-01"))

    def test_annualized_return_percent_total_loss(self) -> None:
        self.assertEqual(-100.0, performance.annualized_return_percent(-100.0, "2023-01-01", "2024-01-01"))

    def test_max_drawdown_percent(self) -> None:
        self.assertAlmostEqual(33.33, performance.max_drawdown_percent([100, 120, 90, 110, 80, 130]), places=1)

    def test_periodic_returns(self) -> None:
        returns = performance.periodic_returns([100, 110, 99])
        self.assertAlmostEqual(0.10, returns[0])
        self.assertAlmostEqual(-0.10, returns[1])

    def test_sharpe_ratio_matches_manual_formula(self) -> None:
        returns = [0.02, -0.01, 0.015, -0.005, 0.01]
        expected = statistics.mean(returns) / statistics.stdev(returns) * (252 ** 0.5)
        self.assertAlmostEqual(expected, performance.sharpe_ratio(returns, periods_per_year=252))

    def test_sharpe_ratio_insufficient_data(self) -> None:
        self.assertIsNone(performance.sharpe_ratio([0.01], periods_per_year=252))

    def test_sharpe_ratio_zero_volatility(self) -> None:
        self.assertIsNone(performance.sharpe_ratio([0.01, 0.01, 0.01], periods_per_year=252))

    def test_win_rate_percent(self) -> None:
        self.assertAlmostEqual(40.0, performance.win_rate_percent([10, -5, 20, -1, 0]))

    def test_win_rate_percent_empty(self) -> None:
        self.assertIsNone(performance.win_rate_percent([]))

    def test_alpha_beta_percent_pure_beta_two_relationship(self) -> None:
        benchmark_returns = [0.01, -0.01, 0.02, -0.02]
        portfolio_returns = [2 * r for r in benchmark_returns]
        alpha, beta = performance.alpha_beta_percent(portfolio_returns, benchmark_returns, periods_per_year=12)
        self.assertAlmostEqual(2.0, beta)
        self.assertAlmostEqual(0.0, alpha, places=6)

    def test_alpha_beta_percent_zero_benchmark_variance(self) -> None:
        alpha, beta = performance.alpha_beta_percent([0.01, 0.02], [0.01, 0.01], periods_per_year=12)
        self.assertIsNone(alpha)
        self.assertIsNone(beta)

    def test_best_worst_contributor(self) -> None:
        best, worst = performance.best_worst_contributor([("A", 100.0), ("B", -50.0), ("C", 30.0)])
        self.assertEqual("A", best)
        self.assertEqual("B", worst)

    def test_best_worst_contributor_empty(self) -> None:
        self.assertEqual((None, None), performance.best_worst_contributor([]))


class PortfolioBacktestEngineTest(unittest.TestCase):
    def _make_engine(
        self, series: dict[str, list[tuple[str, float]]], financials: dict[str, list] | None = None
    ) -> PortfolioBacktestEngine:
        return PortfolioBacktestEngine(
            history_fetcher=lambda symbol: series[symbol],
            financials_fetcher=(lambda symbol: financials.get(symbol, [])) if financials is not None else None,
        )

    def test_run_produces_full_result_and_separates_contributors(self) -> None:
        series = {
            "UP": _trending_closes(100.0, 0.003, 320),
            "DOWN": _trending_closes(100.0, -0.003, 320),
            "SPY": _trending_closes(400.0, 0.0008, 320),
        }
        engine = self._make_engine(series)
        config = StrategyConfig(
            strategy_name="contributor_split",
            symbols=["UP", "DOWN"],
            start_date="2022-03-01",
            end_date="2022-12-30",
            rebalance_frequency="monthly",
            entry_rules=EntryRules(min_technical_score=55),
            exit_rules=ExitRules(max_technical_score=45, stop_loss_percent=0.5),
        )

        result = engine.run(config)

        self.assertEqual(["UP", "DOWN"], result.symbols)
        self.assertGreater(len(result.equity_curve), 0)
        self.assertGreater(len(result.trades), 0)
        self.assertEqual({"UP", "DOWN"}, {c.symbol for c in result.contributions})
        self.assertEqual("UP", result.best_contributor)
        self.assertGreaterEqual(result.max_drawdown_percent, 0.0)
        self.assertIsNotNone(result.benchmark_total_return_percent)
        self.assertTrue(result.risks)
        self.assertEqual("backtesting-v0.2", result.algorithm_version)

    def test_market_cap_weighted_fetches_shares_outstanding_once_per_symbol_per_run(self) -> None:
        # Regression test: shares_outstanding_fetcher backs an uncached, slow
        # SEC EDGAR fetch in production. It must be pre-fetched once per
        # symbol per run, not re-invoked on every rebalance date.
        series = {
            "UP": _trending_closes(100.0, 0.003, 320),
            "DOWN": _trending_closes(100.0, -0.003, 320),
            "SPY": _trending_closes(400.0, 0.0008, 320),
        }
        call_counts: dict[str, int] = {}

        def counting_fetcher(symbol: str) -> float:
            call_counts[symbol] = call_counts.get(symbol, 0) + 1
            return 1_000_000.0

        engine = PortfolioBacktestEngine(
            history_fetcher=lambda symbol: series[symbol],
            shares_outstanding_fetcher=counting_fetcher,
        )
        config = StrategyConfig(
            strategy_name="market_cap_weighted_caching",
            symbols=["UP", "DOWN"],
            start_date="2022-03-01",
            end_date="2022-12-30",
            rebalance_frequency="monthly",
            entry_rules=EntryRules(min_technical_score=0),
            allocation=AllocationConfig(method="market_cap_weighted"),
        )

        result = engine.run(config)

        self.assertGreater(len(result.trades), 0)
        self.assertEqual({"UP": 1, "DOWN": 1}, call_counts)

    def test_run_rejects_empty_symbols(self) -> None:
        engine = self._make_engine({"SPY": _trending_closes(400.0, 0.0, 30)})
        config = StrategyConfig(strategy_name="x", symbols=[], start_date="2022-01-01", end_date="2022-06-01")
        with self.assertRaises(ValueError):
            engine.run(config)

    def test_run_rejects_invalid_date_range(self) -> None:
        engine = self._make_engine({"SPY": _trending_closes(400.0, 0.0, 30), "A": _trending_closes(10.0, 0.0, 30)})
        config = StrategyConfig(strategy_name="x", symbols=["A"], start_date="2022-06-01", end_date="2022-01-01")
        with self.assertRaises(ValueError):
            engine.run(config)

    def test_run_rejects_unsupported_rebalance_frequency(self) -> None:
        engine = self._make_engine({"SPY": _trending_closes(400.0, 0.0, 30), "A": _trending_closes(10.0, 0.0, 30)})
        config = StrategyConfig(
            strategy_name="x", symbols=["A"], start_date="2022-01-01", end_date="2022-06-01",
            rebalance_frequency="daily",
        )
        with self.assertRaises(ValueError):
            engine.run(config)

    def test_run_rejects_ai_score_mode_without_financials_fetcher(self) -> None:
        engine = self._make_engine({"SPY": _trending_closes(400.0, 0.0, 30), "A": _trending_closes(10.0, 0.0, 30)})
        config = StrategyConfig(
            strategy_name="x", symbols=["A"], start_date="2022-01-01", end_date="2022-06-01", signal_mode="ai_score"
        )
        with self.assertRaises(ValueError):
            engine.run(config)

    def test_run_in_ai_score_mode_only_enters_after_financials_are_disclosed(self) -> None:
        # The core lookahead-bias regression test for V2: a fiscal year's
        # financials must not move the entry decision before their own
        # filed_date, even though the engine has the full annual series
        # in memory for the whole backtest.
        dates = _weekday_dates("2022-01-03", 150)
        flat_closes = [(d, 100.0) for d in dates]
        series = {"GOOD": flat_closes, "SPY": flat_closes}
        closes_only = [c for _, c in flat_closes]

        annual = _annual_financials("2021-12-31", "2022-03-15", revenue=1000.0, net_income=300.0)
        score_before, _ = signals.ai_score(None, None, closes_only)
        score_after, _ = signals.ai_score(annual, None, closes_only)
        self.assertLess(score_before, score_after, "strong disclosed financials should raise the ai_score")
        threshold = round((score_before + score_after) / 2)

        engine = self._make_engine(series, financials={"GOOD": [annual]})
        config = StrategyConfig(
            strategy_name="ai_score_lookahead_check",
            symbols=["GOOD"],
            start_date="2022-01-03",
            end_date="2022-06-01",
            rebalance_frequency="monthly",
            signal_mode="ai_score",
            entry_rules=EntryRules(min_technical_score=0, min_ai_score=threshold),
        )

        result = engine.run(config)

        early_trades = [t for t in result.trades if t.date < "2022-03-15"]
        late_trades = [t for t in result.trades if t.date >= "2022-03-15"]
        self.assertEqual([], early_trades, "must not enter before financials are disclosed (lookahead bias)")
        self.assertTrue(any(t.action == "buy" for t in late_trades), "should enter once financials are disclosed")
        self.assertEqual("ai_score", result.signal_mode)

    def test_circuit_breaker_freezes_value_after_drawdown_breach(self) -> None:
        # CRASH falls >12% in one day partway through, then keeps falling
        # further; the circuit breaker should liquidate at the breach and
        # hold flat in cash afterward, not keep losing value.
        flat_then_crash = [(d, 100.0) for d in _weekday_dates("2022-01-03", 40)]
        crash_dates = _weekday_dates("2022-01-03", 80)[40:]
        crashed = []
        price = 100.0
        for d in crash_dates:
            price *= 0.97
            crashed.append((d, round(price, 4)))
        series = {
            "CRASH": flat_then_crash + crashed,
            "SPY": _trending_closes(400.0, 0.0, 80),
        }
        engine = self._make_engine(series)
        config = StrategyConfig(
            strategy_name="circuit_breaker",
            symbols=["CRASH"],
            start_date="2022-01-03",
            end_date=series["CRASH"][-1][0],
            rebalance_frequency="weekly",
            allocation=AllocationConfig(max_position_weight=1.0, min_cash_weight=0.0),
            entry_rules=EntryRules(min_technical_score=0),
            risk=RiskControls(max_portfolio_drawdown=0.12),
        )

        result = engine.run(config)

        breaker_trades = [t for t in result.trades if "熔断" in t.reason]
        self.assertTrue(breaker_trades, "expected the circuit breaker to liquidate at least once")

        # The breaker holds cash only until the *next scheduled rebalance*,
        # which re-evaluates entry rules fresh (by design) — so only assert
        # flatness within that window, not for the rest of the backtest.
        breach_date = breaker_trades[0].date
        breach_index = next(i for i, point in enumerate(result.equity_curve) if point.date == breach_date)
        next_rebalance_index = next(
            (
                i
                for i, point in enumerate(result.equity_curve)
                if i > breach_index and point.date in {t.date for t in result.trades if t.date > breach_date}
            ),
            len(result.equity_curve),
        )
        window = result.equity_curve[breach_index:next_rebalance_index]
        post_breach_values = {point.portfolio_value for point in window}
        self.assertEqual(
            1, len(post_breach_values), "value should stay flat in cash until the next rebalance"
        )

    def test_stop_loss_exits_a_losing_position(self) -> None:
        crashing = []
        price = 100.0
        for d in _weekday_dates("2022-01-03", 70):
            crashing.append((d, round(price, 4)))
            price *= 0.99
        series = {
            "LOSER": crashing,
            "SPY": _trending_closes(400.0, 0.0, 70),
        }
        engine = self._make_engine(series)
        config = StrategyConfig(
            strategy_name="stop_loss",
            symbols=["LOSER"],
            start_date="2022-01-03",
            end_date=series["LOSER"][-1][0],
            rebalance_frequency="weekly",
            entry_rules=EntryRules(min_technical_score=0),
            exit_rules=ExitRules(max_technical_score=0, stop_loss_percent=0.05),
            risk=RiskControls(max_portfolio_drawdown=None),
        )

        result = engine.run(config)

        stop_loss_trades = [t for t in result.trades if "止损" in t.reason]
        self.assertTrue(stop_loss_trades, "expected at least one stop-loss exit on a steadily crashing position")


if __name__ == "__main__":
    unittest.main()
