Determines whether one command is faster than another, or whether the difference is indistinguishable from measurement noise.

Measured the conventional way, all repetitions of A then all of B with means compared using the standard error, a command and an exact copy of itself are declared different most of the time. 

Interleaving the variants within each round removes the attribution. 

![The interface after a run](docs/screenshot-light.png)

- `launchers/benchmeter.cmd` on Windows
- `launchers/benchmeter.sh` on Mac, Linux

Python 3.9+

![A command against an exact copy of itself: the interval crosses zero and the difference sits under the resolution floor, so no verdict is issued](docs/screenshot-inconclusive.png)

## Architecture

![](docs/architecture.svg)

## Method

- **Interleaved rounds.** Every variant runs once per round, in shuffled order. Drift that a sequential design records as a difference between variants becomes variance shared by both.
- **Median and MAD.** Timing distributions are right-skewed; the mean follows the tail.
- **Paired bootstrap.** Round *i* of A and round *i* of B execute seconds apart. Resampling whole rounds preserves the pairing.
- **Resolution floor.** An interval characterises the samples, not the stability of the host. The host is profiled separately, and a difference must clear its measured resolution before it is reported.

## Validation

```
python -m benchmeter.cli --self-proof
```

Times one task, partitions the samples, and compares partitions drawn from it.

Replicated in C to rule out the garbage collector and the interpreter loop as causes, with the same outcome. Source in `native/verify.c`.

## Usage

```bash
python -m benchmeter.cli "a.py" "b.py" --label old --label new
python -m benchmeter.cli "a.py" "b.py" "c.py"
python -m benchmeter.cli "a" "b" -t 60
python -m benchmeter.cli "a" "b" --json
python -m benchmeter.cli "a" "b" --seed 42
python -m benchmeter.cli "a" "b" --save --note "before caching"
python -m benchmeter.cli --check-machine
```

`--check-machine` repeats a fixed workload and reports drift, spread, and the floor below which no difference is resolvable on that host.

Exit codes:

- `0` difference established
- `1` error
- `2` no conclusion

![Dark theme](docs/screenshot-dark.png)

## Experiments

```
python experiments/process_floor.py
python experiments/floor_sensitivity.py
python experiments/against_hyperfine.py <path-to-hyperfine>
```

Three measurements behind the design: how much of a timed run is interpreter
start-up, how the resolution floor behaves as its threshold is moved, and how
the tool compares against hyperfine on the same host. Details in
`experiments/README.md`.

## Tests

```
python -m unittest discover tests
```
