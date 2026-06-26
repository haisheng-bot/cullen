from __future__ import annotations

from typing import Any, Callable

from packages.ai_agents.base import Agent
from packages.algorithm_layer.recommendation import TrendRecommendationAlgorithm
from packages.algorithm_layer.schemas import (
    AlgorithmPoint,
    FinancialFactorsInput,
    NewsSignalInput,
    RecommendationInput,
    TechnicalSeriesInput,
)
from packages.data_sources.market_trend import YahooFinanceChartClient
from packages.news_layer.news_policy import NewsPolicyClient

SYSTEM_INSTRUCTION = (
    "You are a financial research assistant. You synthesize an algorithmic "
    "five-factor stock score and recent news/policy signals for a US-listed "
    "company into a short, plain-English research summary, for research "
    "purposes only. State only what the score and news indicate; do not "
    "predict price moves, promise returns, or tell the reader to buy or "
    "sell. Always note this is research assistance, not investment advice."
)


class ReportAgent(Agent):
    """Report Agent: turns the Algorithm Layer's five-factor score and recent
    news/policy signals into a single readable research conclusion. Reuses
    the same data assembly as the /stocks/{symbol}/recommendation endpoint so
    the report's score always matches what the workbench already shows.
    """

    task_type = "stock_research_report"
    system_instruction = SYSTEM_INSTRUCTION

    def __init__(
        self,
        router,
        trend_client: YahooFinanceChartClient | None = None,
        recommendation_algorithm: TrendRecommendationAlgorithm | None = None,
        news_policy_client: NewsPolicyClient | None = None,
        financial_factors_fetcher: Callable[[str], FinancialFactorsInput | None] | None = None,
        technical_series_fetcher: Callable[[str], TechnicalSeriesInput | None] | None = None,
        news_signals_fetcher: Callable[[str], list[NewsSignalInput]] | None = None,
        news_limit: int = 5,
    ) -> None:
        super().__init__(router)
        self.trend_client = trend_client or YahooFinanceChartClient()
        self.recommendation_algorithm = recommendation_algorithm or TrendRecommendationAlgorithm()
        self.news_policy_client = news_policy_client or NewsPolicyClient()
        self.financial_factors_fetcher = financial_factors_fetcher or (lambda symbol: None)
        self.technical_series_fetcher = technical_series_fetcher or (lambda symbol: None)
        self.news_signals_fetcher = news_signals_fetcher or (lambda symbol: [])
        self.news_limit = news_limit

    def build_context(self, symbol: str) -> dict[str, Any]:
        trend = self.trend_client.fetch_trend(symbol, range_="1d", interval="1m")
        algorithm_input = RecommendationInput(
            symbol=trend.symbol,
            latest_price=trend.regular_market_price or trend.latest_price,
            previous_close=trend.previous_close,
            points=[
                AlgorithmPoint(timestamp=point.timestamp, close=point.close, volume=point.volume)
                for point in trend.points
            ],
            source=trend.source,
            analysis_time=trend.analysis_time,
            financial_factors=self.financial_factors_fetcher(symbol),
            technical_series=self.technical_series_fetcher(symbol),
            news_signals=self.news_signals_fetcher(symbol),
        )
        recommendation = self.recommendation_algorithm.recommend(algorithm_input)
        news = self.news_policy_client.fetch(symbol, years=1, limit=self.news_limit)

        citations = [trend.source] + [item.url for item in news.items if item.url]
        if not citations:
            citations = [trend.source]

        factors_summary = "\n".join(
            f"- {factor.name} ({factor.score}/100, weight {factor.weight}): {factor.explanation}"
            for factor in recommendation.factors
        )
        news_summary = "\n".join(
            f"- [{item.category}] {item.title}: {item.summary}" for item in news.items
        ) or "No recent news found."

        return {
            "citations": citations,
            "total_score": recommendation.total_score,
            "recommendation": recommendation.recommendation,
            "factors_summary": factors_summary,
            "reasons": recommendation.reasons,
            "risks": recommendation.risks,
            "news_summary": news_summary,
            "algorithm_version": recommendation.algorithm_version,
        }

    def build_user_input(self, symbol: str, context: dict[str, Any]) -> str:
        return (
            f"Stock: {symbol}\n"
            f"Algorithm score: {context['total_score']}/100 "
            f"({context['recommendation']}, {context['algorithm_version']})\n"
            f"Factor breakdown:\n{context['factors_summary']}\n\n"
            f"Reasons: {', '.join(context['reasons']) or 'None'}\n"
            f"Risks: {', '.join(context['risks']) or 'None'}\n\n"
            f"Recent news/policy signals:\n{context['news_summary']}\n\n"
            "Write a short research summary (a few sentences) that connects the "
            "factor score to the recent news, and explains what an investor "
            "researching this stock should pay attention to next."
        )
