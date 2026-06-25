"""AI 选股 workflow: scans a candidate pool (Universe Layer) and scores
each candidate with Algorithm Layer, returning a ranked list.

Per requirements-analysis.md section 4.1, output must include per
candidate: symbol, company name, total score, recommendation label,
reasons, risks, data source, and risk disclaimer.
"""
from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from datetime import datetime, timezone

from packages.algorithm_layer.base import RecommendationAlgorithm
from packages.algorithm_layer.schemas import (
    AlgorithmPoint,
    FinancialFactorsInput,
    RecommendationInput,
    TechnicalSeriesInput,
)
from packages.data_sources.market_trend import MarketTrendError
from packages.workflow_layer.schemas import ScreeningCandidate, ScreeningResult, SkippedCandidate

MAX_CONCURRENT_REQUESTS = 8


class StockScreeningWorkflow:
    def __init__(
        self,
        universe_scanner,
        trend_client,
        algorithm: RecommendationAlgorithm,
        financial_factors_fetcher: Callable[[str], FinancialFactorsInput | None],
        technical_series_fetcher: Callable[[str], TechnicalSeriesInput | None] | None = None,
    ) -> None:
        self.universe_scanner = universe_scanner
        self.trend_client = trend_client
        self.algorithm = algorithm
        self.financial_factors_fetcher = financial_factors_fetcher
        self.technical_series_fetcher = technical_series_fetcher or (lambda symbol: None)

    def screen(self, limit: int = 20) -> ScreeningResult:
        universe = self.universe_scanner.scan(limit=limit)

        candidates: list[ScreeningCandidate] = []
        skipped: list[SkippedCandidate] = []

        # Each candidate is an independent, I/O-bound (network) lookup, so
        # threads give real speedup here despite the GIL.
        worker_count = min(MAX_CONCURRENT_REQUESTS, len(universe.items)) or 1
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_to_item = {
                executor.submit(self._score_candidate, item): item for item in universe.items
            }
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    candidates.append(future.result())
                except (MarketTrendError, ValueError) as exc:
                    skipped.append(SkippedCandidate(symbol=item.symbol, reason=str(exc)))

        candidates.sort(key=lambda candidate: candidate.total_score, reverse=True)
        ranked_candidates = [
            replace(candidate, rank=rank) for rank, candidate in enumerate(candidates, start=1)
        ]

        return ScreeningResult(
            market=universe.market,
            requested_limit=limit,
            scored_count=len(ranked_candidates),
            candidates=ranked_candidates,
            skipped=skipped,
            source=f"{universe.source} + Algorithm Layer",
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _score_candidate(self, item) -> ScreeningCandidate:
        trend = self.trend_client.fetch_trend(item.symbol, range_="1d", interval="1m")
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
            financial_factors=self.financial_factors_fetcher(item.symbol),
            technical_series=self.technical_series_fetcher(item.symbol),
        )
        result = self.algorithm.recommend(algorithm_input)

        return ScreeningCandidate(
            rank=0,
            symbol=result.symbol,
            name=item.name,
            sector=item.sector or "",
            total_score=result.total_score,
            recommendation=result.recommendation,
            factors=[factor.to_dict() for factor in result.factors],
            reasons=result.reasons,
            risks=result.risks,
            source=result.source,
            algorithm_version=result.algorithm_version,
        )
