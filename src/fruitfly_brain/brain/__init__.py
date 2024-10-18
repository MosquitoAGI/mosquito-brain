"""Brain backends compatible with the bridge."""

from .base import BrainBackend, BrainOutput
from .connectome import ConnectomeBrain
from .mock import MockBrain

__all__ = ["BrainBackend", "BrainOutput", "ConnectomeBrain", "MockBrain", "make_brain"]


def make_brain(name: str, cfg=None):
    """Return a backend by name (the only place that knows the names)."""
    if name == "mock":
        return MockBrain(cfg)
    if name == "connectome":
        return ConnectomeBrain(cfg)
    raise ValueError("unknown brain backend: %r" % (name,))
