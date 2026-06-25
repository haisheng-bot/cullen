"""SEC EDGAR XBRL company facts: revenue, net income, EPS, equity, shares,
plus the operating income / working capital / debt / cash figures needed
for Magic Formula-style metrics (EBIT/EV earnings yield, ROC).

Free, key-less, reuses SECFilingClient for ticker -> CIK resolution.
Used by Algorithm Layer (algorithm-v0.2+) to compute fundamentals,
growth, and valuation factors from real filed financial data instead
of price action alone.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from packages.data_sources.market_trend import RISK_DISCLAIMER, normalize_symbol
from packages.data_sources.sec_filings import USER_AGENT, SECFilingClient, SECFilingError

COMPANYFACTS_URL_TEMPLATE = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

REVENUE_TAGS = (
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
)
NET_INCOME_TAGS = ("NetIncomeLoss",)
EPS_DILUTED_TAGS = ("EarningsPerShareDiluted", "EarningsPerShareBasic")
ASSETS_TAGS = ("Assets",)
EQUITY_TAGS = (
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
)
SHARES_OUTSTANDING_TAGS = ("CommonStockSharesOutstanding", "CommonStockSharesIssued")
OPERATING_INCOME_TAGS = ("OperatingIncomeLoss",)
CURRENT_ASSETS_TAGS = ("AssetsCurrent",)
CURRENT_LIABILITIES_TAGS = ("LiabilitiesCurrent",)
NET_FIXED_ASSETS_TAGS = ("PropertyPlantAndEquipmentNet",)
CASH_TAGS = (
    "CashAndCashEquivalentsAtCarryingValue",
    "CashAndCashEquivalentsAtCarryingValueIncludingDiscontinuedOperations",
)
LONG_TERM_DEBT_TAGS = ("LongTermDebtNoncurrent", "LongTermDebt")
CURRENT_DEBT_TAGS = ("DebtCurrent", "LongTermDebtCurrent", "ShortTermBorrowings")


class SECFinancialsError(RuntimeError):
    """Raised when SEC XBRL company facts cannot be fetched or parsed."""


@dataclass(frozen=True)
class AnnualFinancials:
    fiscal_year: int | None
    end_date: str | None
    revenue: float | None
    net_income: float | None
    eps_diluted: float | None
    total_assets: float | None
    stockholders_equity: float | None
    shares_outstanding: float | None
    operating_income: float | None
    current_assets: float | None
    current_liabilities: float | None
    net_fixed_assets: float | None
    cash: float | None
    total_debt: float | None


@dataclass(frozen=True)
class FinancialFactsResponse:
    symbol: str
    cik: str
    company_name: str
    latest: AnnualFinancials | None
    previous: AnnualFinancials | None
    source: str
    analysis_time: str
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "cik": self.cik,
            "company_name": self.company_name,
            "latest": self.latest.__dict__ if self.latest else None,
            "previous": self.previous.__dict__ if self.previous else None,
            "source": self.source,
            "analysis_time": self.analysis_time,
            "risk_disclaimer": self.risk_disclaimer,
        }


class SECFinancialsClient:
    source_name = "SEC EDGAR XBRL company facts"

    def __init__(self, filing_client: SECFilingClient | None = None) -> None:
        self.filing_client = filing_client or SECFilingClient()

    def fetch_financial_facts(self, symbol: str) -> FinancialFactsResponse:
        normalized_symbol = normalize_symbol(symbol)
        try:
            cik = self.filing_client.get_cik(normalized_symbol)
        except SECFilingError as exc:
            raise SECFinancialsError(str(exc)) from exc

        url = COMPANYFACTS_URL_TEMPLATE.format(cik=cik)
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise SECFinancialsError(f"Failed to fetch SEC company facts for {normalized_symbol}") from exc

        return parse_companyfacts_payload(payload, normalized_symbol, cik)


def parse_companyfacts_payload(payload: dict[str, Any], symbol: str, cik: str) -> FinancialFactsResponse:
    us_gaap = (payload.get("facts") or {}).get("us-gaap") or {}

    revenue_series = _annual_series(us_gaap, REVENUE_TAGS)
    net_income_series = _annual_series(us_gaap, NET_INCOME_TAGS)
    eps_series = _annual_series(us_gaap, EPS_DILUTED_TAGS)
    assets_series = _annual_series(us_gaap, ASSETS_TAGS)
    equity_series = _annual_series(us_gaap, EQUITY_TAGS)
    shares_series = _annual_series(us_gaap, SHARES_OUTSTANDING_TAGS)
    operating_income_series = _annual_series(us_gaap, OPERATING_INCOME_TAGS)
    current_assets_series = _annual_series(us_gaap, CURRENT_ASSETS_TAGS)
    current_liabilities_series = _annual_series(us_gaap, CURRENT_LIABILITIES_TAGS)
    net_fixed_assets_series = _annual_series(us_gaap, NET_FIXED_ASSETS_TAGS)
    cash_series = _annual_series(us_gaap, CASH_TAGS)
    long_term_debt_series = _annual_series(us_gaap, LONG_TERM_DEBT_TAGS)
    current_debt_series = _annual_series(us_gaap, CURRENT_DEBT_TAGS)

    end_dates = sorted(
        {entry["end"] for entry in revenue_series + net_income_series + eps_series},
        reverse=True,
    )

    def build(end_date: str | None) -> AnnualFinancials | None:
        if end_date is None:
            return None
        long_term_debt = _value_for_end(long_term_debt_series, end_date) or 0
        current_debt = _value_for_end(current_debt_series, end_date) or 0
        return AnnualFinancials(
            fiscal_year=_value_for_end(revenue_series, end_date, "fy"),
            end_date=end_date,
            revenue=_value_for_end(revenue_series, end_date),
            net_income=_value_for_end(net_income_series, end_date),
            eps_diluted=_value_for_end(eps_series, end_date),
            total_assets=_value_for_end(assets_series, end_date),
            stockholders_equity=_value_for_end(equity_series, end_date),
            shares_outstanding=_value_for_end(shares_series, end_date),
            operating_income=_value_for_end(operating_income_series, end_date),
            current_assets=_value_for_end(current_assets_series, end_date),
            current_liabilities=_value_for_end(current_liabilities_series, end_date),
            net_fixed_assets=_value_for_end(net_fixed_assets_series, end_date),
            cash=_value_for_end(cash_series, end_date),
            total_debt=long_term_debt + current_debt,
        )

    latest_end = end_dates[0] if end_dates else None
    previous_end = end_dates[1] if len(end_dates) > 1 else None

    return FinancialFactsResponse(
        symbol=symbol,
        cik=cik,
        company_name=payload.get("entityName", ""),
        latest=build(latest_end),
        previous=build(previous_end),
        source=SECFinancialsClient.source_name,
        analysis_time=datetime.now(timezone.utc).isoformat(),
    )


def _annual_series(us_gaap: dict[str, Any], tags: tuple[str, ...]) -> list[dict[str, Any]]:
    """Return one entry per fiscal year-end, annual (10-K, fp=FY) figures only.

    XBRL company facts repeat the same period's value across multiple
    filings (as prior-year comparatives), so entries are deduped by
    `end` date, keeping the most recently filed value for that period.
    """
    for tag in tags:
        concept = us_gaap.get(tag)
        if not concept:
            continue
        units = concept.get("units") or {}
        if not units:
            continue
        raw_entries = next(iter(units.values()))
        annual_entries = [
            entry
            for entry in raw_entries
            if entry.get("fp") == "FY" and entry.get("form", "").startswith("10-K")
        ]
        if not annual_entries:
            continue

        by_end_date: dict[str, dict[str, Any]] = {}
        for entry in sorted(annual_entries, key=lambda e: e.get("filed", "")):
            by_end_date[entry["end"]] = entry
        return list(by_end_date.values())
    return []


def _value_for_end(series: list[dict[str, Any]], end_date: str, field: str = "val") -> Any:
    for entry in series:
        if entry["end"] == end_date:
            return entry.get(field)
    return None
