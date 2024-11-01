"""Mock backend — the default.

Eight bounded state values that move toward sensory-driven targets with an
exponential leak. Contralateral motion excites the opposite motor group, the
same way a turning reflex works, and the expansion cue feeds a slow arousal
term that raises both drives when something approaches the camera.

It is not a brain. It is a reproducible stand-in that behaves plausibly on a
bench, so the rest of the bridge can be developed and measured without a
connectome file on disk.
"""

from __future__ import annotations

import math

from ..config import BrainConfig
from ..vision import SensoryFrame
from .base import BrainBackend, BrainOutput

_LABELS = (
    "left_motion",
    "right_motion",
    "loom",
    "left_drive",
    "right_drive",
    "arousal",
    "turn_bias",
    "fatigue",
)


class MockBrain(BrainBackend):
    name = "mock"

    def __init__(self, cfg: BrainConfig | None = None):
        super().__init__(cfg or BrainConfig())
        self.reset()

    def reset(self) -> None:
        self.state_vector = [0.0] * len(_LABELS)
        self.steps = 0

    def state(self) -> dict[str, float]:
        return dict(zip(_LABELS, self.state_vector))

    def _approach(self, idx: int, target: float, alpha: float) -> float:
        cur = self.state_vector[idx]
        nxt = cur + alpha * (target - cur)
        self.state_vector[idx] = nxt
        return nxt

    def step(self, sensory: SensoryFrame, dt_ms: float) -> BrainOutput:
        cfg: BrainConfig = self.cfg  # type: ignore[assignment]
        self.steps += 1
        dt = max(dt_ms, 1.0)

        # exponential leak toward the sensory reading
        alpha = 1.0 - math.exp(-dt / max(cfg.leak_ms, 1.0))
        left_motion = self._approach(0, min(sensory.left, 4.0) / 4.0, alpha)
        right_motion = self._approach(1, min(sensory.right, 4.0) / 4.0, alpha)
        loom = self._approach(2, max(sensory.expansion, 0.0), alpha * 0.6)

        arousal = self._approach(5, 0.35 * (left_motion + right_motion) + 0.6 * loom, alpha * 0.5)
        turn = self._approach(6, right_motion - left_motion, alpha * 0.8)
        fatigue = self._approach(7, 0.25 * (left_motion + right_motion), alpha * 0.15)

        # contralateral reflex: motion on the right excites the left drive
        drive_left = self._approach(3, min(1.0, 0.25 + right_motion + 0.5 * arousal), alpha)
        drive_right = self._approach(4, min(1.0, 0.25 + left_motion + 0.5 * arousal), alpha)

        damp = max(0.0, 1.0 - 0.6 * fatigue)
        escape = loom >= cfg.escape_threshold
        if escape:
            drive_left = max(drive_left, 0.9)
            drive_right = max(drive_right, 0.9)

        return BrainOutput(
            left=drive_left * damp,
            right=drive_right * damp,
            escape=escape,
            diagnostics={"arousal": arousal, "turn_bias": turn, "fatigue": fatigue},
        ).clamped()
