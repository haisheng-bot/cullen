from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import html
import re
import xml.etree.ElementTree as ET
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from packages.data_sources.market_trend import normalize_symbol
from packages.data_sources.sec_filings import SECFilingClient, SECFilingError
from packages.news_layer.schemas import NewsItem, NewsPolicyResponse


YAHOO_RSS_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
RECENT_NEWS_LIMIT = 10
COVERAGE_NOTE = (
    "Recent company news is sourced from Yahoo Finance RSS. "
    "SEC EDGAR filings cover regulatory disclosures and governance events within the requested window. "
    "Complete 3-year full-news archives require a dedicated archival news provider."
)


class NewsPolicyError(RuntimeError):
    """Raised when news or policy data cannot be parsed."""


class NewsPolicyClient:
    source_name = "Yahoo Finance RSS + SEC EDGAR"

    def __init__(self, sec_client: SECFilingClient | None = None) -> None:
        self.sec_client = sec_client or SECFilingClient()

    def fetch(self, symbol: str, years: int = 3, limit: int = 30) -> NewsPolicyResponse:
        normalized_symbol = normalize_symbol(symbol)
        normalized_years = max(1, min(years, 3))
        normalized_limit = max(1, min(limit, 100))
        generated_at = datetime.now(timezone.utc)

        items = []
        items.extend(self.fetch_recent_yahoo_news(normalized_symbol, RECENT_NEWS_LIMIT))
        items.extend(self.fetch_sec_policy_items(normalized_symbol, normalized_years, normalized_limit))
        items = sorted(items, key=lambda item: item.published_at, reverse=True)[:normalized_limit]

        return NewsPolicyResponse(
            symbol=normalized_symbol,
            years=normalized_years,
            items=items,
            sources=sorted({item.source for item in items} or {self.source_name}),
            generated_at=generated_at.isoformat(),
            coverage_note=COVERAGE_NOTE,
        )

    def fetch_recent_yahoo_news(self, symbol: str, limit: int) -> list[NewsItem]:
        url = YAHOO_RSS_URL.format(symbol=quote(symbol))
        request = Request(url, headers={"User-Agent": "OpenStockAI/0.1"})
        try:
            with urlopen(request, timeout=12) as response:
                xml_text = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError):
            return []
        return parse_yahoo_rss(xml_text, symbol, limit)

    def fetch_sec_policy_items(self, symbol: str, years: int, limit: int) -> list[NewsItem]:
        cutoff = datetime.now(timezone.utc).date() - timedelta(days=365 * years)
        try:
            filings = self.sec_client.list_filings(symbol, forms=("8-K", "10-K", "10-Q"), limit=limit).filings
        except SECFilingError:
            return []

        items: list[NewsItem] = []
        for filing in filings:
            if filing.filing_date and filing.filing_date < cutoff.isoformat():
                continue
            category = classify_sec_filing(filing.form, filing.primary_document)
            title = f"{symbol} {filing.form} filing"
            if category == "management_change":
                title = f"{symbol} possible management or governance disclosure"
            items.append(
                NewsItem(
                    title=title,
                    summary=f"SEC {filing.form} filed on {filing.filing_date}.",
                    url=filing.document_url,
                    source="SEC EDGAR",
                    published_at=f"{filing.filing_date}T00:00:00+00:00",
                    category=category,
                    symbols=[symbol],
                )
            )
        return items


def parse_yahoo_rss(xml_text: str, symbol: str, limit: int) -> list[NewsItem]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise NewsPolicyError("Failed to parse Yahoo Finance RSS") from exc

    items: list[NewsItem] = []
    for item in root.findall(".//item")[:limit]:
        title = clean_text(item.findtext("title") or "")
        link = item.findtext("link") or ""
        description = clean_text(item.findtext("description") or "")
        published_at = parse_rss_datetime(item.findtext("pubDate") or "")
        items.append(
            NewsItem(
                title=title,
                summary=description,
                url=link,
                source="Yahoo Finance RSS",
                published_at=published_at,
                category="company_news",
                symbols=[symbol],
            )
        )
    return items


def parse_rss_datetime(raw: str) -> str:
    if not raw:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = parsedate_to_datetime(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        return datetime.now(timezone.utc).isoformat()


def classify_sec_filing(form: str, primary_document: str) -> str:
    document = primary_document.lower()
    management_terms = r"5[-_]?02|director|officer|appointment|resignation|departure|management"
    if form.upper() == "8-K" and re.search(management_terms, document):
        return "management_change"
    if form.upper() == "8-K":
        return "governance"
    return "sec_filing"


def clean_text(value: str) -> str:
    text = html.unescape(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
