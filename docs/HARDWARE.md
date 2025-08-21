# Hardware notes

Nothing in this repository has been flashed, wired or driven. This file lists
what the scaffold expects, so the first person to try it knows where the bodies
are buried.

## The PC side

Any machine that runs Python 3.11+ with a camera and a route to the robot's
network. Two sockets are used:

- outbound: `network.robot_host`:`network.robot_port` (default `192.168.4.1:9000`)
- inbound: `0.0.0.0`:`network.bind_port` (default `9001`)

If the robot is an ESP32 in AP mode the PC must join its network. Camera and
WiFi on the same interface is fine; camera over USB and WiFi for the robot is
better, because the camera's USB bus does not compete with the radio.

## The robot side

`firmware/esp32_hbridge/` is an ESP32 scaffold with:

- a UDP listener on the configured port,
- the same strict validation as this side (payload size, JSON, ranges, sequence),
- a 500 ms watchdog that zeroes both channels when commands stop arriving,
- `TODO` stubs where `setMotorSpeed()` and `readIMU()` belong.

Required before the first powered test:

1. Implement `setMotorSpeed(channel, value)` for your driver board, and clamp
   the input to what the hardware accepts.
2. Confirm the watchdog cuts the motors with the wheels off the ground.
3. Implement `readIMU()` and `sendTelemetry()` at 20 Hz.
4. Check the sign convention: positive `left` must move the left side forward.
   Use `motor.invert_left` / `motor.invert_right` on this side if it does not.
5. Start with `motor.max_command: 20` and raise it only after a full run at that
   limit behaves.

## Power

A stalled motor browns out an ESP32 on the same regulator. Give the motors their
own supply and connect grounds; if the board resets when the wheels stall, the
watchdog saved you and the supply is the problem.

## What has been verified

Synthetic frames, a `NullTransport`, and a socket loopback test on the PC side.
Nothing on hardware. Treat every statement in this file as an intention.
