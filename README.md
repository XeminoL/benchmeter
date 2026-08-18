Determines whether one command is faster than another, or whether the difference is indistinguishable from measurement noise.

Compared the conventional way, all repetitions of A then all of B with means and the standard error, a command and an exact copy of itself come back different most of the time. Host throughput drifts during the measurement and a sequential design charges all of it to whichever variant ran second.

Interleaving the variants within each round removes that. Where the data does not support a conclusion, none is reported.

![The interface after a run](docs/screenshot-light.png)

```
python -m benchmeter.cli --web
```

Or `launchers/benchmeter.cmd` on Windows, `launchers/benchmeter.sh` elsewhere. Python 3.9+, no dependencies, loopback only.

![Two identical commands, correctly declared indistinguishable](docs/screenshot-inconclusive.png)

## Architecture

![Module structure](docs/architecture.svg)

## Method

**Interleaved rounds.** Every variant runs once per round, in shuffled order. Drift that a sequential design books as a difference between variants becomes variance shared by both.

**Median and MAD.** Timing distributions are right-skewed, so the mean tracks the tail.

**Paired bootstrap.** Round *i* of A and round *i* of B execute seconds apart. Resampling whole rounds preserves the pairing.

**Resolution floor.** An interval describes the samples and says nothing about the stability of the host. An early version of mine reported a narrow interval between two identical commands on a drifting machine. The host is profiled separately now and a difference has to clear its measured resolution.

The interleaving design is known in the literature as RMIT. What is added here is the packaging and the second gate.

## Validation

```
python -m benchmeter.cli --self-proof
```

Times one task, partitions the samples, compares partitions drawn from it. Every significant difference is a false positive by construction, and both procedures are scored on the same samples.

Replicated in C to rule out the garbage collector and the interpreter loop. Source in `native/verify.c`; the three compiler traps I hit writing it, each of which silently reduces the measurement to zero, are in `native/README.md`.

## Host characterisation

```
python -m benchmeter.cli --check-machine
```

Repeats a fixed workload and reports drift, spread, and the floor below which nothing is resolvable on that host.

## Usage

```bash
python -m benchmeter.cli "a.py" "b.py" --label old --label new
python -m benchmeter.cli "a.py" "b.py" "c.py"
python -m benchmeter.cli "a" "b" -t 60
python -m benchmeter.cli "a" "b" --json
python -m benchmeter.cli "a" "b" --seed 42
python -m benchmeter.cli "a" "b" --save --note "before caching"
```

Exit codes: `0` difference established, `1` error, `2` no conclusion. The `0`/`2` split keeps a busy runner from reading as a regression in CI.

Saved runs record the host state, so a comparison spanning two host states is reported as such.

![Dark theme](docs/screenshot-dark.png)

## Tests

```
python -m unittest discover tests
```

`test_false_positives.py` fixes the answer before the run: samples from one distribution must never be declared different, a twofold difference must never be missed.

## Limitations

Cannot quiet the host. I tried core pinning, priority elevation and disabling the garbage collector; the first two need administrative rights, the third increased drift.

Slower than instruction counting. `cachegrind` has near-zero variance but ignores branch prediction and instruction-level parallelism. Different question.

Executes the commands it is given. The server binds to loopback and rejects requests that did not originate from its own page, but it is not a sandbox.

Figures are properties of the host. `--self-proof` reproduces the experiment locally.

## Origin

A first-year physics laboratory, where a measurement without an uncertainty is not a result and the resolution of the instrument is established before a reading is trusted.

## License

MIT.
