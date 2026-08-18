# benchmeter

Tells you whether one command is genuinely faster than another, or whether you are just looking at noise.

Most of the time it is noise. That is the whole reason this exists.

## The problem, from the helpdesk side

Someone changes a script, runs it twice, and reports back: "the new one is 15% faster, we should ship it."

Then you run it yourself and get the opposite. Nobody is lying. The machine was just in a different mood.

I got tired of having that conversation, so I measured how often it happens. On a normal laptop, comparing a command **against an exact copy of itself**, the usual way of measuring says they are different **62% of the time**. Same command. Same machine. Two thirds of the answers are wrong.

This tool gets that down to about 4%, and when it still cannot tell, it says so instead of picking a number.

## Try it in the browser

```
python -m benchmeter.cli --web
```

Opens a page on your own machine. Type in two commands, press the button, read the answer. No install, no account, nothing leaves your laptop.

## Or from the terminal

```bash
python -m benchmeter.cli "python old.py" "python new.py"
```

You get one of two answers.

When there is a real difference:

```
  variant is 12.4% faster than baseline
  95% confidence interval: -15.1% to -9.7%
  confidence: high
```

When there is not:

```
  NO CONCLUSION
  Observed difference 3.1%, but the confidence interval runs
  from -1.2% to +7.4%
  -> that interval includes zero, so equal speed has not been ruled out.

  What to do next:
    - Machine is drifting 22%. Close other applications and measure again.
    - About 180 more rounds would likely settle it.
```

The second answer is the useful one. Other tools will hand you "3.1% faster" and let you act on it.

## Check the machine first

```
python -m benchmeter.cli --check-machine
```

```
  grade           : noisy
  drift           : 40.4%
  resolves from   : 2.6%
```

That last line is your instrument's limit. On this machine, anything smaller than a 2.6% difference is below the noise floor and no amount of measuring will find it. Worth knowing before you spend an afternoon chasing a 1% regression.

## Don't take my word for it

```
python -m benchmeter.cli --self-proof
```

This measures **one single task**, splits the samples in half, and compares the two halves against each other. They are the same task, so every "significant difference" it finds is a lie by definition. It counts them.

Results from the laptop I wrote this on:

```
                        Python       C
machine drift            29.8%   106.8%
measured one after       62.2%    40.7%
measured alternately      4.1%     0.0%
```

The C column exists because the obvious objection is "that's just Python's garbage collector." It is not. Same story in C.

## Why it works

Not clever statistics. Just a better order of operations.

Everyone measures A a hundred times, then B a hundred times. In between, the machine warms up, or Windows decides to index something, or the CPU drops its clock speed because the laptop is on battery. All of that lands on B, and B gets blamed for it.

This runs them **alternately** — A, B, A, B — and shuffles the order each round. Whatever the machine is doing at any moment, both commands are sitting in it together.

Three smaller things on top:

- Uses the median, so one unlucky run where antivirus woke up doesn't skew everything.
- Keeps each A/B pair together when calculating the interval, because they ran seconds apart under the same conditions.
- Refuses to report a difference smaller than what the machine can actually resolve, even if the statistics look convincing.

## Everything else it does

```bash
# name the things so the output reads properly
python -m benchmeter.cli "python a.py" "python b.py" --label old --label new

# more than two at once
python -m benchmeter.cli "a.py" "b.py" "c.py"

# give it longer, for differences that are small but real
python -m benchmeter.cli "a" "b" -t 60

# for scripts and CI
python -m benchmeter.cli "a" "b" --json

# same seed, same run, useful when someone disputes your numbers
python -m benchmeter.cli "a" "b" --seed 42

# keep a record and compare against last time
python -m benchmeter.cli "a" "b" --save --note "before caching"
```

Exit codes: `0` there is a difference, `1` something broke, `2` cannot tell. The last one matters if you are gating a build on it — a fail should mean "this got slower", not "the runner was busy".

Saved runs store the machine conditions too. If you compare against last week and the machine was in a different state, it says so rather than blaming your code.

## Things it won't do

**It won't make your machine quiet.** I tried. Pinning to a CPU core, raising process priority, disabling garbage collection — all three either failed outright without admin rights or made no measurable difference. So it detects and reports instead of pretending.

**It's slower than counting instructions.** If you want a number that is identical every single time, `cachegrind` counts CPU instructions with essentially zero variance. It is also slow and it ignores things real hardware does, like branch prediction. Different tool for a different question.

**The alternating trick isn't mine.** It's called RMIT in the research literature. What I did was package it so you can actually use it, and make it shut up when it doesn't know.

**One machine, one operating system.** Everything above was measured on a single Windows laptop. Your numbers will differ. Run `--self-proof` and find out.

## Running the tests

```
python -m unittest discover tests
```

31 tests. The important ones are in `test_false_positives.py`, which feeds it cases where the right answer is known in advance — samples from one source that must never be called different, and a doubling that must never be missed — then counts how often it gets them wrong.

A tool that grades its own homework isn't evidence.

## Where this came from

A first-year physics lab course. Every measurement had to carry an uncertainty; a number without one got marked down.

Then you get into software and watch people post benchmark numbers with no error bars at all, and nobody blinks.

Turns out this is known. Mytkowicz and colleagues went through 133 papers from four major systems conferences and could not find one that handled measurement bias properly. The physics undergrads are doing it more rigorously than the computer scientists.