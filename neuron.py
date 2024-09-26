"""Single leaky integrate-and-fire neuron.

    tau_m * dV/dt = -(V - V_rest) + R * I(t)

V is the membrane potential, I(t) the input current for the step.
When V crosses v_th, the neuron emits a spike and V drops to v_reset.
"""


class Neuron:
    def __init__(self, v_rest=-65.0, v_th=-50.0, v_reset=-70.0, tau_m=20.0, dt=1.0):
        self.v = v_rest
        self.v_rest = v_rest
        self.v_th = v_th
        self.v_reset = v_reset
        self.tau_m = tau_m
        self.dt = dt

    def step(self, input_current):
        self.v += (self.dt / self.tau_m) * (-(self.v - self.v_rest) + input_current)
        spike = self.v >= self.v_th
        if spike:
            self.v = self.v_reset
        return spike
