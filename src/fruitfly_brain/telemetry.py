"""Robot state as the bridge sees it.

Telemetry is advisory. It never feeds the control loop directly — it decides
whether the robot is answering at all, which is what the stop-on-silence rule
in the controller needs.
"""

from __future__ import annotations

from dataclasses import dataclass

from .protocol import Telemetry


@dataclass
class TelemetryState:
    last: Telemetry | None = None
    last_seen_ms: float | None = None
    received: int = 0
    rejected: int = 0

    def observe(self, packet: Telemetry, now_ms: float) -> None:
        self.last = packet
        self.last_seen_ms = now_ms
        self.received += 1

    def reject(self) -> None:
        self.rejected += 1

    def age_ms(self, now_ms: float) -> float | None:
        if self.last_seen_ms is None:
            return None
        return now_ms - self.last_seen_ms

    def is_stale(self, now_ms: float, timeout_ms: float) -> bool:
        age = self.age_ms(now_ms)
        if age is None:
            return True
        return age > timeout_ms

    def summary(self) -> str:
        if self.last is None:
            return "telemetry: none"
        return "telemetry: gyro=%.2f accel=%.2f l/r=%.1f/%.1f" % (
            self.last.gyro[0],
            self.last.accel[2],
            self.last.left_speed,
            self.last.right_speed,
        )
