import threading
import time
import unittest

from neuro_fly.output import MockOutput, PulseController, SafetyConfig


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class ManualCall:
    def __init__(self, callback):
        self.callback = callback
        self.cancelled = False

    def cancel(self):
        self.cancelled = True


class ManualScheduler:
    def __init__(self):
        self.calls = []

    def schedule(self, delay_s, callback):
        call = ManualCall(callback)
        self.calls.append((delay_s, call))
        return call


class PulseControllerTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.scheduler = ManualScheduler()
        self.output = MockOutput(self.clock)
        self.controller = PulseController(self.output, clock=self.clock, scheduler=self.scheduler)
        self.addCleanup(self.controller.close)

    def test_thresholds_pulse_reset_and_cooldown(self):
        self.assertFalse(self.controller.update(0.5))
        self.assertTrue(self.controller.update(0.51))
        self.assertTrue(self.output.active)
        self.assertEqual(self.scheduler.calls[0][0], 0.250)
        self.clock.now = 0.25
        self.scheduler.calls[0][1].callback()
        self.assertFalse(self.output.active)
        self.assertFalse(self.controller.update(0.8))  # not rearmed
        self.assertFalse(self.controller.update(0.3))  # reset is strict
        self.assertFalse(self.controller.update(0.29))
        self.clock.now = 0.9
        self.assertFalse(self.controller.update(0.8))  # still in cooldown
        self.clock.now = 1.0
        self.assertTrue(self.controller.update(0.8))
        self.assertEqual(self.controller.trigger_count, 2)

    def test_invalid_or_nonfinite_brain_values_rejected(self):
        for value in (float('nan'), float('inf'), -0.01, 1.01, None, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.controller.update(value)
        self.assertFalse(self.output.active)

    def test_inhibit_stops_pulse_and_requires_a_low_brain_value(self):
        self.controller.update(0.8)
        self.controller.inhibit()
        self.assertFalse(self.output.active)
        self.assertTrue(self.scheduler.calls[0][1].cancelled)
        self.clock.now = 2.0
        self.assertFalse(self.controller.update(0.8))
        self.controller.update(0.0)
        self.assertTrue(self.controller.update(0.8))

    def test_old_cancelled_timer_cannot_end_a_new_pulse(self):
        self.controller.update(0.8)
        old = self.scheduler.calls[0][1]
        self.controller.inhibit()
        self.clock.now = 2.0
        self.controller.update(0.0)
        self.controller.update(0.8)
        old.callback()  # simulate a callback that raced with cancellation
        self.assertTrue(self.output.active)
        self.scheduler.calls[-1][1].callback()
        self.assertFalse(self.output.active)

    def test_scheduler_failure_turns_output_off(self):
        class BrokenScheduler:
            def schedule(self, delay_s, callback):
                raise RuntimeError("scheduler failed")
        output = MockOutput(self.clock)
        controller = PulseController(output, clock=self.clock, scheduler=BrokenScheduler())
        with self.assertRaisesRegex(RuntimeError, "scheduler failed"):
            controller.update(0.9)
        self.assertFalse(output.active)
        controller.close()

    def test_thread_timer_turns_off_during_a_slow_operation(self):
        output = MockOutput()
        controller = PulseController(output, SafetyConfig(pulse_duration_s=0.04))
        try:
            controller.update(0.8)
            threading.Event().wait(0.15)  # stand-in for a slow synchronous brain step
            controller.wait_until_idle()
            self.assertFalse(output.active)
            self.assertEqual([event.active for event in output.events], [True, False])
            self.assertGreaterEqual(output.events[1].timestamp_s - output.events[0].timestamp_s, 0.03)
        finally:
            controller.close()


if __name__ == "__main__":
    unittest.main()
