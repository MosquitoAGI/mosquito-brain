import numpy as np

from fruitfly_brain.brain import ConnectomeBrain, MockBrain, make_brain
from fruitfly_brain.config import BrainConfig
from fruitfly_brain.vision import SensoryFrame


def sensory(left=0.0, right=0.0, expansion=0.0, luminance=0.5):
    return SensoryFrame(left, right, expansion, luminance)


def test_mock_reflex_is_contralateral():
    brain = MockBrain(BrainConfig())
    for _ in range(40):
        out = brain.step(sensory(right=4.0), 33.0)
    assert out.left > out.right


def test_mock_drives_stay_bounded():
    brain = MockBrain(BrainConfig())
    out = brain.step(sensory(left=8.0, right=8.0, expansion=4.0), 33.0)
    assert 0.0 <= out.left <= 1.0
    assert 0.0 <= out.right <= 1.0
    assert set(out.diagnostics) == {"arousal", "turn_bias", "fatigue"}


def test_mock_escape_on_looming():
    brain = MockBrain(BrainConfig(escape_threshold=0.5))
    for _ in range(30):
        out = brain.step(sensory(expansion=0.9), 33.0)
    assert out.escape is True
    assert out.left > 0.5


def test_mock_state_has_labels():
    brain = MockBrain()
    state = brain.state()
    assert "left_motion" in state and len(state) == 8


def test_connectome_is_deterministic():
    a = ConnectomeBrain(BrainConfig(seed=11))
    b = ConnectomeBrain(BrainConfig(seed=11))
    rng = np.random.default_rng(0)
    for _ in range(120):
        frame = sensory(
            left=float(rng.random() * 3),
            right=float(rng.random() * 3),
            expansion=float(rng.random()),
        )
        out_a = a.step(frame, 33.0)
        out_b = b.step(frame, 33.0)
    assert np.allclose(a.spike_counts, b.spike_counts)
    assert out_a.left == out_b.left and out_a.right == out_b.right


def test_connectome_responds_to_input():
    brain = ConnectomeBrain(BrainConfig(seed=3))
    quiet = brain.state()
    for _ in range(200):
        out = brain.step(sensory(left=3.5, right=3.5, expansion=1.0), 33.0)
    assert brain.state()["spikes"] > 0
    assert out.left + out.right > 0
    assert quiet["spikes"] == 0.0


def test_connectome_left_input_drives_left_pool():
    brain = ConnectomeBrain(BrainConfig(seed=5))
    for _ in range(60):
        out = brain.step(sensory(left=3.6, right=0.0), 33.0)
    assert out.left > out.right


def test_connectome_escape_on_sustained_expansion():
    brain = ConnectomeBrain(BrainConfig(seed=5, escape_threshold=5.0))
    for _ in range(30):
        out = brain.step(sensory(expansion=1.0), 33.0)
    assert out.escape is True
    assert out.diagnostics["loom_rate"] > 0.2


def test_connectome_tracks_real_encoder_input():
    """Regression: the network must not be silent on real encoder output.

    The first version of this backend scaled its input assuming hand-written
    sensory values; fed the actual encoder it produced zero drive on every
    frame. This test runs the synthetic camera through the encoder and asserts
    that the pools move.
    """
    from fruitfly_brain.main import MockCamera
    from fruitfly_brain.vision import Encoder

    brain = ConnectomeBrain(BrainConfig(seed=7))
    encoder = Encoder()
    camera = MockCamera(320, 240)
    moving = 0
    peak = 0.0
    for i in range(150):
        reading = encoder.encode(camera.read())
        out = brain.step(reading, 33.0)
        peak = max(peak, out.left, out.right)
        moving += 1 if (out.left + out.right) > 0 else 0
    assert moving > 30, "the network produced drive on only %d frames" % moving
    assert peak > 0.2, "peak drive was %.3f" % peak


def test_connectome_reset_clears():
    brain = ConnectomeBrain()
    for _ in range(50):
        brain.step(sensory(left=4.0, right=4.0), 33.0)
    brain.reset()
    assert brain.spike_counts.sum() == 0.0
    assert brain.steps == 0


def test_make_brain_dispatch():
    assert isinstance(make_brain("mock", BrainConfig()), MockBrain)
    assert isinstance(make_brain("connectome", BrainConfig()), ConnectomeBrain)
