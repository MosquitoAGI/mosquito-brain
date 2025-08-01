import numpy as np

from fruitfly_brain.config import Config
from fruitfly_brain.controller import Bridge, NullTransport
from fruitfly_brain.protocol import Telemetry, encode_telemetry, parse_packet
from fruitfly_brain.telemetry import TelemetryState


def frame(cx):
    f = np.zeros((120, 160), dtype=np.uint8)
    yy, xx = np.ogrid[:120, :160]
    f[(xx - cx) ** 2 + (yy - 60) ** 2 <= 12**2] = 255
    return f


def test_bridge_stops_when_telemetry_is_missing():
    cfg = Config().validate()
    transport = NullTransport()
    bridge = Bridge(cfg, transport)
    result = bridge.tick(frame(40), 0.0)
    assert result.telemetry_stale is True
    assert result.command.emergency_stop is True
    assert bridge.sent_stops == 1
    parsed = parse_packet(transport.sent[-1])
    assert parsed.left == 0.0 and parsed.emergency_stop is True


def test_bridge_tracks_when_telemetry_arrives():
    cfg = Config().validate()
    transport = NullTransport()
    bridge = Bridge(cfg, transport)
    for i in range(6):
        transport.inbox.append(encode_telemetry(Telemetry(sequence=i + 1, left_speed=i, right_speed=i)))
        bridge.tick(frame(30 + i * 8), i * 33.0)
    assert bridge.telemetry.received == 6
    assert bridge.telemetry.rejected == 0
    last = parse_packet(transport.sent[-1])
    assert last.emergency_stop is False
    assert bridge.sent_stops == 0


def test_sequence_regression_is_ignored():
    cfg = Config().validate()
    transport = NullTransport()
    bridge = Bridge(cfg, transport)
    transport.inbox.append(encode_telemetry(Telemetry(sequence=5)))
    bridge.tick(frame(40), 0.0)
    transport.inbox.append(encode_telemetry(Telemetry(sequence=5)))
    bridge.tick(frame(48), 33.0)
    assert bridge.telemetry.received == 1
    assert bridge.gate.dropped == 1


def test_bridge_recovers_after_a_gap():
    cfg = Config().validate()
    transport = NullTransport()
    bridge = Bridge(cfg, transport)
    transport.inbox.append(encode_telemetry(Telemetry(sequence=1)))
    bridge.tick(frame(40), 0.0)
    bridge.tick(frame(48), 33.0)  # still fresh
    stale = bridge.tick(frame(56), 2000.0)
    assert stale.telemetry_stale is True
    transport.inbox.append(encode_telemetry(Telemetry(sequence=2)))
    fresh = bridge.tick(frame(64), 2030.0)
    assert fresh.telemetry_stale is False
    assert fresh.command.emergency_stop is False


def test_bad_packets_are_counted_not_fatal():
    cfg = Config().validate()
    transport = NullTransport()
    bridge = Bridge(cfg, transport)
    transport.inbox.append(b"garbage")
    transport.inbox.append(b'{"type":"motor_command","sequence":1,"left":0,"right":0}')
    bridge.tick(frame(40), 0.0)
    assert bridge.telemetry.rejected == 2


def test_sequence_numbers_advance_and_wrap():
    cfg = Config().validate()
    transport = NullTransport()
    bridge = Bridge(cfg, transport)
    for i in range(4):
        transport.inbox.append(encode_telemetry(Telemetry(sequence=i + 1)))
        bridge.tick(frame(40 + i), i * 33.0)
    seqs = [parse_packet(p).sequence for p in transport.sent]
    assert seqs == [1, 2, 3, 4]


def test_telemetry_state_helpers():
    state = TelemetryState()
    assert state.is_stale(0.0, 400.0) is True
    state.observe(Telemetry(left_speed=3), 100.0)
    assert state.is_stale(300.0, 400.0) is False
    assert state.is_stale(600.0, 400.0) is True
    assert state.age_ms(300.0) == 200.0
    assert "telemetry" in state.summary()
