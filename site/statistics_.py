from __future__ import annotations

import math
import random
import statistics
from typing import Sequence

BOOTSTRAP_RESAMPLES = 2000
CONFIDENCE_LEVEL = 0.95
DECISION_MARGIN = 0.005
HIGH_DRIFT = 0.20
MODERATE_DRIFT = 0.08
MAD_TO_SIGMA = 1.4826
MEDIAN_STANDARD_ERROR_FACTOR = 1.253
Z_95 = 1.959964
MIN_BLOCKS_FOR_DRIFT = 4


def median(samples: Sequence[float]) -> float:
    return statistics.median(samples)


def median_absolute_deviation(samples: Sequence[float]) -> float:
    center = median(samples)
    return statistics.median([abs(x - center) for x in samples])


def robust_sigma(samples: Sequence[float]) -> float:
    return median_absolute_deviation(samples) * MAD_TO_SIGMA


def coefficient_of_variation(samples: Sequence[float]) -> float:
    center = median(samples)
    if not center:
        return 0.0
    return robust_sigma(samples) / center


def ratio_confidence_interval(
    baseline: Sequence[float],
    variant: Sequence[float],
    level: float = CONFIDENCE_LEVEL,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int | None = None,
) -> tuple[float, float, float]:
    pairs = list(zip(baseline, variant))
    if len(pairs) < 2:
        return 1.0, 0.0, 0.0

    rng = random.Random(seed)
    count = len(pairs)
    ratios = []
    for _ in range(resamples):
        drawn = rng.choices(pairs, k=count)
        base = statistics.median([pair[0] for pair in drawn])
        var = statistics.median([pair[1] for pair in drawn])
        ratios.append(var / base if base else 1.0)
    ratios.sort()

    tail = (1 - level) / 2
    base_median = median(baseline)
    point = median(variant) / base_median if base_median else 1.0
    return (
        point,
        ratios[int(tail * resamples)],
        ratios[int((1 - tail) * resamples) - 1],
    )


def drift(samples: Sequence[float], blocks: int = 8) -> float:
    if len(samples) < blocks * 2:
        blocks = max(2, len(samples) // 2)
    block_size = len(samples) // blocks
    if block_size < 1:
        return 0.0

    medians = [
        median(samples[index * block_size:(index + 1) * block_size])
        for index in range(blocks)
    ]
    medians = [value for value in medians if value > 0]
    if len(medians) < MIN_BLOCKS_FOR_DRIFT:
        return 0.0
    return (max(medians) - min(medians)) / min(medians)


def autocorrelation(samples: Sequence[float], lag: int = 1) -> float:
    count = len(samples)
    if count <= lag + 1:
        return 0.0
    mean = statistics.fmean(samples)
    covariance = sum(
        (samples[i] - mean) * (samples[i + lag] - mean)
        for i in range(count - lag)
    )
    variance = sum((x - mean) ** 2 for x in samples)
    return covariance / variance if variance else 0.0


def resolvable_difference(samples: Sequence[float]) -> float:
    count = len(samples)
    center = median(samples)
    if count < 2 or not center:
        return float("inf")
    standard_error = (
        MEDIAN_STANDARD_ERROR_FACTOR * robust_sigma(samples) / math.sqrt(count)
    )
    return Z_95 * math.sqrt(2) * standard_error / center


def is_conclusive(lower: float, upper: float,
                  margin: float = DECISION_MARGIN) -> bool:
    return lower > 1.0 + margin or upper < 1.0 - margin


def confidence_label(drift_ratio: float, sample_count: int,
                     variation: float) -> str:
    if drift_ratio >= HIGH_DRIFT or variation > 0.5:
        return "low"
    if drift_ratio >= MODERATE_DRIFT or sample_count < 30:
        return "moderate"
    return "high"