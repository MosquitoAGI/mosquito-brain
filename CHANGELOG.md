# Changelog

All notable changes to this project are recorded here.

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
