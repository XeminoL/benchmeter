from __future__ import annotations

from dataclasses import dataclass

from . import statistics_ as stats
from .clock import format_duration
from .experiment import Measurement, Series
from .layout import rule
from .machine import MachineState

MAX_SUGGESTED_ROUNDS = 5000
NEGLIGIBLE_DIFFERENCE_PERCENT = 1.0


@dataclass(frozen=True)
class Comparison:
    baseline: Series
    variant: Series
    ratio: float
    lower: float
    upper: float
    conclusive: bool

    @property
    def percent(self) -> float:
        return (self.ratio - 1) * 100

    @property
    def faster(self) -> bool:
        return self.ratio < 1

    @property
    def half_width_percent(self) -> float:
        return ((self.upper - self.lower) / 2) * 100


@dataclass(frozen=True)
class Report:
    measurement: Measurement
    machine: MachineState
    comparisons: list[Comparison]

    @property
    def conclusive(self) -> bool:
        return all(item.conclusive for item in self.comparisons)


def analyse(measurement: Measurement, machine: MachineState,
            seed: int | None = None) -> Report:
    baseline = measurement.series[0]
    comparisons = []

    for variant in measurement.series[1:]:
        paired = min(len(baseline), len(variant))
        ratio, lower, upper = stats.ratio_confidence_interval(
            baseline.timings[:paired], variant.timings[:paired], seed=seed)
        conclusive = stats.is_conclusive(lower, upper)

        if conclusive and machine.measured:
            if abs(ratio - 1) < machine.resolution:
                conclusive = False

        comparisons.append(Comparison(
            baseline=baseline, variant=variant, ratio=ratio,
            lower=lower, upper=upper, conclusive=conclusive))

    return Report(measurement=measurement, machine=machine,
                  comparisons=comparisons)


def format_series_line(series: Series) -> str:
    center = stats.median(series.timings)
    spread = stats.coefficient_of_variation(series.timings) * 100
    return f"{series.label:<28} {format_duration(center):>12}   +-{spread:>5.1f}%"


def suggest_additional_rounds(comparison: Comparison,
                               measurement: Measurement) -> int:
    observed = abs(comparison.percent)
    width = comparison.half_width_percent
    if observed <= 0 or width <= observed:
        return 0
    factor = (width / observed) ** 2
    needed = int(measurement.rounds * (factor - 1))
    return needed if 0 < needed <= MAX_SUGGESTED_ROUNDS else 0


def explain_inconclusive(comparison: Comparison, machine: MachineState,
                          measurement: Measurement) -> list[str]:
    observed = abs(comparison.percent)
    lines = [
        "  NO CONCLUSION",
        f"  Observed difference {observed:.1f}%, but the confidence interval "
        f"runs from {(comparison.lower - 1) * 100:+.1f}% "
        f"to {(comparison.upper - 1) * 100:+.1f}%",
        "  -> that interval includes zero, so equal speed has not been "
        "ruled out.",
        "",
        "  What to do next:",
    ]

    if machine.busy:
        lines.append(
            f"    - Machine is drifting {machine.drift * 100:.0f}%. "
            f"Close other applications and measure again."
        )
    if machine.measured and observed < machine.resolution * 100:
        lines.append(
            f"    - This machine resolves differences of "
            f"{machine.resolution * 100:.1f}% and above."
        )
        lines.append(
            f"      The observed {observed:.1f}% falls below that floor."
        )

    additional = suggest_additional_rounds(comparison, measurement)
    if additional:
        lines.append(f"    - About {additional} more rounds would likely "
                     f"settle it.")
    if observed < NEGLIGIBLE_DIFFERENCE_PERCENT:
        lines.append("    - These two are almost certainly the same speed.")
    return lines


def explain_conclusive(comparison: Comparison,
                        machine: MachineState) -> list[str]:
    direction = "faster" if comparison.faster else "slower"
    label = stats.confidence_label(
        machine.drift, len(comparison.baseline), machine.variation)
    return [
        f"  {comparison.variant.label} is {abs(comparison.percent):.1f}% "
        f"{direction} than {comparison.baseline.label}",
        f"  95% confidence interval: "
        f"{(comparison.lower - 1) * 100:+.1f}% to "
        f"{(comparison.upper - 1) * 100:+.1f}%",
        f"  confidence: {label}",
    ]


def render(report: Report) -> str:
    measurement = report.measurement
    machine = report.machine
    lines = ["", "MEASUREMENT", rule()]

    for series in measurement.series:
        lines.append("  " + format_series_line(series))

    lines.append("")
    early = " (stopped early, difference already clear)" \
        if measurement.stopped_early else ""
    lines.append(f"  {measurement.rounds} interleaved rounds{early}")

    if machine.measured:
        lines.append(
            f"  machine: {machine.grade} "
            f"(drift {machine.drift * 100:.0f}%, "
            f"resolves from {machine.resolution * 100:.1f}%)"
        )
    else:
        lines.append("  machine: not checked")

    for comparison in report.comparisons:
        lines.append("")
        lines.append(rule())
        if comparison.conclusive:
            lines.extend(explain_conclusive(comparison, machine))
        else:
            lines.extend(
                explain_inconclusive(comparison, machine, measurement))

    failed = [s for s in measurement.series if s.failures]
    if failed:
        lines.append("")
        for series in failed:
            lines.append(f"  warning: {series.label} failed "
                         f"{series.failures} times")

    lines.append("")
    return "\n".join(lines)