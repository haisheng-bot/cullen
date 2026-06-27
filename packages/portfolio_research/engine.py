from __future__ import annotations

from collections.abc import Callable

from packages.portfolio_research.schemas import PortfolioResearchRunRequest
from packages.portfolio_research.view_model import build_portfolio_research_view


class PortfolioResearchEngine:
    """Unified product-facing orchestrator for the portfolio research experience."""

    def __init__(
        self,
        workflow_runner: Callable[[PortfolioResearchRunRequest], dict],
        risk_runner: Callable[[PortfolioResearchRunRequest], dict | None],
        optimizer_runner: Callable[[PortfolioResearchRunRequest], dict | None],
        archive_writer: Callable[[PortfolioResearchRunRequest, dict], None],
    ) -> None:
        self.workflow_runner = workflow_runner
        self.risk_runner = risk_runner
        self.optimizer_runner = optimizer_runner
        self.archive_writer = archive_writer

    def run(self, request: PortfolioResearchRunRequest) -> dict:
        workflow_response = self.workflow_runner(request)
        risk_response = None
        optimizer_response = None
        if workflow_response.get("state") != "Failed":
            risk_response = self.risk_runner(request)
            optimizer_response = self.optimizer_runner(request)
        result = build_portfolio_research_view(
            request,
            workflow_response=workflow_response,
            risk_response=risk_response,
            optimizer_response=optimizer_response,
        ).to_dict()
        self.archive_writer(request, result)
        return result
