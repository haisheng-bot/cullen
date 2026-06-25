"""Risk Engine: per-symbol stop-loss, portfolio max-drawdown circuit
breaker, and best-effort sector exposure checks.
"""
from __future__ import annotations


def is_stop_loss_breached(
    entry_price: float, current_price: float, stop_loss_percent: float | None
) -> bool:
    if stop_loss_percent is None or entry_price <= 0:
        return False
    loss_percent = (entry_price - current_price) / entry_price
    return loss_percent >= stop_loss_percent


def drawdown_from_peak(current_value: float, peak_value: float) -> float:
    """Positive fraction, e.g. 0.12 means down 12% from the running peak."""
    if peak_value <= 0:
        return 0.0
    return max(0.0, (peak_value - current_value) / peak_value)


def is_portfolio_drawdown_breached(
    current_value: float, peak_value: float, max_portfolio_drawdown: float | None
) -> bool:
    if max_portfolio_drawdown is None:
        return False
    return drawdown_from_peak(current_value, peak_value) >= max_portfolio_drawdown


def sector_exposures(weights: dict[str, float], sector_map: dict[str, str]) -> dict[str, float]:
    """Aggregate portfolio weight by sector. Symbols missing from
    `sector_map` are silently excluded (best-effort, see
    PORTFOLIO_STRATEGY_STANDARD.md) rather than blocking the computation.
    """
    exposures: dict[str, float] = {}
    for symbol, weight in weights.items():
        sector = sector_map.get(symbol)
        if not sector:
            continue
        exposures[sector] = exposures.get(sector, 0.0) + weight
    return exposures


def breached_sectors(exposures: dict[str, float], max_sector_exposure: float | None) -> list[str]:
    if max_sector_exposure is None:
        return []
    return [sector for sector, exposure in exposures.items() if exposure > max_sector_exposure]
