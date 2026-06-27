from __future__ import annotations

from abc import ABC, abstractmethod

from packages.algorithm_layer.schemas import RecommendationInput, RecommendationResult
from packages.scoring_profiles.schemas import ScoringProfile


class RecommendationAlgorithm(ABC):
    algorithm_version: str

    @abstractmethod
    def recommend(
        self, data: RecommendationInput, profile: ScoringProfile | None = None
    ) -> RecommendationResult:
        """Return a structured recommendation result. `profile` selects the
        factor weights (defaults to the Balanced scoring profile)."""

