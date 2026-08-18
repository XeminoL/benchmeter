from __future__ import annotations

import json
import math
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

HYPERFINE_RUNS = 12
HYPERFINE_WARMUP = 2
BENCHMETER_BUDGET = "6"
TASK_ITERATIONS = 120_000
Z_95 = 1.959964
REPO = Path(__file__).resolve().parent.parent

TASK_SOURCE = (
    "import sys\n"
    "n = 0\n"
    f"for i in range({TASK_ITERATIONS}):\n"
    "    n = (n * 31 + i) % 1000003\n"
    "sys.stdout.write(str(n))\n"
)


def write_identical_pair(directory: Path) -> tuple[str, str]:
    first = directory / "task_a.py"
    second = directory / "task_b.py"
    first.write_text(TASK_SOURCE, encoding="utf-8")
    second.write_text(TASK_SOURCE, encoding="utf-8")
    return f'python "{first}"', f'python "{second}"'


def hyperfine_times(binary: str, first: str, second: str,
                    directory: Path) -> tuple[list[float], list[float]]:
    export = directory / "hyperfine.json"
    subprocess.run(
        [binary, "--warmup", str(HYPERFINE_WARMUP), "--runs", str(HYPERFINE_RUNS),
         "--style", "none", "--export-json", str(export), first, second],
        cwd=directory, capture_output=True,
    )
    payload = json.loads(export.read_text(encoding="utf-8"))
    export.unlink()
    return payload["results"][0]["times"], payload["results"][1]["times"]


def welch_declares_difference(left: list[float], right: list[float]) -> bool:
    if len(left) < 2 or len(right) < 2:
        return False
    spread = math.sqrt(
        statistics.stdev(left) ** 2 / len(left)
        + statistics.stdev(right) ** 2 / len(right)
    )
    if spread == 0:
        return False
    gap = abs(statistics.mean(left) - statistics.mean(right))
    return gap / spread > Z_95


def benchmeter_declares_difference(first: str, second: str) -> bool | None:
    finished = subprocess.run(
        [sys.executable, "-m", "benchmeter.cli", first, second,
         "-t", BENCHMETER_BUDGET, "--json"],
        cwd=REPO, capture_output=True, text=True,
    )
    if finished.returncode not in (0, 2):
        return None
    return bool(json.loads(finished.stdout)["conclusive"])


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python against_hyperfine.py <path-to-hyperfine> [trials]")
        return 1
    binary = sys.argv[1]
    trials = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    hyperfine_wrong = 0
    benchmeter_wrong = 0
    completed = 0

    with tempfile.TemporaryDirectory() as raw:
        directory = Path(raw)
        first, second = write_identical_pair(directory)
        for index in range(trials):
            left, right = hyperfine_times(binary, first, second, directory)
            if welch_declares_difference(left, right):
                hyperfine_wrong += 1

            verdict = benchmeter_declares_difference(first, second)
            if verdict is None:
                print(f"trial {index + 1}: benchmeter did not run")
                continue
            if verdict:
                benchmeter_wrong += 1
            completed += 1
            print(f"trial {index + 1:2d}/{trials}   "
                  f"hyperfine {hyperfine_wrong}   benchmeter {benchmeter_wrong}",
                  flush=True)

    print()
    print("Two identical commands. Every claim of a difference is a false positive.")
    print(f"  trials                     {completed}")
    print(f"  hyperfine, mean and SEM    {hyperfine_wrong}/{completed}")
    print(f"  benchmeter                 {benchmeter_wrong}/{completed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
