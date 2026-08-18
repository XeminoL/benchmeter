from __future__ import annotations

import statistics
import time
from dataclasses import dataclass
from typing import Callable, Sequence

from . import statistics_ as stats
from .clock import format_duration
from .layout import rule

TOTAL_RUNS = 6000
BLOCK_SIZE = 300
WINDOW_SIZE = 40
MAX_PAIRS = 150
TASK_ITERATIONS = 3000
SELFPROOF_RESAMPLES = 400
BANNER_WIDTH = 58


@dataclass(frozen=True)
class ProofResult:
    drift: float
    sequential_false_positive_rate: float
    interleaved_false_positive_rate: float

    @property
    def improvement(self) -> float:
        if not self.sequential_false_positive_rate:
            return 0.0
        return 1 - (self.interleaved_false_positive_rate
                    / self.sequential_false_positive_rate)


def proof_task() -> int:
    total = 0
    for index in range(TASK_ITERATIONS):
        total += index * index
    return total


def collect_samples(runs: int) -> list[int]:
    samples = []
    for _ in range(runs):
        started = time.perf_counter_ns()
        proof_task()
        samples.append(time.perf_counter_ns() - started)
    return samples


def classical_test_says_different(left: Sequence[float],
                                   right: Sequence[float]) -> bool:
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    left_error = statistics.stdev(left) / len(left) ** 0.5
    right_error = statistics.stdev(right) / len(right) ** 0.5
    return abs(left_mean - right_mean) > stats.Z_95 * (left_error + right_error)


def count_sequential_errors(samples: Sequence[int]) -> tuple[int, int]:
    errors = trials = 0
    step = WINDOW_SIZE * 2
    for start in range(0, len(samples) - step, step):
        left = samples[start:start + WINDOW_SIZE]
        right = samples[start + WINDOW_SIZE:start + step]
        trials += 1
        if classical_test_says_different(left, right):
            errors += 1
        if trials >= MAX_PAIRS:
            break
    return errors, trials


def count_interleaved_errors(samples: Sequence[int]) -> tuple[int, int]:
    errors = trials = 0
    step = WINDOW_SIZE * 2
    for start in range(0, len(samples) - step, step):
        window = samples[start:start + step]
        trials += 1
        _, lower, upper = stats.ratio_confidence_interval(
            window[0::2], window[1::2],
            resamples=SELFPROOF_RESAMPLES, seed=start)
        if stats.is_conclusive(lower, upper):
            errors += 1
        if trials >= MAX_PAIRS:
            break
    return errors, trials


def run(emit: Callable[[str], None] = print,
        total_runs: int = TOTAL_RUNS) -> ProofResult:
    emit("")
    emit("SELF-PROOF")
    emit(rule(BANNER_WIDTH, "="))
    emit("Measures one single task repeatedly, then splits the samples")
    emit("in two. Any 'significant difference' found is a false positive,")
    emit("because both halves are the same task.")
    emit("")
    emit(f"Collecting {total_runs:,} samples...")

    samples = collect_samples(total_runs)

    blocks = [
        statistics.median(samples[start:start + BLOCK_SIZE])
        for start in range(0, len(samples), BLOCK_SIZE)
        if len(samples[start:start + BLOCK_SIZE]) >= BLOCK_SIZE // 2
    ]
    fastest, slowest = min(blocks), max(blocks)
    drift = (slowest - fastest) / fastest

    emit("")
    emit("1. DOES THE MACHINE DRIFT WHILE MEASURING?")
    emit(rule(BANNER_WIDTH))
    emit(f"   fastest block : {format_duration(fastest)}")
    emit(f"   slowest block : {format_duration(slowest)}")
    emit(f"   difference    : {drift * 100:.1f}%")
    emit("")
    emit("   -> Same task, nothing changed, yet the speed moves.")
    emit("      There is no single true value to converge on.")

    sequential_errors, sequential_trials = count_sequential_errors(samples)
    sequential_rate = sequential_errors / sequential_trials

    emit("")
    emit("2. SEQUENTIAL MEASUREMENT, CLASSICAL TEST")
    emit(rule(BANNER_WIDTH))
    emit(f"   reported a difference {sequential_errors}/{sequential_trials} "
         f"times = {sequential_rate * 100:.1f}%")
    emit("   -> every one of them is wrong; it is the same task.")

    interleaved_errors, interleaved_trials = count_interleaved_errors(samples)
    interleaved_rate = interleaved_errors / interleaved_trials

    emit("")
    emit("3. INTERLEAVED MEASUREMENT")
    emit(rule(BANNER_WIDTH))
    emit(f"   reported a difference {interleaved_errors}/{interleaved_trials} "
         f"times = {interleaved_rate * 100:.1f}%")

    result = ProofResult(drift, sequential_rate, interleaved_rate)

    emit("")
    emit(rule(BANNER_WIDTH, "="))
    if result.improvement > 0:
        emit(f"   Interleaving removed {result.improvement * 100:.0f}% of the "
             f"false positives")
    emit(f"   ({sequential_rate * 100:.1f}% -> {interleaved_rate * 100:.1f}%)")
    emit("")
    emit("   Re-run this at any time to verify it yourself.")
    emit("")

    return result