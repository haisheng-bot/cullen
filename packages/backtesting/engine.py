"""Strategy Engine + Backtest Engine: simulates a portfolio day-by-day over
a historical price series, applying entry/exit rules and position sizing
on each scheduled rebalance date, with a daily portfolio-drawdown circuit
breaker in between rebalances.
"""
from __future__ import annotations

import calendar
from bisect import bisect_left, bisect_right
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from packages.backtesting import allocation, performance, risk, signals
from packages.backtesting.schemas import (
    REBALANCE_FREQUENCIES,
    SIGNAL_MODES,
    BacktestResult,
    EquityPoint,
    StrategyConfig,
    SymbolContribution,
    Trade,
)
from packages.data_sources.sec_financials import AnnualFinancials

ALGORITHM_VERSION = "backtesting-v0.2"


@dataclass
class _SymbolSeries:
    dates: list[str]
    closes: list[float]

    def closes_through(self, as_of_date: str) -> list[float]:
        return self.closes[: bisect_right(self.dates, as_of_date)]

    def price_on_or_before(self, as_of_date: str) -> float | None:
        index = bisect_right(self.dates, as_of_date)
        return self.closes[index - 1] if index > 0 else None


@dataclass
class _Position:
    shares: float = 0.0
    avg_cost: float = 0.0
    entry_price: float = 0.0


@dataclass
class _RunState:
    cash: float
    positions: dict[str, _Position] = field(default_factory=dict)
    trades: list[Trade] = field(default_factory=list)
    realized_trade_pnls: list[float] = field(default_factory=list)
    realized_pnl_by_symbol: dict[str, float] = field(default_factory=dict)


class PortfolioBacktestEngine:
    def __init__(
        self,
        history_fetcher: Callable[[str], list[tuple[str, float]]],
        shares_outstanding_fetcher: Callable[[str], float | None] | None = None,
        financials_fetcher: Callable[[str], list[AnnualFinancials]] | None = None,
    ) -> None:
        """`history_fetcher(symbol)` must return the full available
        (date_iso, close) history for a symbol, any order. Used for every
        symbol plus the benchmark. `financials_fetcher(symbol)` must return
        every fiscal year's `AnnualFinancials` (with `filed_date` populated,
        e.g. via `parse_companyfacts_series`) — required when a config uses
        `signal_mode="ai_score"`.
        """
        self.history_fetcher = history_fetcher
        self.shares_outstanding_fetcher = shares_outstanding_fetcher or (lambda symbol: None)
        self.financials_fetcher = financials_fetcher

    def run(self, config: StrategyConfig) -> BacktestResult:
        _validate_config(config)
        if config.signal_mode == "ai_score" and self.financials_fetcher is None:
            raise ValueError("signal_mode='ai_score' requires a financials_fetcher to be configured")

        series_by_symbol = {
            symbol: self._load_series(symbol)
            for symbol in [*config.symbols, config.benchmark_symbol]
        }
        financials_by_symbol = (
            {symbol: self.financials_fetcher(symbol) for symbol in config.symbols}
            if config.signal_mode == "ai_score"
            else {}
        )
        benchmark_series = series_by_symbol[config.benchmark_symbol]
        master_dates = [
            d for d in benchmark_series.dates if config.start_date <= d <= config.end_date
        ]
        if not master_dates:
            raise ValueError("no trading dates available in the requested period")

        rebalance_dates = set(
            _align_rebalance_dates(
                config.start_date, config.end_date, config.rebalance_frequency, master_dates
            )
        )

        state = _RunState(
            cash=config.initial_cash,
            realized_pnl_by_symbol={symbol: 0.0 for symbol in config.symbols},
        )
        peak_value = config.initial_cash
        in_circuit_breaker = False
        equity_curve: list[EquityPoint] = []
        benchmark_start_price = benchmark_series.price_on_or_before(master_dates[0])

        for current_date in master_dates:
            prices = {
                symbol: series_by_symbol[symbol].price_on_or_before(current_date)
                for symbol in config.symbols
            }
            portfolio_value = _mark_to_market(state, prices)
            peak_value = max(peak_value, portfolio_value)

            if not in_circuit_breaker and risk.is_portfolio_drawdown_breached(
                portfolio_value, peak_value, config.risk.max_portfolio_drawdown
            ):
                in_circuit_breaker = True
                for symbol in list(state.positions):
                    price = prices.get(symbol)
                    if price is not None:
                        _close_position(state, symbol, price, current_date, "组合回撤触发熔断，清仓至现金")
                portfolio_value = _mark_to_market(state, prices)

            if current_date in rebalance_dates:
                in_circuit_breaker = False
                self._rebalance(config, series_by_symbol, financials_by_symbol, state, prices, current_date)
                portfolio_value = _mark_to_market(state, prices)

            benchmark_price = benchmark_series.price_on_or_before(current_date)
            benchmark_value = (
                config.initial_cash * benchmark_price / benchmark_start_price
                if benchmark_price and benchmark_start_price
                else None
            )
            equity_curve.append(
                EquityPoint(
                    date=current_date,
                    portfolio_value=round(portfolio_value, 2),
                    benchmark_value=round(benchmark_value, 2) if benchmark_value is not None else None,
                )
            )

        final_date = master_dates[-1]
        final_prices = {
            symbol: series_by_symbol[symbol].price_on_or_before(final_date) for symbol in config.symbols
        }
        for symbol, position in state.positions.items():
            price = final_prices.get(symbol)
            if price is not None and position.shares > 0:
                state.realized_pnl_by_symbol[symbol] += (price - position.avg_cost) * position.shares

        return _build_result(config, equity_curve, state)

    def _rebalance(
        self,
        config: StrategyConfig,
        series_by_symbol: dict[str, _SymbolSeries],
        financials_by_symbol: dict[str, list[AnnualFinancials]],
        state: _RunState,
        prices: dict[str, float | None],
        current_date: str,
    ) -> None:
        for symbol in list(state.positions):
            price = prices.get(symbol)
            if price is None:
                continue
            closes = series_by_symbol[symbol].closes_through(current_date)
            technical, _ = signals.technical_score(closes)
            cross_state = signals.ma_cross_state(closes)
            reasons = []
            if risk.is_stop_loss_breached(
                state.positions[symbol].entry_price, price, config.exit_rules.stop_loss_percent
            ):
                reasons.append("触发止损")
            if technical <= config.exit_rules.max_technical_score:
                reasons.append(f"技术分跌破 {config.exit_rules.max_technical_score}")
            # Unlike entry_rules (where None means "no restriction, always
            # passes"), a None exit filter must mean "this check is
            # disabled" — matches_ma_cross_filter's "always matches when
            # None" semantics would otherwise force an exit every rebalance.
            if config.exit_rules.require_ma_cross is not None and signals.matches_ma_cross_filter(
                cross_state, config.exit_rules.require_ma_cross
            ):
                reasons.append("均线状态触发卖出条件")
            if config.signal_mode == "ai_score" and config.exit_rules.max_ai_score is not None:
                ai = _composite_score(config, closes, financials_by_symbol.get(symbol, []), current_date, technical)
                if ai <= config.exit_rules.max_ai_score:
                    reasons.append(f"AI综合评分跌破 {config.exit_rules.max_ai_score}")
            if reasons:
                _close_position(state, symbol, price, current_date, "、".join(reasons))

        eligible_scores: dict[str, int] = {}
        eligible_closes: dict[str, list[float]] = {}
        for symbol in state.positions:
            price = prices.get(symbol)
            if price is None:
                continue
            closes = series_by_symbol[symbol].closes_through(current_date)
            technical, _ = signals.technical_score(closes)
            score = _composite_score(config, closes, financials_by_symbol.get(symbol, []), current_date, technical)
            eligible_scores[symbol] = score
            eligible_closes[symbol] = closes

        for symbol in config.symbols:
            if symbol in state.positions:
                continue
            price = prices.get(symbol)
            if price is None:
                continue
            closes = series_by_symbol[symbol].closes_through(current_date)
            if not closes:
                continue
            technical, _ = signals.technical_score(closes)
            momentum = signals.momentum_percent(closes)
            cross_state = signals.ma_cross_state(closes)
            score = _composite_score(config, closes, financials_by_symbol.get(symbol, []), current_date, technical)
            passes_score = technical >= config.entry_rules.min_technical_score
            passes_momentum = config.entry_rules.min_momentum_percent is None or (
                momentum is not None and momentum >= config.entry_rules.min_momentum_percent
            )
            passes_cross = signals.matches_ma_cross_filter(cross_state, config.entry_rules.require_ma_cross)
            passes_ai = (
                config.signal_mode != "ai_score"
                or config.entry_rules.min_ai_score is None
                or score >= config.entry_rules.min_ai_score
            )
            if passes_score and passes_momentum and passes_cross and passes_ai:
                eligible_scores[symbol] = score
                eligible_closes[symbol] = closes

        if not eligible_scores:
            return

        market_caps = None
        if config.allocation.method == "market_cap_weighted":
            market_caps = {
                symbol: self._market_cap(symbol, prices.get(symbol)) for symbol in eligible_scores
            }

        raw_weights = allocation.compute_target_weights(
            config.allocation.method,
            list(eligible_scores.keys()),
            closes_by_symbol=eligible_closes,
            technical_scores=eligible_scores,
            market_caps=market_caps,
        )
        target_weights = allocation.apply_weight_constraints(
            raw_weights, config.allocation.max_position_weight, config.allocation.min_cash_weight
        )

        portfolio_value = _mark_to_market(state, prices)
        for symbol, weight in target_weights.items():
            price = prices.get(symbol)
            if price is None or price <= 0:
                continue
            target_shares = (weight * portfolio_value) / price
            current_shares = state.positions[symbol].shares if symbol in state.positions else 0.0
            delta_shares = target_shares - current_shares
            if abs(delta_shares * price) < 1e-6:
                continue
            if delta_shares > 0:
                _open_or_add_position(state, symbol, price, delta_shares, current_date)
            else:
                _reduce_position(state, symbol, price, -delta_shares, current_date, "按目标权重调仓卖出")

        for symbol in list(state.positions):
            if symbol not in target_weights:
                price = prices.get(symbol)
                if price is not None:
                    _close_position(state, symbol, price, current_date, "不在本次调仓目标权重内，清仓")

    def _load_series(self, symbol: str) -> _SymbolSeries:
        raw = self.history_fetcher(symbol)
        if not raw:
            raise ValueError(f"no price history available for {symbol}")
        ordered = sorted(raw, key=lambda item: item[0])
        return _SymbolSeries(dates=[d for d, _ in ordered], closes=[c for _, c in ordered])

    def _market_cap(self, symbol: str, price: float | None) -> float | None:
        shares = self.shares_outstanding_fetcher(symbol)
        if shares is None or price is None:
            return None
        return shares * price


def _mark_to_market(state: _RunState, prices: dict[str, float | None]) -> float:
    holdings_value = sum(
        position.shares * prices[symbol]
        for symbol, position in state.positions.items()
        if prices.get(symbol) is not None
    )
    return state.cash + holdings_value


def _close_position(state: _RunState, symbol: str, price: float, current_date: str, reason: str) -> None:
    position = state.positions.pop(symbol)
    pnl = (price - position.avg_cost) * position.shares
    state.cash += position.shares * price
    state.realized_trade_pnls.append(pnl)
    state.realized_pnl_by_symbol[symbol] = state.realized_pnl_by_symbol.get(symbol, 0.0) + pnl
    state.trades.append(Trade(symbol=symbol, action="sell", date=current_date, price=price, shares=position.shares, reason=reason))


def _open_or_add_position(state: _RunState, symbol: str, price: float, shares: float, current_date: str) -> None:
    state.cash -= shares * price
    if symbol in state.positions:
        position = state.positions[symbol]
        new_shares = position.shares + shares
        position.avg_cost = (position.avg_cost * position.shares + price * shares) / new_shares
        position.shares = new_shares
    else:
        state.positions[symbol] = _Position(shares=shares, avg_cost=price, entry_price=price)
    state.trades.append(Trade(symbol=symbol, action="buy", date=current_date, price=price, shares=shares, reason="按目标权重调仓买入"))


def _reduce_position(state: _RunState, symbol: str, price: float, shares: float, current_date: str, reason: str) -> None:
    position = state.positions[symbol]
    sell_shares = min(shares, position.shares)
    pnl = (price - position.avg_cost) * sell_shares
    state.cash += sell_shares * price
    state.realized_trade_pnls.append(pnl)
    state.realized_pnl_by_symbol[symbol] = state.realized_pnl_by_symbol.get(symbol, 0.0) + pnl
    position.shares -= sell_shares
    state.trades.append(Trade(symbol=symbol, action="sell", date=current_date, price=price, shares=sell_shares, reason=reason))
    if position.shares <= 1e-9:
        state.positions.pop(symbol)


def _composite_score(
    config: StrategyConfig,
    closes: list[float],
    annual_series: list[AnnualFinancials],
    as_of_date: str,
    technical: int,
) -> int:
    """The score used for entry/exit ai-threshold checks and for ranking/
    weighting eligible symbols. In `signal_mode="technical"` this is just
    `technical` (no extra computation); in `"ai_score"` mode it's the
    point-in-time-safe composite from `signals.ai_score`.
    """
    if config.signal_mode != "ai_score":
        return technical
    latest, previous = signals.select_financials_as_of(annual_series, as_of_date)
    score, _ = signals.ai_score(latest, previous, closes)
    return score


def _validate_config(config: StrategyConfig) -> None:
    if not config.symbols:
        raise ValueError("symbols is required")
    if config.start_date >= config.end_date:
        raise ValueError("start_date must be before end_date")
    if config.rebalance_frequency not in REBALANCE_FREQUENCIES:
        raise ValueError(f"unsupported rebalance frequency: {config.rebalance_frequency}")
    if config.signal_mode not in SIGNAL_MODES:
        raise ValueError(f"unsupported signal mode: {config.signal_mode}")
    if not 0 <= config.allocation.min_cash_weight < 1:
        raise ValueError("min_cash_weight must be in [0, 1)")
    if not 0 < config.allocation.max_position_weight <= 1:
        raise ValueError("max_position_weight must be in (0, 1]")


def _align_rebalance_dates(
    start_date: str, end_date: str, frequency: str, master_dates: list[str]
) -> list[str]:
    scheduled = _scheduled_dates(date.fromisoformat(start_date), date.fromisoformat(end_date), frequency)
    aligned = []
    for scheduled_date in scheduled:
        iso = scheduled_date.isoformat()
        index = bisect_left(master_dates, iso)
        if index < len(master_dates):
            aligned.append(master_dates[index])
    return aligned


def _scheduled_dates(start: date, end: date, frequency: str) -> list[date]:
    dates = [start]
    current = start
    while True:
        current = current + timedelta(days=7) if frequency == "weekly" else _add_months(
            current, 3 if frequency == "quarterly" else 1
        )
        if current > end:
            break
        dates.append(current)
    return dates


def _add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _build_result(config: StrategyConfig, equity_curve: list[EquityPoint], state: _RunState) -> BacktestResult:
    final_value = equity_curve[-1].portfolio_value
    total_return = performance.total_return_percent(config.initial_cash, final_value)
    annualized_return = performance.annualized_return_percent(total_return, config.start_date, config.end_date)

    portfolio_values = [point.portfolio_value for point in equity_curve]
    max_dd = performance.max_drawdown_percent(portfolio_values)
    daily_returns = performance.periodic_returns(portfolio_values)
    sharpe = performance.sharpe_ratio(daily_returns, periods_per_year=252)
    win_rate = performance.win_rate_percent(state.realized_trade_pnls)

    benchmark_values = [point.benchmark_value for point in equity_curve if point.benchmark_value is not None]
    benchmark_total_return = (
        performance.total_return_percent(benchmark_values[0], benchmark_values[-1])
        if len(benchmark_values) >= 2
        else None
    )
    benchmark_returns = performance.periodic_returns(benchmark_values) if benchmark_values else []
    alpha_percent, beta = (
        performance.alpha_beta_percent(daily_returns, benchmark_returns, periods_per_year=252)
        if len(daily_returns) == len(benchmark_returns) and daily_returns
        else (None, None)
    )

    contributions = [
        SymbolContribution(
            symbol=symbol,
            pnl_cash=round(pnl, 2),
            contribution_percent=round(pnl / config.initial_cash * 100, 2) if config.initial_cash else 0.0,
        )
        for symbol, pnl in state.realized_pnl_by_symbol.items()
    ]
    best_symbol, worst_symbol = performance.best_worst_contributor(
        [(c.symbol, c.pnl_cash) for c in contributions]
    )

    return BacktestResult(
        strategy_name=config.strategy_name,
        symbols=config.symbols,
        start_date=config.start_date,
        end_date=config.end_date,
        signal_mode=config.signal_mode,
        initial_cash=config.initial_cash,
        final_value=final_value,
        total_return_percent=round(total_return, 2),
        annualized_return_percent=round(annualized_return, 2),
        max_drawdown_percent=round(max_dd, 2),
        sharpe_ratio=round(sharpe, 2) if sharpe is not None else None,
        win_rate_percent=round(win_rate, 2) if win_rate is not None else None,
        best_contributor=best_symbol,
        worst_contributor=worst_symbol,
        contributions=contributions,
        benchmark_symbol=config.benchmark_symbol,
        benchmark_total_return_percent=round(benchmark_total_return, 2) if benchmark_total_return is not None else None,
        alpha_percent=round(alpha_percent, 2) if alpha_percent is not None else None,
        beta=round(beta, 2) if beta is not None else None,
        equity_curve=equity_curve,
        trades=state.trades,
        suggestions=_build_suggestions(best_symbol, worst_symbol),
        risks=_build_risks(config),
        source="Yahoo Finance chart API (yfinance-compatible)",
        algorithm_version=ALGORITHM_VERSION,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def _build_suggestions(best_symbol: str | None, worst_symbol: str | None) -> list[str]:
    if best_symbol and worst_symbol and best_symbol != worst_symbol:
        return [f"建议降低 {worst_symbol} 权重，提高 {best_symbol} 权重。"]
    if best_symbol:
        return [f"{best_symbol} 是本次回测期内贡献最大的标的。"]
    return []


def _build_risks(config: StrategyConfig) -> list[str]:
    if config.signal_mode == "ai_score":
        risks = [
            "AI 综合评分基于按披露日期重建的历史财报快照（基本面/成长/估值/技术/波动风险），"
            "不含新闻情绪因子（无历史新闻归档数据源，权重已按比例分配至其余因子），"
            "与 /stocks/{symbol}/recommendation 的实时评分权重不完全相同。",
            "历史回测结果不代表未来表现，不构成任何投资建议。",
        ]
    else:
        risks = [
            "回测信号仅基于价格/技术指标（动量、RSI、均线），未使用财报基本面数据，"
            "与 /stocks/{symbol}/recommendation 的完整 AI 评分不是同一套逻辑。",
            "历史回测结果不代表未来表现，不构成任何投资建议。",
        ]
    if config.risk.max_sector_exposure is not None and not config.sector_map:
        risks.append("未提供 sector_map，行业暴露限制未生效。")
    return risks
