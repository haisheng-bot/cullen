import unittest

from packages.algorithm_layer.technical_indicators import (
    calculate_momentum_percent,
    calculate_rsi,
    calculate_sma,
    calculate_sma_series,
    detect_ma_cross,
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


if __name__ == "__main__":
    unittest.main()
