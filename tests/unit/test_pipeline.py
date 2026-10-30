import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import unittest
import uuid

from neuro_fly.interfaces import DistanceSample
from neuro_fly.output import MockOutput, PulseController, SafetyConfig
from neuro_fly.pipeline import Pipeline, make_report, run_pipeline
from neuro_fly.sensor import ApproachConfig, ApproachEncoder, MockDistanceSensor


class ListSensor:
    def __init__(self, samples):
        self.samples = iter(samples)

    def read(self):
        return next(self.samples, None)


class FakeBrain:
    """Explicit testdouble; it is never used by the application CLI."""
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.inputs = []

    def step(self, looming_strength):
        self.inputs.append(looming_strength)
        result = next(self.outputs)
        if isinstance(result, Exception):
            raise result
        return result


class PipelineTests(unittest.TestCase):
    def make_pipeline(self, samples, outputs):
        output = MockOutput()
        controller = PulseController(output, SafetyConfig(pulse_duration_s=0.2))
        encoder = ApproachEncoder(ApproachConfig(median_window=1, smoothing_alpha=1.0))
        brain = FakeBrain(outputs)
        pipeline = Pipeline(ListSensor(samples), encoder, brain, controller)
        self.addCleanup(controller.close)
        return pipeline, brain, output

    def test_approach_alone_cannot_trigger_output(self):
        samples = [DistanceSample(1000.0, 0.0), DistanceSample(700.0, 0.1)]
        pipeline, brain, output = self.make_pipeline(samples, [0.0, 0.0])
        pipeline.step()
        result = pipeline.step()
        self.assertGreater(result.looming_strength, 0.0)
        self.assertEqual(brain.inputs, [0.0, result.looming_strength])
        self.assertFalse(result.triggered)
        self.assertFalse(output.active)

    def test_snn_output_triggers_even_without_distance_threshold(self):
        samples = [DistanceSample(1000.0, 0.0), DistanceSample(1000.0, 0.1)]
        pipeline, _, output = self.make_pipeline(samples, [0.0, 0.8])
        pipeline.step()
        result = pipeline.step()
        self.assertEqual(result.looming_strength, 0.0)
        self.assertTrue(result.triggered)
        self.assertTrue(output.active)

    def test_invalid_sensor_input_turns_output_off_and_inhibits_new_trigger(self):
        samples = [DistanceSample(1000.0, 0.0), DistanceSample(800.0, 0.1),
                   DistanceSample(None, 0.2, False), DistanceSample(700.0, 0.3),
                   DistanceSample(600.0, 0.4)]
        pipeline, brain, output = self.make_pipeline(samples, [0.0, 0.8, 0.8, 0.8, 0.8])
        pipeline.step()
        self.assertTrue(pipeline.step().triggered)
        self.assertTrue(output.active)
        invalid = pipeline.step()
        self.assertFalse(invalid.sample_usable)
        self.assertEqual(brain.inputs[2], 0.0)
        self.assertFalse(output.active)
        self.assertFalse(pipeline.step().triggered)  # first reading after reset
        self.assertFalse(pipeline.step().triggered)  # no low SNN value to rearm

    def test_brain_error_and_nonfinite_output_fail_closed(self):
        samples = [DistanceSample(1000.0, 0.0), DistanceSample(800.0, 0.1), DistanceSample(700.0, 0.2)]
        for bad in (RuntimeError("brain failure"), float('nan'), 1.1):
            with self.subTest(bad=bad):
                pipeline, _, output = self.make_pipeline(samples, [0.0, 0.8, bad])
                pipeline.step()
                pipeline.step()
                with self.assertRaises((RuntimeError, ValueError)):
                    pipeline.step()
                self.assertFalse(output.active)

    def test_sensor_exception_fails_closed(self):
        class FailingSensor:
            def __init__(self):
                self.count = 0
            def read(self):
                self.count += 1
                if self.count == 3:
                    raise OSError('sensor failed')
                return DistanceSample(1000.0 - self.count * 100, self.count * 0.1)
        output = MockOutput()
        controller = PulseController(output, SafetyConfig(pulse_duration_s=0.2))
        pipeline = Pipeline(FailingSensor(), ApproachEncoder(), FakeBrain([0.0, 0.8]), controller)
        pipeline.step()
        self.assertTrue(pipeline.step().triggered)
        with self.assertRaisesRegex(OSError, 'sensor failed'):
            pipeline.step()
        self.assertFalse(output.active)

    def test_pulse_ends_while_next_brain_step_is_slow(self):
        output = MockOutput()
        class SlowBrain:
            def __init__(self):
                self.count = 0
                self.off_during_step = False
            def step(self, strength):
                self.count += 1
                if self.count == 3:
                    deadline = time.monotonic() + 1.0
                    while output.active and time.monotonic() < deadline:
                        threading.Event().wait(0.01)
                    self.off_during_step = not output.active
                return (0.0, 0.8, 0.8)[self.count - 1]
        brain = SlowBrain()
        controller = PulseController(output, SafetyConfig(pulse_duration_s=0.04))
        pipeline = Pipeline(ListSensor([DistanceSample(1000, 0.0), DistanceSample(900, 0.1),
                                        DistanceSample(800, 0.2)]), ApproachEncoder(), brain, controller)
        try:
            pipeline.step()
            self.assertTrue(pipeline.step().triggered)
            pipeline.step()
            self.assertTrue(brain.off_during_step)
        finally:
            controller.close()

    def test_invalid_numeric_sample_is_safe_in_json_report(self):
        pipeline, brain, output = self.make_pipeline([DistanceSample(float('nan'), float('nan'))], [0.0])
        cycles, overruns = run_pipeline(pipeline, sleep=lambda _: None)
        report = make_report(scenario='invalid', brain=brain, output=output,
                             controller=pipeline.controller, cycles=cycles, overruns=overruns,
                             wall_s=0.01, cpu_s=0.01)
        self.assertIsNone(report['cycles'][0]['distance_mm'])
        self.assertIsNone(report['cycles'][0]['sample_timestamp_s'])
        json.dumps(report, allow_nan=False)

    def test_mock_run_and_report_are_json_serializable(self):
        sensor = MockDistanceSensor("still")
        output = MockOutput()
        controller = PulseController(output)
        brain = FakeBrain([0.0] * 60)
        pipeline = Pipeline(sensor, ApproachEncoder(), brain, controller)
        cycles, overruns = run_pipeline(pipeline, sleep=lambda _: None)
        report = make_report(scenario="still", brain=brain, output=output,
                             controller=controller, cycles=cycles, overruns=overruns,
                             wall_s=0.1, cpu_s=0.05)
        self.assertEqual(len(cycles), 60)
        self.assertEqual(report['non_approach_trigger_count'], 0)
        json.dumps(report, allow_nan=False)

    def test_mock_approach_reaches_output_through_explicit_brain_double(self):
        class EchoBrain:
            def step(self, strength):
                return strength
        output = MockOutput()
        controller = PulseController(output, SafetyConfig(pulse_duration_s=0.02))
        pipeline = Pipeline(MockDistanceSensor('approach'), ApproachEncoder(), EchoBrain(), controller)
        cycles, _ = run_pipeline(pipeline, sleep=lambda _: None)
        self.assertGreater(max(c.looming_strength for c in cycles), 0.9)
        self.assertEqual(controller.trigger_count, 1)
        self.assertTrue(any(c.triggered and c.escape_magnitude > 0.5 for c in cycles))
        self.assertEqual([event.active for event in output.events], [True, False])

    def test_cli_missing_reference_fails_without_dummy_fallback(self):
        missing = Path.cwd() / ('missing-reference-' + uuid.uuid4().hex)
        completed = subprocess.run([sys.executable, '-m', 'neuro_fly', 'demo',
                                    '--reference', str(missing)], capture_output=True, text=True)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn('Connectome data missing', completed.stderr)
        self.assertNotIn('Using dummy data', completed.stdout + completed.stderr)

    def test_package_import_does_not_require_brian2(self):
        script = "import sys, neuro_fly; assert 'brian2' not in sys.modules"
        completed = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
