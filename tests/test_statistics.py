import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmeter import statistics_ as stats


class TestRobustSummaries(unittest.TestCase):
    def test_median_ignores_outliers(self):
        clean = [100] * 20
        contaminated = clean + [100_000]
        self.assertEqual(stats.median(clean), 100)
        self.assertEqual(stats.median(contaminated), 100)

    def test_drift_is_zero_for_stable_samples(self):
        self.assertAlmostEqual(stats.drift([1000] * 200), 0.0, places=6)

    def test_drift_detects_gradual_slowdown(self):
        slowing = [1000 + index * 10 for index in range(200)]
        self.assertGreater(stats.drift(slowing), 0.5)

    def test_autocorrelation_is_zero_for_independent_samples(self):
        rng = random.Random(1)
        independent = [rng.gauss(1000, 50) for _ in range(2000)]
        self.assertLess(abs(stats.autocorrelation(independent)), 0.1)

    def test_autocorrelation_detects_dependence(self):
        rng = random.Random(2)
        samples = [1000.0]
        for _ in range(2000):
            samples.append(samples[-1] * 0.9 + 100 + rng.gauss(0, 1))
        self.assertGreater(stats.autocorrelation(samples), 0.5)


class TestConfidenceInterval(unittest.TestCase):
    def test_identical_series_interval_spans_parity(self):
        samples = [100 + (index % 7) for index in range(120)]
        _, lower, upper = stats.ratio_confidence_interval(
            samples, list(samples), seed=3)
        self.assertLessEqual(lower, 1.0)
        self.assertGreaterEqual(upper, 1.0)
        self.assertFalse(stats.is_conclusive(lower, upper))

    def test_clear_difference_is_conclusive(self):
        slow = [200 + (index % 5) for index in range(120)]
        fast = [100 + (index % 5) for index in range(120)]
        ratio, lower, upper = stats.ratio_confidence_interval(
            slow, fast, seed=3)
        self.assertTrue(stats.is_conclusive(lower, upper))
        self.assertLess(ratio, 1.0)

    def test_interval_narrows_with_more_samples(self):
        rng = random.Random(5)

        def width(count):
            left = [rng.gauss(1000, 100) for _ in range(count)]
            right = [rng.gauss(1000, 100) for _ in range(count)]
            _, lower, upper = stats.ratio_confidence_interval(
                left, right, seed=9)
            return upper - lower

        self.assertLess(width(400), width(30))


class TestResolution(unittest.TestCase):
    def test_quiet_machine_resolves_finer_than_noisy_one(self):
        rng = random.Random(11)
        quiet = [rng.gauss(1000, 5) for _ in range(300)]
        noisy = [rng.gauss(1000, 200) for _ in range(300)]
        self.assertLess(stats.resolvable_difference(quiet),
                        stats.resolvable_difference(noisy))

    def test_confidence_label_drops_when_machine_drifts(self):
        self.assertEqual(stats.confidence_label(0.01, 200, 0.05), "high")
        self.assertEqual(stats.confidence_label(0.30, 200, 0.05), "low")


class TestDecisionMargin(unittest.TestCase):
    def test_interval_grazing_parity_is_not_conclusive(self):
        self.assertFalse(stats.is_conclusive(1.000, 1.05))
        self.assertFalse(stats.is_conclusive(0.95, 1.000))

    def test_interval_clear_of_parity_is_conclusive(self):
        self.assertTrue(stats.is_conclusive(1.02, 1.10))
        self.assertTrue(stats.is_conclusive(0.90, 0.98))


if __name__ == "__main__":
    unittest.main(verbosity=2)
