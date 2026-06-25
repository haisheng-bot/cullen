import unittest

from packages.algorithm_layer.technical_indicators import (
    calculate_momentum_percent,
    calculate_rsi,
    calculate_sma,
    calculate_sma_series,
    detect_ma_cross,
    rsi_score,
    technical_indicator_score,
    trend_score,
)


class TechnicalIndicatorsTest(unittest.TestCase):
    def test_calculate_sma(self) -> None:
        closes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.assertEqual(8.0, calculate_sma(closes, 5))

    def test_calculate_sma_returns_none_when_insufficient_data(self) -> None:
        self.assertIsNone(calculate_sma([1, 2, 3], 5))

    def test_calculate_sma_series(self) -> None:
        closes = [1, 2, 3, 4, 5]
        self.assertEqual([2.0, 3.0, 4.0], calculate_sma_series(closes, 3))

    def test_calculate_rsi_balanced_gains_and_losses_is_fifty(self) -> None:
        closes = [10, 11, 10, 11, 10, 11, 10, 11, 10, 11, 10, 11, 10, 11, 10]
        self.assertAlmostEqual(50.0, calculate_rsi(closes, period=14))

    def test_calculate_rsi_all_gains_is_one_hundred(self) -> None:
        closes = list(range(1, 16))
        self.assertEqual(100.0, calculate_rsi(closes, period=14))

    def test_calculate_rsi_returns_none_when_insufficient_data(self) -> None:
        self.assertIsNone(calculate_rsi([1, 2, 3], period=14))

    def test_detect_ma_cross_golden_cross(self) -> None:
        closes = [10, 10, 10, 1, 10, 10]
        self.assertEqual("golden_cross", detect_ma_cross(closes, short_period=2, long_period=3))

    def test_detect_ma_cross_death_cross(self) -> None:
        closes = [1, 1, 1, 10, 1, 1]
        self.assertEqual("death_cross", detect_ma_cross(closes, short_period=2, long_period=3))

    def test_detect_ma_cross_returns_flat_when_insufficient_data(self) -> None:
        self.assertEqual("flat", detect_ma_cross([1, 2, 3], short_period=5, long_period=20))

    def test_calculate_momentum_percent(self) -> None:
        closes = [100.0] * 9 + [110.0]
        self.assertAlmostEqual(10.0, calculate_momentum_percent(closes, lookback=9))

    def test_calculate_momentum_percent_returns_none_when_insufficient_data(self) -> None:
        self.assertIsNone(calculate_momentum_percent([1, 2, 3], lookback=10))

    def test_trend_score_centers_on_fifty_at_zero_percent(self) -> None:
        self.assertEqual(60, trend_score(0.0))
        self.assertEqual(100, trend_score(5.0))
        self.assertEqual(0, trend_score(-7.5))

    def test_rsi_score_bands(self) -> None:
        self.assertEqual(20, rsi_score(10.0))
        self.assertEqual(50, rsi_score(55.0))
        self.assertEqual(65, rsi_score(70.0))
        self.assertEqual(45, rsi_score(90.0))

    def test_technical_indicator_score_matches_hand_computed_components(self) -> None:
        # 30 days flat at 100 then a sharp 10% jump on the last close: golden
        # cross (short MA pulled above long MA by the jump), strong positive
        # momentum, and a high RSI from the one large gain.
        closes = [100.0] * 29 + [110.0]

        score, explanation = technical_indicator_score(closes)

        momentum_percent = calculate_momentum_percent(closes, lookback=10)
        rsi = calculate_rsi(closes, period=14)
        cross_state = detect_ma_cross(closes, short_period=5, long_period=20)
        expected = round(trend_score(momentum_percent) * 0.4 + rsi_score(rsi) * 0.3 + 80 * 0.3)
        self.assertEqual("golden_cross", cross_state)
        self.assertEqual(max(0, min(100, expected)), score)
        self.assertIn("RSI(14)", explanation)
        self.assertIn("均线(5/20)状态：金叉", explanation)


if __name__ == "__main__":
    unittest.main()
