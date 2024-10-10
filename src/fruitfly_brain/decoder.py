"""Spikes become numbers a motor driver can execute.

The decoder is the only component that knows about limits, inversion and
smoothing. It also owns the timeout rule: if nobody calls ``update`` for
``command_timeout_ms``, ``read`` returns zero. That rule is the reason the
firmware has its own watchdog as well — a Python process that hangs cannot run
code that says "stop", no matter what this class promises.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import MotorConfig


@dataclass
class Command:
    left: float = 0.0
    right: float = 0.0
    emergency_stop: bool = False
    stale: bool = False
    reason: str = "init"

    def as_pair(self) -> tuple[float, float]:
        return (self.left, self.right)


class MotorDecoder:
    def __init__(self, cfg: MotorConfig | None = None):
        self.cfg = cfg or MotorConfig()
        self.cfg.validate()
        self._target = (0.0, 0.0)
        self._last_update: float | None = None
        self._estop = False
        self.escapes = 0

    # ------------------------------------------------------------------ shaping
    def _shape(self, drive: float, invert: bool) -> float:
        value = drive * self.cfg.max_command
        if invert:
            value = -value
        if abs(value) < self.cfg.dead_zone:
            return 0.0
        return max(-self.cfg.max_command, min(self.cfg.max_command, value))

    def _smooth(self, current: float, target: float) -> float:
        a = self.cfg.smoothing
        return current + (1.0 - a) * (target - current)

    def emergency_stop(self, now_ms: float | None = None) -> Command:
        """Immediate stop — bypasses smoothing entirely."""
        self._target = (0.0, 0.0)
        self._estop = True
        self._last_update = now_ms if now_ms is not None else self._last_update
        return Command(0.0, 0.0, emergency_stop=True, reason="estop")

    def clear_emergency(self) -> None:
        self._estop = False

    def zero_now(self, now_ms: float) -> None:
        """Force the shaped state to zero without latching the e-stop.

        Used by the controller when telemetry goes quiet: the robot is told to
        stop *and* the smoother is emptied, so the next real command ramps up
        from zero instead of from a stale value.
        """
        self._target = (0.0, 0.0)
        self._last_update = now_ms

    # ------------------------------------------------------------------- update
    def update(self, left: float, right: float, escape: bool, now_ms: float) -> Command:
        if not (0.0 <= left <= 1.0 and 0.0 <= right <= 1.0):
            raise ValueError("drives must be in 0..1")
        if self._estop:
            return Command(0.0, 0.0, emergency_stop=True, reason="estop")

        target_left = self._shape(left, self.cfg.invert_left)
        target_right = self._shape(right, self.cfg.invert_right)
        reason = "track"
        if escape:
            self.escapes += 1
            target_left = self.cfg.max_command * (-1.0 if self.cfg.invert_left else 1.0)
            target_right = self.cfg.max_command * (-1.0 if self.cfg.invert_right else 1.0)
            reason = "escape"

        cur_left, cur_right = self._target
        cur_left = self._smooth(cur_left, target_left)
        cur_right = self._smooth(cur_right, target_right)
        self._target = (cur_left, cur_right)
        self._last_update = now_ms

        if escape:
            # an escape bypasses smoothing: the shape is already at the limit
            cur_left, cur_right = target_left, target_right
            self._target = (cur_left, cur_right)

        return Command(cur_left, cur_right, emergency_stop=False, reason=reason)

    # --------------------------------------------------------------------- read
    def read(self, now_ms: float) -> Command:
        if self._estop:
            return Command(0.0, 0.0, emergency_stop=True, reason="estop")
        if self._last_update is None:
            return Command(0.0, 0.0, stale=True, reason="never-updated")
        if now_ms - self._last_update > self.cfg.command_timeout_ms:
            return Command(0.0, 0.0, stale=True, reason="timeout")
        return Command(self._target[0], self._target[1], reason="hold")
