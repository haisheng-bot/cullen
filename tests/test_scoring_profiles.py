import unittest

from packages.scoring_profiles.backtest_weights import renormalize_excluding
from packages.scoring_profiles.profiles import (
    FACTOR_NAMES,
    PROFILE_NAMES,
    get_profile,
    list_profiles,
)


class ScoringProfilesTest(unittest.TestCase):
    def test_every_profile_weights_sum_to_one_over_all_factors(self) -> None:
        for profile in list_profiles():
            self.assertEqual(set(FACTOR_NAMES), set(profile.weights))
            self.assertAlmostEqual(1.0, sum(profile.weights.values()), places=6)

    def test_get_profile_returns_known_profile(self) -> None:
        profile = get_profile("balanced")
        self.assertEqual("balanced", profile.name)

    def test_get_profile_rejects_unknown_name(self) -> None:
        with self.assertRaises(ValueError):
            get_profile("not-a-real-profile")

    def test_profile_names_match_built_in_profiles(self) -> None:
        self.assertEqual(5, len(PROFILE_NAMES))
        self.assertIn("balanced", PROFILE_NAMES)
        self.assertIn("growth", PROFILE_NAMES)
        self.assertIn("value", PROFILE_NAMES)
        self.assertIn("defensive", PROFILE_NAMES)
        self.assertIn("momentum", PROFILE_NAMES)


class RenormalizeExcludingTest(unittest.TestCase):
    def test_balanced_excluding_news_sentiment_matches_existing_ai_score_weights(self) -> None:
        # Regression guard: these are the exact values that used to be the
        # hardcoded AI_SCORE_WEIGHTS constant in packages.backtesting.signals.
        weights = renormalize_excluding(get_profile("balanced"), {"news_sentiment"})
        self.assertAlmostEqual(1 / 3, weights["fundamentals"], places=6)
        self.assertAlmostEqual(2 / 9, weights["growth"], places=6)
        self.assertAlmostEqual(2 / 9, weights["valuation"], places=6)
        self.assertAlmostEqual(1 / 9, weights["technical"], places=6)
        self.assertAlmostEqual(1 / 9, weights["volatility_risk"], places=6)
        self.assertNotIn("news_sentiment", weights)

    def test_renormalized_weights_sum_to_one(self) -> None:
        for profile in list_profiles():
            weights = renormalize_excluding(profile, {"news_sentiment"})
            self.assertAlmostEqual(1.0, sum(weights.values()), places=6)


if __name__ == "__main__":
    unittest.main()
