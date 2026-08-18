Determines whether one command is faster than another, or whether the difference is indistinguishable from measurement noise.

Compare a command against an exact copy of itself by the conventional method, all repetitions of A followed by all repetitions of B with means compared using the standard error, and the two come back different most of the time. The cause is drift: host throughput changes during the measurement, and a sequential design charges all of it to whichever variant ran second.

Interleaving the variants within each round removes that. Where the data still does not support a conclusion, none is reported.

![The interface after a run](docs/screenshot-light.png)

```
python -m benchmeter.cli --web
```

Or `launchers/benchmeter.cmd` on Windows, `launchers/benchmeter.sh` elsewhere. Python 3.9+, no dependencies. Runs locally; nothing leaves the host.

## Output

Two outcomes. A difference, reported as an effect size with a confidence interval. Or no conclusion, with the reason: the host is drifting beyond the resolution of the measurement, or the time budget allowed too few rounds.

![Two identical commands, correctly declared indistinguishable](docs/screenshot-inconclusive.png)

## Architecture

![Module structure](docs/architecture.svg)

## Method

**Interleaved rounds.** Each round executes every variant once, in shuffled order. Under a sequential design, drift between the two collection windows appears in the estimate as a difference between variants. Under interleaving it appears as variance shared by both.

**Median and MAD.** Timing distributions are right-skewed: a process can be delayed arbitrarily but cannot finish faster than its instruction stream permits. The mean tracks the tail.

**Paired bootstrap.** Round *i* of A and round *i* of B execute seconds apart under the same conditions. Resampling whole rounds preserves that pairing.

**Resolution floor.** A confidence interval describes the collected samples and carries no information about the stability of the host. An early version of mine reported a difference between two identical commands on a drifting machine, and the interval was narrow. The host is now profiled independently and a difference must clear its measured resolution as well.

The interleaving design is established in the literature under the name RMIT. What is added here is the packaging and the second gate.

## Validation

```
python -m benchmeter.cli --self-proof
```

Times one task, partitions the samples, and compares partitions drawn from the same task. Every significant difference is a false positive by construction, and both procedures are scored on the same collected samples.

Replicated in C to exclude the garbage collector and the interpreter loop as causes. Source in `native/verify.c`; the three compiler traps I hit writing it, each of which silently reduces the measurement to zero, are documented in `native/README.md`.

## Host characterisation

```
python -m benchmeter.cli --check-machine
```

Repeats a fixed workload. Since the workload does not change, observed variation originates in the host. The output includes a floor below which no difference is resolvable, however long the measurement runs.

## Usage

```bash
python -m benchmeter.cli "a.py" "b.py" --label old --label new
python -m benchmeter.cli "a.py" "b.py" "c.py"     # more than two
python -m benchmeter.cli "a" "b" -t 60            # seconds
python -m benchmeter.cli "a" "b" --json
python -m benchmeter.cli "a" "b" --seed 42        # reproducible
python -m benchmeter.cli "a" "b" --save --note "before caching"
```

Exit codes: `0` difference established, `1` error, `2` no conclusion. The `0`/`2` distinction matters in CI, where a failure should mean a regression and not a busy runner.

Saved runs record the host state, so a comparison spanning two different host states is reported as such.

![Dark theme](docs/screenshot-dark.png)

## Tests

```
python -m unittest discover tests
```

`test_false_positives.py` fixes the correct answer before the run: samples from one distribution must never be declared different, a twofold difference must never be missed. Everything else is counted as an error.

## Limitations

Cannot quiet the host. I tried core pinning, priority elevation and disabling the garbage collector; the first two require administrative rights, the third increased drift. The tool characterises the host instead.

Slower than instruction counting. `cachegrind` has near-zero variance but ignores branch prediction and instruction-level parallelism. Different question.

Executes the commands it is given. The server binds to loopback and rejects requests that did not originate from its own page, but it is not a sandbox.

Figures are properties of the host, not of the tool. `--self-proof` reproduces the experiment locally.

## Origin

A first-year physics laboratory, where a measurement without an uncertainty is not a result, and the resolution of the instrument is established before a reading is trusted.

## License

MIT.
