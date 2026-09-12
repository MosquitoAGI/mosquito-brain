# Changelog

All notable changes to this module. Dates in YYYY-MM-DD.

## 0.4.0 — 2026-09-12
- rate coder: sensory vectors to input currents
- step benchmark for 20k neurons
- readme refresh: the loop, the model, the status

## 0.3.0 — 2026-06-10
- config file support (config.yaml)
- synapse conduction delays up to 3 steps
- fix: clamp membrane during refraction to stop re-triggering

## 0.2.0 — 2026-01-14
- vectorized population updates (numpy) - 20k neurons step in milliseconds
- reward-modulated plasticity traces, experimental
- two-neuron example

## 0.1.0 — 2025-07-02
- leaky integrate-and-fire neuron with threshold, reset and refraction
- first synapse model with signed weights
- small network wiring helper
- tests cover threshold crossing and reset behaviour

