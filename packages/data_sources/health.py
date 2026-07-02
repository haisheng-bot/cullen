from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from packages.config import Settings, get_settings
from packages.data_sources.market_trend import RISK_DISCLAIMER


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _health_item(
    *,
    name: str,
    source: str,
    configured: bool,
    available: bool,
    capabilities: list[str],
    fallback: str,
    last_error: str | None = None,
    requires_config: bool = False,
    checked_at: str,
) -> dict[str, Any]:
    status = "available" if available else "not_configured" if not configured else "degraded"
    return {
        "name": name,
        "source": source,
        "configured": configured,
        "available": available,
        "status": status,
        "capabilities": capabilities,
        "requires_config": requires_config,
        "last_error": last_error,
        "fallback": fallback,
        "checked_at": checked_at,
    }


def build_data_source_health(
    settings: Settings | None = None,
    tiger_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    checked_at = _now()
    tiger_status = tiger_status or {}
    tiger_configured = bool(tiger_status.get("configured"))
    tiger_available = tiger_configured and bool(tiger_status.get("sdk_available"))
    tiger_missing = tiger_status.get("missing_fields") or []

    items = [
        _health_item(
            name="Yahoo Market Data",
            source="Yahoo Finance chart API",
            configured=True,
            available=True,
            capabilities=["quote", "trend", "history", "most_active_universe"],
            fallback="Use cached price history where available; otherwise show source error.",
            checked_at=checked_at,
        ),
        _health_item(
            name="SEC EDGAR",
            source="SEC EDGAR submissions + XBRL company facts",
            configured=True,
            available=True,
            capabilities=["filings", "financial_facts", "news_policy_disclosures"],
            fallback="Financial factors degrade to empty fundamentals when SEC data is missing.",
            checked_at=checked_at,
        ),
        _health_item(
            name="FRED Macro",
            source="FRED API",
            configured=bool(settings.fred_api_key),
            available=bool(settings.fred_api_key),
            capabilities=["macro_series"],
            requires_config=True,
            last_error=None if settings.fred_api_key else "FRED_API_KEY is not configured.",
            fallback="Macro panel remains unavailable until FRED_API_KEY is configured.",
            checked_at=checked_at,
        ),
        _health_item(
            name="Tiger Brokers OpenAPI",
            source="Tiger Brokers OpenAPI",
            configured=tiger_configured,
            available=tiger_available,
            capabilities=["quote", "history"],
            requires_config=True,
            last_error=None if tiger_available else ", ".join(tiger_missing) or "Tiger SDK is unavailable.",
            fallback="Use Yahoo market data while Tiger OpenAPI is not configured or SDK is unavailable.",
            checked_at=checked_at,
        ),
    ]
    available_count = sum(1 for item in items if item["available"])
    required_sources_available = all(item["available"] for item in items if not item["requires_config"])
    return {
        "overall_status": "ok" if required_sources_available else "degraded",
        "available_count": available_count,
        "total_count": len(items),
        "items": items,
        "risk_disclaimer": RISK_DISCLAIMER,
        "checked_at": checked_at,
    }
