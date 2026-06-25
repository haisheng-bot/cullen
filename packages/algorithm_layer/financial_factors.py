"""Fundamentals/growth/valuation scoring, shared by the live Algorithm
Layer recommendation (`recommendation.py`) and the Backtesting Signal
Engine's `ai_score` (`packages/backtesting/signals.py`). Pure functions of
a `FinancialFactorsInput` snapshot — callers decide which snapshot to pass
(today's latest SEC filing, or a point-in-time historical one).
"""
from __future__ import annotations

from packages.algorithm_layer.schemas import FinancialFactorsInput

NO_DATA_SCORE = 50


def _net_margin_score(factors: FinancialFactorsInput) -> tuple[int, str] | None:
    if factors.revenue in (None, 0) or factors.net_income is None:
        return None
    net_margin_percent = factors.net_income / factors.revenue * 100
    score = max(10, min(95, round(50 + net_margin_percent * 1.5)))
    return score, f"净利润率约 {net_margin_percent:.1f}%"


def _roc_score(factors: FinancialFactorsInput) -> tuple[int, str] | None:
    """Greenblatt-style Return on Capital: EBIT / (net working capital +
    net fixed assets). Measures capital efficiency independent of margin.
    """
    if factors.operating_income is None or factors.current_assets is None:
        return None
    if factors.current_liabilities is None or factors.net_fixed_assets is None:
        return None

    net_working_capital = factors.current_assets - factors.current_liabilities
    capital_employed = net_working_capital + factors.net_fixed_assets
    if capital_employed <= 0:
        return None

    roc_percent = factors.operating_income / capital_employed * 100
    score = max(10, min(95, round(50 + roc_percent * 1.5)))
    return score, f"资本回报率(ROC)约 {roc_percent:.1f}%"


def fundamentals_score(factors: FinancialFactorsInput | None) -> tuple[int, str]:
    if factors is None:
        return NO_DATA_SCORE, "未提供财务数据，暂以中性分计入。"

    net_margin = _net_margin_score(factors)
    roc = _roc_score(factors)
    if net_margin is None and roc is None:
        return NO_DATA_SCORE, "未提供财务数据，暂以中性分计入。"
    if net_margin is None:
        score, explanation = roc
        return score, f"{explanation}（基于最近年度 SEC 财报，缺净利润率数据）"
    if roc is None:
        score, explanation = net_margin
        return score, f"{explanation}（基于最近年度 SEC 财报，缺 ROC 数据）"

    margin_score, margin_explanation = net_margin
    roc_score, roc_explanation = roc
    score = round(margin_score * 0.5 + roc_score * 0.5)
    return score, f"{margin_explanation}，{roc_explanation}（基于最近年度 SEC 财报）"


def growth_score(factors: FinancialFactorsInput | None) -> tuple[int, str]:
    if factors is None or not factors.previous_revenue or factors.revenue is None:
        return NO_DATA_SCORE, "未提供同比营收数据，暂以中性分计入。"

    growth_percent = (factors.revenue - factors.previous_revenue) / factors.previous_revenue * 100
    score = max(10, min(95, round(50 + growth_percent * 1.2)))
    return score, f"营收同比增长约 {growth_percent:.1f}%（基于最近两个年度 SEC 财报）"


def _pe_score(factors: FinancialFactorsInput, latest_price: float) -> tuple[int, str] | None:
    if not factors.eps_diluted or factors.eps_diluted <= 0:
        return None
    pe_ratio = latest_price / factors.eps_diluted
    return _pe_band_score(pe_ratio), f"P/E 约 {pe_ratio:.1f}"


def _ev_to_ebit_score(factors: FinancialFactorsInput, latest_price: float) -> tuple[int, str] | None:
    """Greenblatt-style earnings yield, expressed as an EV/EBIT ratio so it
    can reuse the same cheap/expensive band as P/E.
    """
    if factors.operating_income is None or factors.operating_income <= 0:
        return None
    if factors.shares_outstanding is None or factors.shares_outstanding <= 0:
        return None

    market_cap = latest_price * factors.shares_outstanding
    enterprise_value = market_cap + (factors.total_debt or 0) - (factors.cash or 0)
    if enterprise_value <= 0:
        return None

    ev_to_ebit = enterprise_value / factors.operating_income
    return _pe_band_score(ev_to_ebit), f"EV/EBIT 约 {ev_to_ebit:.1f}"


def valuation_score(factors: FinancialFactorsInput | None, latest_price: float) -> tuple[int, str]:
    if factors is None:
        return NO_DATA_SCORE, "未提供估值相关数据，暂以中性分计入。"

    pe = _pe_score(factors, latest_price)
    ev_to_ebit = _ev_to_ebit_score(factors, latest_price)
    if pe is None and ev_to_ebit is None:
        return NO_DATA_SCORE, "未提供估值相关数据，暂以中性分计入。"
    if pe is None:
        score, explanation = ev_to_ebit
        return score, f"{explanation}（绝对档位估算，非行业相对，缺 EPS 数据）"
    if ev_to_ebit is None:
        score, explanation = pe
        return score, f"{explanation}（绝对档位估算，非行业相对，缺企业价值数据）"

    pe_score, pe_explanation = pe
    ev_score, ev_explanation = ev_to_ebit
    score = round(pe_score * 0.5 + ev_score * 0.5)
    return score, f"{pe_explanation}，{ev_explanation}（绝对档位估算，非行业相对）"


def _pe_band_score(pe_ratio: float) -> int:
    if pe_ratio < 15:
        return 85
    if pe_ratio < 25:
        return 70
    if pe_ratio < 40:
        return 55
    if pe_ratio < 60:
        return 40
    return 25
