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
  el("machine-resolution").textContent =
    `${plain(data.resolution * 100)} and above`;
  el("machine-advice").textContent = data.advice;
  el("machine-readout").hidden = false;
}

async function checkMachine() {
  const button = el("check-machine");
  const status = el("machine-status");
  button.disabled = true;
  setStatus(status, "measuring the machine…");
  try {
    const response = await fetch("/api/machine");
    renderMachine(await response.json());
    setStatus(status, "");
  } catch (error) {
    setStatus(status, "could not reach the local server", true);
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

function intervalBar(comparison) {
  const span = Math.max(
    Math.abs(comparison.lowerPercent),
    Math.abs(comparison.upperPercent),
    Math.abs(comparison.percent),
    1
  ) * 1.35;

  const toOffset = (value) => ((value + span) / (2 * span)) * 100;
  const left = toOffset(comparison.lowerPercent);
  const right = toOffset(comparison.upperPercent);

  const wrapper = document.createElement("div");
  wrapper.className = "interval";

  const scale = document.createElement("div");
  scale.className = "interval__scale";

  const zero = document.createElement("div");
  zero.className = "interval__zero";
  zero.style.left = `${toOffset(0)}%`;

  const band = document.createElement("div");
  band.className = "interval__band";
  band.style.left = `${left}%`;
  band.style.width = `${Math.max(right - left, 0.6)}%`;

  const point = document.createElement("div");
  point.className = "interval__point";
  point.style.left = `${toOffset(comparison.percent)}%`;

  scale.append(zero, band, point);

  const caption = document.createElement("p");
  caption.className = "interval__caption";
  caption.textContent =
    `Interval ${percent(comparison.lowerPercent)} to ` +
    `${percent(comparison.upperPercent)}. ` +
    (comparison.conclusive
      ? "Clear of the zero line."
      : "Crosses the zero line, so no difference is established.");

  wrapper.append(scale, caption);
  return wrapper;
}

function nextSteps(comparison, machine) {
  const steps = [];
  if (machine.drift >= 0.15) {
    steps.push(
      `The machine drifted ${plain(machine.drift * 100)} while idle. ` +
      `Closing other applications will tighten this.`
    );
  }
  if (comparison.belowResolution) {
    steps.push(
      `This machine resolves ${plain(machine.resolution * 100)} and above; ` +
      `the observed ${plain(Math.abs(comparison.percent))} sits underneath it.`
    );
  }
  if (Math.abs(comparison.percent) < 1) {
    steps.push("The two are almost certainly the same speed.");
  } else {
    steps.push("Raising the time allowed gives the interval room to narrow.");
  }
  return steps;
}

function renderVerdict(comparison, machine) {
  const box = document.createElement("div");
  box.className =
    `verdict verdict--${comparison.conclusive ? "conclusive" : "inconclusive"}`;

  const label = document.createElement("p");
  label.className = "verdict__label";
  label.textContent = comparison.conclusive ? "Result" : "No conclusion";
  box.appendChild(label);

  const detail = document.createElement("p");
  detail.className = "verdict__detail";
  if (comparison.conclusive) {
    detail.textContent =
      `${comparison.variant} is ` +
      `${plain(Math.abs(comparison.percent))} ` +
      `${comparison.faster ? "faster" : "slower"} than ${comparison.baseline}.`;
  } else {
    detail.textContent =
      `Observed ${plain(Math.abs(comparison.percent))} between ` +
      `${comparison.baseline} and ${comparison.variant}, which is not ` +
      `enough to rule out equal speed.`;
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

function renderResults(data) {
  renderRows(data.series);
  el("run-caption").textContent =
    `Timings over ${data.rounds} interleaved rounds` +
    (data.stoppedEarly ? ", stopped early once clear" : "");

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
  setStatus(status, "measuring, this takes about the time you allowed…");

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
    setStatus(status, "could not reach the local server", true);
  } finally {
    button.disabled = false;
  }
}

el("check-machine").addEventListener("click", checkMachine);
el("run").addEventListener("click", runMeasurement);
