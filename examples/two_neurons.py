"""Two neurons, one excitatory connection. Run:

    python3 examples/two_neurons.py
"""
import numpy as np

from neuron import LIFPopulation
from synapse import SynapseMatrix

pop = LIFPopulation(size=2, refractory=2)
syn = SynapseMatrix(2, 2)
syn.weights[:] = 0.0
syn.excite(0, 1, 1.2)

drive = np.array([11.0, 4.0])

total = 0
for step in range(120):
    spikes = pop.step(drive)
    syn.currents(spikes)
    total += int(spikes.sum())
    if step % 20 == 0:
        print("step=%3d spikes=%s v=%s" % (step, spikes.astype(int), np.round(pop.v, 1)))

print("total spikes over 120 steps: %d" % total)
