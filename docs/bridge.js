const PACKAGE_FILES = [
  "__init__.py", "clock.py", "statistics_.py", "machine.py",
  "experiment.py", "report.py", "layout.py", "history.py",
];
const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js";

const nativeFetch = window.fetch.bind(window);

let pyodide = null;
let loading = null;

function announce(message) {
  for (const id of ["machine-status", "run-status"]) {
    const node = document.getElementById(id);
    if (node && !node.textContent) node.textContent = message;
  }
}

function clearAnnouncement() {
  for (const id of ["machine-status", "run-status"]) {
    const node = document.getElementById(id);
    if (node && node.textContent.startsWith("loading")) node.textContent = "";
  }
}

async function loadPyodideScript() {
  await new Promise((resolve, reject) => {
    const tag = document.createElement("script");
    tag.src = PYODIDE_URL;
    tag.onload = resolve;
    tag.onerror = () => reject(new Error("could not reach the Python runtime"));
    document.head.appendChild(tag);
  });
}

async function boot() {
  announce("loading the Python runtime, about 6 MB");
  await loadPyodideScript();
  const py = await loadPyodide();

  py.FS.mkdir("/app");
  py.FS.mkdir("/app/benchmeter");
  py.FS.mkdir("/app/benchmeter/web");
  for (const name of PACKAGE_FILES) {
    const source = await (await nativeFetch("pkg/" + name)).text();
    py.FS.writeFile("/app/benchmeter/" + name, source);
  }
  for (const name of ["__init__.py", "bridge_server.py"]) {
    const source = await (await nativeFetch("pkg/web/" + name)).text();
    py.FS.writeFile("/app/benchmeter/web/" + name, source);
  }

  py.runPython(`
import sys
sys.path.insert(0, "/app")

import time
from benchmeter import clock

_bridge = None

def _install(fn):
    global _bridge
    _bridge = fn

def _time_once(command, label=""):
    started = time.perf_counter_ns()
    failed = _bridge(command)
    elapsed = time.perf_counter_ns() - started
    return clock.Run(label=label, elapsed_ns=elapsed, exit_code=int(failed))

clock.time_once = _time_once

import benchmeter.experiment as experiment
experiment.time_once = _time_once

def _is_runnable(command):
    run = _time_once(command)
    return run.succeeded, run.elapsed_ns

clock.is_runnable = _is_runnable
`);

  py.globals.get("_install")(runSnippet);
  clearAnnouncement();
  window.__pyodide = py;
  return py;
}

const compiled = new Map();
let sink = 0;

function runSnippet(source) {
  let fn = compiled.get(source);
  if (fn === undefined) {
    try {
      fn = new Function('"use strict";' + source
        + ";return typeof s !== 'undefined' ? s : 0;");
    } catch (error) {
      fn = null;
    }
    compiled.set(source, fn);
  }
  if (fn === null) return 1;
  try {
    sink += fn();
    return 0;
  } catch (error) {
    return 1;
  }
}

function ready() {
  if (!loading) loading = boot().then(py => { pyodide = py; return py; });
  return loading;
}

async function machinePayload() {
  const py = await ready();
  return py.runPython(`
import json
from benchmeter import machine
state = machine.probe()
json.dumps({
    "grade": state.grade,
    "drift": state.drift,
    "resolution": state.resolution,
    "variation": state.variation,
    "autocorrelation": state.autocorrelation,
    "advice": state.advice,
})
`);
}

async function measurePayload(body) {
  const py = await ready();
  py.globals.set("_request", JSON.stringify(body));
  return py.runPython(`
import json
from benchmeter.web.bridge_server import run_measurement
json.dumps(run_measurement(json.loads(_request)))
`);
}

window.fetch = async function (resource, options = {}) {
  const url = typeof resource === "string" ? resource
    : (resource && resource.url) || String(resource);
  let path = url;
  try {
    path = new URL(url, window.location.href).pathname;
  } catch (error) {
    path = url;
  }

  if (path === "/api/machine") {
    return new Response(await machinePayload(),
      { status: 200, headers: { "Content-Type": "application/json" } });
  }
  if (path === "/api/measure") {
    const body = JSON.parse(options.body || "{}");
    return new Response(await measurePayload(body),
      { status: 200, headers: { "Content-Type": "application/json" } });
  }
  return nativeFetch(resource, options);
};

ready().catch(error => {
  for (const id of ["machine-status", "run-status"]) {
    const node = document.getElementById(id);
    if (node) {
      node.textContent = error.message;
      node.classList.add("status--error");
    }
  }
});
