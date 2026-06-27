from __future__ import annotations

from packages.scoring_profiles.schemas import ScoringProfile


def renormalize_excluding(profile: ScoringProfile, exclude: set[str]) -> dict[str, float]:
    """Drop `exclude` factors from `profile.weights` and rescale the rest to
    sum back to 1.0. Backtesting drops `news_sentiment`: no historical news
    archive exists, so scoring it during a backtest would be lookahead bias
    (see docs/standards/PORTFOLIO_STRATEGY_STANDARD.md).
    """
    remaining = {name: weight for name, weight in profile.weights.items() if name not in exclude}
    total = sum(remaining.values())
    return {name: weight / total for name, weight in remaining.items()}
