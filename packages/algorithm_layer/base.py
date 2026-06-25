from __future__ import annotations

from abc import ABC, abstractmethod

from packages.algorithm_layer.schemas import RecommendationInput, RecommendationResult


class RecommendationAlgorithm(ABC):
    algorithm_version: str

    @abstractmethod
    def recommend(self, data: RecommendationInput) -> RecommendationResult:
        """Return a structured recommendation result."""

