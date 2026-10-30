"""Mock output and a nonblocking, fail-closed pulse controller."""

from dataclasses import dataclass
import math
import threading
import time
from typing import Callable, Protocol

from .interfaces import Output


@dataclass(frozen=True)
class OutputEvent:
    timestamp_s: float
    active: bool


class MockOutput:
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._lock = threading.Lock()
        self._active = False
        self._events: list[OutputEvent] = []

    def set_active(self, active: bool) -> None:
        with self._lock:
            active = bool(active)
            if active != self._active:
                self._active = active
                self._events.append(OutputEvent(self._clock(), active))

    @property
    def active(self) -> bool:
        with self._lock:
            return self._active

    @property
    def events(self) -> list[OutputEvent]:
        with self._lock:
            return list(self._events)


@dataclass(frozen=True)
class SafetyConfig:
    trigger_threshold: float = 0.5
    reset_threshold: float = 0.3
    pulse_duration_s: float = 0.250
    cooldown_s: float = 1.0

    def __post_init__(self) -> None:
        if not (0 <= self.reset_threshold < self.trigger_threshold <= 1):
            raise ValueError("thresholds must satisfy 0 <= reset < trigger <= 1")
        if not math.isfinite(self.pulse_duration_s) or self.pulse_duration_s <= 0:
            raise ValueError("pulse_duration_s must be finite and positive")
        if not math.isfinite(self.cooldown_s) or self.cooldown_s < 0:
            raise ValueError("cooldown_s must be finite and nonnegative")


class ScheduledCall(Protocol):
    def cancel(self) -> None: ...


class Scheduler(Protocol):
    def schedule(self, delay_s: float, callback: Callable[[], None]) -> ScheduledCall: ...


class ThreadScheduler:
    def schedule(self, delay_s: float, callback: Callable[[], None]) -> ScheduledCall:
        timer = threading.Timer(delay_s, callback)
        timer.daemon = True
        timer.start()
        return timer


class PulseController:
    """Pulse only on SNN output; a timer ends the pulse even during a slow step.

    Timing is based on a monotonic wall clock. Thread scheduling is not a
    real-time guarantee, and must be measured on the eventual hardware.
    """

    def __init__(self, output: Output, config: SafetyConfig | None = None, *,
                 clock: Callable[[], float] = time.monotonic,
                 scheduler: Scheduler | None = None) -> None:
        self.output = output
        self.config = config or SafetyConfig()
        self._clock = clock
        self._scheduler = scheduler or ThreadScheduler()
        self._lock = threading.RLock()
        self._idle = threading.Event()
        self._idle.set()
        self._armed = True
        self._active = False
        self._closed = False
        self._last_trigger: float | None = None
        self._timer: ScheduledCall | None = None
        self._timer_error: Exception | None = None
        self._generation = 0
        self.trigger_count = 0
        self.output.set_active(False)

    def _check_timer_error(self) -> None:
        if self._timer_error is not None:
            raise RuntimeError("failed to deactivate output after pulse") from self._timer_error

    def update(self, escape_magnitude: float) -> bool:
        try:
            if isinstance(escape_magnitude, bool):
                raise ValueError("boolean is not a motor magnitude")
            magnitude = float(escape_magnitude)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("escape_magnitude must be finite and in [0, 1]") from exc
        if not math.isfinite(magnitude) or not 0 <= magnitude <= 1:
            raise ValueError("escape_magnitude must be finite and in [0, 1]")
        with self._lock:
            self._check_timer_error()
            if self._closed:
                raise RuntimeError("pulse controller is closed")
            if magnitude < self.config.reset_threshold:
                self._armed = True
            now = self._clock()
            cooled = self._last_trigger is None or now - self._last_trigger >= self.config.cooldown_s
            if not (self._armed and not self._active and cooled and magnitude > self.config.trigger_threshold):
                return False
            self._armed = False
            self._last_trigger = now
            self._active = True
            self._idle.clear()
            self._generation += 1
            generation = self._generation
            try:
                self.output.set_active(True)
                self._timer = self._scheduler.schedule(
                    self.config.pulse_duration_s, lambda: self._end_pulse(generation)
                )
            except Exception:
                self._active = False
                self._idle.set()
                self.output.set_active(False)
                raise
            self.trigger_count += 1
            return True

    def _end_pulse(self, generation: int) -> None:
        with self._lock:
            if generation != self._generation or not self._active or self._closed:
                return
            try:
                self.output.set_active(False)
            except Exception as exc:
                self._timer_error = exc
            else:
                self._active = False
            finally:
                self._idle.set()

    def inhibit(self) -> None:
        """Turn off on unusable sensor input; require a later reset to re-arm."""
        with self._lock:
            self._check_timer_error()
            if self._closed:
                raise RuntimeError("pulse controller is closed")
            self._armed = False
            self._generation += 1
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            try:
                self.output.set_active(False)
            finally:
                self._active = False
                self._idle.set()

    def wait_until_idle(self, timeout_s: float | None = None) -> None:
        timeout = timeout_s if timeout_s is not None else self.config.pulse_duration_s + 2.0
        if not self._idle.wait(timeout):
            raise TimeoutError("output pulse did not finish in time")
        with self._lock:
            self._check_timer_error()

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._generation += 1
            if self._timer is not None:
                self._timer.cancel()
            try:
                self.output.set_active(False)
            finally:
                self._active = False
                self._idle.set()
