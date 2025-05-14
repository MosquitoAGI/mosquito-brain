"""Run a network for a number of steps and log what happens."""
from network import Network


class Simulation:
    def __init__(self, network, steps=500, log_every=10):
        self.network = network
        self.steps = steps
        self.log_every = log_every

    def run(self, drive):
        log = []
        for step in range(self.steps):
            spikes = self.network.step(drive(step))
            if step % self.log_every == 0:
                log.append({"step": step, "spikes": spikes})
        self.log = log
        return log


def constant_drive(value):
    return lambda step: value
