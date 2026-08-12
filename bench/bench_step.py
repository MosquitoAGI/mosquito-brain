"""Benchmark: step 20,000 LIF neurons for 1,000 steps.

Run: python3 bench/bench_step.py
"""
import time
import numpy as np

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neuron import LIFPopulation


def main():
    pop = LIFPopulation(size=20000)
    rng = np.random.default_rng(3)
    drive = rng.uniform(0.4, 1.2, size=20000) * 8.0
    pop.step(drive)

    t0 = time.perf_counter()
    total = 0
    for _ in range(1000):
        total += int(pop.step(drive).sum())
    dt = time.perf_counter() - t0
    print("neurons=20000 steps=1000 spikes=%d total=%.3fs per_step=%.2fms"
          % (total, dt, dt))


if __name__ == "__main__":
    main()
