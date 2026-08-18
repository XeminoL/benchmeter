Three measurements behind the design. Each writes its own inputs to a
temporary directory and prints a table.

```
python experiments/process_floor.py
python experiments/floor_sensitivity.py
python experiments/against_hyperfine.py <path-to-hyperfine> [trials]
```

`process_floor.py` times an empty script to establish the cost of starting the
interpreter, then times increasing workloads against it. The output gives the
share of each measurement that belongs to process creation rather than to the
code under test.

`floor_sensitivity.py` multiplies the resolution floor by k and counts both
false positives and misses against a known answer. Throughput steps up halfway
through each simulated run, which is the shape a thermal event or a competing
process produces. The shipped threshold is k=1.0.

`against_hyperfine.py` gives the same commands to hyperfine and to benchmeter
in one session. hyperfine reports means and standard deviations without a
verdict, so the conventional decision rule is applied to its output: means
separated by more than 1.96 standard errors count as different. The first pair
is a command and an exact copy of itself, where every claim of a difference is
a false positive. A hyperfine binary is required and is not vendored.

Figures are properties of the host and will not reproduce exactly elsewhere.
