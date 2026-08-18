# Verification in C

The obvious objection to the Python numbers is that Python causes them. It has a garbage collector and an interpreter loop, both of which add noise of their own.

So the same experiment is here in C, where neither exists.

```bash
gcc -O2 -Wall -o verify verify.c -lm
./verify 20000
```

## Result on the laptop this was written on

```
                        Python       C
machine drift            29.8%   106.8%
measured one after       62.2%    40.7%
measured alternately      4.1%     0.0%
```

Same story. The noise is the machine, not the language. Switching to C does not fix it; changing how you measure does.

## Three traps that all produce 0 ns

Worth knowing if you ever write timing code in C yourself. Each of these silently returned zero until it was fixed.

**The compiler deletes the loop.** At `-O2`, if nothing reads the result, gcc removes the work entirely. Writing to a `volatile` variable stops that.

**The compiler precomputes the answer.** If every call returns the same value, gcc runs it once and reuses the result. Passing a changing argument prevents it.

**The task is faster than the clock.** The clock here ticks every 100 ns. A task that takes 50 ns mostly reads as zero. The fix is to repeat the task inside a single measurement and divide.

That last one is the same lesson as a physics lab: a ruler marked in millimetres cannot measure anything smaller than a millimetre.
