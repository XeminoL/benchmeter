Determines whether one command is faster than another, or whether the difference is indistinguishable from measurement noise.

![The interface after a run](docs/screenshot-light.png)

- `launchers/benchmeter.cmd` on Windows
- `launchers/benchmeter.sh` on Mac, Linux

Python 3.9+

![A command against an exact copy of itself: the interval crosses zero and the difference sits under the resolution floor, so no verdict is issued](docs/screenshot-inconclusive.png)

## Architecture

![](docs/architecture.svg)

## Method

- **Interleaved rounds.** Every variant runs once per round, in shuffled order.
- **Median and MAD.** Timing distributions are right-skewed.
- **Paired bootstrap.** Round *i* of A and round *i* of B execute seconds apart. 
- **Resolution floor.** An interval characterises the samples.

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
Exit codes:

- `0` difference established
- `1` error
- `2` no conclusion

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
