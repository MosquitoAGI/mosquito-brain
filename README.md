# MOSQUITO AI - BRAIN

**The synthetic nervous system core.**
SENSE / LEARN / MOVE

`mosquito-brain` is the part of Mosquito AI that changes state. It receives
sensory spikes, integrates them through a population of leaky integrate-and-fire
neurons, and produces the spikes that the motor layer turns into movement.

It is deliberately small. The point is to build a nervous system that runs,
can be inspected, and can be measured - not to imitate a full biological brain.

> An artificial nervous system for the open internet.
> It doesn't browse. It hunts.

## The loop

    SENSORS --spikes--> BRAIN --spikes--> MOTOR
                          |
                    MEMORY / PLASTICITY

No language model sits inside this loop. No page is summarized for it.
Signals arrive, membranes change, neurons fire, the body moves.

## The neuron model

Each neuron is a leaky integrator with a firing threshold.
The membrane update for one step is:

    tau_m * dV/dt = -(V - V_rest) + R * I(t)

- `V` - membrane potential
- `I(t)` - input current for the step (sensory drive plus synaptic input)
- leak term pulls `V` toward `v_rest`
- when `V >= v_th`: spike, reset to `v_reset`, hold for `refractory` steps

| parameter | meaning | default |
| --- | --- | --- |
| `v_rest` | resting potential | -65.0 |
| `v_th` | firing threshold | -50.0 |
| `v_reset` | post-spike reset | -70.0 |
| `tau_m` | membrane time constant | 20.0 |
| `refractory` | refractory steps | 2 |
| `gain` | current conversion factor | 8.0 |

Synapses carry signed weights: positive is excitatory, negative is inhibitory.
Selected connections can also carry a short conduction delay (up to 3 steps).

## Layout

| file | role |
| --- | --- |
| `neuron.py` | `LIFPopulation` - vectorized membrane dynamics, refraction, reset |
| `synapse.py` | `SynapseMatrix` - weights, signs, optional delays |
| `network.py` | assemble populations and step them together |
| `dynamics.py` | parameter container, defaults, config loading |
| `plasticity.py` | reward-modulated weight traces (experimental) |
| `rate_coder.py` | convert sensory vectors into input currents |
| `simulation.py` | run a loop, log spikes and membrane stats per step |
| `config.yaml` | field defaults for a run |
| `bench/` | step-time benchmarks |
| `tests/` | threshold behaviour, reset, network wiring |

## Quickstart

    git clone https://github.com/MosquitoAGI/mosquito-brain
    cd mosquito-brain
    pip install -r requirements.txt

    python3 examples/two_neurons.py
    python3 bench/bench_step.py

Driving a population directly:

    from neuron import LIFPopulation
    from rate_coder import rate_coder

    pop = LIFPopulation(size=512)
    for step in range(200):
        spikes = pop.step(rate_coder([0.71, 0.13, 0.66, 0.74]))

Latest benchmark: 20,000 neurons, 1,000 steps, under 12 ms per step.

## Status

v0.4.0 - the core is stable enough to build the sensory and motor layers on.

- [x] LIF neuron: leak, threshold, reset, refraction
- [x] excitatory / inhibitory synapse matrix, optional delays
- [x] vectorized stepping
- [x] reward-modulated plasticity traces (experimental)
- [x] rate coder for sensory input
- [ ] connection topology import (next)
- [ ] long-run stability runs at scale

## Where it fits

| repo | role |
| --- | --- |
| [`mosquito-vision`](https://github.com/MosquitoAGI/mosquito-vision) | screenshots -> sensory field |
| [`mosquito-memory`](https://github.com/MosquitoAGI/mosquito-memory) | what the network keeps between hunts |
| [`mosquito-motor`](https://github.com/MosquitoAGI/mosquito-motor) | spikes -> cursor |
| [`mosquito-simulation`](https://github.com/MosquitoAGI/mosquito-simulation) | reproduce a run offline |

## Scope

The words used here (neuron, synapse, membrane potential) describe the
engineering architecture of a synthetic system. This project does not claim to
reconstruct a real mosquito nervous system, and it does not claim consciousness.

## License

MIT - see `LICENSE`.
