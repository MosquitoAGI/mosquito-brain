"""Shared dynamics parameters, defaults and config loading."""
from dataclasses import dataclass, fields


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


def load_params(path):
    """Load a flat key: value file. Unknown keys are rejected."""
    known = {f.name: f.type for f in fields(Dynamics)}
    params = {}
    with open(path) as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            key, _, value = line.partition(":")
            key = key.strip()
            if key not in known:
                raise ValueError("unknown parameter: %s" % key)
            params[key] = float(value.strip())
    return Dynamics(**params).validate()


CONFIG_EXAMPLE = '''"""brain defaults for a run."""

tau_m: 20.0
refractory: 2
gain: 8.0
'''
