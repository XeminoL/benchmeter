from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmeter import statistics_ as stats

REPEATS = 300
ROUNDS = 24
PROBE_RUNS = 200
BASE_NS = 60_000_000
JITTER = 0.04
MULTIPLIERS = (0.0, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0)
STEP_SIZES = (0.0, 0.20, 0.50)
TRUE_EFFECTS = (0.03, 0.08, 0.20)
SEED = 4242


def stepped_pair(rng, step, count, effect=0.0):
    switch = count // 2
    left, right = [], []
    for index in range(count):
        level = 1.0 + (step if index >= switch else 0.0)
        left.append(BASE_NS * level * (1.0 + rng.gauss(0, JITTER)))
        right.append(BASE_NS * (1.0 - effect) * level
                     * (1.0 + rng.gauss(0, JITTER)))
    return left, right


def floor_for(rng, step):
    samples, _ = stepped_pair(rng, step, PROBE_RUNS)
    return stats.resolvable_difference(samples)


def as_sequential(left, right):
    half = len(left) // 2
    first, second = left[:half], right[half:]
    shared = min(len(first), len(second))
    return first[:shared], second[:shared]


def verdict(rng, step, effect, interleaved, multiplier):
    resolution = floor_for(rng, step)
    left, right = stepped_pair(rng, step, ROUNDS, effect)
    if not interleaved:
        left, right = as_sequential(left, right)
    ratio, lower, upper = stats.ratio_confidence_interval(
        left, right, seed=rng.randrange(10 ** 6))
    interval_clears = stats.is_conclusive(lower, upper)
    return interval_clears and abs(ratio - 1) >= resolution * multiplier


def table(title, columns, label, decide):
    print(title)
    print("  k    " + "".join(f"{label(c):>11}" for c in columns))
    for multiplier in MULTIPLIERS:
        cells = []
        for column in columns:
            rng = random.Random(SEED)
            hits = sum(decide(rng, column, multiplier)
                       for _ in range(REPEATS))
            cells.append(f"{hits / REPEATS:10.1%}")
        print(f"  {multiplier:<5.2f}" + "".join(cells), flush=True)
    print()


def main() -> int:
    print(f"{REPEATS} repeats per cell, {ROUNDS} rounds, {JITTER:.0%} jitter,")
    print("throughput steps up halfway through the measurement")
    print()

    table("Sequential collection, identical commands: false positives",
          STEP_SIZES, lambda v: f"step {v:.0%}",
          lambda rng, step, k: verdict(rng, step, 0.0, False, k))

    table("Interleaved, identical commands: false positives",
          STEP_SIZES, lambda v: f"step {v:.0%}",
          lambda rng, step, k: verdict(rng, step, 0.0, True, k))

    table("Interleaved under a 20% step, real effect: misses",
          TRUE_EFFECTS, lambda v: f"effect {v:.0%}",
          lambda rng, effect, k: not verdict(rng, 0.20, effect, True, k))

    print("k multiplies the resolution floor; k=1.0 is what ships,")
    print("k=0 disables the second gate entirely.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
