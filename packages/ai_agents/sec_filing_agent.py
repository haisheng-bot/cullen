from __future__ import annotations

from typing import Any

from packages.ai_agents.base import Agent
from packages.data_sources.sec_filings import DEFAULT_FORM_TYPES, SECFilingClient

SYSTEM_INSTRUCTION = (
    "You are a financial research assistant. You summarize recent SEC EDGAR "
    "filings for a US-listed company in plain English, for research purposes "
    "only. State only what the filings indicate; do not predict price moves, "
    "promise returns, or tell the reader to buy or sell. Always note this is "
    "research assistance, not investment advice."
)


class SECFilingAgent(Agent):
    """SEC Filing Agent: summarizes a company's recent EDGAR filings."""

    task_type = "sec_filing_summary"
    system_instruction = SYSTEM_INSTRUCTION

    def __init__(
        self,
        router,
        sec_client: SECFilingClient | None = None,
        forms: tuple[str, ...] = DEFAULT_FORM_TYPES,
        limit: int = 5,
    ) -> None:
        super().__init__(router)
        self.sec_client = sec_client or SECFilingClient()
        self.forms = forms
        self.limit = limit

    def build_context(self, symbol: str) -> dict[str, Any]:
        filing_list = self.sec_client.list_filings(symbol, forms=self.forms, limit=self.limit)
        citations = [filing.document_url for filing in filing_list.filings] or [filing_list.source]
        filings_summary = "\n".join(
            f"- {filing.form} filed {filing.filing_date}: {filing.document_url}"
            for filing in filing_list.filings
        ) or "No recent filings found."

        return {
            "citations": citations,
            "company_name": filing_list.company_name,
            "cik": filing_list.cik,
            "filings_summary": filings_summary,
        }

    def build_user_input(self, symbol: str, context: dict[str, Any]) -> str:
        return (
            f"Company: {context['company_name']} ({symbol}, CIK {context['cik']})\n"
            f"Recent SEC filings:\n{context['filings_summary']}\n\n"
            "Summarize what these filings indicate about the company's recent "
            "regulatory and financial disclosure activity."
        )
