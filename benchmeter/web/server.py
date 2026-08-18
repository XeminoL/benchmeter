from __future__ import annotations

import json
import secrets
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .. import machine, report as reporting
from ..clock import format_duration, is_runnable
from ..experiment import measure
from .. import statistics_ as stats

STATIC_DIR = Path(__file__).parent / "static"
ASSET_VERSION = str(int(time.time()))
SESSION_TOKEN = secrets.token_urlsafe(24)
ALLOWED_HOSTS = {"127.0.0.1", "localhost", "[::1]"}
DEFAULT_PORT = 7801
MAX_COMMANDS = 4
MAX_BUDGET_SECONDS = 120
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}


def run_measurement(payload: dict) -> dict:
    commands = [c.strip() for c in payload.get("commands", []) if c.strip()]
    if len(commands) < 1:
        return {"error": "Enter at least one command."}
    if len(commands) > MAX_COMMANDS:
        return {"error": f"At most {MAX_COMMANDS} commands."}

    for command in commands:
        runnable, _ = is_runnable(command)
        if not runnable:
            return {"error": f"This command did not run: {command}"}

    labels = payload.get("labels") or []
    labels = [
        (labels[i].strip() if i < len(labels) and labels[i].strip()
         else f"command {i + 1}")
        for i in range(len(commands))
    ]

    budget = float(payload.get("budget", 20))
    budget = max(5.0, min(budget, MAX_BUDGET_SECONDS))

    state = machine.probe()
    measurement = measure(
        commands, labels,
        budget_seconds=budget,
        resolution=state.resolution,
    )
    report = reporting.analyse(measurement, state)

    return {
        "machine": {
            "grade": state.grade,
            "drift": state.drift,
            "resolution": state.resolution,
            "variation": state.variation,
            "autocorrelation": state.autocorrelation,
            "advice": state.advice,
        },
        "rounds": measurement.rounds,
        "stoppedEarly": measurement.stopped_early,
        "conclusive": report.conclusive,
        "series": [
            {
                "label": series.label,
                "median": stats.median(series.timings) if series.timings else 0,
                "medianText": (format_duration(stats.median(series.timings))
                               if series.timings else "-"),
                "spread": (stats.coefficient_of_variation(series.timings)
                           if series.timings else 0),
                "fastestText": (format_duration(min(series.timings))
                                if series.timings else "-"),
                "slowestText": (format_duration(max(series.timings))
                                if series.timings else "-"),
                "timings": series.timings,
                "samples": len(series),
                "failures": series.failures,
            }
            for series in measurement.series
        ],
        "comparisons": [
            {
                "baseline": item.baseline.label,
                "variant": item.variant.label,
                "percent": item.percent,
                "lowerPercent": (item.lower - 1) * 100,
                "upperPercent": (item.upper - 1) * 100,
                "conclusive": item.conclusive,
                "faster": item.faster,
                "belowResolution": (
                    abs(item.ratio - 1) < state.resolution
                ),
            }
            for item in report.comparisons
        ],
    }


def probe_machine() -> dict:
    state = machine.probe()
    return {
        "grade": state.grade,
        "drift": state.drift,
        "resolution": state.resolution,
        "variation": state.variation,
        "autocorrelation": state.autocorrelation,
        "advice": state.advice,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "benchmeter"

    def log_message(self, format, *args):
        return

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, name: str) -> None:
        path = (STATIC_DIR / name).resolve()
        if not path.is_file() or STATIC_DIR.resolve() not in path.parents:
            self.send_error(404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type",
                         CONTENT_TYPES.get(path.suffix, "text/plain"))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(body)

    def request_is_local(self) -> bool:
        """Reject anything that did not come from a page we served.

        The server executes shell commands, so a page on any other site
        must not be able to reach it. Browsers cannot forge Origin, and
        they cannot read the token out of a cross-origin response, so
        checking both closes the hole.
        """
        origin = self.headers.get("Origin")
        if origin:
            host = urlparse(origin).hostname
            if host not in ALLOWED_HOSTS:
                return False
        host_header = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        if host_header and host_header not in ALLOWED_HOSTS:
            return False
        return self.headers.get("X-Benchmeter-Token") == SESSION_TOKEN

    def send_index(self) -> None:
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        html = html.replace('href="style.css"',
                            f'href="style.css?v={ASSET_VERSION}"')
        html = html.replace('src="app.js"',
                            f'src="app.js?v={ASSET_VERSION}"')
        token_tag = (f'<meta name="benchmeter-token" '
                     f'content="{SESSION_TOKEN}">')
        html = html.replace("</head>", token_tag + "\n</head>")
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPES[".html"])
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/":
            self.send_index()
        elif route == "/api/machine":
            if not self.request_is_local():
                self.send_json({"error": "Rejected: request did not "
                                         "originate from this page."}, 403)
                return
            self.send_json(probe_machine())
        else:
            self.send_static(route.lstrip("/"))

    def do_POST(self):
        if urlparse(self.path).path != "/api/measure":
            self.send_error(404)
            return
        if not self.request_is_local():
            self.send_json({"error": "Rejected: request did not originate "
                                     "from this page."}, 403)
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_json({"error": "Malformed request."}, 400)
            return
        try:
            self.send_json(run_measurement(payload))
        except Exception as error:
            self.send_json({"error": str(error)}, 500)


def serve(port: int = DEFAULT_PORT, open_browser: bool = True) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    address = f"http://127.0.0.1:{port}"
    print(f"benchmeter is running at {address}")
    print("press Ctrl+C to stop")
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(address)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
