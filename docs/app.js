const PROBE_RUNS = 150;
const PROBE_ITERATIONS = 400000;
const WARMUP_ROUNDS = 3;
const MIN_ROUNDS = 8;
const MODULES = ["statistics_.py", "machine.py"];
const PYODIDE_TIMEOUT_NOTE = "First run downloads the Python runtime, about 6 MB.";

const el = id => document.getElementById(id);
const status = el("status");
const result = el("result");
const runButton = el("run");

let pyodide = null;

function setStatus(text) {
  status.textContent = text;
}

async function ensurePyodide() {
  if (pyodide) return pyodide;
  setStatus(PYODIDE_TIMEOUT_NOTE);
  pyodide = await loadPyodide();
  pyodide.FS.mkdir("/bm");
  for (const name of MODULES) {
    const source = await (await fetch(name, { cache: "force-cache" })).text();
    pyodide.FS.writeFile("/bm/" + name, source);
  }
  pyodide.runPython(`
import sys
if "/bm" not in sys.path:
    sys.path.insert(0, "/bm")
import statistics_ as stats
`);
  return pyodide;
}

let sink = 0;

function compile(source, label) {
  try {
    const body = '"use strict";' + source
      + ";return typeof s !== 'undefined' ? s : 0;";
    return new Function(body);
  } catch (error) {
    throw new Error(label + " does not parse: " + error.message);
  }
}

function timeOnce(fn) {
  const started = performance.now();
  sink += fn();
  return performance.now() - started;
}

function referenceTask() {
  let total = 0;
  for (let i = 0; i < PROBE_ITERATIONS; i++) total = (total * 31 + i) % 1000003;
  return total;
}

function probeHost() {
  const samples = [];
  for (let i = 0; i < PROBE_RUNS; i++) samples.push(timeOnce(referenceTask));
  return samples;
}

function roundTooFast(a, b) {
  const quickest = Math.min(...a, ...b);
  return quickest < 1.0;
}

function shuffle(items) {
  for (let i = items.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [items[i], items[j]] = [items[j], items[i]];
  }
  return items;
}

function nextFrame() {
  return new Promise(resolve => setTimeout(resolve, 0));
}

async function collect(first, second, budgetMs) {
  for (let i = 0; i < WARMUP_ROUNDS; i++) { first(); second(); }

  const a = [];
  const b = [];
  const deadline = performance.now() + budgetMs;
  const order = [0, 1];
  let rounds = 0;

  while (true) {
    const roundStarted = performance.now();
    if (rounds >= MIN_ROUNDS && roundStarted >= deadline) break;

    shuffle(order);
    for (const which of order) {
      const elapsed = which === 0 ? timeOnce(first) : timeOnce(second);
      (which === 0 ? a : b).push(elapsed);
    }
    rounds += 1;

    if (rounds % 4 === 0) {
      const left = Math.max(0, deadline - performance.now());
      setStatus(`round ${rounds}, ${(left / 1000).toFixed(1)}s left`);
      await nextFrame();
    }
  }
  return { a, b, rounds };
}

function decide(py, a, b, probe) {
  py.globals.set("series_a", py.toPy(a));
  py.globals.set("series_b", py.toPy(b));
  py.globals.set("probe_samples", py.toPy(probe));
  return py.runPython(`
import json
import statistics_ as stats

a = list(series_a)
b = list(series_b)
probe = list(probe_samples)

ratio, lower, upper = stats.ratio_confidence_interval(a, b)
resolution = stats.resolvable_difference(probe)
drift = stats.drift(probe)
variation = stats.coefficient_of_variation(probe)
observed = abs(ratio - 1)

conclusive = stats.is_conclusive(lower, upper)
below_floor = conclusive and observed < resolution
if below_floor:
    conclusive = False

json.dumps({
    "ratio": ratio,
    "lower": lower,
    "upper": upper,
    "resolution": resolution,
    "drift": drift,
    "variation": variation,
    "observed": observed,
    "conclusive": conclusive,
    "below_floor": below_floor,
    "median_a": stats.median(a),
    "median_b": stats.median(b),
})
`);
}

function percent(value) {
  return (value * 100).toFixed(1) + "%";
}

function milliseconds(value) {
  return value.toFixed(2) + " ms";
}

function render(verdict, rounds, tooFast) {
  const change = (1 - verdict.ratio) * 100;
  const faster = change > 0 ? "Variant" : "Baseline";
  const lowEnd = (1 - verdict.upper) * 100;
  const highEnd = (1 - verdict.lower) * 100;

  const headline = verdict.conclusive
    ? `${faster} is ${Math.abs(change).toFixed(1)}% faster`
    : "No conclusion";

  const reasons = [];
  if (tooFast) {
    reasons.push("A single run finishes in under a millisecond, which is near "
      + "the resolution of the browser clock. Raise the iteration count until "
      + "each snippet takes a few milliseconds.");
  }
  if (!verdict.conclusive) {
    if (verdict.below_floor) {
      reasons.push(`Observed ${percent(verdict.observed)}, below the `
        + `${percent(verdict.resolution)} this browser resolves.`);
    } else {
      reasons.push(`The interval spans parity, from `
        + `${lowEnd.toFixed(1)}% to ${highEnd.toFixed(1)}%.`);
    }
    if (verdict.drift > 0.15) {
      reasons.push(`The machine drifted ${percent(verdict.drift)} during the `
        + `probe. Close other tabs and measure again.`);
    }
  }

  result.innerHTML = `
    <div class="verdict">
      <p class="headline">${headline}</p>
      ${verdict.conclusive ? `<p>95% confidence interval: `
        + `${lowEnd.toFixed(1)}% to ${highEnd.toFixed(1)}%</p>` : ""}
      ${reasons.length ? `<ul class="reasons">`
        + reasons.map(r => `<li>${r}</li>`).join("") + `</ul>` : ""}
      <dl>
        <dt>baseline median</dt><dd>${milliseconds(verdict.median_a)}</dd>
        <dt>variant median</dt><dd>${milliseconds(verdict.median_b)}</dd>
        <dt>rounds</dt><dd>${rounds}</dd>
        <dt>browser resolves from</dt><dd>${percent(verdict.resolution)}</dd>
        <dt>drift during probe</dt><dd>${percent(verdict.drift)}</dd>
      </dl>
    </div>`;
}

async function measure() {
  runButton.disabled = true;
  result.innerHTML = "";
  try {
    const first = compile(el("a").value, "Baseline");
    const second = compile(el("b").value, "Variant");
    const budget = Math.max(1, Number(el("budget").value) || 4) * 1000;

    const py = await ensurePyodide();

    setStatus("measuring this browser");
    await nextFrame();
    const probe = probeHost();

    setStatus("comparing");
    await nextFrame();
    const { a, b, rounds } = await collect(first, second, budget);

    const verdict = JSON.parse(decide(py, a, b, probe));
    render(verdict, rounds, roundTooFast(a, b));
    setStatus("");
  } catch (error) {
    result.innerHTML = `<div class="verdict"><p class="headline">Cannot measure</p>`
      + `<p>${error.message}</p></div>`;
    setStatus("");
  } finally {
    runButton.disabled = false;
  }
}

const SLOWER = `let s = 0;
for (let i = 0; i < 3000000; i++) {
  s = (s * 31 + i) % 1000003;
}`;

const FASTER = `let s = 0;
for (let i = 0; i < 2100000; i++) {
  s = (s * 31 + i) % 1000003;
}`;

function loadDifference() {
  el("a").value = SLOWER;
  el("b").value = FASTER;
  result.innerHTML = "";
  setStatus("Variant now does 30% less work. Measure again.");
}

runButton.addEventListener("click", measure);
el("differ").addEventListener("click", loadDifference);
