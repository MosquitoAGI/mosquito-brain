import numpy as np
from network import Network
from synapse import SynapseMatrix


def test_matrix_signs():
    m = SynapseMatrix(4, 4)
    m.excite(0, 1, 1.0)
    m.inhibit(0, 2, 1.0)
    assert m.weights[1, 0] == 1.0
    assert m.weights[2, 0] == -1.0
    assert m.excitatory_count >= 1
    assert m.inhibitory_count >= 1


def test_matrix_rest():
    sizes = [4, 4]
    net = Network(sizes)
    out = net.step([np.zeros(4), np.zeros(4)])
    assert out == [0, 0]


def test_currents_follow_spikes():
    m = SynapseMatrix(2, 2)
    m.weights[:] = 0.0
    m.excite(0, 1, 1.0)
    spikes = np.array([True, False])
    currents = m.currents(spikes)
    assert currents[1] == 1.0


def test_single_neuron_network_smoke():
    net = Network([3, 3], seed=1)
    rng = np.random.default_rng(2)
    for _ in range(20):
        net.step([rng.uniform(0, 8, 3), rng.uniform(0, 8, 3)])
