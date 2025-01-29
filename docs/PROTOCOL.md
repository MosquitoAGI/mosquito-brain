# Protocol

Two datagram types, both UTF-8 JSON objects, both under 512 bytes. No handshake,
no acknowledgement, no retry — UDP as the bench robot can implement it.

## Bridge → robot: `motor_command`

```json
{"type":"motor_command","sequence":42,"left":35,"right":28,"emergency_stop":false}
```

| field | type | rule |
|---|---|---|
| `type` | string | must be `motor_command` |
| `sequence` | int | 0 … 2147483647, strictly increasing |
| `left`, `right` | number | finite, within ±100, typical range ±60 |
| `emergency_stop` | bool | optional, default `false` |

The receiver must do two things with it: execute the speeds, and **stop the
motors if a fresh command has not arrived within 500 ms**. The second rule is not
optional — it is the only protection against the PC dying mid-run.

## Robot → bridge: `telemetry`

```json
{"type":"telemetry","sequence":42,"gyro":[0.12,0.0,-0.2],"accel":[0.0,0.1,0.98],
 "left_speed":34,"right_speed":27}
```

All six fields are required. `gyro` and `accel` are exactly three numbers each.
Telemetry drives exactly one decision on this side: fresh or stale. It never
feeds the control loop directly.

## Validation

Both sides validate strictly and reject rather than guess:

- invalid JSON, non-UTF8 bytes, or a payload larger than 512 bytes;
- a top-level value that is not an object, or an unknown `type`;
- missing required fields;
- booleans where numbers belong (`true` is not `1`);
- non-finite numbers (`NaN`, `Infinity`) and out-of-range speeds;
- sequence numbers that do not advance.

Extra keys are ignored, so a robot can add its own diagnostics without breaking
the bridge. Rejections are counted (`TelemetryState.rejected`) instead of raising:
a broken packet on the bench should not take the run down.

## Deliberate omissions

- **No authentication or encryption.** Anything on the bench network can send
  commands. Do not run this on a network you do not control.
- **No fragmentation or retransmission.** A command is one datagram or it is not
  a command.
- **No version field.** Version negotiation is a state machine, and this project
  would rather keep the failure mode obvious: add fields, never repurpose them.
