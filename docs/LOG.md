# Build log

Short dated notes from the bench, oldest first. Not a changelog —
[CHANGELOG.md](../CHANGELOG.md) has releases; this file has days. Quiet weeks
have no line, which is most weeks.

- 2024-09-30 — first synthetic sweep on the desk. the right half reads low; suspect the test scene, not the maths.
- 2024-11-01 — the mock backend is eight leaky groups and one confused developer. it demonstrates the wiring, nothing else.
- 2024-11-11 — spent the morning chasing a flaky usb cable. it was the cable. it is always the cable.
- 2024-11-25 — first end-to-end run: frame to drives in a few milliseconds per tick on this laptop. dry-run kept an actual robot from moving by accident today.
- 2024-11-25 — wrote the malformed-packet cases first this time. better day than last week.
- 2024-12-07 — read three other optical-flow encoders tonight; all of them blur more than mine and none of them say why. keeping mine.
- 2024-12-18 — the screenshot folder for this project is now 400 images. future me will thank present me, or not.
- 2024-12-29 — spent an evening tuning the synthetic scene instead of the encoder; the scene was the bug all along.
- 2025-01-10 — the dead-zone test failed by one hundredth of a unit; the test was wrong, not the code.
- 2025-01-20 — quiet week: no code, just reading the protocol doc until it made sense. it needed two fixes.
- 2025-02-18 — measured the tick budget honestly today: encoder dominates, backend is cheap, the decoder is noise. optimise accordingly.
- 2025-03-02 — renamed three variables in the decoder. the diff is ugly and the code is clearer.
- 2025-03-15 — cut 0.1.0. it runs on my desk; that is the whole acceptance test.
- 2025-03-27 — added an assert that fired within ten minutes. best kind of test.
- 2025-05-08 — started a ledger of every packet the robot refused. two lines so far, both my fault.
- 2025-05-22 — thought about failure modes on the walk home: cable, process, power. each needs its own stop. wrote it down.
- 2025-06-05 — hunted for a fixture for the encoder tests; ended up generating frames from a formula instead. faster and reproducible.
- 2025-06-19 — the board idles at 11 mA with the radio up. fine for the bench, noted for the battery build.
- 2025-07-03 — spike counts drift when the camera exposure changes. noted in the validation notes; the gain is not the fix.
- 2025-07-17 — week of small diffs: naming, comments, one constant. nothing to see, everything to keep.
- 2025-08-12 — the watchdog question: stop, or keep the last command? stop. always stop. no debate after today.
- 2025-08-13 — telemetry at 30 Hz is fine; at 120 Hz the laptop fans spin up. 30 it is.
- 2025-09-02 — the harness moved to the drawer and the stand came out. cable management is a feature.
- 2025-09-15 — first day with the board on the desk: nothing flashed, but the pin map is agreed and the motor hooks are honest TODO stubs.
