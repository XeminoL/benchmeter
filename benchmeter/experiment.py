from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Sequence

from . import statistics_ as stats
from .clock import Run, estimate_duration_ns, time_once

WARMUP_ROUNDS = 3
WARMUP_BUDGET_THRESHOLD = 3.0
MIN_ROUNDS = 1
MIN_ROUNDS_FOR_INTERVAL = 10
MAX_ROUNDS = 400
CHECK_INTERVAL = 10
DEFAULT_BUDGET_SECONDS = 30
NANOSECONDS_PER_SECOND = 1_000_000_000


@dataclass
class Series:
    label: str
    timings: list[int] = field(default_factory=list)
    failures: int = 0

    def record(self, run: Run) -> None:
        if run.succeeded:
            self.timings.append(run.elapsed_ns)
        else:
            self.failures += 1

    def __len__(self) -> int:
        return len(self.timings)


@dataclass(frozen=True)
class Measurement:
    series: list[Series]
    rounds: int
    stopped_early: bool

    @property
    def labels(self) -> list[str]:
        return [item.label for item in self.series]


def warm_up(commands: Sequence[str], rounds: int = WARMUP_ROUNDS) -> None:
    for _ in range(rounds):
        for command in commands:
            time_once(command)


def plan_rounds(commands: Sequence[str], budget_seconds: float) -> int:
    probe_runs = 1 if budget_seconds < WARMUP_BUDGET_THRESHOLD else None
    per_round = sum(
        estimate_duration_ns(command)
        if probe_runs is None
        else estimate_duration_ns(command, runs=probe_runs)
        for command in commands
    )
    if per_round <= 0:
        return MAX_ROUNDS
    affordable = int(budget_seconds * NANOSECONDS_PER_SECOND / per_round)
    return max(min(affordable, MAX_ROUNDS), MIN_ROUNDS)


def is_settled(series: Sequence[Series], seed: int | None,
               resolution: float = 0.0) -> bool:
    if len(series) < 2:
        return False

    baseline = series[0]
    for variant in series[1:]:
        if (len(baseline) < MIN_ROUNDS_FOR_INTERVAL
                or len(variant) < MIN_ROUNDS_FOR_INTERVAL):
            return False
        ratio, lower, upper = stats.ratio_confidence_interval(
            baseline.timings, variant.timings, seed=seed)
        if not stats.is_conclusive(lower, upper):
            return False
        if abs(ratio - 1) < resolution:
            return False
    return True


def measure(
    commands: Sequence[str],
    labels: Sequence[str] | None = None,
    rounds: int | None = None,
    budget_seconds: float = DEFAULT_BUDGET_SECONDS,
    seed: int | None = None,
    shuffle: bool = True,
    on_progress: Callable[[int, int], None] | None = None,
    resolution: float = 0.0,
) -> Measurement:
    labels = list(labels or [f"command {i + 1}" for i in range(len(commands))])
    rng = random.Random(seed)
    series = [Series(label) for label in labels]

    if budget_seconds >= WARMUP_BUDGET_THRESHOLD:
        warm_up(commands)
    if rounds is None:
        rounds = plan_rounds(commands, budget_seconds)

    order = list(range(len(commands)))
    stopped_early = False
    completed = 0

    for completed in range(1, rounds + 1):
        if shuffle:
            rng.shuffle(order)
        for index in order:
            series[index].record(time_once(commands[index], labels[index]))

        if on_progress:
            on_progress(completed, rounds)

        long_enough = completed >= MIN_ROUNDS_FOR_INTERVAL * 2
        at_checkpoint = completed % CHECK_INTERVAL == 0
        if long_enough and at_checkpoint and len(series) > 1:
            if is_settled(series, seed, resolution):
                stopped_early = True
                break

    return Measurement(series=series, rounds=completed,
                       stopped_early=stopped_early)
