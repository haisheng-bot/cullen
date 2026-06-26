"""SEC EDGAR filing lookup (10-K / 10-Q / 8-K), free and key-less.

Per SEC's fair access policy, all requests must send a descriptive
User-Agent identifying the application. See
https://www.sec.gov/os/accessing-edgar-data for details.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from http.client import IncompleteRead
import json
import threading
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from packages.data_sources.market_trend import RISK_DISCLAIMER, normalize_symbol

USER_AGENT = "OpenStockAI/0.1 (research tool; contact: support@openstock.ai)"
TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL_TEMPLATE = "https://data.sec.gov/submissions/CIK{cik}.json"
DEFAULT_FORM_TYPES = ("10-K", "10-Q", "8-K")


class SECFilingError(RuntimeError):
    """Raised when SEC EDGAR data cannot be fetched or parsed."""


@dataclass(frozen=True)
class Filing:
    form: str
    filing_date: str
    report_date: str | None
    accession_number: str
    primary_document: str
    document_url: str


@dataclass(frozen=True)
class FilingListResponse:
    symbol: str
    cik: str
    company_name: str
    filings: list[Filing]
    source: str
    analysis_time: str
    risk_disclaimer: str = RISK_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "cik": self.cik,
            "company_name": self.company_name,
            "filings": [filing.__dict__ for filing in self.filings],
            "source": self.source,
            "analysis_time": self.analysis_time,
            "risk_disclaimer": self.risk_disclaimer,
        }


class SECFilingClient:
    source_name = "SEC EDGAR"

    def __init__(self) -> None:
        self._cik_cache: dict[str, str] = {}
        self._cik_cache_lock = threading.Lock()

    def get_cik(self, symbol: str) -> str:
        normalized_symbol = normalize_symbol(symbol)
        if normalized_symbol not in self._cik_cache:
            with self._cik_cache_lock:
                # Re-check after acquiring the lock: another thread may have
                # populated the cache while we were waiting (otherwise N
                # concurrent cold symbols redundantly download the same
                # multi-thousand-ticker mapping file N times).
                if normalized_symbol not in self._cik_cache:
                    payload = self._fetch_json(TICKER_MAP_URL)
                    self._cik_cache.update(parse_ticker_map_full(payload))

        if normalized_symbol not in self._cik_cache:
            raise SECFilingError(f"No SEC CIK found for symbol {normalized_symbol}")
        return self._cik_cache[normalized_symbol]

    def list_filings(
        self,
        symbol: str,
        forms: tuple[str, ...] = DEFAULT_FORM_TYPES,
        limit: int = 10,
    ) -> FilingListResponse:
        normalized_symbol = normalize_symbol(symbol)
        cik = self.get_cik(normalized_symbol)
        payload = self._fetch_json(SUBMISSIONS_URL_TEMPLATE.format(cik=cik))
        return parse_submissions_payload(payload, normalized_symbol, cik, forms, limit)

    def _fetch_json(self, url: str) -> dict[str, Any]:
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, IncompleteRead, json.JSONDecodeError) as exc:
            raise SECFilingError(f"Failed to fetch SEC EDGAR data from {url}") from exc


def parse_ticker_map_payload(payload: dict[str, Any], symbol: str) -> str:
    normalized_symbol = normalize_symbol(symbol)
    for entry in payload.values():
        if str(entry.get("ticker", "")).upper() == normalized_symbol:
            return str(entry["cik_str"]).zfill(10)
    raise SECFilingError(f"No SEC CIK found for symbol {normalized_symbol}")


def parse_ticker_map_full(payload: dict[str, Any]) -> dict[str, str]:
    """Every ticker -> CIK pair in one pass, so a single download of the
    (shared, multi-thousand-entry) mapping file can resolve any symbol for
    the rest of the process's lifetime instead of one download per symbol.
    """
    mapping: dict[str, str] = {}
    for entry in payload.values():
        ticker = str(entry.get("ticker", "")).upper()
        if ticker:
            mapping[ticker] = str(entry["cik_str"]).zfill(10)
    return mapping


def parse_submissions_payload(
    payload: dict[str, Any],
    symbol: str,
    cik: str,
    forms: tuple[str, ...],
    limit: int,
) -> FilingListResponse:
    recent = (payload.get("filings") or {}).get("recent") or {}
    form_list = recent.get("form") or []
    filing_dates = recent.get("filingDate") or []
    report_dates = recent.get("reportDate") or []
    accession_numbers = recent.get("accessionNumber") or []
    primary_documents = recent.get("primaryDocument") or []

    wanted_forms = {form.upper() for form in forms}
    cik_no_zeros = str(int(cik))

    filings: list[Filing] = []
    for index, form in enumerate(form_list):
        if form.upper() not in wanted_forms:
            continue
        accession_number = accession_numbers[index]
        primary_document = primary_documents[index] if index < len(primary_documents) else ""
        accession_no_dashes = accession_number.replace("-", "")
        document_url = (
            f"https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/"
            f"{accession_no_dashes}/{primary_document}"
        )
        filings.append(
            Filing(
                form=form,
                filing_date=filing_dates[index] if index < len(filing_dates) else "",
                report_date=report_dates[index] if index < len(report_dates) else None,
                accession_number=accession_number,
                primary_document=primary_document,
                document_url=document_url,
            )
        )
        if len(filings) >= limit:
            break

    return FilingListResponse(
        symbol=symbol,
        cik=cik,
        company_name=payload.get("name", ""),
        filings=filings,
        source=SECFilingClient.source_name,
        analysis_time=datetime.now(timezone.utc).isoformat(),
    )
