"""Vectorized leaky integrate-and-fire neuron population.

    tau_m * dV/dt = -(V - V_rest) + R * I(t)

A population keeps membrane potentials, refractory timers and a boolean
spike mask. All updates are numpy operations over the full array.
"""
import numpy as np


class LIFPopulation:
    def __init__(self, size, v_rest=-65.0, v_th=-50.0, v_reset=-70.0,
                 tau_m=20.0, refractory=2, dt=1.0):
        self.size = size
        self.v_rest = v_rest
        self.v_th = v_th
        self.v_reset = v_reset
        self.tau_m = tau_m
        self.refractory = refractory
        self.dt = dt
        self.v = np.full(size, v_rest, dtype=np.float64)
        self.refract_timer = np.zeros(size, dtype=np.int32)

    def step(self, input_current):
        """Advance one timestep. Returns a boolean spike mask."""
        input_current = np.asarray(input_current, dtype=np.float64)
        active = self.refract_timer == 0
        leak = -(self.v - self.v_rest)
        self.v[active] += (self.dt / self.tau_m) * (leak[active] + input_current[active])
        crossed = active & (self.v >= self.v_th)
        # clamp the membrane before extending the refractory window;
        # without this, a spike re-triggers on the following step when the
        # drive current stays high.
        self.v[crossed] = self.v_reset
        self.v[~active] = np.maximum(self.v[~active], self.v_reset)
        self.refract_timer[crossed] = self.refractory
        self.refract_timer = np.maximum(self.refract_timer - 1, 0)
        return crossed

    def reset(self):
        self.v.fill(self.v_rest)
        self.refract_timer.fill(0)

    def stats(self):
        return {
            "v_mean": float(self.v.mean()),
            "v_min": float(self.v.min()),
            "v_max": float(self.v.max()),
            "refractory": int((self.refract_timer > 0).sum()),
        }
