from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.db.models import ReportArchive


def save_report_archive(
    session: Session,
    *,
    trace_id: str,
    portfolio_name: str,
    title: str,
    markdown: str,
    html: str,
    source_summary: dict,
    risk_disclaimer: str,
    generated_at: str,
) -> ReportArchive:
    record = session.scalar(select(ReportArchive).where(ReportArchive.trace_id == trace_id))
    if record is None:
        record = ReportArchive(trace_id=trace_id)
        session.add(record)
    record.portfolio_name = portfolio_name
    record.title = title
    record.markdown = markdown
    record.html = html
    record.source_summary = source_summary
    record.risk_disclaimer = risk_disclaimer
    record.generated_at = generated_at
    session.flush()
    return record


def get_report_archive(session: Session, trace_id: str) -> ReportArchive | None:
    return session.scalar(select(ReportArchive).where(ReportArchive.trace_id == trace_id))


def list_report_archives(session: Session, *, portfolio_name: str | None = None) -> list[ReportArchive]:
    stmt = select(ReportArchive).order_by(ReportArchive.created_at.desc())
    if portfolio_name is not None:
        stmt = stmt.where(ReportArchive.portfolio_name == portfolio_name)
    return list(session.scalars(stmt))
