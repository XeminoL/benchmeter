# Verification in C

Python has a garbage collector and an interpreter loop, either of which could
account for the variance measured on the Python side. The same experiment is
implemented here in C, where neither exists.

```bash
gcc -O2 -Wall -o verify verify.c -lm
./verify 20000
```

## Result

```
                        Python       C
machine drift            29.8%   106.8%
measured one after       62.2%    40.7%
measured alternately      4.1%     0.0%
```

Drift and false positives persist without a managed runtime. Changing the
language does not remove them; changing the order of collection does.

## Notes on timing in C

A timing loop must be written so the compiler cannot discard it. Three
conditions matter, and each of them silently reduces the measurement to zero:

**A result nothing reads.** At `-O2` the loop is eliminated when its value is
unused. Writing to a `volatile` variable prevents it.

**A result that never changes.** A call returning the same value on every
invocation is computed once and reused. Passing a varying argument prevents
it.

**A task shorter than the clock tick.** The clock here advances every 100 ns,
so a task of 50 ns reads as zero more often than not. Repeating the task
inside one measurement and dividing recovers the figure.

The last condition is the resolution limit the tool exists to detect: an
instrument cannot report a quantity smaller than the interval it advances in.
