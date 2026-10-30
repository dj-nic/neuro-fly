"""Convert distance samples into a bounded approximation of looming input."""

from collections import deque
from dataclasses import dataclass
import math
from statistics import median

from .interfaces import DistanceSample


@dataclass(frozen=True)
class ApproachConfig:
    min_distance_mm: float = 50.0
    full_scale_rate_per_s: float = 1.0
    max_sample_gap_s: float = 0.5
    smoothing_alpha: float = 0.35
    median_window: int = 3

    def __post_init__(self) -> None:
        for name in ("min_distance_mm", "full_scale_rate_per_s", "max_sample_gap_s"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if not math.isfinite(self.smoothing_alpha) or not 0 < self.smoothing_alpha <= 1:
            raise ValueError("smoothing_alpha must be in (0, 1]")
        if not isinstance(self.median_window, int) or isinstance(self.median_window, bool) or self.median_window < 1:
            raise ValueError("median_window must be a positive integer")


class ApproachEncoder:
    """Estimate max(0, closing speed / distance), scaled to [0, 1].

    The constants are provisional software-demo settings, not a calibrated
    sensor or a physiological simulation of a fly eye.
    """

    def __init__(self, config: ApproachConfig | None = None) -> None:
        self.config = config or ApproachConfig()
        self._distances: deque[float] = deque(maxlen=self.config.median_window)
        self.reset()

    def reset(self) -> None:
        self._distances.clear()
        self._previous_distance: float | None = None
        self._previous_time: float | None = None
        self._strength = 0.0
        self.sample_usable = False
        self.sample_valid = False

    def _baseline(self, distance: float, timestamp: float, *, valid: bool = True) -> float:
        self.reset()
        self._distances.append(distance)
        self._previous_distance = distance
        self._previous_time = timestamp
        self.sample_valid = valid
        return 0.0

    def update(self, sample: DistanceSample) -> float:
        try:
            if not sample.valid or isinstance(sample.distance_mm, bool) or isinstance(sample.timestamp_s, bool):
                raise ValueError("invalid reading")
            distance = float(sample.distance_mm)  # type: ignore[arg-type]
            timestamp = float(sample.timestamp_s)
            if not math.isfinite(distance) or distance <= 0 or not math.isfinite(timestamp):
                raise ValueError("invalid reading")
        except (TypeError, ValueError, OverflowError):
            self.reset()
            return 0.0

        if self._previous_time is None:
            return self._baseline(distance, timestamp)
        dt = timestamp - self._previous_time
        if not math.isfinite(dt) or dt <= 0 or dt > self.config.max_sample_gap_s:
            return self._baseline(distance, timestamp, valid=False)

        self._distances.append(distance)
        filtered_distance = float(median(self._distances))
        closing_speed = max(0.0, (self._previous_distance - filtered_distance) / dt)
        rate = closing_speed / max(filtered_distance, self.config.min_distance_mm)
        target = min(1.0, rate / self.config.full_scale_rate_per_s)
        alpha = self.config.smoothing_alpha
        self._strength = min(1.0, max(0.0, alpha * target + (1.0 - alpha) * self._strength))
        self._previous_distance = filtered_distance
        self._previous_time = timestamp
        self.sample_usable = True
        self.sample_valid = True
        return self._strength


class MockDistanceSensor:
    """Finite, repeatable distance recordings; timestamps are synthetic, not wall time."""

    SCENARIOS = ("approach", "still", "receding", "jitter", "invalid", "far")

    def __init__(self, scenario: str = "approach", sample_period_s: float = 0.02) -> None:
        if scenario not in self.SCENARIOS:
            raise ValueError(f"unknown mock scenario: {scenario}")
        if not math.isfinite(sample_period_s) or sample_period_s <= 0:
            raise ValueError("sample_period_s must be finite and positive")
        self.scenario = scenario
        self.sample_period_s = sample_period_s
        self._index = 0
        self._samples = self._make_samples()

    def _make_samples(self) -> list[DistanceSample]:
        values: list[float | None] = []
        if self.scenario == "approach":
            distance = 2000.0
            values.extend([distance] * 5)
            # The recording has 20-ms sample timestamps. A sustained approach
            # follows a gradual ramp and is then followed by a stationary tail.
            for i in range(20):
                rate = 2.5 * (i + 1) / 20.0
                distance /= 1.0 + rate * self.sample_period_s
                values.append(distance)
            for _ in range(25):
                distance /= 1.0 + 2.5 * self.sample_period_s
                values.append(distance)
            values.extend([distance] * 10)
        elif self.scenario == "still":
            values = [1200.0] * 60
        elif self.scenario == "far":
            values = [5000.0] * 60
        elif self.scenario == "receding":
            values = [600.0 + i * 5.0 for i in range(60)]
        elif self.scenario == "jitter":
            values = [1200.0 + (-1.0, 0.0, 1.0, 0.0)[i % 4] for i in range(60)]
        else:
            values = [1200.0 if i % 3 == 0 else None for i in range(60)]
        return [
            DistanceSample(value, index * self.sample_period_s, value is not None)
            for index, value in enumerate(values)
        ]

    def read(self) -> DistanceSample | None:
        if self._index >= len(self._samples):
            return None
        sample = self._samples[self._index]
        self._index += 1
        return sample
