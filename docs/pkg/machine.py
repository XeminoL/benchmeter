from __future__ import annotations

import time
from dataclasses import dataclass

from . import statistics_ as stats

PROBE_RUNS = 60
PROBE_ITERATIONS = 60000
BUSY_THRESHOLD = 0.15
QUIET_DRIFT = 0.05
QUIET_VARIATION = 0.10


@dataclass(frozen=True)
class MachineState:
    drift: float
    variation: float
    resolution: float
    autocorrelation: float
    measured: bool = True

    @property
    def busy(self) -> bool:
        return self.measured and self.drift >= BUSY_THRESHOLD

    @property
    def grade(self) -> str:
        if not self.measured:
            return "unmeasured"
        if self.drift < QUIET_DRIFT and self.variation < QUIET_VARIATION:
            return "quiet"
        if self.drift < BUSY_THRESHOLD:
            return "unsettled"
        return "noisy"

    @property
    def advice(self) -> str:
        if not self.measured:
            return "Nothing measured yet."
        if self.grade == "quiet":
            return "Your machine is steady, so results should hold up."
        if self.grade == "unsettled":
            return (
                "Your machine wobbles a little. Big differences are fine, "
                "small ones may get lost."
            )
        return (
            "Your machine is busy. Close what you can, plug in power, and "
            "measure again. Until then, trust only large differences."
        )


def unmeasured() -> MachineState:
    return MachineState(0.0, 0.0, 0.0, 0.0, measured=False)


def reference_task() -> int:
    total = 0
    for index in range(PROBE_ITERATIONS):
        total += index * index
    return total


def probe(runs: int = PROBE_RUNS) -> MachineState:
    samples = []
    for _ in range(runs):
        started = time.perf_counter_ns()
        reference_task()
        samples.append(time.perf_counter_ns() - started)

    return MachineState(
        drift=stats.drift(samples),
        variation=stats.coefficient_of_variation(samples),
        resolution=stats.resolvable_difference(samples),
        autocorrelation=stats.autocorrelation(samples),
    )