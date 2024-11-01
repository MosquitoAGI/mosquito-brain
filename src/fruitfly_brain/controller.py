"""The loop, with no clock of its own.

``Bridge.tick`` is a pure function of (frame, now_ms, inbound packets). That is
what makes the whole pipeline testable: a test can hand it a synthetic frame
and a timestamp and assert on the bytes that would go out. The real socket
lives behind the ``Transport`` interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from . import protocol
from .brain import make_brain
from .config import Config
from .decoder import Command, MotorDecoder
from .telemetry import TelemetryState
from .vision import Encoder, SensoryFrame


class Transport(Protocol):
    def send(self, payload: bytes) -> None: ...

    def poll(self) -> list[bytes]: ...


class NullTransport:
    """Keeps every packet in memory — used by tests and by ``--dry-run``."""

    def __init__(self) -> None:
        self.sent: list[bytes] = []
        self.inbox: list[bytes] = []

    def send(self, payload: bytes) -> None:
        self.sent.append(payload)

    def poll(self) -> list[bytes]:
        out, self.inbox = self.inbox, []
        return out


@dataclass
class TickResult:
    command: Command
    sensory: SensoryFrame
    escape: bool
    telemetry_stale: bool
    payload: bytes


class Bridge:
    def __init__(self, cfg: Config, transport: Transport | None = None):
        self.cfg = cfg.validate()
        self.transport = transport or NullTransport()
        self.encoder = Encoder(cfg.vision)
        self.brain = make_brain(cfg.brain.backend, cfg.brain)
        self.decoder = MotorDecoder(cfg.motor)
        self.telemetry = TelemetryState()
        self.gate = protocol.SequenceGate()
        self.sequence = 0
        self.frames = 0
        self.sent_stops = 0
        self.last_sensory = SensoryFrame(0.0, 0.0, 0.0, 0.5)
        self._last_ms: float | None = None

    # ------------------------------------------------------------------- input
    def ingest(self, now_ms: float) -> None:
        for raw in self.transport.poll():
            try:
                packet = protocol.parse_packet(raw)
            except protocol.ProtocolError:
                self.telemetry.reject()
                continue
            if not isinstance(packet, protocol.Telemetry):
                # A motor_command arriving here means something else is talking
                # on this port; count it and move on.
                self.telemetry.reject()
                continue
            if self.gate.accept(packet.sequence):
                self.telemetry.observe(packet, now_ms)

    # -------------------------------------------------------------------- tick
    def tick(self, frame: np.ndarray | None, now_ms: float) -> TickResult:
        dt_ms = 1000.0 / max(self.cfg.camera.fps, 1)
        if self._last_ms is not None:
            dt_ms = max(now_ms - self._last_ms, 1.0)
        self._last_ms = now_ms

        self.ingest(now_ms)

        if frame is None:
            sensory = self.last_sensory
        else:
            sensory = self.encoder.encode(frame)
            self.last_sensory = sensory
        out = self.brain.step(sensory, dt_ms)

        stale = self.telemetry.is_stale(now_ms, self.cfg.network.telemetry_timeout_ms)
        if stale:
            self.decoder.zero_now(now_ms)
            command = Command(0.0, 0.0, emergency_stop=True, stale=True, reason="telemetry-timeout")
            self.sent_stops += 1
        else:
            command = self.decoder.update(out.left, out.right, out.escape, now_ms)

        self.sequence = (self.sequence + 1) % (protocol.MAX_SEQUENCE + 1)
        payload = protocol.MotorCommand(
            left=command.left,
            right=command.right,
            sequence=self.sequence,
            emergency_stop=command.emergency_stop,
        ).payload()
        self.transport.send(payload)
        self.frames += 1
        return TickResult(command, sensory, out.escape, stale, payload)
