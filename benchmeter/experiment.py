from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Sequence

import time

from . import statistics_ as stats
from .clock import Run, time_once

WARMUP_ROUNDS = 3
MIN_ROUNDS_FOR_INTERVAL = 10
MAX_ROUNDS = 400
CHECK_INTERVAL = 10
DEFAULT_BUDGET_SECONDS = 30
WARMUP_BUDGET_SHARE = 0.1
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
    elapsed_ns: int = 0
    budget_ns: int = 0

    @property
    def overran(self) -> bool:
        if not self.budget_ns or not self.rounds:
            return False
        return self.elapsed_ns / self.rounds > self.budget_ns

    @property
    def labels(self) -> list[str]:
        return [item.label for item in self.series]


def warm_up(commands: Sequence[str], deadline_ns: int) -> None:
    for _ in range(WARMUP_ROUNDS):
        for command in commands:
            if time.perf_counter_ns() >= deadline_ns:
                return
            time_once(command)


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


def decided_early(series: Sequence[Series], completed: int,
                  seed: int | None, resolution: float) -> bool:
    if len(series) < 2 or completed < MIN_ROUNDS_FOR_INTERVAL * 2:
        return False
    if completed % CHECK_INTERVAL:
        return False
    return is_settled(series, seed, resolution)


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

    started_ns = time.perf_counter_ns()
    budget_ns = int(max(budget_seconds, 0) * NANOSECONDS_PER_SECOND)
    deadline_ns = started_ns + budget_ns

    warm_up(commands, started_ns + int(budget_ns * WARMUP_BUDGET_SHARE))

    limit = rounds if rounds is not None else MAX_ROUNDS
    bounded_by_time = rounds is None
    order = list(range(len(commands)))
    stopped_early = False
    completed = 0

    while completed < limit:
        out_of_time = (bounded_by_time and completed > 0
                       and time.perf_counter_ns() >= deadline_ns)
        if out_of_time:
            break

        if shuffle:
            rng.shuffle(order)
        for index in order:
            series[index].record(time_once(commands[index], labels[index]))
        completed += 1

        if on_progress:
            on_progress(completed, limit)

        if decided_early(series, completed, seed, resolution):
            stopped_early = True
            break

    return Measurement(
        series=series,
        rounds=completed,
        stopped_early=stopped_early,
        elapsed_ns=time.perf_counter_ns() - started_ns,
        budget_ns=budget_ns,
    )
