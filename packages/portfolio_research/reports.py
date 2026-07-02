from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any

RISK_DISCLAIMER = "本系统仅用于投资研究辅助，不构成任何投资建议。"


@dataclass(frozen=True)
class ResearchReport:
    trace_id: str
    portfolio_name: str
    title: str
    markdown: str
    html: str
    source_summary: dict[str, Any]
    risk_disclaimer: str
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "portfolio_name": self.portfolio_name,
            "title": self.title,
            "markdown": self.markdown,
            "html": self.html,
            "source_summary": self.source_summary,
            "risk_disclaimer": self.risk_disclaimer,
            "generated_at": self.generated_at,
        }


def report_summary(record) -> dict[str, Any]:
    return {
        "trace_id": record.trace_id,
        "portfolio_name": record.portfolio_name,
        "title": record.title,
        "source_summary": record.source_summary,
        "risk_disclaimer": record.risk_disclaimer,
        "generated_at": record.generated_at,
    }


def report_detail(record) -> dict[str, Any]:
    payload = report_summary(record)
    payload.update({"markdown": record.markdown, "html": record.html})
    return payload


def build_report_from_run(run: dict) -> ResearchReport:
    portfolio = run.get("portfolio") or {}
    portfolio_name = portfolio.get("name") or "Portfolio Research"
    trace_id = run["trace_id"]
    generated_at = run.get("completed_at") or run.get("started_at") or ""
    title = f"{portfolio_name} Research Report"
    markdown = _markdown_report(run, title)
    return ResearchReport(
        trace_id=trace_id,
        portfolio_name=portfolio_name,
        title=title,
        markdown=markdown,
        html=_markdown_to_html(markdown),
        source_summary={
            "workflow_name": run.get("workflow_name"),
            "workflow_version": run.get("workflow_version"),
            "state": run.get("state"),
            "symbols": portfolio.get("symbols") or [],
        },
        risk_disclaimer=run.get("risk_disclaimer") or RISK_DISCLAIMER,
        generated_at=generated_at,
    )


def _markdown_report(run: dict, title: str) -> str:
    portfolio = run.get("portfolio") or {}
    backtest = run.get("backtest_summary") or (run.get("workflow") or {}).get("response", {}).get("backtest") or {}
    risk = run.get("risk_summary") or {}
    optimizer = run.get("optimized_weights") or {}
    ai = run.get("ai_explanation") or {}
    recommendation = run.get("recommendation") or {}
    symbols = ", ".join(portfolio.get("symbols") or []) or "-"
    weights = optimizer.get("target_weights") or {}
    weight_lines = [f"- {symbol}: {float(weight) * 100:.2f}%" for symbol, weight in sorted(weights.items())]

    sections = [
        f"# {title}",
        f"- Trace ID: {run.get('trace_id', '-')}",
        f"- Portfolio: {portfolio.get('name', '-')}",
        f"- Symbols: {symbols}",
        f"- Generated at: {run.get('completed_at') or run.get('started_at') or '-'}",
        "",
        "## Recommendation",
        f"- Action: {recommendation.get('action', '-')}",
        *_list("Reasons", recommendation.get("reasons")),
        *_list("Suggestions", recommendation.get("suggestions")),
        *_list("Risks", recommendation.get("risks")),
        "",
        "## Backtest",
        f"- Total return: {_percent(backtest.get('total_return_percent'))}",
        f"- Annualized return: {_percent(backtest.get('annualized_return_percent'))}",
        f"- Max drawdown: {_percent(backtest.get('max_drawdown_percent'))}",
        f"- Sharpe: {backtest.get('sharpe_ratio', '-')}",
        "",
        "## Risk",
        f"- Volatility: {_percent(risk.get('volatility_percent'))}",
        f"- Beta: {risk.get('beta', '-')}",
        f"- Concentration: {_percent(risk.get('concentration_percent'))}",
        "",
        "## Optimized Weights",
        *(weight_lines or ["- No optimized weights."]),
        "",
        "## AI Explanation",
        f"- Conclusion: {ai.get('conclusion', '-')}",
        *_list("Key findings", ai.get("key_findings")),
        "",
        f"> {run.get('risk_disclaimer') or RISK_DISCLAIMER}",
    ]
    return "\n".join(sections)


def _list(title: str, items: list[str] | None) -> list[str]:
    values = items or []
    return [f"- {title}:"] + [f"  - {item}" for item in values] if values else [f"- {title}: -"]


def _percent(value: Any) -> str:
    return "-" if value is None else f"{float(value):.2f}%"


def _markdown_to_html(markdown: str) -> str:
    lines = []
    in_list = False
    for raw in markdown.splitlines():
        line = raw.rstrip()
        if in_list and not line.startswith("- ") and not line.startswith("  - "):
            lines.append("</ul>")
            in_list = False
        if line.startswith("# "):
            lines.append(f"<h1>{escape(line[2:])}</h1>")
        elif line.startswith("## "):
            lines.append(f"<h2>{escape(line[3:])}</h2>")
        elif line.startswith("> "):
            lines.append(f"<blockquote>{escape(line[2:])}</blockquote>")
        elif line.startswith("- ") or line.startswith("  - "):
            if not in_list:
                lines.append("<ul>")
                in_list = True
            lines.append(f"<li>{escape(line.lstrip('- '))}</li>")
        elif line:
            lines.append(f"<p>{escape(line)}</p>")
    if in_list:
        lines.append("</ul>")
    return "\n".join(lines)
