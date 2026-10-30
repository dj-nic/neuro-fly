"""Interfaces shared by real and simulated devices.

Sample timestamps are monotonic seconds within one sensor clock. They need not
equal wall-clock time: a recorded/mock sequence may have its own timeline.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DistanceSample:
    distance_mm: float | None
    timestamp_s: float
    valid: bool = True


class DistanceSensor(Protocol):
    def read(self) -> DistanceSample | None:
        """Return the next sample, or None when a finite recording ends."""
        ...


class Brain(Protocol):
    def step(self, looming_strength: float) -> float:
        """Advance the neural model by 20 simulated ms and return its output."""
        ...


class Output(Protocol):
    def set_active(self, active: bool) -> None:
        """Change the physical or simulated output state."""
        ...
