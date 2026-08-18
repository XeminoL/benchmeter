import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmeter import experiment, history, machine, report as reporting

TRIVIAL_COMMAND = "python -c pass"
FAILING_COMMAND = 'python -c "raise SystemExit(1)"'


def series_of(label, timings):
    series = experiment.Series(label)
    series.timings = list(timings)
    return series


def measurement_of(*series):
    return experiment.Measurement(
        series=list(series), rounds=len(series[0].timings),
        stopped_early=False)


class TestInterleavedMeasurement(unittest.TestCase):
    def test_every_command_gets_the_same_number_of_rounds(self):
        result = experiment.measure(
            [TRIVIAL_COMMAND, TRIVIAL_COMMAND], ["a", "b"],
            rounds=12, seed=1)
        self.assertEqual(len(result.series), 2)
        for series in result.series:
            self.assertEqual(len(series), result.rounds)

    def test_failures_are_counted_separately_from_timings(self):
        result = experiment.measure(
            [TRIVIAL_COMMAND, FAILING_COMMAND], ["ok", "broken"],
            rounds=10, seed=1)
        self.assertEqual(result.series[0].failures, 0)
        self.assertEqual(result.series[1].failures, 10)
        self.assertEqual(len(result.series[1]), 0)

    def test_single_command_is_supported(self):
        result = experiment.measure([TRIVIAL_COMMAND], ["only"],
                                    rounds=8, seed=2)
        self.assertEqual(len(result.series), 1)
        self.assertGreater(len(result.series[0]), 0)


class TestMachineProbe(unittest.TestCase):
    def test_probe_reports_every_indicator(self):
        state = machine.probe(runs=60)
        self.assertGreaterEqual(state.drift, 0)
        self.assertGreater(state.resolution, 0)
        self.assertIn(state.grade, ("quiet", "unsettled", "noisy"))
        self.assertTrue(state.advice)

    def test_unmeasured_state_does_not_pretend_to_know(self):
        state = machine.unmeasured()
        self.assertEqual(state.grade, "unmeasured")
        self.assertFalse(state.busy)


class TestReport(unittest.TestCase):
    def _report(self, left, right, resolution=0.01, drift=0.02):
        state = machine.MachineState(drift, 0.05, resolution, 0.0)
        return reporting.analyse(
            measurement_of(series_of("a", left), series_of("b", right)),
            state, seed=1)

    def test_identical_series_yield_no_conclusion(self):
        samples = [1000 + (index % 11) for index in range(80)]
        report = self._report(samples, list(samples))
        self.assertFalse(report.conclusive)
        self.assertIn("NO CONCLUSION", reporting.render(report))

    def test_clear_difference_is_reported_with_direction(self):
        slow = [2000 + (index % 7) for index in range(80)]
        fast = [1000 + (index % 7) for index in range(80)]
        report = self._report(slow, fast)
        self.assertTrue(report.conclusive)
        self.assertTrue(report.comparisons[0].faster)
        self.assertIn("faster", reporting.render(report))

    def test_unmeasured_machine_is_stated_not_hidden(self):
        samples = [1000 + (index % 11) for index in range(60)]
        report = reporting.analyse(
            measurement_of(series_of("a", samples), series_of("b", samples)),
            machine.unmeasured(), seed=1)
        self.assertIn("not checked", reporting.render(report))


class TestResolutionFloor(unittest.TestCase):

    def _report(self, left, right, resolution):
        state = machine.MachineState(0.48, 0.15, resolution, 0.0)
        return reporting.analyse(
            measurement_of(series_of("a", left), series_of("b", right)),
            state, seed=1)

    def test_difference_below_machine_resolution_is_refused(self):
        baseline = [1000 + (index % 3) for index in range(200)]
        variant = [1019 + (index % 3) for index in range(200)]
        report = self._report(baseline, variant, resolution=0.045)
        self.assertFalse(
            report.conclusive,
            "1.9% claimed on a machine that resolves only 4.5%")

    def test_difference_above_machine_resolution_still_reported(self):
        baseline = [1000 + (index % 3) for index in range(200)]
        variant = [1500 + (index % 3) for index in range(200)]
        report = self._report(baseline, variant, resolution=0.045)
        self.assertTrue(report.conclusive)

    def test_early_stopping_respects_the_same_floor(self):
        series = [series_of("a", [1000] * 40), series_of("b", [1019] * 40)]
        self.assertFalse(experiment.is_settled(series, seed=1,
                                               resolution=0.045))
        self.assertTrue(experiment.is_settled(series, seed=1, resolution=0.0))


class TestHistory(unittest.TestCase):
    def _report(self, drift):
        samples = [1000] * 40
        state = machine.MachineState(drift, 0.05, 0.01, 0.0)
        return reporting.analyse(
            measurement_of(series_of("a", samples)), state, seed=1)

    def test_saved_run_can_be_read_back(self):
        with tempfile.TemporaryDirectory() as directory:
            history.save(self._report(0.02), "first", directory)
            entries = history.load(directory)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["note"], "first")

    def test_machine_change_between_runs_is_flagged(self):
        with tempfile.TemporaryDirectory() as directory:
            history.save(self._report(0.01), "", directory)
            comparison = history.compare_with_previous(
                self._report(0.40), directory)
            self.assertTrue(comparison.machine_changed)
            self.assertIn("WARNING", history.render(comparison))

    def test_no_history_means_no_comparison(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNone(
                history.compare_with_previous(self._report(0.02), directory))


if __name__ == "__main__":
    unittest.main(verbosity=2)