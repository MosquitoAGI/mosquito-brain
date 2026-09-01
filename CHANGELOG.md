# Changelog

All notable changes to this project are recorded here. Dates live in the
build log (docs/LOG.md); versions live here.

## [0.4.0]

- Added `brain.input_gain` after the connectome backend measured silent on real
  encoder output; the default (1.5) is the value chosen from those measurements.
- Fixed the loom pool latching on: the escape flag stayed set for minutes after
  a single approach because two of its neurons excited each other.
- Added `brain.escape_threshold: 0.45`, measured against the synthetic approach.
- The synthetic camera now sweeps exactly one full cycle every 150 frames.
- Replaced the flow-based approach cue with covered-area growth after the
  validation run showed the wrong sign on synthetic blobs.
- Added `docs/VALIDATION.md` with the measurements.
- Added per-reason commands (`track`, `escape`, `telemetry-timeout`) to the
  journal.

## [0.3.0]

- Added the `connectome` backend: 26 hand-wired neurons, three feed-forward
  layers, cross-inhibition between the motor pools.
- Motor drives are now rates normalised per pool instead of raw spike counts.
- Added `--brain` to the CLI.

## [0.2.0]

- Added the UDP transport and the stop-on-silent-telemetry rule.
- Added `SequenceGate`; duplicate and out-of-order telemetry is now dropped and
  counted instead of accepted.
- Added the JSONL journal and `--no-journal`.

## [0.1.0]

- First working bridge: encoder, 8-group mock backend, decoder, protocol, CLI.
- Dry-run by default; `--send` was not needed because the transport is only
  constructed when `--dry-run` is absent.
- 41 tests.
