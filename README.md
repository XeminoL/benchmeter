# benchmeter

Compares the running time of two commands and reports how much confidence the result deserves.

![benchmeter interface](docs/screenshot-light.png)

## The problem

Execution time is not a constant. The same command on the same machine gives different answers on consecutive runs: CPU frequency responds to temperature and power source, the operating system schedules other work, caches warm and cool.

The consequence is that most observed differences between two versions of a piece of code fall inside the measurement noise rather than reflecting a real change.

A concrete measurement on an ordinary laptop: take one command, compare it against an exact copy of itself, and use the common approach — run all of A, then all of B, compare the means with the standard-error-over-root-N formula. The result declares the two different in **62% of trials**, although they are the same command.

The method used here brings that to roughly **4%**, and withholds a verdict when the data does not support one.

## Installation

Python 3.9 or later. No third-party dependencies.

```
python -m benchmeter.cli --web
```

On Windows, `launchers/benchmeter.cmd` can be double-clicked; on macOS and Linux, `launchers/benchmeter.sh`. Both locate a suitable interpreter and explain where to obtain Python if none is present.

From a terminal:

```bash
python -m benchmeter.cli "python old.py" "python new.py"
```

## Output

Two forms. When the confidence interval sits entirely on one side of parity:

```
  variant is 12.4% faster than baseline
  95% confidence interval: -15.1% to -9.7%
  confidence: high
```

When equal performance has not been ruled out:

```
  NO CONCLUSION
  Observed difference 3.1%, but the confidence interval runs
  from -1.2% to +7.4%
  -> that interval includes zero, so equal speed has not been ruled out.

  What to do next:
    - Machine is drifting 22%. Close other applications and measure again.
    - About 180 more rounds would likely settle it.
```

The second form is the main departure from comparable tools. Rather than returning 3.1% and leaving the interpretation to the reader, it states that the evidence is insufficient and what would change that.

![no conclusion](docs/screenshot-inconclusive.png)

*Two identical copies of one command. The interval spans zero, so no difference is reported.*

## Architecture

![architecture](docs/architecture.svg)

Two entry points share one measurement core. The browser interface is served by a local HTTP server that accepts requests only from the page it served itself, authenticated by a per-session token; the command line calls the same functions directly.

| Module | Responsibility |
|---|---|
| `clock.py` | Times a single subprocess launch with `perf_counter_ns` |
| `machine.py` | Repeats a fixed workload to derive drift, spread and noise floor |
| `experiment.py` | Runs interleaved rounds under a wall-clock deadline |
| `statistics_.py` | Median, MAD, paired bootstrap interval, drift, autocorrelation |
| `report.py` | Applies both decision rules and phrases the verdict |
| `history.py` | Stores results alongside the machine state at the time |
| `selfproof.py` | Counts false positives by splitting one task in half |
| `cli.py` | Argument handling and terminal output |
| `web/server.py` | Static files, JSON endpoints, request authentication |

## Method

**Interleaved rounds.** Each round runs both commands once, in shuffled order. Sequential measurement places all of B's samples in a different time window from A's, so any drift between the two windows is attributed entirely to B. Interleaving distributes it across both.

**Median rather than mean.** Outliers from operating-system interference do not move the estimate.

**Paired bootstrap.** Round *i* of A and round *i* of B execute seconds apart under the same conditions. Resampling whole pairs preserves that relationship instead of mixing the two series.

**A noise floor gate.** A confidence interval describes only the samples collected; it carries no information about the machine drifting underneath them. A difference must clear the machine's measured resolution as well as parity before it is reported.

The multi-level interleaving scheme is known in the literature as randomised multiple interleaved trials (RMIT). What is added here is the packaging and the second decision rule.

## Independent verification

```
python -m benchmeter.cli --self-proof
```

This times a single task, splits the samples into two halves in collection order, and compares the halves using both methods. Since both halves are the same task, every "significant difference" is a false positive and can be counted.

Reference machine, Intel i7-1185G7, Windows, integrated graphics:

```
                          Python       C
machine drift              29.8%   106.8%
sequential → false pos.    62.2%    40.7%
interleaved → false pos.    4.1%     0.0%
```

The C column exists to rule out the Python garbage collector and interpreter as the source. Source in `native/verify.c`; three compiler pitfalls encountered while writing it are documented in `native/README.md`.

## Machine characterisation

```
python -m benchmeter.cli --check-machine
```

```
  grade           : noisy
  drift           : 40.4%
  resolves from   : 2.6%
```

A workload of fixed size runs repeatedly. Because the workload does not change, every variation observed originates in the machine.

The last line is the resolution floor: on this machine differences below 2.6% lie under the noise and cannot be established regardless of sample count.

## Options

```bash
# display names
python -m benchmeter.cli "python a.py" "python b.py" --label old --label new

# more than two commands
python -m benchmeter.cli "a.py" "b.py" "c.py"

# time limit in seconds
python -m benchmeter.cli "a" "b" -t 60

# JSON output
python -m benchmeter.cli "a" "b" --json

# fixed seed, for a reproducible run
python -m benchmeter.cli "a" "b" --seed 42

# record and compare against the previous run
python -m benchmeter.cli "a" "b" --save --note "before caching"
```

Exit codes: `0` a difference was found, `1` an error occurred, `2` no conclusion. Distinguishing `0` from `2` matters in continuous integration, so that a failure means performance regressed rather than the runner being busy.

Saved records include the machine state at the time of measurement. When a comparison spans two different machine states, the tool says so.

![dark theme](docs/screenshot-dark.png)

## Tests

```
python -m unittest discover tests
```

31 tests. The substantive ones are in `test_false_positives.py`, which supplies cases with a known correct answer — samples drawn from one distribution must never be called different, a twofold difference must never be missed — and counts the error rate. A measurement tool that grades its own output is not evidence.

## Limitations

**It does not reduce machine variation.** Pinning the process to one CPU core, raising scheduling priority and disabling garbage collection were all measured. Without administrator rights the first two are refused by the operating system and the third produced no reduction in drift. The tool detects and reports instead.

**It is slower than instruction counting.** `cachegrind` counts CPU instructions with near-zero variance, but runs slowly and disregards hardware behaviour such as branch prediction and instruction-level parallelism. The two answer different questions.

**It executes the commands it is given.** The server binds to loopback only and rejects requests that did not originate from its own page, but it does run what it receives.

**Figures come from one machine.** Every number in this document was measured on a single Windows laptop. Results elsewhere will differ; `--self-proof` reproduces the experiment locally.

**Distributed measurement across machines is not supported.**

## Background

The governing principle comes from an undergraduate physics laboratory course: a measurement is reported with its uncertainty, and the resolution of the instrument is established before the reading is trusted.

The principle is applied unevenly in software performance work. Mytkowicz et al. surveyed 133 papers from ASPLOS, PACT, PLDI and CGO and found none that adequately accounted for measurement bias.

## References

1. Mytkowicz, T., Diwan, A., Hauswirth, M., Sweeney, P. F. *Producing Wrong Data Without Doing Anything Obviously Wrong!* ASPLOS 2009.
2. Curtsinger, C., Berger, E. D. *STABILIZER: Statistically Sound Performance Evaluation.* ASPLOS 2013.
3. Laaber, C., Würsten, S., Gall, H. C., Leitner, P. *Dynamically Reconfiguring Software Microbenchmarks: Reducing Execution Time without Sacrificing Result Quality.* ESEC/FSE 2020.
4. Kalibera, T., Jones, R. *Rigorous Benchmarking in Reasonable Time.* ISMM 2013.
5. Efron, B., Tibshirani, R. J. *An Introduction to the Bootstrap.* Chapman & Hall, 1993.

## Licence

MIT.
