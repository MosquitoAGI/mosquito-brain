"""Wire neurons together into a small network."""
from neuron import Neuron
from synapse import Synapse


class Network:
    def __init__(self):
        self.neurons = []
        self.connections = {}

    def add_neuron(self, **kwargs):
        self.neurons.append(Neuron(**kwargs))
        return len(self.neurons) - 1

    def connect(self, pre, post, weight=0.5, delay=0):
        self.connections[(pre, post)] = Synapse(weight=weight, delay=delay)

    def step(self, currents):
        drive = dict(currents)
        for (pre, post), syn in self.connections.items():
            if self.last_spikes and pre in self.last_spikes:
                drive[post] = drive.get(post, 0.0) + syn.current(True)

        self.last_spikes = set()
        for idx, neuron in enumerate(self.neurons):
            if neuron.step(drive.get(idx, 0.0)):
                self.last_spikes.add(idx)
        return sorted(self.last_spikes)

    last_spikes = set()
