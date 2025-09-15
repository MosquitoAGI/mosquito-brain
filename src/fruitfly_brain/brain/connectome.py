"""Connectome backend — a fixed, hand-checked spiking network.

Twenty-six leaky integrate-and-fire neurons wired into a small fixed graph.
The graph is not learned and not scanned from a real insect: it is written out
below, one line per connection, so the whole model fits in your head.

    sensory (4)  ->  inter (16)  ->  motor pool (6: 3 left, 3 right)

Each sensory neuron receives a constant current proportional to one channel of
the encoder output (left motion, right motion, expansion, luminance). Motor
pools are read as spike rates normalised to the pool size.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..config import BrainConfig
from ..vision import SensoryFrame
from .base import BrainBackend, BrainOutput

# (presynaptic, postsynaptic, weight) — positive is excitatory.
# Three feed-forward layers plus two recurrent touches. A neuron needs a net
# input above roughly 1.9 to leave rest and fire, which is what the weights
# below are sized for (see docs/ARCHITECTURE.md).
CONNECTIONS: tuple[tuple[int, int, float], ...] = (
    # sensory -> layer 1
    (0, 4, 2.0), (2, 4, 1.2), (3, 4, 0.6),
    (0, 5, 1.2), (2, 5, 1.2),
    (1, 6, 2.0), (2, 6, 1.2), (3, 6, 0.6),
    (1, 7, 1.2), (2, 7, 1.2),
    (2, 8, 2.2), (2, 9, 2.2),
    (3, 10, 1.4), (2, 10, 0.8),
    (3, 11, 1.4), (2, 11, 0.8),
    # layer 1 -> layer 2
    (4, 12, 1.8), (5, 12, 1.8),
    (6, 13, 1.8), (7, 13, 1.8),
    (8, 14, 1.6), (9, 14, 1.6),
    (10, 15, 1.4), (11, 15, 1.4),
    # layer 2 -> motor pools
    (12, 16, 1.8), (14, 16, 0.8), (16, 17, 1.5),
    (13, 18, 1.8), (14, 18, 0.8), (18, 19, 1.5),
    (14, 20, 1.6), (14, 21, 1.6),
    # recurrent touches: a pool keeps its own driver warm
    (16, 12, 0.5), (18, 13, 0.5),
    # loom pool: the two neurons hand excitation back and forth
    (20, 21, 1.2), (21, 20, 1.2),
    # cross-inhibition: a strongly driven side suppresses the other
    (12, 18, -0.4), (13, 16, -0.4),
)

N_NEURONS = 26
SENSORY = (0, 1, 2, 3)
LEFT_POOL = (16, 17)
RIGHT_POOL = (18, 19)
LOOM_POOL = (20, 21)


@dataclass
class LifParams:
    v_rest: float = -65.0
    v_th: float = -50.0
    v_reset: float = -70.0
    tau_m: float = 20.0
    refractory_ms: float = 2.0
    gain: float = 8.0
    noise: float = 0.0
    seed: int = 7
    extra: dict = field(default_factory=dict)


class ConnectomeBrain(BrainBackend):
    name = "connectome"

    def __init__(self, cfg: BrainConfig | None = None):
        cfg = cfg or BrainConfig()
        super().__init__(cfg)
        self.p = LifParams(seed=cfg.seed)
        self.reset()

    def reset(self) -> None:
        self.v = np.full(N_NEURONS, self.p.v_rest, dtype=np.float64)
        self.refractory_until = np.full(N_NEURONS, -1e9, dtype=np.float64)
        self.last_spike = np.zeros(N_NEURONS, dtype=bool)
        self.t = 0.0
        self.spike_counts = np.zeros(N_NEURONS, dtype=np.float64)
        self.history = np.zeros((READOUT_WINDOW, N_NEURONS), dtype=bool)
        self.hist_index = 0
        self.steps = 0
        self._rng = np.random.default_rng(self.p.seed)
        self._w_in = np.zeros((N_NEURONS, len(SENSORY)), dtype=np.float64)
        for pre, post, w in CONNECTIONS:
            if pre in SENSORY:
                self._w_in[post, SENSORY.index(pre)] += w

    def state(self) -> dict[str, float]:
        return {
            "mean_v": float(self.v.mean()),
            "left_rate": self._rate(LEFT_POOL),
            "right_rate": self._rate(RIGHT_POOL),
            "loom_rate": self._rate(LOOM_POOL),
            "spikes": float(self.spike_counts.sum()),
        }

    def _rate(self, idx) -> float:
        """Firing rate of a pool over the run so far."""
        if self.steps == 0:
            return 0.0
        return float(self.spike_counts[list(idx)].sum() / (self.steps * len(idx)))

    def _drive(self, rate: float) -> float:
        """Firing rate to drive, scaled to the pool."""
        return float(np.clip(rate * 3.0, 0.0, 1.0))

    # ------------------------------------------------------------------- step
    def step(self, sensory: SensoryFrame, dt_ms: float) -> BrainOutput:
        dt = max(dt_ms, 1.0)
        self.t += dt
        self.steps += 1

        currents = np.zeros(N_NEURONS, dtype=np.float64)
        drive = np.clip(
            np.array(
                [
                    sensory.left,
                    sensory.right,
                    sensory.expansion,
                    (sensory.luminance - 0.5),
                ],
                dtype=np.float64,
            ),
            -8.0,
            8.0,
        )
        currents += self._w_in @ drive
        for pre, post, w in CONNECTIONS:
            if pre in SENSORY:
                continue
            if self.last_spike[pre]:
                currents[post] += w
        if self.p.noise:
            currents += self._rng.normal(0.0, self.p.noise, size=N_NEURONS)

        active = self.t >= self.refractory_until
        dv = (-(self.v - self.p.v_rest) + self.p.gain * currents) * (dt / self.p.tau_m)
        self.v = np.where(active, self.v + dv, self.v)

        fired = active & (self.v >= self.p.v_th)
        self.last_spike = fired
        self.history[self.hist_index] = fired
        self.hist_index = (self.hist_index + 1) % READOUT_WINDOW
        if np.any(fired):
            self.v = np.where(fired, self.p.v_reset, self.v)
            self.refractory_until = np.where(
                fired, self.t + self.p.refractory_ms, self.refractory_until
            )
            self.spike_counts += fired.astype(np.float64)

        left = self._drive(self._rate(LEFT_POOL))
        right = self._drive(self._rate(RIGHT_POOL))
        loom = max(sensory.expansion, 0.0)
        # The loom pool is what actually declares an escape: a single frame of
        # expansion is not enough, the pool has to be driven for a few frames.
        escape = self._rate(LOOM_POOL) > 0.2 or loom >= float(self.cfg.escape_threshold)

        return BrainOutput(
            left=left,
            right=right,
            escape=escape,
            diagnostics={
                "spikes": float(self.spike_counts.sum()),
                "loom": loom,
                "loom_rate": self._rate(LOOM_POOL),
            },
        ).clamped()
