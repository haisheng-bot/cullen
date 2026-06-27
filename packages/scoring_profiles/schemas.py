from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoringProfile:
    """A named, reusable set of Algorithm Layer factor weights. Replaces the
    hardcoded weights in `packages.algorithm_layer.recommendation` and
    `packages.backtesting.signals` (Project Constitution #12, Configuration
    First: no magic numbers in business logic).
    """

    name: str
    label: str
    description: str
    weights: dict[str, float]
