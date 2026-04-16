"""Synaptic connection matrix with optional conduction delays.

Positive weights are excitatory, negative weights are inhibitory.
When delays are enabled, contributions land in a small FIFO queue and are
released after 0..max_delay steps.
"""
import numpy as np


class SynapseMatrix:
    def __init__(self, pre_size, post_size, rng=None):
        rng = rng or np.random.default_rng(7)
        self.weights = rng.normal(0.0, 0.35, size=(post_size, pre_size))
        self.delays = np.zeros((post_size, pre_size), dtype=np.int32)
        self._queue = None
        self.last_current = np.zeros(post_size)

    def enable_delays(self, max_delay=3):
        rng = np.random.default_rng(11)
        self.delays = rng.integers(0, max_delay + 1, size=self.weights.shape)
        depth = int(self.delays.max()) + 1
        self._queue = [np.zeros(self.weights.shape[0]) for _ in range(depth)]

    @property
    def excitatory_count(self):
        return int((self.weights > 0).sum())

    @property
    def inhibitory_count(self):
        return int((self.weights < 0).sum())

    def currents(self, spikes):
        contrib = self.weights @ spikes.astype(np.float64)
        if self._queue is None:
            self.last_current = contrib
            return contrib
        delayed = self._queue.pop(0)
        self._queue.append(contrib)
        self.last_current = delayed
        return delayed

    def inhibit(self, pre, post, strength=1.0):
        self.weights[post, pre] = -abs(strength)

    def excite(self, pre, post, strength=1.0):
        self.weights[post, pre] = abs(strength)
