"""Backend interface.

A backend is a state machine with two methods and no I/O. It is stepped once
per frame and returns two motor drives in ``0..1`` plus a few diagnostics.
Anything that needs a clock, a socket or a file lives outside this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..vision import SensoryFrame


@dataclass
class BrainOutput:
    """Motor drives and diagnostics for one step."""

    left: float
    right: float
    escape: bool = False
    diagnostics: dict[str, float] = field(default_factory=dict)

    def clamped(self) -> "BrainOutput":
        self.left = min(max(self.left, 0.0), 1.0)
        self.right = min(max(self.right, 0.0), 1.0)
        return self


class BrainBackend(ABC):
    """Base class for the demonstrator backends."""

    name = "base"

    def __init__(self, cfg=None):
        self.cfg = cfg
        self.steps = 0

    @abstractmethod
    def reset(self) -> None:
        """Return to the initial state."""

    @abstractmethod
    def step(self, sensory: SensoryFrame, dt_ms: float) -> BrainOutput:
        """Advance one frame and return the drive for the motors."""

    def state(self) -> dict[str, float]:
        """Optional introspection for the journal."""
        return {}
