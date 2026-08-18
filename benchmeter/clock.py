from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass

NANOSECONDS_PER_SECOND = 1_000_000_000


@dataclass(frozen=True)
class Run:
    label: str
    elapsed_ns: int
    exit_code: int

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0


def time_once(command: str, label: str = "") -> Run:
    started = time.perf_counter_ns()
    completed = subprocess.run(command, shell=True, capture_output=True)
    elapsed = time.perf_counter_ns() - started
    return Run(label=label, elapsed_ns=elapsed, exit_code=completed.returncode)


def is_runnable(command: str) -> tuple[bool, int]:
    run = time_once(command)
    return run.succeeded, run.elapsed_ns


def to_seconds(nanoseconds: float) -> float:
    return nanoseconds / NANOSECONDS_PER_SECOND


def format_duration(nanoseconds: float) -> str:
    seconds = to_seconds(nanoseconds)
    if seconds >= 1:
        return f"{seconds:.3f} s"
    if seconds >= 0.001:
        return f"{seconds * 1_000:.2f} ms"
    return f"{seconds * 1_000_000:.1f} us"
