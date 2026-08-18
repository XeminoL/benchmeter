from __future__ import annotations

import time

from benchmeter import machine, report as reporting
from benchmeter import statistics_ as stats
from benchmeter.clock import format_duration
from benchmeter.experiment import measure

MAX_COMMANDS = 4
MAX_BUDGET_SECONDS = 120
MIN_BUDGET_SECONDS = 0.01


def run_measurement(payload: dict) -> dict:
    commands = [c.strip() for c in payload.get("commands", []) if c.strip()]
    if len(commands) < 1:
        return {"error": "Enter at least one command."}
    if len(commands) > MAX_COMMANDS:
        return {"error": f"At most {MAX_COMMANDS} commands."}

    labels = payload.get("labels") or []
    labels = [
        (labels[i].strip() if i < len(labels) and labels[i].strip()
         else f"command {i + 1}")
        for i in range(len(commands))
    ]

    budget = float(payload.get("budget", 20))
    budget = max(MIN_BUDGET_SECONDS,
                 min(budget, MAX_BUDGET_SECONDS))

    started = time.perf_counter()
    state = machine.probe()
    remaining = budget - (time.perf_counter() - started)

    measurement = measure(
        commands, labels,
        budget_seconds=max(remaining, 0.0),
        resolution=state.resolution,
    )
    report = reporting.analyse(measurement, state)

    broken = [s.label for s in measurement.series if not s.timings]
    if broken:
        return {"error": "These commands did not run: "
                         + ", ".join(broken)}

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
        "overran": measurement.overran,
        "elapsedSeconds": measurement.elapsed_ns / 1e9,
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
