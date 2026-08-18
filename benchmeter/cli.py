from __future__ import annotations

import argparse
import json
import sys

from . import history, machine, report as reporting
from .clock import is_runnable
from .experiment import DEFAULT_BUDGET_SECONDS, measure
from .web.server import DEFAULT_PORT, serve

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_INCONCLUSIVE = 2
RULE_WIDTH = 56


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="benchmeter",
        description="Measure performance and refuse to guess when the "
                    "evidence is too weak.",
    )
    parser.add_argument("commands", nargs="*",
                        help="commands to compare, each quoted")
    parser.add_argument("-n", "--rounds", type=int, default=None,
                        help="fixed number of rounds instead of a budget")
    parser.add_argument("-t", "--budget", type=float,
                        default=DEFAULT_BUDGET_SECONDS,
                        help="time budget in seconds")
    parser.add_argument("--label", action="append", default=None,
                        help="display name for each command")
    parser.add_argument("--seed", type=int, default=None,
                        help="fix the random seed for a repeatable run")
    parser.add_argument("--no-shuffle", action="store_true",
                        help="keep command order fixed within each round")
    parser.add_argument("--json", action="store_true",
                        help="emit machine readable output")
    parser.add_argument("--save", action="store_true",
                        help="append this run to the history file")
    parser.add_argument("--note", default="",
                        help="note stored alongside a saved run")
    parser.add_argument("--check-machine", action="store_true",
                        help="report machine conditions and exit")
    parser.add_argument("--self-proof", action="store_true",
                        help="run the demonstration that the problem is real")
    parser.add_argument("--skip-machine-check", action="store_true",
                        help="do not characterise the machine first")
    parser.add_argument("--web", action="store_true",
                        help="open the browser interface")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help="port for the browser interface")
    return parser


def print_machine(state: machine.MachineState) -> None:
    print()
    print("MACHINE")
    print("-" * RULE_WIDTH)
    print(f"  grade           : {state.grade}")
    print(f"  drift           : {state.drift * 100:.1f}%")
    print(f"  variation       : {state.variation * 100:.1f}%")
    print(f"  resolves from   : {state.resolution * 100:.1f}%")
    print(f"  autocorrelation : {state.autocorrelation:+.3f}")
    print()
    print(f"  {state.advice}")
    print()


def to_json(report: reporting.Report) -> str:
    payload = {
        "rounds": report.measurement.rounds,
        "stopped_early": report.measurement.stopped_early,
        "conclusive": report.conclusive,
        "machine": {
            "grade": report.machine.grade,
            "drift": report.machine.drift,
            "resolution": report.machine.resolution,
            "measured": report.machine.measured,
        },
        "series": [
            {
                "label": series.label,
                "samples": len(series),
                "failures": series.failures,
                "timings_ns": series.timings,
            }
            for series in report.measurement.series
        ],
        "comparisons": [
            {
                "baseline": item.baseline.label,
                "variant": item.variant.label,
                "ratio": item.ratio,
                "lower": item.lower,
                "upper": item.upper,
                "conclusive": item.conclusive,
            }
            for item in report.comparisons
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def validate_arguments(commands: list[str], labels: list[str] | None) -> str | None:
    for command in commands:
        runnable, _ = is_runnable(command)
        if not runnable:
            return f"command is not runnable: {command}"
    if labels and len(labels) != len(commands):
        return "number of labels does not match number of commands"
    return None


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.web:
        serve(port=args.port)
        return EXIT_OK

    if args.check_machine:
        print_machine(machine.probe())
        return EXIT_OK

    if args.self_proof:
        from . import selfproof
        selfproof.run()
        return EXIT_OK

    if not args.commands:
        parser.print_help()
        return EXIT_ERROR

    problem = validate_arguments(args.commands, args.label)
    if problem:
        print(f"error: {problem}", file=sys.stderr)
        return EXIT_ERROR

    if args.skip_machine_check:
        state = machine.unmeasured()
    else:
        state = machine.probe()
        if not args.json:
            print_machine(state)

    show_progress = not args.json and sys.stderr.isatty()

    def on_progress(current: int, total: int) -> None:
        if show_progress:
            print(f"\r  measuring... round {current}/{total}",
                  end="", file=sys.stderr, flush=True)

    measurement = measure(
        args.commands,
        args.label,
        rounds=args.rounds,
        budget_seconds=args.budget,
        seed=args.seed,
        shuffle=not args.no_shuffle,
        on_progress=on_progress,
        resolution=state.resolution,
    )
    if show_progress:
        print("\r" + " " * 40 + "\r", end="", file=sys.stderr)

    report = reporting.analyse(measurement, state, seed=args.seed)

    if args.json:
        print(to_json(report))
    else:
        print(reporting.render(report))
        print(history.render(history.compare_with_previous(report)), end="")

    if args.save:
        history.save(report, args.note)

    return EXIT_OK if report.conclusive else EXIT_INCONCLUSIVE


if __name__ == "__main__":
    sys.exit(main())
