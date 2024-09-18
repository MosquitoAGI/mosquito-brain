"""A single leaky integrator. No spikes yet."""


class Neuron:
    def __init__(self, v_rest=-65.0, tau_m=20.0, dt=1.0):
        self.v = v_rest
        self.v_rest = v_rest
        self.tau_m = tau_m
        self.dt = dt

    def step(self, input_current):
        self.v += (self.dt / self.tau_m) * (-(self.v - self.v_rest) + input_current)
        return self.v
