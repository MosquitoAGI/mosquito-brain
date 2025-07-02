from neuron import LIFPopulation


def test_threshold_crossing():
    pop = LIFPopulation(size=1)
    fired = False
    for _ in range(50):
        if pop.step([12.0])[0]:
            fired = True
            break
    assert fired


def test_reset_after_spike():
    pop = LIFPopulation(size=1)
    for _ in range(50):
        if pop.step([12.0])[0]:
            assert pop.v[0] == pop.v_reset
            return
    raise AssertionError("never fired")


def test_refractory_blocks_immediate_respike():
    pop = LIFPopulation(size=1, refractory=5)
    pop.step([80.0])
    assert pop.refract_timer[0] >= 4
    assert not pop.step([80.0])[0]


def test_stats_shape():
    pop = LIFPopulation(size=8)
    stats = pop.stats()
    assert set(stats) == {"v_mean", "v_min", "v_max", "refractory"}
