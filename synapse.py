"""Synapses: signed weights between two neurons.

Positive weight = excitatory, negative weight = inhibitory.
"""


class Synapse:
    def __init__(self, weight=0.5, delay=0):
        if weight == 0:
            raise ValueError("weight must be non-zero")
        self.weight = weight
        self.delay = delay

    @property
    def excitatory(self):
        return self.weight > 0

    def current(self, spiked):
        return self.weight * 8.0 if spiked else 0.0
