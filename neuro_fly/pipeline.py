"""Connect sensor, SNN and protected output without GPIO dependencies."""

from dataclasses import asdict, dataclass
import math
from pathlib import Path
import platform
import sys
import time
from typing import Callable

from .interfaces import Brain, DistanceSensor
from .output import MockOutput, PulseController
from .sensor import ApproachEncoder


@dataclass(frozen=True)
class CycleResult:
    cycle_started_monotonic_s: float
    sample_timestamp_s: float | None
    distance_mm: float | None
    sample_usable: bool
    looming_strength: float
    escape_magnitude: float
    triggered: bool
    sensor_ms: float
    encoder_ms: float
    brain_ms: float
    output_ms: float
    cycle_ms: float


class Pipeline:
    def __init__(self, sensor: DistanceSensor, encoder: ApproachEncoder,
                 brain: Brain, controller: PulseController, *,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.sensor = sensor
        self.encoder = encoder
        self.brain = brain
        self.controller = controller
        self._clock = clock

    def step(self) -> CycleResult | None:
        """Process one sample; None means a finite recording has ended."""
        cycle_start = self._clock()
        try:
            started = self._clock()
            sample = self.sensor.read()
            sensor_ms = (self._clock() - started) * 1000.0
            if sample is None:
                return None
            started = self._clock()
            strength = self.encoder.update(sample)
            encoder_ms = (self._clock() - started) * 1000.0
            output_ms = 0.0
            if not self.encoder.sample_usable:
                # Stop an active pulse immediately when the sensor becomes
                # unusable. The SNN still receives zero to advance its state.
                started = self._clock()
                self.controller.inhibit()
                output_ms += (self._clock() - started) * 1000.0
            started = self._clock()
            result = self.brain.step(strength)
            brain_ms = (self._clock() - started) * 1000.0
            if isinstance(result, bool):
                raise ValueError("brain output must be a finite number in [0, 1]")
            magnitude = float(result)
            if not math.isfinite(magnitude) or not 0 <= magnitude <= 1:
                raise ValueError("brain output must be a finite number in [0, 1]")
            triggered = False
            if (self.encoder.sample_usable or
                    (self.encoder.sample_valid and magnitude < self.controller.config.reset_threshold)):
                started = self._clock()
                triggered = self.controller.update(magnitude)
                output_ms += (self._clock() - started) * 1000.0
            return CycleResult(
                cycle_start, _finite_or_none(sample.timestamp_s), _finite_or_none(sample.distance_mm),
                self.encoder.sample_usable, strength, magnitude, triggered,
                sensor_ms, encoder_ms, brain_ms, output_ms,
                (self._clock() - cycle_start) * 1000.0,
            )
        except BaseException:
            self.controller.close()
            raise


def _finite_or_none(value: object) -> float | None:
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def run_pipeline(pipeline: Pipeline, *, period_s: float = 0.02,
                 clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep) -> tuple[list[CycleResult], int]:
    """Run a finite recording, pacing at most to period_s without hiding overruns."""
    if not math.isfinite(period_s) or period_s <= 0:
        raise ValueError("period_s must be finite and positive")
    cycles: list[CycleResult] = []
    overruns = 0
    try:
        while True:
            started = clock()
            cycle = pipeline.step()
            if cycle is None:
                break
            cycles.append(cycle)
            elapsed = clock() - started
            if elapsed > period_s:
                overruns += 1
            else:
                sleep(period_s - elapsed)
        pipeline.controller.wait_until_idle()
    finally:
        pipeline.controller.close()
    return cycles, overruns


def _peak_rss_mib() -> float | None:
    try:
        import resource
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return value / (1024 * 1024 if sys.platform == "darwin" else 1024)
    except (ImportError, AttributeError, OSError):
        return None


def _cpu_model() -> str | None:
    if sys.platform.startswith("linux"):
        try:
            for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
                key, separator, value = line.partition(":")
                if separator and key.strip() in ("model name", "Hardware"):
                    return value.strip()
        except OSError:
            pass
    return platform.processor() or None


def make_report(*, scenario: str, brain: Brain, output: MockOutput,
                controller: PulseController, cycles: list[CycleResult],
                overruns: int, wall_s: float, cpu_s: float) -> dict:
    """Report synthetic software measurements; never claim physical latency."""
    events = output.events
    first_stimulus = next((c.cycle_started_monotonic_s for c in cycles if c.looming_strength > 0), None)
    first_trigger = next((event.timestamp_s for event in events if event.active), None)
    reaction_s = (first_trigger - first_stimulus
                  if first_trigger is not None and first_stimulus is not None else None)
    brain_steps = [cycle.brain_ms for cycle in cycles]
    return {
        "measurement_scope": "synthetic sensor and mock output; no physical hardware latency",
        "scenario": scenario,
        "sensor_timestamp_basis": "synthetic recording, 20 ms per sample",
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": _cpu_model(),
        "python": platform.python_version(),
        "backend": getattr(brain, "backend", None),
        "brian2_version": getattr(brain, "brian2_version", None),
        "numpy_version": getattr(brain, "numpy_version", None),
        "reference_commit": getattr(brain, "reference_commit", None),
        "connectome": asdict(brain.connectome) if hasattr(brain, "connectome") else None,
        "brain_initialization_s": getattr(brain, "initialization_s", None),
        "first_brain_step_ms": brain_steps[0] if brain_steps else None,
        "later_brain_step_mean_ms": (sum(brain_steps[1:]) / len(brain_steps[1:])
                                     if len(brain_steps) > 1 else None),
        "cython_cache_state": "unknown; first step and later steps reported separately",
        "step_simulated_ms": 20.0,
        "simulated_duration_s": len(cycles) * 0.020,
        "wall_duration_s": wall_s,
        "process_cpu_s": cpu_s,
        "peak_process_rss_mib": _peak_rss_mib(),
        "resource_scope": "current process only; compiler child processes excluded",
        "cycle_overruns": overruns,
        "trigger_count": controller.trigger_count,
        "non_approach_trigger_count": controller.trigger_count if scenario != "approach" else None,
        "synthetic_first_input_to_trigger_wall_s": reaction_s,
        "output_events": [asdict(event) for event in events],
        "cycles": [asdict(cycle) for cycle in cycles],
    }
