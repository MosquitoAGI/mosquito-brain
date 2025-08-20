# Architecture

Four moving parts and one rule.

```text
                 ┌──────────────┐
   camera ──────►│   Encoder    │  left / right / expansion / luminance
   (or mock)     └──────┬───────┘
                        │ SensoryFrame
                        ▼
                 ┌──────────────┐
                 │ BrainBackend │  left drive / right drive / escape
                 └──────┬───────┘
                        │ BrainOutput
                        ▼
                 ┌──────────────┐
                 │ MotorDecoder │  limits, dead zone, smoothing, inversion
                 └──────┬───────┘
                        │ Command
                        ▼
                 ┌──────────────┐        UDP         ┌────────┐
                 │   Transport  │ ─────────────────► │ robot  │
                 └──────▲───────┘ ◄───────────────── └────────┘
                        │            telemetry
                 ┌──────┴───────┐
                 │TelemetryState│  fresh? stale? -> stop rule
                 └──────────────┘
```

## The five pieces

**Encoder** (`vision.py`). Resizes to 160x120, blurs, estimates dense flow with
Farneback, and reports the mean flow magnitude in each half of the field. The
approach cue is the frame-to-frame change in *covered area* — the fraction of
pixels above the midpoint of the frame's own intensity range. It is a proxy, and
`docs/VALIDATION.md` explains why the flow-based version was rejected.

**BrainBackend** (`brain/`). Two implementations behind one interface:

| backend | state | outputs | notes |
|---|---|---|---|
| `mock` | 8 leaky groups | 2 drives + escape | default; smooth, easy to reason about |
| `connectome` | 26 LIF neurons | 2 drives + escape | fixed weights, deterministic, no RNG in the loop |

Both are stepped once per frame and return drives in `0..1`. Neither touches a
clock or a socket.

**MotorDecoder** (`decoder.py`). Scales a drive to `max_command`, applies a dead
zone, smooths toward the target, applies per-side inversion. An escape request
bypasses smoothing — it is a brake, not a suggestion. `zero_now()` empties the
smoother without latching the emergency stop, so the loop recovers by itself
when telemetry comes back.

**Transport / TelemetryState** (`controller.py`, `telemetry.py`). The bridge
never opens a socket itself; it writes to a `Transport` and polls it. That is
what makes the whole loop testable and what makes `NullTransport` a real
implementation rather than a mocking trick.

**Bridge** (`controller.py`). `Bridge.tick(frame, now_ms)` runs: ingest →
encode → step → shape → send. Time is an argument, so a five-minute scenario runs
in a test in microseconds.

## The rule

```
if telemetry is missing, or older than network.telemetry_timeout_ms:
    command = (0, 0), emergency flag set, decoder emptied
else:
    command = decoder.update(brain_output)
```

Both sides implement it independently. See `docs/PROTOCOL.md` for the wire
format and the reasons the format is deliberately boring.

## Why the backends are small

A backend that cannot be read in one sitting cannot be debugged at a bench. Both
implementations are sized to fit in `brain/` in under 150 lines each, with the
weights and the state written out literally:

- the mock's eight groups are named in `mock.py` and nothing is hidden;
- the connectome's 35 connections are a tuple of `(pre, post, weight)` rows at
  the top of `connectome.py`.

The numbers come from tuning the harness, not from a recording. They are meant
to move a robot plausibly and to be easy to change when the robot says otherwise.
