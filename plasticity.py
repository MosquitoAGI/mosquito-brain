"""Reward-modulated plasticity traces (experimental).

Each synapse keeps an eligibility trace that decays every step. When a reward
signal arrives, weights move along the trace. This is an engineering choice,
not a claim about biology.
"""
import numpy as np


class PlasticityTrace:
    def __init__(self, shape, decay=0.95, lr=0.01):
        self.trace = np.zeros(shape)
        self.decay = decay
        self.lr = lr

    def observe(self, pre_spikes, post_spikes):
        self.trace *= self.decay
        self.trace += np.outer(post_spikes.astype(float), pre_spikes.astype(float))

    def apply_reward(self, weights, reward):
        weights += self.lr * reward * self.trace
        np.clip(weights, -4.0, 4.0, out=weights)
        return weights
