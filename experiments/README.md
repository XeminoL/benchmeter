Three experiments behind the figures in the report. Each writes its own
inputs to a temporary directory and prints a table.

```
python experiments/process_floor.py
python experiments/floor_sensitivity.py
python experiments/against_hyperfine.py <path-to-hyperfine> [trials]
```

`process_floor.py` times an empty script to establish the cost of starting
the interpreter, then times increasing workloads against it. Below the point
where the workload exceeds start-up, the measurement is dominated by process
creation.

`floor_sensitivity.py` multiplies the resolution floor by k and counts both
kinds of error against a known answer. Throughput steps up halfway through
each simulated run, which is the shape a thermal event or a competing
process produces. k=1.0 is what ships.

`against_hyperfine.py` gives two identical commands to hyperfine and to
benchmeter in the same session. hyperfine reports means and standard
deviations without a verdict, so the conventional decision rule is applied
to its output: means differing by more than 1.96 standard errors. Every
claim of a difference is a false positive. Requires a hyperfine binary,
which is not vendored.

Figures depend on the host and will not reproduce exactly.
