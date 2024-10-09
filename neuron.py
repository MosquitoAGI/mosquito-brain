"""Single leaky integrate-and-fire neuron with a refractory window."""


class Neuron:
    def __init__(self, v_rest=-65.0, v_th=-50.0, v_reset=-70.0, tau_m=20.0,
                 refractory=2, dt=1.0):
        self.v = v_rest
        self.v_rest = v_rest
        self.v_th = v_th
        self.v_reset = v_reset
        self.tau_m = tau_m
        self.refractory = refractory
        self.dt = dt
        self.timer = 0

    def step(self, input_current):
        if self.timer > 0:
            self.timer -= 1
            return False
        self.v += (self.dt / self.tau_m) * (-(self.v - self.v_rest) + input_current)
        if self.v >= self.v_th:
            self.v = self.v_reset
            self.timer = self.refractory
            return True
        return False
