# ESP32 bridge scaffold (disarmed)

This is a scaffold, not firmware. It receives commands, validates them exactly
like the Python side does, and zeroes both channels when they stop arriving.
It does not move anything, because the two functions that would are `TODO`.

## Wiring it up

1. Implement `setMotorSpeed(channel, value)` for your driver board.
2. Implement `readIMU()` and `sendTelemetry()` (target 20 Hz).
3. Set `WIFI_SSID` / `WIFI_PASS` and, if you change it on the PC side, the port.
4. Verify that the watchdog cuts both channels with the wheels off the ground
   before you put the robot down.
5. Start at `motor.max_command: 20` on the PC side and raise it slowly.

## What is finished

- The UDP listener and the validation rules (length, JSON, ranges, sequence).
- The 500 ms watchdog and its "stale command" counter.
- The trip count, so a bench session can tell how often the watchdog fired.

## What is not

- Motor output, IMU reads, WiFi credentials — all stubs.
- No hardware test has been performed. See `docs/HARDWARE.md`.

## Rules worth keeping

- **The watchdog stays.** Even if you rewrite everything else, an independent
  "no command for 500 ms means stop" belongs on the microcontroller, not in the
  script that might be the thing that hung.
- **Validate before acting.** Check the payload size before parsing, check the
  ranges before moving. `parseFloat` on garbage returns 0.0, which is a command
  to stop — convenient here, dangerous in general.
