"""Turn a sensory vector into input currents for the network."""
import numpy as np


def rate_coder(values, scale=10.0):
    v = np.asarray(values, dtype=np.float64)
    v = np.clip(v, 0.0, 1.0)
    return v * scale


def expand(values, repeats=8):
    """Broadcast each sensory value across a small group of input neurons."""
    return np.repeat(rate_coder(values), repeats)
