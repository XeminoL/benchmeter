import math
import random
import statistics
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmeter import statistics_ as stats

REPETITIONS = 60
SAMPLES_PER_SERIES = 60
MAX_FALSE_POSITIVE_RATE = 0.10
MAX_FALSE_POSITIVE_RATE_UNDER_DRIFT = 0.15
MAX_MISS_RATE = 0.05
OUTLIER_PROBABILITY = 0.03


def synthetic_series(rng, center, noise, count=SAMPLES_PER_SERIES, drift=0.0):
    samples = []
    for index in range(count):
        scale = 1 + drift * (index / count)
        value = rng.gauss(center * scale, noise)
        if rng.random() < OUTLIER_PROBABILITY:
            value *= rng.uniform(1.5, 4.0)
        samples.append(max(value, 1.0))
    return samples


def classical_test_says_different(left, right):
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    left_error = statistics.stdev(left) / math.sqrt(len(left))
    right_error = statistics.stdev(right) / math.sqrt(len(right))
    return abs(left_mean - right_mean) > 1.96 * (left_error + right_error)


class TestDoesNotInventDifferences(unittest.TestCase):
    def test_samples_from_one_source_are_rarely_called_different(self):
        false_positives = 0
        for repetition in range(REPETITIONS):
            rng = random.Random(repetition)
            left = synthetic_series(rng, 1000, 80)
            right = synthetic_series(rng, 1000, 80)
            _, lower, upper = stats.ratio_confidence_interval(
                left, right, seed=repetition)
            if stats.is_conclusive(lower, upper):
                false_positives += 1

        rate = false_positives / REPETITIONS
        self.assertLessEqual(
            rate, MAX_FALSE_POSITIVE_RATE,
            f"false positive rate {rate:.1%} on identical sources")

    def test_drift_does_not_manufacture_differences(self):
        false_positives = 0
        for repetition in range(REPETITIONS):
            rng = random.Random(100 + repetition)
            left, right = [], []
            for index in range(SAMPLES_PER_SERIES):
                scale = 1 + 0.4 * (index / SAMPLES_PER_SERIES)
                left.append(rng.gauss(1000 * scale, 80))
                right.append(rng.gauss(1000 * scale, 80))
            _, lower, upper = stats.ratio_confidence_interval(
                left, right, seed=repetition)
            if stats.is_conclusive(lower, upper):
                false_positives += 1

        rate = false_positives / REPETITIONS
        self.assertLessEqual(
            rate, MAX_FALSE_POSITIVE_RATE_UNDER_DRIFT,
            f"false positive rate {rate:.1%} under 40% drift")


class TestDetectsRealDifferences(unittest.TestCase):
    def test_a_doubling_is_never_missed(self):
        misses = 0
        for repetition in range(REPETITIONS):
            rng = random.Random(200 + repetition)
            fast = synthetic_series(rng, 1000, 80)
            slow = synthetic_series(rng, 2000, 160)
            _, lower, upper = stats.ratio_confidence_interval(
                fast, slow, seed=repetition)
            if not stats.is_conclusive(lower, upper):
                misses += 1

        rate = misses / REPETITIONS
        self.assertLessEqual(rate, MAX_MISS_RATE,
                             f"missed a doubling {rate:.1%} of the time")

    def test_estimated_ratio_is_close_to_truth(self):
        rng = random.Random(999)
        baseline = synthetic_series(rng, 1000, 50, count=300)
        variant = synthetic_series(rng, 1500, 75, count=300)
        ratio, _, _ = stats.ratio_confidence_interval(
            baseline, variant, seed=1)
        self.assertGreater(ratio, 1.3)
        self.assertLess(ratio, 1.7)


class TestAgainstSequentialMeasurement(unittest.TestCase):
    def test_interleaving_beats_measuring_one_after_the_other(self):
        sequential_errors = interleaved_errors = 0

        for repetition in range(REPETITIONS):
            rng = random.Random(300 + repetition)
            total = SAMPLES_PER_SERIES * 2
            drift = [1 + 0.4 * (index / total) for index in range(total)]

            sequential_left = [
                rng.gauss(1000 * drift[index], 80)
                for index in range(SAMPLES_PER_SERIES)
            ]
            sequential_right = [
                rng.gauss(1000 * drift[SAMPLES_PER_SERIES + index], 80)
                for index in range(SAMPLES_PER_SERIES)
            ]
            if classical_test_says_different(sequential_left,
                                             sequential_right):
                sequential_errors += 1

            interleaved_left = [
                rng.gauss(1000 * drift[2 * index], 80)
                for index in range(SAMPLES_PER_SERIES)
            ]
            interleaved_right = [
                rng.gauss(1000 * drift[2 * index + 1], 80)
                for index in range(SAMPLES_PER_SERIES)
            ]
            _, lower, upper = stats.ratio_confidence_interval(
                interleaved_left, interleaved_right, seed=repetition)
            if stats.is_conclusive(lower, upper):
                interleaved_errors += 1

        self.assertLess(
            interleaved_errors, sequential_errors,
            f"interleaved {interleaved_errors} vs "
            f"sequential {sequential_errors}")
        print(f"\n    [sequential {sequential_errors}/{REPETITIONS} false "
              f"positives, interleaved {interleaved_errors}/{REPETITIONS}]")


if __name__ == "__main__":
    unittest.main(verbosity=2)