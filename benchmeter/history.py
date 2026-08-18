from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from . import statistics_ as stats
from .layout import rule
from .report import Report

HISTORY_FILENAME = "benchmeter-history.json"
COMPARABILITY_THRESHOLD = 0.10


@dataclass(frozen=True)
class HistoryComparison:
    machine_changed: bool
    previous_drift: float
    current_drift: float
    changes: list[tuple[str, float]]
    previous_timestamp: float


def history_path(directory: str | Path | None = None) -> Path:
    root = Path(directory) if directory else Path.cwd()
    return root / HISTORY_FILENAME


def load(directory: str | Path | None = None) -> list[dict]:
    path = history_path(directory)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save(report: Report, note: str = "",
         directory: str | Path | None = None) -> dict:
    record = {
        "timestamp": time.time(),
        "note": note,
        "machine": {
            "drift": report.machine.drift,
            "resolution": report.machine.resolution,
            "variation": report.machine.variation,
        },
        "series": [
            {
                "label": series.label,
                "median_ns": stats.median(series.timings),
                "samples": len(series),
            }
            for series in report.measurement.series
        ],
    }
    entries = load(directory)
    entries.append(record)
    history_path(directory).write_text(
        json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    return record


def compare_with_previous(
    report: Report, directory: str | Path | None = None
) -> HistoryComparison | None:
    entries = load(directory)
    if not entries:
        return None

    previous = entries[-1]
    current_medians = {
        series.label: stats.median(series.timings)
        for series in report.measurement.series
    }
    previous_medians = {
        entry["label"]: entry["median_ns"] for entry in previous["series"]
    }

    shared = set(current_medians) & set(previous_medians)
    if not shared:
        return None

    changes = [
        (label,
         (current_medians[label] - previous_medians[label])
         / previous_medians[label] * 100)
        for label in sorted(shared)
        if previous_medians[label]
    ]

    previous_drift = previous["machine"]["drift"]
    return HistoryComparison(
        machine_changed=abs(report.machine.drift - previous_drift)
        > COMPARABILITY_THRESHOLD,
        previous_drift=previous_drift,
        current_drift=report.machine.drift,
        changes=changes,
        previous_timestamp=previous["timestamp"],
    )


def render(comparison: HistoryComparison | None) -> str:
    if not comparison:
        return ""

    lines = ["", "COMPARED WITH PREVIOUS RUN", rule()]
    for label, percent in comparison.changes:
        direction = "slower" if percent > 0 else "faster"
        lines.append(f"  {label:<28} {direction} by {abs(percent):.1f}%")

    if comparison.machine_changed:
        lines.extend([
            "",
            "  WARNING: the machine was in a different state this time",
            f"  (drift {comparison.previous_drift * 100:.0f}% -> "
            f"{comparison.current_drift * 100:.0f}%)",
            "  The change above may be the machine, not the code.",
        ])

    lines.append("")
    return "\n".join(lines)