# mosquito-brain

The nervous system core of Mosquito AI — a small, inspectable spiking network
built from leaky integrate-and-fire neurons.

It is not an LLM wrapper. Nothing in this repository calls a language model.
The loop is: signals in, membrane dynamics, spikes out.

    SENSORS --spikes--> BRAIN --spikes--> MOTOR

## The neuron model

    tau_m * dV/dt = -(V - V_rest) + R * I(t)

A neuron integrates its input current, leaks toward rest, and emits a spike
when the membrane potential crosses the threshold. After a spike the membrane
resets and the neuron is held for a refractory window.

| parameter | meaning | default |
| --- | --- | --- |
| `v_rest` | resting potential | -65.0 |
| `v_th` | firing threshold | -50.0 |
| `v_reset` | post-spike reset | -70.0 |
| `tau_m` | membrane time constant | 20.0 |
| `refractory` | refractory steps | 2 |

## Layout

| file | role |
| --- | --- |
| `neuron.py` | LIF neuron population |
| `synapse.py` | signed connection weights |
| `network.py` | wire populations together |
| `dynamics.py` | shared parameters |
| `simulation.py` | run a loop and log it |

## Quickstart

    git clone https://github.com/MosquitoAGI/mosquito-brain
    cd mosquito-brain
    pip install -r requirements.txt
    python3 examples/two_neurons.py

## Status

v0.2.0 — neuron, synapse and network are under test. Plasticity is a stub.

Part of the Mosquito AI project.
