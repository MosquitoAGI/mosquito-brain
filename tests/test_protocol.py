import json
import math

import pytest

from fruitfly_brain.protocol import (
    MAX_PACKET,
    MAX_SEQUENCE,
    MotorCommand,
    ProtocolError,
    SequenceGate,
    Telemetry,
    encode_telemetry,
    parse_packet,
)


def test_command_roundtrip():
    payload = MotorCommand(left=35.0, right=-12.5, sequence=42).payload()
    parsed = parse_packet(payload)
    assert isinstance(parsed, MotorCommand)
    assert parsed.left == 35.0 and parsed.right == -12.5 and parsed.sequence == 42


def test_telemetry_roundtrip():
    t = Telemetry(gyro=(0.1, 0.0, -0.2), accel=(0.0, 0.1, 0.98), left_speed=34, right_speed=27, sequence=7)
    parsed = parse_packet(encode_telemetry(t))
    assert isinstance(parsed, Telemetry)
    assert parsed.gyro == pytest.approx((0.1, 0.0, -0.2))
    assert parsed.right_speed == 27
    assert parsed.is_moving() is True


def test_extra_keys_are_allowed():
    body = {"type": "motor_command", "sequence": 1, "left": 0, "right": 0, "note": "bench"}
    parsed = parse_packet(json.dumps(body).encode())
    assert parsed.sequence == 1


@pytest.mark.parametrize(
    "body",
    [
        {"type": "motor_command", "sequence": 1, "left": True, "right": 0},
        {"type": "motor_command", "sequence": True, "left": 0, "right": 0},
        {"type": "motor_command", "sequence": -1, "left": 0, "right": 0},
        {"type": "motor_command", "sequence": MAX_SEQUENCE + 1, "left": 0, "right": 0},
        {"type": "motor_command", "sequence": 1, "left": 0},
        {"type": "motor_command", "sequence": 1, "left": 0, "right": 101},
        {"type": "motor_command", "sequence": 1, "left": 0, "right": math.inf},
        {"type": "motor_command", "sequence": 1, "left": 0, "right": math.nan},
        {"type": "telemetry", "sequence": 1, "gyro": [0, 0], "accel": [0, 0, 1], "left_speed": 0, "right_speed": 0},
        {"type": "telemetry", "sequence": 1, "gyro": [0, 0, 0], "accel": [0, 0, "1"], "left_speed": 0, "right_speed": 0},
        {"type": "hello", "sequence": 1},
        {"type": None},
    ],
)
def test_invalid_packets_rejected(body):
    with pytest.raises(ProtocolError):
        parse_packet(json.dumps(body).encode())


def test_malformed_json_rejected():
    with pytest.raises(ProtocolError, match="invalid JSON"):
        parse_packet(b"{not json")


def test_non_utf8_rejected():
    with pytest.raises(ProtocolError):
        parse_packet(b'{"type":"motor_command","sequence":1,"left":0,"right":0,"x":"\xff"}')


def test_oversized_packet_rejected():
    big = b'{"type":"motor_command","sequence":1,"left":0,"right":0,"pad":"%s"}' % (b"x" * MAX_PACKET)
    with pytest.raises(ProtocolError, match="larger than"):
        parse_packet(big)


def test_non_object_rejected():
    with pytest.raises(ProtocolError, match="JSON object"):
        parse_packet(b"[1,2,3]")


def test_sequence_gate_requires_progress():
    gate = SequenceGate()
    assert gate.accept(1) is True
    assert gate.accept(1) is False
    assert gate.accept(0) is False
    assert gate.accept(2) is True
    assert gate.dropped == 2
    gate.reset()
    assert gate.accept(1) is True
