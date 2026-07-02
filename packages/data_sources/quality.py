from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _first_present(payload: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = payload.get(key)
        if value:
            return str(value)
    return None


def _freshness(as_of: str | None) -> str:
    if not as_of:
        return "unknown"
    try:
        timestamp = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
    except ValueError:
        return "unknown"
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    age_seconds = (datetime.now(timezone.utc) - timestamp).total_seconds()
    if age_seconds <= 86_400:
        return "fresh"
    if age_seconds <= 604_800:
        return "recent"
    return "stale"


def _missing_fields(payload: dict[str, Any], required_fields: tuple[str, ...]) -> list[str]:
    missing = []
    for field in required_fields:
        value = payload.get(field)
        if value is None or value == "" or value == [] or value == {}:
            missing.append(field)
    return missing


def attach_data_quality(
    payload: dict[str, Any],
    *,
    fallback: str,
    required_fields: tuple[str, ...] = (),
    as_of_keys: tuple[str, ...] = ("analysis_time", "generated_at"),
) -> dict[str, Any]:
    result = dict(payload)
    as_of = _first_present(result, as_of_keys)
    source = str(result.get("source") or ", ".join(result.get("sources") or []) or "unknown")
    result["data_quality"] = {
        "source": source,
        "as_of": as_of,
        "freshness": _freshness(as_of),
        "missing_fields": _missing_fields(result, required_fields),
        "fallback": fallback,
    }
    return result
