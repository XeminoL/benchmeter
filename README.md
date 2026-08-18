Tells you whether one command is really faster than another, or whether the difference is just noise.

Most of the time it is noise. Take a command, compare it against an exact copy of itself, and measure the usual way — all of A, then all of B, means compared with the standard error. On an ordinary laptop that says the two differ in **62% of trials**. Same command, same machine.

Interleaving the two brings it to **4%**, and when the data still cannot support an answer, this says so instead of picking a number.

![The interface after a run](docs/screenshot-light.png)

Type two commands, press the button. Runs on your own machine, nothing is uploaded.

```
python -m benchmeter.cli --web
```

Or double-click `launchers/benchmeter.cmd` on Windows, `launchers/benchmeter.sh` elsewhere. Python 3.9+, no dependencies.

## The two answers

```
variant is 12.4% faster than baseline
95% confidence interval: -15.1% to -9.7%
```

```
NO CONCLUSION
Observed difference 3.1%, but the confidence interval runs
from -1.2% to +7.4%
  - Machine is drifting 22%. Close other applications and measure again.
  - About 180 more rounds would likely settle it.
```

The second one is the point. Other tools hand you 3.1% and let you act on it.

![Two identical commands, correctly declared indistinguishable](docs/screenshot-inconclusive.png)

## Architecture

![Module structure](docs/architecture.svg)

## How it works

**Interleaved rounds.** Each round runs both commands once, in shuffled order. Measure all of A and then all of B, and the machine warms up in between — that drift lands on B and B gets blamed. Interleaving makes both share it.

**Median, not mean.** Timing distributions are right-skewed: a process can be delayed indefinitely but cannot finish faster than its instructions allow. On the test machine the mean sat 16.9% above the median.

**Bootstrap over pairs.** Round *i* of A and round *i* of B ran seconds apart under the same conditions. Resampling whole rounds keeps that pairing instead of mixing the two series.

**A noise floor.** A confidence interval describes the samples you collected and knows nothing about the machine drifting underneath them. During development this reported a 1.9% difference between two identical commands while the machine drifted 48%, because the interval alone looked convincing. So the host is profiled separately and a difference must clear its measured resolution too.

The interleaving scheme is called RMIT in the literature. What is added here is the packaging and that second gate.

## Prove it yourself

```
python -m benchmeter.cli --self-proof
```

Times one task, splits the samples in half, compares the halves both ways. Both halves are the same task, so every "significant difference" is a false positive and gets counted.

```
                          Python       C
machine drift              29.8%   106.8%
sequential → false pos.    62.2%    40.7%
interleaved → false pos.    4.1%     0.0%
```

The C column rules out the Python garbage collector. Source in `native/verify.c` — three compiler traps hit while writing it are in `native/README.md`.

## Check the machine

```
python -m benchmeter.cli --check-machine
```

```
grade           : noisy
drift           : 40.4%
resolves from   : 2.6%
```

A fixed workload runs repeatedly. Since the workload never changes, every variation seen is the machine. The last line is the floor: below 2.6% nothing can be established here, however long you measure.

## Options

```bash
python -m benchmeter.cli "a.py" "b.py" --label old --label new
python -m benchmeter.cli "a.py" "b.py" "c.py"     # more than two
python -m benchmeter.cli "a" "b" -t 60            # seconds
python -m benchmeter.cli "a" "b" --json
python -m benchmeter.cli "a" "b" --seed 42        # reproducible
python -m benchmeter.cli "a" "b" --save --note "before caching"
```

Exit codes: `0` difference found, `1` error, `2` no conclusion. The `0`/`2` split matters in CI, so a failure means performance regressed and not that the runner was busy.

Saved runs store the machine state too, so comparing across two different machine states says so rather than blaming the code.

![Dark theme](docs/screenshot-dark.png)

## Tests

```
python -m unittest discover tests
```

31 tests. The ones that matter are in `test_false_positives.py`, where the right answer is fixed in advance — samples from one distribution must never be called different, a twofold difference must never be missed — and the error rate is counted. A measurement tool that grades its own output is not evidence.

## What it won't do

It won't quiet your machine. Pinning to a core, raising priority and disabling the garbage collector were all tried; without admin rights the first two are refused and the third changed nothing measurable. So it profiles and reports instead.

It's slower than counting instructions. `cachegrind` has near-zero variance but ignores branch prediction and instruction-level parallelism. Different question.

It runs what you give it. The server binds to loopback and rejects requests that didn't come from its own page, but it does execute the commands.

Every number here came from one Windows laptop. Yours will differ — `--self-proof` reproduces it locally.

## Where it came from

A first-year physics lab, where a measurement without an uncertainty is not a result and you establish the resolution of the instrument before trusting a reading.

Mytkowicz et al. surveyed 133 papers from ASPLOS, PACT, PLDI and CGO and found none that handled measurement bias properly.

MIT licence.
