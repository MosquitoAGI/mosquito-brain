"""Wire populations together with a synapse matrix."""
import numpy as np
from neuron import LIFPopulation
from synapse import SynapseMatrix


class Network:
    def __init__(self, sizes, seed=7):
        self.populations = [LIFPopulation(size=s) for s in sizes]
        self.matrices = {}
        rng = np.random.default_rng(seed)
        for i in range(len(sizes)):
            for j in range(len(sizes)):
                if i == j:
                    continue
                self.matrices[(i, j)] = SynapseMatrix(sizes[i], sizes[j], rng=rng)

    def step(self, external):
        spikes = [pop.step(drive) for pop, drive in zip(self.populations, external)]
        next_external = [np.zeros(pop.size) for pop in self.populations]
        for (src, dst), matrix in self.matrices.items():
            next_external[dst] += matrix.currents(spikes[src])
        self.last_spikes = spikes
        return [int(s.sum()) for s in spikes]
