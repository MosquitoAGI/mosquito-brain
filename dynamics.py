"""Shared dynamics parameters and defaults."""
from dataclasses import dataclass


@dataclass
class Dynamics:
    v_rest: float = -65.0
    v_th: float = -50.0
    v_reset: float = -70.0
    tau_m: float = 20.0
    refractory: int = 2
    dt: float = 1.0
    gain: float = 8.0

    def validate(self):
        if not (self.v_reset <= self.v_rest < self.v_th):
            raise ValueError("expected v_reset <= v_rest < v_th")
        if self.tau_m <= 0:
            raise ValueError("tau_m must be positive")
        return self
