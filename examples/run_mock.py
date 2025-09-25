"""Run the whole pipeline against synthetic frames and print a summary.

    python examples/run_mock.py [--frames 120] [--brain connectome]

No camera, no robot, no sockets. The numbers printed here are the same numbers
the tests assert on, which is the point of keeping the loop free of I/O.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fruitfly_brain.config import Config  # noqa: E402
from fruitfly_brain.controller import Bridge, NullTransport  # noqa: E402
from fruitfly_brain.main import MockCamera  # noqa: E402
from fruitfly_brain.protocol import Telemetry, encode_telemetry, parse_packet  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=120)
    parser.add_argument("--brain", default="mock", choices=("mock", "connectome"))
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args(argv)

    cfg = Config().validate()
    cfg.brain.backend = args.brain
    cfg.camera.fps = args.fps

    camera = MockCamera(cfg.camera.width, cfg.camera.height)
    transport = NullTransport()
    bridge = Bridge(cfg, transport)

    rows = []
    escapes = 0
    stops = 0
    for i in range(args.frames):
        # A synthetic IMU: the robot reports a slow oscillation, so the stop
        # rule stays quiet unless we deliberately starve it.
        transport.inbox.append(
            encode_telemetry(
                Telemetry(
                    sequence=i + 1,
                    gyro=(0.2 * (i % 10 - 5) / 5.0, 0.0, 0.1),
                    accel=(0.0, 0.0, 0.98),
                    left_speed=20.0,
                    right_speed=20.0,
                )
            )
        )
        result = bridge.tick(camera.read(), i * (1000.0 / args.fps))
        row = parse_packet(result.payload)
        rows.append((i, result, row))
        escapes += 1 if result.escape else 0
        stops += 1 if result.telemetry_stale else 0

    print("fruitfly-brain mock run — backend=%s frames=%d" % (args.brain, args.frames))
    print("%6s %10s %10s %8s %8s %8s" % ("frame", "left", "right", "sensoryL", "sensoryR", "loom"))
    for i, result, row in rows[:: max(args.frames // 10, 1)]:
        s = result.sensory
        print("%6d %10.2f %10.2f %8.2f %8.2f %8.2f" % (i, row.left, row.right, s.left, s.right, s.expansion))

    tail = rows[-1][2]
    print()
    print("last command : left=%.2f right=%.2f sequence=%d" % (tail.left, tail.right, tail.sequence))
    print("escapes      : %d" % escapes)
    print("stale stops  : %d" % stops)
    print("packets sent : %d" % len(transport.sent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
