"""Command line entry point.

    fruitfly-brain --config config.yaml --source mock --frames 600
    fruitfly-brain --source webcam --brain connectome --dry-run
    fruitfly-brain --print-config

``--source mock`` synthesises a moving blob so the whole pipeline can be
exercised without a camera and without a robot. Nothing in this module decides
anything about control; it only wires clock, camera and socket together.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from . import __version__
from .config import Config, ConfigError, load
from .controller import Bridge
from .journal import Journal

SOURCES = ("mock", "webcam", "video")


class MockCamera:
    """A deterministic synthetic scene.

    One full sweep every ``PERIOD`` frames (five seconds at 30 fps): the blob
    starts in the centre, drifts right, comes back, and grows during the last
    20% of each cycle — an approach event that ends when the cycle restarts.
    The cycle length is fixed so that a 150-frame run contains exactly one
    sweep, which is what makes the demo animation balanced and the tests stable.
    """

    PERIOD = 150

    def __init__(self, width: int = 320, height: int = 240):
        self.width = width
        self.height = height
        self.i = 0

    def read(self) -> np.ndarray:
        frame = np.zeros((self.height, self.width), dtype=np.uint8)
        phase = 2.0 * np.pi * (self.i % self.PERIOD) / self.PERIOD
        cx = int(self.width * (0.5 + 0.36 * np.sin(phase)))
        cy = int(self.height * 0.5)
        radius = 24 + int(6 * np.sin(2 * phase))
        progress = (self.i % self.PERIOD) / self.PERIOD
        if progress > 0.933:  # approach: fast growth over the last ten frames
            radius += int(70 * (progress - 0.933) / 0.067)
        yy, xx = np.ogrid[: self.height, : self.width]
        mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius**2
        frame[mask] = 220
        self.i += 1
        return frame


class VideoCamera:
    def __init__(self, source: str, width: int, height: int):
        try:
            import cv2
        except ImportError as exc:  # pragma: no cover
            raise SystemExit("OpenCV is required for --source video/webcam") from exc
        self.cap = cv2.VideoCapture(int(source) if source.isdigit() else source)
        if not self.cap.isOpened():
            raise SystemExit("could not open video source: %s" % source)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def read(self) -> np.ndarray | None:
        ok, frame = self.cap.read()
        return frame if ok else None

    def close(self) -> None:
        self.cap.release()


class UdpTransport:
    """The real thing: two sockets, no handshake, no retries."""

    def __init__(self, host: str, robot_port: int, bind_port: int):
        import socket

        self.robot = (host, robot_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", bind_port))
        self.sock.setblocking(False)

    def send(self, payload: bytes) -> None:
        self.sock.sendto(payload, self.robot)

    def poll(self) -> list[bytes]:
        out = []
        while True:
            try:
                data, addr = self.sock.recvfrom(2048)
            except BlockingIOError:
                return out
            except OSError:
                return out
            out.append(data)

    def close(self) -> None:
        self.sock.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fruitfly-brain", description=__doc__)
    p.add_argument("--config", type=Path, help="path to config.yaml")
    p.add_argument("--source", default="mock", choices=SOURCES)
    p.add_argument("--video", help="file or device index for --source video")
    p.add_argument("--brain", choices=("mock", "connectome"))
    p.add_argument("--frames", type=int, default=300, help="0 = run until interrupted")
    p.add_argument("--fps", type=float)
    p.add_argument("--dry-run", action="store_true", help="print packets instead of sending")
    p.add_argument("--print-config", action="store_true")
    p.add_argument("--no-journal", action="store_true")
    p.add_argument("--version", action="version", version="fruitfly-brain %s" % __version__)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cfg = load(args.config) if args.config else Config().validate()
    except ConfigError as exc:
        print("config error: %s" % exc, file=sys.stderr)
        return 2

    if args.brain:
        cfg.brain.backend = args.brain
    if args.fps:
        cfg.camera.fps = int(args.fps)

    if args.print_config:
        print(json.dumps(cfg.to_dict(), indent=2))
        return 0

    camera = MockCamera(cfg.camera.width, cfg.camera.height) if args.source == "mock" else None
    if args.source in ("webcam", "video"):
        camera = VideoCamera(args.video or ("0" if args.source == "webcam" else ""), cfg.camera.width, cfg.camera.height)

    transport = None
    if not args.dry_run:
        transport = UdpTransport(cfg.network.robot_host, cfg.network.robot_port, cfg.network.bind_port)

    bridge = Bridge(cfg, transport)
    journal = Journal(cfg.log.dir, enabled=cfg.log.jsonl and not args.no_journal, every_n=cfg.log.every_n_frames)
    print(
        "fruitfly-brain %s | source=%s brain=%s dry_run=%s telemetry=%s"
        % (__version__, args.source, cfg.brain.backend, args.dry_run, cfg.network.robot_host)
    )

    period = 1.0 / max(cfg.camera.fps, 1)
    start = time.monotonic()
    target = args.frames
    frame_no = 0
    stops = 0
    try:
        while target == 0 or frame_no < target:
            loop_start = time.monotonic()
            now_ms = (loop_start - start) * 1000.0
            frame = camera.read() if camera is not None else None
            result = bridge.tick(frame, now_ms)
            if result.telemetry_stale:
                stops += 1
            journal.write(
                frame_no,
                "stop" if result.telemetry_stale else "tick",
                left=round(result.command.left, 2),
                right=round(result.command.right, 2),
                escape=result.escape,
                stale=result.telemetry_stale,
            )
            if args.dry_run and frame_no % max(cfg.log.every_n_frames, 1) == 0:
                print("frame %5d  %s" % (frame_no, result.payload.decode()))
            frame_no += 1
            slack = period - (time.monotonic() - loop_start)
            if slack > 0:
                time.sleep(slack)
    except KeyboardInterrupt:
        print("\ninterrupted after %d frames" % frame_no)
    finally:
        bridge.decoder.emergency_stop()
        final = bridge.decoder.read(0.0)
        if not args.dry_run:
            from .protocol import MotorCommand

            bridge.transport.send(MotorCommand(0.0, 0.0, bridge.sequence, True).payload())
        journal.write(frame_no, "shutdown", left=final.left, right=final.right)
        journal.close()
        if camera is not None and hasattr(camera, "close"):
            camera.close()
        if transport is not None:
            transport.close()

    elapsed = max(time.monotonic() - start, 1e-6)
    print(
        "done: %d frames in %.1fs (%.1f fps), sent_stops=%d, journal=%s"
        % (frame_no, elapsed, frame_no / elapsed, stops, journal.path if journal.path else "off")
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
