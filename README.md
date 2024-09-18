<div align="center">

# FruitFlyBrain

**Camera to robot, with a small spiking backend in the middle.**

![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-79cce8?style=flat-square)
![Tests](https://img.shields.io/badge/tests-41_passing-38c172?style=flat-square)
[![License: MIT](https://img.shields.io/badge/License-MIT-60dfb3?style=flat-square)](LICENSE)

</div>

A camera looks at the world, a small neural model decides, two motors move. This
repository is the glue in between: an encoder that turns frames into a handful
of sensory numbers, a pluggable backend that turns those numbers into two motor
drives, a decoder that shapes them into commands a microcontroller will accept,
and a strict little UDP protocol for both directions.

Personal bench project. It runs on this desk before it runs anywhere else.

## What it does

- Runs locally with synthetic frames.
- Estimates motion in the left and right half of the field.
- Steps a backend of your choice: `mock` (8 activity groups) today, more later.
- Shapes two drives into motor commands with limits and a dead zone.
- Speaks JSON/UDP in both directions, validates every packet.

## Quick start

Requires Python 3.11+.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
fruitfly-brain --source mock --brain mock --frames 300
```

The default run lasts 300 frames, stays in dry-run mode, and prints the packets
it would send.

## Current limitations

- **No hardware validation.** Everything here has run against synthetic frames
  and a `NullTransport`.
- **The mock backend is a demonstrator.** Eight leaky activity groups, not
  anatomy.
- **UDP without authentication.**

## Repository structure

```text
src/fruitfly_brain/        CLI, config, encoder, decoder, protocol
tests/                     41 checks
```

## License

MIT — see [LICENSE](LICENSE).
