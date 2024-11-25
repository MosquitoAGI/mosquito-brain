"""Wire format.

One UTF-8 JSON object per UDP datagram, in both directions. Validation is
strict on the way in and boring on the way out: unknown types, missing fields,
invalid JSON, booleans where numbers belong, non-finite values and oversized
packets are all rejected rather than guessed at.

    {"type":"motor_command","sequence":42,"left":35,"right":28,"emergency_stop":false}
    {"type":"telemetry","sequence":42,"gyro":[0.1,0,-0.2],"accel":[0,0.1,0.98],
     "left_speed":34,"right_speed":27}
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

MAX_SEQUENCE = 2_147_483_647
MAX_PACKET = 512
SPEED_LIMIT = 100.0


class ProtocolError(ValueError):
    """Raised for any packet that does not match the wire format."""


def _number(value: Any, name: str, limit: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProtocolError("%s must be a number" % name)
    value = float(value)
    if not math.isfinite(value):
        raise ProtocolError("%s must be finite" % name)
    if limit is not None and abs(value) > limit:
        raise ProtocolError("%s must be within +-%g" % (name, limit))
    return value


def _sequence(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ProtocolError("sequence must be an integer")
    if not 0 <= value <= MAX_SEQUENCE:
        raise ProtocolError("sequence must be in 0..%d" % MAX_SEQUENCE)
    return value


def _vector(value: Any, name: str) -> tuple[float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ProtocolError("%s must be a list of three numbers" % name)
    return tuple(_number(v, "%s[%d]" % (name, i)) for i, v in enumerate(value))  # type: ignore[return-value]


@dataclass
class MotorCommand:
    left: float
    right: float
    sequence: int = 0
    emergency_stop: bool = False

    def payload(self) -> bytes:
        body = {
            "type": "motor_command",
            "sequence": _sequence(self.sequence),
            "left": round(_number(self.left, "left", SPEED_LIMIT), 3),
            "right": round(_number(self.right, "right", SPEED_LIMIT), 3),
            "emergency_stop": bool(self.emergency_stop),
        }
        return json.dumps(body, separators=(",", ":")).encode("utf-8")


@dataclass
class Telemetry:
    gyro: tuple[float, float, float] = (0.0, 0.0, 0.0)
    accel: tuple[float, float, float] = (0.0, 0.0, 1.0)
    left_speed: float = 0.0
    right_speed: float = 0.0
    sequence: int = 0

    def is_moving(self, threshold: float = 1.0) -> bool:
        return abs(self.left_speed) > threshold or abs(self.right_speed) > threshold


def encode_telemetry(t: Telemetry) -> bytes:
    body = {
        "type": "telemetry",
        "sequence": _sequence(t.sequence),
        "gyro": [round(float(v), 4) for v in _vector(list(t.gyro), "gyro")],
        "accel": [round(float(v), 4) for v in _vector(list(t.accel), "accel")],
        "left_speed": round(_number(t.left_speed, "left_speed", SPEED_LIMIT), 3),
        "right_speed": round(_number(t.right_speed, "right_speed", SPEED_LIMIT), 3),
    }
    return json.dumps(body, separators=(",", ":")).encode("utf-8")


def parse_packet(data: bytes) -> MotorCommand | Telemetry:
    """Parse and validate one datagram."""
    if not isinstance(data, (bytes, bytearray)):
        raise ProtocolError("packet must be bytes")
    if len(data) > MAX_PACKET:
        raise ProtocolError("packet larger than %d bytes" % MAX_PACKET)
    try:
        body = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("invalid JSON: %s" % exc) from exc
    if not isinstance(body, dict):
        raise ProtocolError("packet must be a JSON object")
    kind = body.get("type")
    if kind == "motor_command":
        for key in ("left", "right", "sequence"):
            if key not in body:
                raise ProtocolError("motor_command is missing %r" % key)
        return MotorCommand(
            left=_number(body["left"], "left", SPEED_LIMIT),
            right=_number(body["right"], "right", SPEED_LIMIT),
            sequence=_sequence(body["sequence"]),
            emergency_stop=bool(body.get("emergency_stop", False)),
        )
    if kind == "telemetry":
        for key in ("sequence", "gyro", "accel", "left_speed", "right_speed"):
            if key not in body:
                raise ProtocolError("telemetry is missing %r" % key)
        return Telemetry(
            gyro=_vector(body["gyro"], "gyro"),
            accel=_vector(body["accel"], "accel"),
            left_speed=_number(body["left_speed"], "left_speed", SPEED_LIMIT),
            right_speed=_number(body["right_speed"], "right_speed", SPEED_LIMIT),
            sequence=_sequence(body["sequence"]),
        )
    raise ProtocolError("unknown packet type: %r" % (kind,))


class SequenceGate:
    """Drop packets whose sequence did not advance.

    Both sides share this rule, and both sides reset it when they restart. It
    protects against duplicates on a lossy bench, not against an attacker.
    """

    def __init__(self) -> None:
        self._last = -1
        self.dropped = 0

    def accept(self, sequence: int) -> bool:
        if sequence <= self._last:
            self.dropped += 1
            return False
        self._last = sequence
        return True

    def reset(self) -> None:
        self._last = -1
