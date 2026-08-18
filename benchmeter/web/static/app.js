const percent = (value) => `${value >= 0 ? "+" : ""}${value.toFixed(1)}%`;
const plain = (value) => `${value.toFixed(1)}%`;

const el = (id) => document.getElementById(id);

function setStatus(node, message, isError = false) {
  node.textContent = message;
  node.classList.toggle("status--error", isError);
}

function renderMachine(data) {
  el("machine-grade").textContent = data.grade;
  el("machine-drift").textContent = plain(data.drift * 100);
  el("machine-variation").textContent = plain(data.variation * 100);
  el("machine-autocorr").textContent =
    (data.autocorrelation === undefined
      ? "—"
      : (data.autocorrelation >= 0 ? "+" : "") +
        data.autocorrelation.toFixed(3));
  el("machine-resolution").textContent = plain(data.resolution * 100);
  el("machine-advice").textContent = data.advice;
  el("machine-table").hidden = false;
}

async function checkMachine() {
  const button = el("check-machine");
  const status = el("machine-status");
  button.disabled = true;
  setStatus(status, "working…");
  try {
    const response = await fetch("/api/machine");
    renderMachine(await response.json());
    setStatus(status, "");
  } catch (error) {
    setStatus(status, "lost the local server", true);
  } finally {
    button.disabled = false;
  }
}

function renderRows(series) {
  const body = el("results-body");
  body.textContent = "";
  for (const item of series) {
    const row = document.createElement("tr");
    const cells = [
      item.label,
      item.medianText,
      `±${plain(item.spread * 100)}`,
      item.fastestText,
      item.slowestText,
      String(item.samples),
    ];
    cells.forEach((text, index) => {
      const cell = document.createElement(index === 0 ? "th" : "td");
      if (index === 0) cell.scope = "row";
      cell.textContent = text;
      row.appendChild(cell);
    });
    body.appendChild(row);
  }
}

const SVG_NS = "http://www.w3.org/2000/svg";

function svg(tag, attrs) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attrs)) {
    node.setAttribute(key, value);
  }
  return node;
}

function niceStep(span) {
  const raw = span / 4;
  const magnitude = Math.pow(10, Math.floor(Math.log10(raw)));
  const normalised = raw / magnitude;
  const step = normalised >= 5 ? 5 : normalised >= 2 ? 2 : 1;
  return step * magnitude;
}

function intervalBar(comparison) {
  const reach = Math.max(
    Math.abs(comparison.lowerPercent),
    Math.abs(comparison.upperPercent),
    Math.abs(comparison.percent),
    0.5
  );
  const span = reach * 1.4;
  const step = niceStep(span);

  const width = 640;
  const height = 96;
  const padX = 28;
  const axisY = 62;
  const plotWidth = width - padX * 2;

  const toX = (value) => padX + ((value + span) / (2 * span)) * plotWidth;

  const figure = document.createElement("figure");
  figure.className = "interval";

  const chart = svg("svg", {
    viewBox: `0 0 ${width} ${height}`,
    class: "interval__chart",
    role: "img",
    "aria-label":
      `Confidence interval from ${percent(comparison.lowerPercent)} ` +
      `to ${percent(comparison.upperPercent)}`,
  });

  for (let tick = -Math.floor(span / step) * step;
       tick <= span; tick += step) {
    const x = toX(tick);
    const isZero = Math.abs(tick) < step / 100;
    chart.appendChild(svg("line", {
      x1: x, y1: axisY - 5, x2: x, y2: axisY + 5,
      class: isZero ? "tick tick--zero" : "tick",
    }));
    const text = svg("text", {
      x: x, y: axisY + 20, class: "tick-label", "text-anchor": "middle",
    });
    text.textContent = `${tick > 0 ? "+" : ""}${Number(tick.toFixed(2))}%`;
    chart.appendChild(text);
  }

  chart.appendChild(svg("line", {
    x1: padX, y1: axisY, x2: width - padX, y2: axisY, class: "axis",
  }));

  const zeroX = toX(0);
  chart.appendChild(svg("line", {
    x1: zeroX, y1: 14, x2: zeroX, y2: axisY, class: "zero-line",
  }));
  const zeroLabel = svg("text", {
    x: zeroX, y: 10, class: "zero-label", "text-anchor": "middle",
  });
  zeroLabel.textContent = "no difference";
  chart.appendChild(zeroLabel);

  const barY = 34;
  const left = toX(comparison.lowerPercent);
  const right = toX(comparison.upperPercent);
  const cls = comparison.conclusive ? "band band--clear" : "band band--crossing";

  chart.appendChild(svg("line", {
    x1: left, y1: barY, x2: right, y2: barY, class: cls,
  }));
  chart.appendChild(svg("line", {
    x1: left, y1: barY - 7, x2: left, y2: barY + 7, class: cls,
  }));
  chart.appendChild(svg("line", {
    x1: right, y1: barY - 7, x2: right, y2: barY + 7, class: cls,
  }));

  const centre = toX(comparison.percent);
  chart.appendChild(svg("circle", {
    cx: centre, cy: barY, r: 3.5, class: "estimate",
  }));
  const estimateLabel = svg("text", {
    x: centre, y: barY - 13, class: "estimate-label", "text-anchor": "middle",
  });
  estimateLabel.textContent = percent(comparison.percent);
  chart.appendChild(estimateLabel);

  const caption = document.createElement("figcaption");
  caption.className = "interval__caption";
  caption.textContent =
    `Best guess ${percent(comparison.percent)}. The real answer is ` +
    `somewhere between ${percent(comparison.lowerPercent)} and ` +
    `${percent(comparison.upperPercent)}` +
    (comparison.conclusive
      ? ", all on one side of zero, so you can rely on it."
      : ", which crosses zero, so it might be nothing at all.");

  figure.append(chart, caption);
  return figure;
}

function nextSteps(comparison, machine) {
  const steps = [];
  if (machine.drift >= 0.15) {
    steps.push(
      `Your machine drifted ${plain(machine.drift * 100)} with nothing ` +
      `running. Close what you can and try again.`
    );
  }
  if (comparison.belowResolution) {
    steps.push(
      `Your machine can only spot differences of ` +
      `${plain(machine.resolution * 100)} or more.`
    );
  }
  if (Math.abs(comparison.percent) < 1) {
    steps.push("Under 1% apart. Treat them as the same.");
  } else {
    steps.push("Give it more time and the answer may sharpen.");
  }
  return steps;
}

function renderVerdict(comparison, machine) {
  const box = document.createElement("div");
  box.className =
    `verdict verdict--${comparison.conclusive ? "conclusive" : "inconclusive"}`;

  const label = document.createElement("p");
  label.className = "verdict__label";
  label.textContent = comparison.conclusive
    ? "Answer"
    : "Too close to call";
  box.appendChild(label);

  const detail = document.createElement("p");
  detail.className = "verdict__detail";
  if (comparison.conclusive) {
    detail.textContent =
      `Your ${comparison.variant} is ` +
      `${plain(Math.abs(comparison.percent))} ` +
      `${comparison.faster ? "faster" : "slower"} than ` +
      `${comparison.baseline}.`;
  } else {
    detail.textContent =
      `They came out ${plain(Math.abs(comparison.percent))} apart, which ` +
      `is too close for your machine to call.`;
  }
  box.appendChild(detail);
  box.appendChild(intervalBar(comparison));

  if (!comparison.conclusive) {
    const list = document.createElement("ul");
    list.className = "verdict__next";
    for (const step of nextSteps(comparison, machine)) {
      const item = document.createElement("li");
      item.textContent = step;
      list.appendChild(item);
    }
    box.appendChild(list);
  }
  return box;
}

function renderScatter(series) {
  const host = el("scatter");
  host.textContent = "";
  const withData = series.filter((s) => s.timings && s.timings.length);
  if (withData.length < 1) return;

  const width = 900;
  const height = 210;
  const padLeft = 62;
  const padRight = 16;
  const padTop = 14;
  const padBottom = 30;
  const rounds = Math.max(...withData.map((s) => s.timings.length));
  const all = withData.flatMap((s) => s.timings);
  const sortedAll = [...all].sort((a, b) => a - b);
  const low = sortedAll[0];
  const cutoff = sortedAll[Math.floor(sortedAll.length * 0.97)];
  const high = cutoff > low ? cutoff : sortedAll[sortedAll.length - 1];
  const range = high - low || 1;
  const clipped = all.filter((v) => v > high).length;

  const toX = (index) =>
    padLeft + (index / Math.max(rounds - 1, 1)) *
    (width - padLeft - padRight);
  const toY = (value) => {
    const capped = Math.min(value, high);
    return height - padBottom -
      ((capped - low) / range) * (height - padTop - padBottom);
  };

  const chart = svg("svg", {
    viewBox: `0 0 ${width} ${height}`,
    class: "scatter",
    role: "img",
    "aria-label": "Every timing sample in measurement order",
  });

  for (let step = 0; step <= 4; step++) {
    const value = low + (range * step) / 4;
    const y = toY(value);
    chart.appendChild(svg("line", {
      x1: padLeft, y1: y, x2: width - padRight, y2: y, class: "gridline",
    }));
    const label = svg("text", {
      x: padLeft - 8, y: y + 3, class: "axis-label", "text-anchor": "end",
    });
    label.textContent = `${(value / 1e6).toFixed(1)} ms`;
    chart.appendChild(label);
  }

  chart.appendChild(svg("rect", {
    x: padLeft, y: padTop, width: width - padLeft - padRight,
    height: height - padTop - padBottom, class: "frame",
  }));

  withData.forEach((item, seriesIndex) => {
    const sorted = [...item.timings].sort((a, b) => a - b);
    const mid = sorted[Math.floor(sorted.length / 2)];
    chart.appendChild(svg("line", {
      x1: padLeft, y1: toY(mid), x2: width - padRight, y2: toY(mid),
      class: seriesIndex === 0 ? "median-a" : "median-b",
    }));
    item.timings.forEach((value, index) => {
      const beyond = value > high;
      const marker = seriesIndex === 0
        ? svg("circle", { cx: toX(index), cy: toY(value), r: 2.4,
                          class: "dot-a" })
        : svg("circle", { cx: toX(index), cy: toY(value), r: 2.9,
                          class: "dot-b" });
      if (beyond) {
        marker.setAttribute("class", `${marker.getAttribute("class")} beyond`);
      }
      chart.appendChild(marker);
    });
  });

  const xLabel = svg("text", {
    x: (padLeft + width - padRight) / 2, y: height - 6,
    class: "axis-label", "text-anchor": "middle",
  });
  xLabel.textContent = `round 1 to ${rounds}`;
  chart.appendChild(xLabel);

  host.appendChild(chart);

  const legend = document.createElement("div");
  legend.className = "legend";
  withData.forEach((item, index) => {
    const entry = document.createElement("span");
    const marker = document.createElement("i");
    marker.className = index === 0 ? "a" : "b";
    entry.append(marker, document.createTextNode(item.label));
    legend.appendChild(entry);
  });
  const dashed = document.createElement("span");
  dashed.textContent = "dashed line: typical";
  legend.appendChild(dashed);
  host.appendChild(legend);

  const clippedNote = clipped
    ? ` ${clipped} run${clipped > 1 ? "s" : ""} went off the top of the ` +
      `chart and sit against the edge.`
    : "";
  el("scatter-caption").textContent =
    "A tilt or a sudden jump means your machine changed speed while " +
    "measuring." + clippedNote;
}

function renderResults(data) {
  renderRows(data.series);
  el("run-caption").textContent =
    "Run one after the other, in random order";
  el("results-state").textContent =
    `${data.rounds} rounds` +
    (data.stoppedEarly ? ", stopped once clear" : "");
  renderScatter(data.series);

  const verdicts = el("verdicts");
  verdicts.textContent = "";
  for (const comparison of data.comparisons) {
    verdicts.appendChild(renderVerdict(comparison, data.machine));
  }
  el("results").hidden = false;
  renderMachine(data.machine);
}

async function runMeasurement() {
  const button = el("run");
  const status = el("run-status");
  const payload = {
    commands: [el("command-a").value, el("command-b").value],
    labels: [el("label-a").value, el("label-b").value],
    budget: Number(el("budget").value),
  };

  button.disabled = true;
  setStatus(status, "working…");

  try {
    const response = await fetch("/api/measure", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (data.error) {
      setStatus(status, data.error, true);
      return;
    }
    renderResults(data);
    setStatus(status, "");
  } catch (error) {
    setStatus(status, "lost the local server", true);
  } finally {
    button.disabled = false;
  }
}

el("check-machine").addEventListener("click", checkMachine);
el("run").addEventListener("click", runMeasurement);

const THEME_KEY = "benchmeter-theme";

function applyTheme(theme) {
  const root = document.documentElement;
  if (theme) {
    root.setAttribute("data-theme", theme);
  } else {
    root.removeAttribute("data-theme");
  }
  const dark = theme
    ? theme === "dark"
    : window.matchMedia("(prefers-color-scheme: dark)").matches;
  el("theme-toggle").textContent = dark ? "Light" : "Dark";
}

function currentTheme() {
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === "dark" || stored === "light") return stored;
  return null;
}

function toggleTheme() {
  const root = document.documentElement;
  const dark = root.getAttribute("data-theme") === "dark" ||
    (!root.hasAttribute("data-theme") &&
      window.matchMedia("(prefers-color-scheme: dark)").matches);
  const next = dark ? "light" : "dark";
  localStorage.setItem(THEME_KEY, next);
  applyTheme(next);
}

applyTheme(currentTheme());
el("theme-toggle").addEventListener("click", toggleTheme);
