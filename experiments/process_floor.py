from __future__ import annotations

import statistics
import subprocess
import tempfile
import time
from pathlib import Path

RUNS = 40
WORKLOADS = (1_000, 10_000, 60_000, 300_000, 1_500_000)
NANOSECONDS_PER_MILLISECOND = 1_000_000

LOOP_SOURCE = (
    "n = 0\n"
    "for i in range({iterations}):\n"
    "    n = (n * 31 + i) % 1000003\n"
)


def median_milliseconds(command: str, runs: int = RUNS) -> float:
    observed = []
    for _ in range(runs):
        started = time.perf_counter_ns()
        subprocess.run(command, capture_output=True, shell=True)
        observed.append(time.perf_counter_ns() - started)
    return statistics.median(observed) / NANOSECONDS_PER_MILLISECOND


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        directory = Path(raw)
        empty = directory / "empty.py"
        empty.write_text("", encoding="utf-8")
        floor = median_milliseconds(f'python "{empty}"')

        print(f"bare interpreter start   {floor:8.1f} ms")
        print()
        print(f"{'iterations':>12}  {'measured':>10}  {'work':>10}  {'start-up':>10}")
        for iterations in WORKLOADS:
            script = directory / f"loop_{iterations}.py"
            script.write_text(LOOP_SOURCE.format(iterations=iterations),
                              encoding="utf-8")
            measured = median_milliseconds(f'python "{script}"')
            work = max(0.0, measured - floor)
            share = floor / measured if measured else 1.0
            print(f"{iterations:>12,}  {measured:9.1f}ms  {work:9.1f}ms  "
                  f"{share:9.0%}", flush=True)

    print()
    print("Start-up dominates until the workload itself exceeds it.")
    print("Below that point the tool is measuring the interpreter, not the code.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
