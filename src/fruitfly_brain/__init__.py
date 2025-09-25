"""FruitFlyBrain — camera-to-robot bridge with a spiking neural backend.

The package is deliberately small and readable: an encoder that turns a camera
frame into a handful of sensory numbers, a pluggable brain backend that turns
those numbers into two motor drives, a decoder that shapes the drives into
commands a microcontroller can execute, and a strict UDP protocol between them.
"""

__version__ = "0.3.0"

__all__ = ["__version__"]
