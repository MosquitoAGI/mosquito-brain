# Validation

A record of what has been measured, including the parts that did not work. If a
number appears here it came out of a script in this repository, on synthetic
input, on the stated date.

## 1. Approach cue: flow expansion vs covered area

The first implementation of the looming channel used the mean radial component
of the optical flow, `mean(u·x/|r| + v·y/|r|)` over the field: the textbook
"expanding flow means approach" detector.

Measured on synthetic discs, 160x120, Farneback with the default parameters used
in `vision.py`:

| input | radial mean | flow divergence | covered-area delta |
|---|---|---|---|
| disc grows 12 px → 26 px | **-0.79** | -0.0000 | +1680 px |
| disc grows 12 px → 40 px | **-0.31** | -0.0000 | +4584 px |
| disc shrinks 26 px → 12 px | **+0.54** | -0.0000 | -1680 px |
| static | 0.00 | 0.0000 | 0 |
| moving and growing | -0.01 | 0.0000 | +1680 px |

The radial mean reports growth as receding. The divergence estimate is zero at
this resolution and cannot separate the cases either. The sign error survived
window sizes 7–21 and pyramid levels 1–5; on a 160x120 frame a 14 px growth is
mostly explained by intensity change rather than by translation, and Farneback
minimises brightness constancy, so the field it returns is dominated by that
change.

Conclusion: the looming channel reports the frame-to-frame change in covered area
instead — the fraction of pixels above the midpoint of the frame's own intensity
range, differenced against the previous frame. It has the right sign on the same
inputs, costs one comparison pass, and is trivially testable
(`tests/test_vision.py::test_growing_blob_reads_as_expansion`). It is a proxy and
it will report a change in exposure the same way it reports an approaching
object.

## 2. The connectome backend was silent on real input

First integration of the `connectome` backend with the real encoder (synthetic
camera, 300 frames, no telemetry): every frame produced `left=0.0 right=0.0`.
The weights had been sized against the hand-written sensory values used in the
unit tests (3.5–4.0), where the encoder's own readings over the same scene are
0.6–1.0 on average. No pool reached its firing threshold.

Measured, with the sensory drive scaled by a constant factor:

| input gain | spikes over 300 frames | mean left drive | mean right drive |
|---|---|---|---|
| 0.5 | 0 | 0.000 | 0.000 |
| 1.0 | 46 | 0.000 | 0.032 |
| 1.5 | 310 | 0.110 | 0.371 |
| 2.0 | 619 | 0.256 | 0.751 |
| 3.0 | 506 | 0.044 | 0.964 |

The default is `brain.input_gain: 1.5`: the pools track the scene instead of
staying quiet, and a strongly driven pool sits near the top of its range rather
than clipping at every frame. Two further changes came out of the same
integration: the readout is a 15-step sliding window (a session-long average
meant a pool that fired once early reported drive seconds later, and the command
never came back down), and the drive mapping has a floor and a ceiling instead
of a hard on/off threshold, which had made the commands bang between zero and
the cap. The regression test is
`tests/test_brain.py::test_connectome_tracks_real_encoder_input`, which runs the
synthetic camera through the encoder and fails if the network goes quiet again.

The left/right asymmetry visible in that table is the scene, not the network: the
raw frame-to-frame activity of the synthetic camera is 1.48x higher in the right
half over 300 frames (the blob's cycle was not symmetric at the time of the
measurement). The camera now sweeps one full cycle every 150 frames.

## 3. Escape threshold

The synthetic camera approaches once per 150-frame cycle, growing its blob by
70 px over the last ten frames. Measured approach cue over one cycle: peaks of
0.46–0.65, crossing 0.45 in the last four frames and 0.20 for eight frames. The
default `brain.escape_threshold` is therefore 0.45 — high enough that ordinary
motion in the scene (peaks of 0.14) never trips it, low enough that the
demonstrated approach does. Both the cue and the threshold are relative to this
scene; a real camera will need its own calibration run.

## 4. Loop timing

`time.sleep` in the main loop, 300 frames at a nominal 30 fps, one core of an
M-series laptop with the mock backend: a median of 33.4 ms between ticks, and a
99th percentile of 41 ms. The loop does not compensate for lateness, so a busy
machine runs slow. Anything that needs a stable rate should drive `Bridge.tick`
from a timer of its own — that is why time is a parameter.

## 5. Motor decoder behaviour

Checked in `tests/test_decoder.py` rather than by hand:

| property | expectation | test |
|---|---|---|
| full drive | maps to `max_command` exactly | `test_full_drive_maps_to_max_command` |
| dead zone | a target below it becomes 0 | `test_dead_zone_clamps_small_targets` |
| smoothing | first-order, factor `1-smoothing` | `test_smoothing_is_exponential` |
| escape | bypasses smoothing | `test_escape_bypasses_smoothing` |
| silence | zero after `command_timeout_ms` | `test_read_goes_stale_after_timeout` |
| recovery | `zero_now` does not latch the e-stop | `test_zero_now_does_not_latch` |

## 6. What is not validated

- No hardware. No camera. No video file from a real scene has been run through
  the encoder except by hand at the command line.
- The connectome backend's weights were tuned against the harness, not against
  any recording of a real animal.
- The UDP path has been exercised on loopback only.
