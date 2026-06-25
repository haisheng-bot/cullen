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
    def _make_engine(self, series: dict[str, list[tuple[str, float]]]) -> PortfolioBacktestEngine:
        return PortfolioBacktestEngine(history_fetcher=lambda symbol: series[symbol])

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
        self.assertEqual("backtesting-v0.1", result.algorithm_version)

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
